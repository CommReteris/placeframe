import os
from pathlib import Path

import typer
from common.bash import bash_handoff
from common.detect_gpu import Gpu, detect_gpu

ENV_FILE = Path(".env")
LOCK_FILE = Path(".env.lock")
LOCAL_LOCK_FILE = Path(".env.local.lock")


def _resolve_context_sha(*, use_local: bool = True) -> None:
    if use_local and LOCAL_LOCK_FILE.exists():
        for line in LOCAL_LOCK_FILE.read_text(encoding="utf-8").splitlines():
            if line.startswith("CONTEXT_SHA="):
                os.environ["CONTEXT_SHA"] = line.split("=", 1)[1].strip()
                return

    from .context_sha import compute_context_sha

    os.environ["CONTEXT_SHA"] = compute_context_sha(Path.cwd())


app = typer.Typer(add_completion=False)


@app.command()
def up(
    use_lock: bool = typer.Option(False, "--locked", "-l", help="Use .env.lock even if .env.local.lock exists."),
    attached: bool = typer.Option(False, "--attached", "-a", help="Run in foreground (not detached)"),
    gpu: Gpu = typer.Option("auto", "--gpu", help="auto|cuda|rocm|none"),
) -> None:
    if not LOCK_FILE.exists() and not LOCAL_LOCK_FILE.exists():
        raise RuntimeError("No lock file found; run 'lock.py' first")

    if not ENV_FILE.exists():
        raise RuntimeError("No .env file found; create one first (e.g., copy .env.example)")

    if gpu == "auto":
        gpu = detect_gpu()

    _resolve_context_sha(use_local=not use_lock)

    command = (
        "docker compose "
        "-f compose.yml "
        f"{f'-f compose.{gpu}.yml ' if gpu != 'none' else ''}"
        "--env-file .env "
        f"--env-file {LOCAL_LOCK_FILE if not use_lock and LOCAL_LOCK_FILE.exists() else LOCK_FILE} "
        "up"
    )

    if not attached:
        command += " -d"

    bash_handoff(command)


def main():
    app()


if __name__ == "__main__":
    main()
