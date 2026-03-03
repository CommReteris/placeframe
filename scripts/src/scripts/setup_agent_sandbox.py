import getpass
import shlex
import shutil
import sys
import tempfile
from pathlib import Path
from subprocess import CalledProcessError

import typer
from common.run_command import check_command, run_command

INCUS_PRESEED = """\
config: {}
networks:
- config:
    ipv4.address: 10.250.250.1/24
    ipv4.nat: "true"
    ipv6.address: none
  name: incusbr0
  type: bridge
storage_pools:
- name: default
  driver: btrfs
  config:
    size: 50GiB
profiles:
- name: default
  devices:
    eth0:
      name: eth0
      network: incusbr0
      type: nic
    root:
      path: /
      pool: default
      type: disk
"""

COI_REPO_URL = "https://github.com/mensfeld/code-on-incus.git"
COI_REPO_DIR = Path("/opt/code-on-incus")
COI_BINARY_URL = "https://github.com/mensfeld/code-on-incus/releases/latest/download/coi-linux-amd64"
PLACEFRAME_IMAGE = "coi-placeframe"

app = typer.Typer(add_completion=False)


@app.command()
def setup_agent_sandbox(
    rebuild: bool = typer.Option(False, "--rebuild", help="Delete and rebuild the coi-placeframe image"),
) -> None:
    print("Provisioning COI (code-on-incus) on Ubuntu")

    # Host dependencies
    print("Installing host dependencies...")
    run_command("sudo apt update", stream_log=True)
    run_command("sudo apt install -y ca-certificates curl git firewalld btrfs-progs uidmap", stream_log=True)

    # Firewalld
    print("Configuring firewalld...")
    check_command("sudo ufw disable")
    run_command("sudo systemctl enable --now firewalld")
    run_command(
        "sudo tee /etc/sudoers.d/coi-firewalld",
        stdin_text=f"{getpass.getuser()} ALL=(root) NOPASSWD: /usr/bin/firewall-cmd\n",
    )
    run_command("sudo chmod 440 /etc/sudoers.d/coi-firewalld")
    run_command("sudo visudo -cf /etc/sudoers.d/coi-firewalld")
    check_command("sudo firewall-cmd --permanent --new-zone=incus")

    # Subuid/subgid mappings
    for path in [Path("/etc/subuid"), Path("/etc/subgid")]:
        content = path.read_text() if path.exists() else ""
        if not any(line.startswith("root:") for line in content.splitlines()):
            print(f"Adding root mapping to {path}")
            run_command(f"sudo tee -a {path}", stdin_text="root:100000:65536\n")

    # Incus
    if not shutil.which("incus"):
        print("Installing Incus from Zabbly repo...")
        run_command("sudo mkdir -p /etc/apt/keyrings")
        run_command("sudo curl -fsSL https://pkgs.zabbly.com/key.asc -o /etc/apt/keyrings/zabbly.asc")
        codename = run_command("lsb_release -cs").strip()
        repo_line = f"deb [signed-by=/etc/apt/keyrings/zabbly.asc] https://pkgs.zabbly.com/incus/stable {codename} main"
        run_command("sudo tee /etc/apt/sources.list.d/zabbly.list", stdin_text=repo_line + "\n")
        run_command("sudo apt update", stream_log=True)
        run_command("sudo apt install -y incus", stream_log=True)

    username = getpass.getuser()
    run_command(f"sudo usermod -aG incus-admin {username}")
    if "incus-admin" not in run_command("id -nG").strip().split():
        print(f"Added {username} to incus-admin. Open a NEW terminal and re-run this script.")
        sys.exit(0)

    # Initialize Incus storage
    if "default" not in run_command("incus storage list"):
        print("Initializing Incus with preseed...")
        run_command("incus admin init --preseed", stdin_text=INCUS_PRESEED)

    # Firewall rules for incusbr0
    if check_command("incus network show incusbr0"):
        print("Configuring firewall rules for incusbr0...")
        for rule in [
            "--add-interface=incusbr0",
            "--set-target=ACCEPT",
            "--add-service=dhcp",
            "--add-service=dns",
            "--add-masquerade",
        ]:
            check_command(f"sudo firewall-cmd --permanent --zone=incus {rule}")
        check_command("sudo firewall-cmd --reload")

    # GPU passthrough
    if "gpu:" not in run_command("incus profile device show default"):
        print("Adding GPU passthrough to default profile...")
        check_command("incus profile device add default gpu gpu")

    # COI binary
    print("Installing COI binary...")
    with tempfile.NamedTemporaryFile(delete=False) as temporary_file:
        temporary_path = temporary_file.name
    run_command(f"curl -fsSL -o {temporary_path} {COI_BINARY_URL}")
    run_command(f"chmod +x {temporary_path}")
    run_command(f"sudo mv {temporary_path} /usr/local/bin/coi")

    # COI repo (needed because build scripts aren't embedded in the binary yet)
    # Upstream: https://github.com/mensfeld/code-on-incus/issues/50
    # Tracking: agent/tickets/T57.md
    if not COI_REPO_DIR.exists():
        print("Cloning COI repo...")
        run_command(f"sudo git clone --depth 1 {COI_REPO_URL} {COI_REPO_DIR}", stream_log=True)
    else:
        print("Updating COI repo...")
        run_command(f"sudo git -C {COI_REPO_DIR} pull --ff-only", stream_log=True)

    # Base COI image
    if not check_command("incus image info coi"):
        print("Building base COI image...")
        run_command("coi build", cwd=COI_REPO_DIR, stream_log=True)

    # Placeframe image
    if rebuild:
        print(f"Removing existing {PLACEFRAME_IMAGE} image (--rebuild)...")
        check_command(f"incus image delete {PLACEFRAME_IMAGE}")
    if not check_command(f"incus image info {PLACEFRAME_IMAGE}"):
        build_script = Path(__file__).resolve().parents[3] / "agent" / "coi-placeframe-build.sh"
        print(f"Building {PLACEFRAME_IMAGE} image...")
        run_command(f"coi build custom {PLACEFRAME_IMAGE} --script {build_script}", cwd=COI_REPO_DIR, stream_log=True)
        print(f"{PLACEFRAME_IMAGE} image published.")

    # COI config
    config_directory = Path.home() / ".config" / "coi"
    config_directory.mkdir(parents=True, exist_ok=True)
    (config_directory / "config.toml").write_text(f'[defaults]\npersistent = true\nimage = "{PLACEFRAME_IMAGE}"\n')

    # Git identity in Incus profile
    try:
        name = run_command("git config user.name").strip()
        email = run_command("git config user.email").strip()
    except CalledProcessError:
        name = ""
        email = ""

    if name and email:
        for variable in ["GIT_AUTHOR_NAME", "GIT_COMMITTER_NAME"]:
            run_command(f"incus profile set default environment.{variable}={shlex.quote(name)}")
        for variable in ["GIT_AUTHOR_EMAIL", "GIT_COMMITTER_EMAIL"]:
            run_command(f"incus profile set default environment.{variable}={shlex.quote(email)}")
        print(f"Git identity set in Incus default profile: {name} <{email}>")
    else:
        print("WARNING: Could not read git user.name/user.email from host. Set them and re-run, or set manually:")
        print("  incus profile set default environment.GIT_AUTHOR_NAME='Your Name'")
        print("  incus profile set default environment.GIT_AUTHOR_EMAIL='you@example.com'")
        print("  incus profile set default environment.GIT_COMMITTER_NAME='Your Name'")
        print("  incus profile set default environment.GIT_COMMITTER_EMAIL='you@example.com'")

    # UV project environment
    run_command('incus profile set default environment.UV_PROJECT_ENVIRONMENT="/home/code/.venvs/placeframe"')

    print("Done.")
    print("Run: uv run agent-shell")


def main() -> None:
    app()


if __name__ == "__main__":
    main()
