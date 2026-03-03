import hashlib
import signal
import subprocess
import sys
import threading
import time
from pathlib import Path
from subprocess import CalledProcessError

import typer
from common.run_command import check_command, exec_command, run_command

from .setup_agent_sandbox import PLACEFRAME_IMAGE

DEVICE_NAME = "main-git"

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


@app.command()
def agent_shell() -> None:
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
        exec_command(SHELL_COMMAND)
    else:
        assert main_git_path is not None

        def add_mount_when_ready() -> None:
            for _ in range(60):
                time.sleep(1)
                try:
                    running = "Status: RUNNING" in run_command(f"incus info {container_name}")
                except CalledProcessError:
                    running = False
                if running:
                    add_git_mount(container_name, main_git_path)
                    print(f"Worktree mount added: {main_git_path}")
                    return

        threading.Thread(target=add_mount_when_ready, daemon=True).start()

        process = subprocess.Popen(["coi", "shell", "--image", PLACEFRAME_IMAGE])
        signal.signal(signal.SIGINT, lambda signum, frame: process.send_signal(signum))
        signal.signal(signal.SIGTERM, lambda signum, frame: process.send_signal(signum))
        sys.exit(process.wait())


def main() -> None:
    app()


if __name__ == "__main__":
    main()
