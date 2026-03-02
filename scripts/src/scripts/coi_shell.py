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
from scripts.setup_sandbox import PLACEFRAME_IMAGE

DEVICE_NAME = "main-git"

# COI's config.toml supports [defaults] image = "..." but the binary never applies it —
# PersistentPreRunE only wires up the "persistent" default, not "image". The empty --image
# flag falls through to the hardcoded "coi" base image. We pass --image explicitly until
# this is fixed upstream. Tracking: agent/tickets/T56.md
SHELL_COMMAND = f"coi shell --image {PLACEFRAME_IMAGE}"

app = typer.Typer(add_completion=False)


def detect_worktree() -> Path | None:
    git_path = Path(".git")
    if not git_path.exists() or git_path.is_dir():
        return None
    main_git = Path(run_command("git rev-parse --git-common-dir").strip()).resolve()
    return main_git


def compute_container_name(workspace: Path, slot: int = 1) -> str:
    workspace_hash = hashlib.sha256(str(workspace).encode()).hexdigest()[:8]
    return f"coi-{workspace_hash}-{slot}"


def container_exists(name: str) -> bool:
    return check_command(f"incus info {name}")


def container_running(name: str) -> bool:
    try:
        output = run_command(f"incus info {name}")
        return "Status: RUNNING" in output
    except CalledProcessError:
        return False


def add_git_mount(container_name: str, main_git_path: Path) -> None:
    try:
        run_command(
            f"incus config device add {container_name} {DEVICE_NAME} disk"
            f" source={main_git_path} path={main_git_path} shift=true"
        )
    except CalledProcessError:
        pass

    repo_path = main_git_path.parent
    try:
        run_command(f"incus exec {container_name} -- git config --system --add safe.directory {repo_path}")
    except CalledProcessError:
        pass


@app.command()
def coi_shell() -> None:
    main_git_path = detect_worktree()

    if main_git_path is None:
        exec_command(SHELL_COMMAND)

    container_name = compute_container_name(Path.cwd())

    if container_exists(container_name):
        assert main_git_path is not None
        add_git_mount(container_name, main_git_path)
        exec_command(SHELL_COMMAND)
    else:
        assert main_git_path is not None

        def add_mount_when_ready() -> None:
            for _ in range(60):
                time.sleep(1)
                if container_running(container_name):
                    add_git_mount(container_name, main_git_path)
                    print(f"Worktree mount added: {main_git_path}")
                    return

        thread = threading.Thread(target=add_mount_when_ready, daemon=True)
        thread.start()

        process = subprocess.Popen(["coi", "shell", "--image", PLACEFRAME_IMAGE])
        signal.signal(signal.SIGINT, lambda signum, frame: process.send_signal(signum))
        signal.signal(signal.SIGTERM, lambda signum, frame: process.send_signal(signum))
        sys.exit(process.wait())


def main() -> None:
    app()


if __name__ == "__main__":
    main()
