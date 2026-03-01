# Deterministic wrapper for the LLM-generated tidy-commits.sh script.
#
# Guarantees three things regardless of what the generated script contains:
# 1. A backup branch is created before any destructive operations
# 2. The generated script runs with BRANCH, BASE, and BACKUP env vars
# 3. Tree-tip invariance is verified after the rewrite (and rolled back on failure)

import os
import sys
from pathlib import Path

import typer
from common.run_command import check_command, run_command

app = typer.Typer(add_completion=False)


def find_available_backup_name(branch: str) -> str:
    base_backup = f"{branch}-backup"
    existing = run_command(f"git branch --list {base_backup} {base_backup}-*").strip().splitlines()
    if not existing:
        return base_backup
    suffix = len(existing) + 1
    return f"{base_backup}-{suffix}"


def restore_from_backup(branch: str, backup: str) -> None:
    print("Restoring from backup...", file=sys.stderr)
    run_command(f"git checkout {backup}")
    run_command(f"git branch -f {branch} {backup}")
    run_command(f"git checkout {branch}")
    print(f"Restored {branch} from {backup}.")


@app.command()
def tidy_commits_wrapper() -> None:
    if not Path("tidy-commits.sh").exists():
        print("FATAL: tidy-commits.sh not found.", file=sys.stderr)
        sys.exit(1)

    branch = run_command("git rev-parse --abbrev-ref HEAD").strip()

    remote_branch = f"origin/{branch}"
    if check_command(f"git rev-parse --verify {remote_branch}"):
        base = run_command(f"git rev-parse {remote_branch}").strip()
    elif check_command("git rev-parse --verify origin/main"):
        base = run_command("git merge-base origin/main HEAD").strip()
    else:
        base = run_command("git merge-base main HEAD").strip()

    backup = find_available_backup_name(branch)

    run_command(f"git branch {backup}")
    print(f"Backup created: {backup}")

    if not check_command(
        "bash tidy-commits.sh",
        env={**os.environ, "BRANCH": branch, "BASE": base, "BACKUP": backup},
        stream_output=True,
    ):
        restore_from_backup(branch, backup)
        sys.exit(1)

    if not check_command(f"git diff --quiet {branch} {backup}"):
        print("FATAL: tree mismatch after rewrite!", file=sys.stderr)
        print(run_command(f"git diff --stat {branch} {backup}"), file=sys.stderr)
        restore_from_backup(branch, backup)
        sys.exit(1)

    print("Tree invariance check passed.")
    print(run_command(f"git log --oneline {base}..{branch}"))


def main():
    app()


if __name__ == "__main__":
    main()
