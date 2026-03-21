import os
from pathlib import Path

import typer
from common.bash import bash_handoff
from common.detect_gpu import Gpu, detect_gpu

ENV_FILE = Path(".env")
LOCK_FILE = Path(".env.lock")
LOCAL_LOCK_FILE = Path(".env.local.lock")


def _resolve_context_sha() -> None:
    if LOCAL_LOCK_FILE.exists():
        for line in LOCAL_LOCK_FILE.read_text(encoding="utf-8").splitlines():
            if line.startswith("CONTEXT_SHA="):
                os.environ["CONTEXT_SHA"] = line.split("=", 1)[1].strip()
                return

    from .context_sha import compute_context_sha

    os.environ["CONTEXT_SHA"] = compute_context_sha(Path.cwd())


app = typer.Typer(add_completion=False)


@app.command()
def down(
    volumes: bool = typer.Option(False, "--volumes", "-v", help="Remove named volumes."),
    gpu: Gpu = typer.Option("auto", "--gpu", help="auto|cuda|rocm|none"),
) -> None:
    if not ENV_FILE.exists():
        raise RuntimeError("No .env file found")

    if not LOCK_FILE.exists() and not LOCAL_LOCK_FILE.exists():
        raise RuntimeError("No lock file found; run 'lock.py' first")

    if gpu == "auto":
        gpu = detect_gpu()

    lock_file = LOCAL_LOCK_FILE if LOCAL_LOCK_FILE.exists() else LOCK_FILE

    _resolve_context_sha()

    command = (
        "docker compose "
        "-f compose.yml "
        f"{f'-f compose.{gpu}.yml ' if gpu != 'none' else ''}"
        "--env-file .env "
        f"--env-file {lock_file} "  # Needed so compose won't error on missing variables, even though they are irrelevant for 'down'
        "down --remove-orphans"
    )

    if volumes:
        command += " -v"

    bash_handoff(command)


def main():
    app()


if __name__ == "__main__":
    main()
