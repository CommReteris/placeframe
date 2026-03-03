import hashlib
import shlex
import signal
import subprocess
import sys
import threading
import time
from pathlib import Path
from subprocess import CalledProcessError

import typer
from common.run_command import check_command, exec_command, run_command

from .setup_agent_sandbox import PLACEFRAME_IMAGE, UNITY_CREDENTIALS_PATH, _parse_unity_credentials

DEVICE_NAME = "main-git"
UNITY_EDITOR_PATH = "/opt/unity/6000.0.66f1/Editor/Unity"

# COI's config.toml supports [defaults] image = "..." but the binary never applies it —
# PersistentPreRunE only wires up the "persistent" default, not "image". The empty --image
# flag falls through to the hardcoded "coi" base image. We pass --image explicitly until
# this is fixed upstream. Tracking: agent/tickets/T56.md
SHELL_COMMAND = f"coi shell --image {PLACEFRAME_IMAGE}"

app = typer.Typer(add_completion=False)


def add_git_mount(container_name: str, main_git_path: Path) -> None:
    check_command(
        f"incus config device add {container_name} {DEVICE_NAME} disk"
        f" source={main_git_path} path={main_git_path} shift=true"
    )
    check_command(f"incus exec {container_name} -- git config --system --add safe.directory {main_git_path.parent}")


def ensure_unity_activated(container_name: str, credentials: tuple[str, str, str]) -> None:
    if check_command(f"incus exec {container_name} -- test -f /root/.local/share/unity3d/Unity/Unity_lic.ulf"):
        return
    serial, email, password = credentials
    print("Activating Unity license...")
    activated = check_command(
        f"incus exec {container_name} --"
        f" {UNITY_EDITOR_PATH} -batchmode -quit -nographics"
        f" -serial {shlex.quote(serial)} -username {shlex.quote(email)} -password {shlex.quote(password)}"
    )
    if activated:
        print("Unity license activated.")
    else:
        print("WARNING: Unity license activation failed. Batchmode compilation will not work.")
        print("Check credentials in:", UNITY_CREDENTIALS_PATH)


@app.command()
def agent_shell(
    no_unity: bool = typer.Option(False, "--no-unity", help="Launch without Unity license activation"),
) -> None:
    credentials = None
    if not no_unity:
        if not UNITY_CREDENTIALS_PATH.exists():
            credentials = None
        else:
            parsed = _parse_unity_credentials(UNITY_CREDENTIALS_PATH)
            serial = parsed.get("UNITY_SERIAL")
            email = parsed.get("UNITY_EMAIL")
            password = parsed.get("UNITY_PASSWORD")
            if serial and email and password:
                credentials = (serial, email, password)
        if credentials is None:
            print(f"ERROR: Unity credentials not found or incomplete at {UNITY_CREDENTIALS_PATH}")
            print("Either run 'uv run setup-agent-sandbox' for setup instructions,")
            print("or use --no-unity to launch without Unity license activation.")
            sys.exit(1)
    else:
        print("WARNING: Launching without Unity license — batchmode compilation will fail.")

    git_path = Path(".git")
    if git_path.exists() and not git_path.is_dir():
        main_git_path: Path | None = Path(run_command("git rev-parse --git-common-dir").strip()).resolve()
    else:
        main_git_path = None

    if main_git_path is None:
        exec_command(SHELL_COMMAND)

    container_name = f"coi-{hashlib.sha256(str(Path.cwd()).encode()).hexdigest()[:8]}-1"

    if check_command(f"incus info {container_name}"):
        assert main_git_path is not None
        add_git_mount(container_name, main_git_path)
        if credentials:
            ensure_unity_activated(container_name, credentials)
        exec_command(SHELL_COMMAND)
    else:
        assert main_git_path is not None

        def configure_container_when_ready() -> None:
            for _ in range(60):
                time.sleep(1)
                try:
                    running = "Status: RUNNING" in run_command(f"incus info {container_name}")
                except CalledProcessError:
                    running = False
                if running:
                    add_git_mount(container_name, main_git_path)
                    print(f"Worktree mount added: {main_git_path}")
                    if credentials:
                        ensure_unity_activated(container_name, credentials)
                    return

        threading.Thread(target=configure_container_when_ready, daemon=True).start()

        process = subprocess.Popen(["coi", "shell", "--image", PLACEFRAME_IMAGE])
        signal.signal(signal.SIGINT, lambda signum, frame: process.send_signal(signum))
        signal.signal(signal.SIGTERM, lambda signum, frame: process.send_signal(signum))
        sys.exit(process.wait())


def main() -> None:
    app()


if __name__ == "__main__":
    main()
