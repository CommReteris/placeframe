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


def install_host_dependencies() -> None:
    print("Installing host dependencies...")
    run_command("sudo apt update", stream_log=True)
    run_command("sudo apt install -y ca-certificates curl git firewalld btrfs-progs uidmap", stream_log=True)


def configure_firewalld() -> None:
    print("Configuring firewalld...")
    check_command("sudo ufw disable")
    run_command("sudo systemctl enable --now firewalld")

    username = getpass.getuser()
    sudoers_content = f"{username} ALL=(root) NOPASSWD: /usr/bin/firewall-cmd\n"
    run_command("sudo tee /etc/sudoers.d/coi-firewalld", stdin_text=sudoers_content)
    run_command("sudo chmod 440 /etc/sudoers.d/coi-firewalld")
    run_command("sudo visudo -cf /etc/sudoers.d/coi-firewalld")

    check_command("sudo firewall-cmd --permanent --new-zone=incus")


def ensure_subuid_subgid() -> None:
    for path in [Path("/etc/subuid"), Path("/etc/subgid")]:
        content = path.read_text() if path.exists() else ""
        if not any(line.startswith("root:") for line in content.splitlines()):
            print(f"Adding root mapping to {path}")
            run_command(f"sudo tee -a {path}", stdin_text="root:100000:65536\n")


def install_incus() -> None:
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

    groups = run_command("id -nG").strip().split()
    if "incus-admin" not in groups:
        print(f"Added {username} to incus-admin. Open a NEW terminal and re-run this script.")
        sys.exit(0)


def initialize_incus() -> None:
    output = run_command("incus storage list")
    if "default" not in output:
        print("Initializing Incus with preseed...")
        run_command("incus admin init --preseed", stdin_text=INCUS_PRESEED)


def configure_firewall_rules() -> None:
    if not check_command("incus network show incusbr0"):
        return
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


def add_gpu_passthrough() -> None:
    profile_devices = run_command("incus profile device show default")
    if "gpu:" not in profile_devices:
        print("Adding GPU passthrough to default profile...")
        check_command("incus profile device add default gpu gpu")


def install_coi_binary() -> None:
    print("Installing COI binary...")
    with tempfile.NamedTemporaryFile(delete=False) as temporary_file:
        temporary_path = temporary_file.name
    run_command(f"curl -fsSL -o {temporary_path} {COI_BINARY_URL}")
    run_command(f"chmod +x {temporary_path}")
    run_command(f"sudo mv {temporary_path} /usr/local/bin/coi")


# `coi build` requires the repo cloned locally because build scripts aren't embedded in the
# binary. Once a release ships with embedded scripts, we can drop clone_or_update_coi_repo()
# and the cwd= argument to the build calls below.
# Upstream: https://github.com/mensfeld/code-on-incus/issues/50
# Tracking: agent/tickets/T57.md
def clone_or_update_coi_repo() -> None:
    if not COI_REPO_DIR.exists():
        print("Cloning COI repo...")
        run_command(f"sudo git clone --depth 1 {COI_REPO_URL} {COI_REPO_DIR}", stream_log=True)
    else:
        print("Updating COI repo...")
        run_command(f"sudo git -C {COI_REPO_DIR} pull --ff-only", stream_log=True)


def build_base_image() -> None:
    if not check_command("incus image info coi"):
        print("Building base COI image...")
        run_command("coi build", cwd=COI_REPO_DIR, stream_log=True)


def build_placeframe_image(rebuild: bool) -> None:
    if rebuild:
        print(f"Removing existing {PLACEFRAME_IMAGE} image (--rebuild)...")
        check_command(f"incus image delete {PLACEFRAME_IMAGE}")

    if not check_command(f"incus image info {PLACEFRAME_IMAGE}"):
        build_script = Path(__file__).resolve().parents[3] / "agent" / "coi-placeframe-build.sh"
        print(f"Building {PLACEFRAME_IMAGE} image...")
        run_command(f"coi build custom {PLACEFRAME_IMAGE} --script {build_script}", cwd=COI_REPO_DIR, stream_log=True)
        print(f"{PLACEFRAME_IMAGE} image published.")


def write_coi_config() -> None:
    config_directory = Path.home() / ".config" / "coi"
    config_directory.mkdir(parents=True, exist_ok=True)
    (config_directory / "config.toml").write_text(f'[defaults]\npersistent = true\nimage = "{PLACEFRAME_IMAGE}"\n')


def propagate_git_identity() -> None:
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


def set_uv_project_environment() -> None:
    run_command('incus profile set default environment.UV_PROJECT_ENVIRONMENT="/home/code/.venvs/placeframe"')


@app.command()
def setup_sandbox(
    rebuild: bool = typer.Option(False, "--rebuild", help="Delete and rebuild the coi-placeframe image"),
) -> None:
    print("Provisioning COI (code-on-incus) on Ubuntu")
    install_host_dependencies()
    configure_firewalld()
    ensure_subuid_subgid()
    install_incus()
    initialize_incus()
    configure_firewall_rules()
    add_gpu_passthrough()
    install_coi_binary()
    clone_or_update_coi_repo()
    build_base_image()
    build_placeframe_image(rebuild)
    write_coi_config()
    propagate_git_identity()
    set_uv_project_environment()
    print("Done.")
    print("Run: coi shell")


def main() -> None:
    app()


if __name__ == "__main__":
    main()
