from pathlib import Path
from typing import Annotated

import typer
from common.bash import bash_check_stream

from ..shared.check_tracked_files import check_tracked_files
from .projects import load_unity_projects
from .unity_batch_mode_command import unity_batchmode_command

app = typer.Typer(add_completion=False, pretty_exceptions_show_locals=False)


@app.command()
def lock_unity(
    check: bool = typer.Option(False, "--check", help="Validate locks without writing. Exit non-zero if stale."),
    project: Annotated[str | None, typer.Option(help="Limit to a specific project.")] = None,
) -> None:
    config = load_unity_projects()

    if project is not None and project not in config.projects:
        raise typer.BadParameter(f"Unknown project '{project}'. Valid: {', '.join(config.projects)}")

    all_projects = {name: project_config.path for name, project_config in config.projects.items()}
    projects = {project: all_projects[project]} if project else all_projects

    stale = False

    for name, path in projects.items():
        project_path = Path.cwd() / path
        lock_file = project_path / "Packages" / "packages-lock.json"
        print(f"{'Checking' if check else 'Resolving'} {name} ({lock_file})...")

        succeeded = bash_check_stream(f"{unity_batchmode_command(project_path)} -logFile /dev/stdout")
        if not succeeded:
            print(f"  WARNING: Unity exited non-zero for {name} (package resolution may still have succeeded)")

        # In check mode, no intended output — all changes are problems (stale lock or unexpected)
        # In normal mode, packages-lock.json is intended output (the whole point of locking)
        intended_output = None if check else {"Packages/packages-lock.json"}
        unexpected = check_tracked_files(project_path, intended_output=intended_output)

        if check:
            lock_relative = str(path / "Packages" / "packages-lock.json")
            lock_changed = lock_relative in unexpected
            other_unexpected = [file for file in unexpected if file != lock_relative]

            if lock_changed:
                print(f"  STALE: {lock_file} is out of date.")
                stale = True
            if other_unexpected:
                print("  Unexpected tracked-file changes detected (restored):")
                for file in other_unexpected:
                    print(f"    {file}")
                stale = True
            if not lock_changed and not other_unexpected:
                print("  OK")
        else:
            if unexpected:
                print("  Unexpected tracked-file changes detected (restored):")
                for file in unexpected:
                    print(f"    {file}")
            print("  Done")

    if check and stale:
        raise SystemExit(1)

    if check:
        print("\nAll Unity lock files are up to date.")
