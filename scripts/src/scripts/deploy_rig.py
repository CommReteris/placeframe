from pathlib import Path

import typer
from common.run_command import run_command

app = typer.Typer()

IMAGE = "ghcr.io/outernet-foundation/placeframe/zed-capture:latest"
COMPOSE_SOURCE = Path(__file__).resolve().parent.parent.parent.parent / "zed" / "compose.rig.yml"
REMOTE_TAR = "/tmp/zed-capture.tar"
REMOTE_COMPOSE = "/tmp/compose.rig.yml"
LOCAL_TAR = "/tmp/zed-capture.tar"


def _run(command: str, *, dry_run: bool) -> None:
    if dry_run:
        print(f"  {command}")
    else:
        run_command(command, stream_log=True)


@app.command()
def main(
    host: str = typer.Option("user@192.168.55.1", help="SSH target for the ZED Box"),
    dry_run: bool = typer.Option(False, "--dry-run", help="Print commands without executing"),
) -> None:
    print("Step 1: Pull image on host")
    _run(f"docker pull {IMAGE}", dry_run=dry_run)

    print("Step 2: Save image to tarball")
    _run(f"docker save -o {LOCAL_TAR} {IMAGE}", dry_run=dry_run)

    print("Step 3: Transfer image and compose file to ZED Box")
    _run(f"scp {LOCAL_TAR} {host}:{REMOTE_TAR}", dry_run=dry_run)
    _run(f"scp {COMPOSE_SOURCE} {host}:{REMOTE_COMPOSE}", dry_run=dry_run)

    print("Step 4: Load image and start container on ZED Box")
    _run(f'ssh {host} "docker load -i {REMOTE_TAR} && docker compose -f {REMOTE_COMPOSE} up -d"', dry_run=dry_run)

    print("Step 5: Cleanup tarballs")
    _run(f"rm {LOCAL_TAR}", dry_run=dry_run)
    _run(f'ssh {host} "rm {REMOTE_TAR}"', dry_run=dry_run)

    print("Done." if not dry_run else "Dry run complete.")
