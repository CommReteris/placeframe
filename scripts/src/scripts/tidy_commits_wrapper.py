import os
import sys
from pathlib import Path

import typer
from common.run_command import check_command, run_command
from pydantic import BaseModel, model_validator

app = typer.Typer(add_completion=False)

PLAN_FILE = "tidy-commits.json"


class Committer(BaseModel):
    name: str
    email: str


class Commit(BaseModel):
    message: str
    author: str
    checkout: list[str] = []
    delete: list[str] = []
    content: dict[str, str] = {}

    @model_validator(mode="after")
    def has_file_operations(self) -> "Commit":
        if not self.checkout and not self.delete and not self.content:
            raise ValueError("commit has no file operations (needs 'checkout', 'delete', or 'content')")
        return self


class TidyCommitsPlan(BaseModel):
    committer: Committer
    commits: list[Commit]

    @model_validator(mode="after")
    def has_commits(self) -> "TidyCommitsPlan":
        if not self.commits:
            raise ValueError("plan must have a non-empty 'commits' list")
        return self


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


def execute_plan(plan: TidyCommitsPlan, branch: str, base: str, backup: str) -> None:
    commit_environment = {
        **os.environ,
        "GIT_COMMITTER_NAME": plan.committer.name,
        "GIT_COMMITTER_EMAIL": plan.committer.email,
    }
    temporary_branch = f"{branch}-tmp"

    run_command(["git", "checkout", "-b", temporary_branch, base])

    for index, commit in enumerate(plan.commits):
        print(f"Building commit {index + 1}/{len(plan.commits)}: {commit.message.splitlines()[0]}")

        if commit.checkout:
            run_command(["git", "checkout", backup, "--"] + commit.checkout)

        for file_path in commit.delete:
            run_command(["git", "rm", file_path])

        for file_path, file_content in commit.content.items():
            Path(file_path).parent.mkdir(parents=True, exist_ok=True)
            Path(file_path).write_text(file_content)
            run_command(["git", "add", file_path])

        run_command(["git", "commit", f"--author={commit.author}", "-m", commit.message], env=commit_environment)

    run_command(["git", "branch", "-f", branch, temporary_branch])
    run_command(["git", "checkout", branch])
    run_command(["git", "branch", "-d", temporary_branch])


@app.command()
def tidy_commits_wrapper() -> None:
    if not Path(PLAN_FILE).exists():
        print(f"FATAL: {PLAN_FILE} not found.", file=sys.stderr)
        sys.exit(1)

    try:
        plan = TidyCommitsPlan.model_validate_json(Path(PLAN_FILE).read_text())
    except Exception as error:
        print(f"FATAL: Invalid plan: {error}", file=sys.stderr)
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

    try:
        execute_plan(plan, branch, base, backup)
    except Exception as error:
        print(f"FATAL: Plan execution failed: {error}", file=sys.stderr)
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
