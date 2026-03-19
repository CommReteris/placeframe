from pathlib import Path
from typing import Annotated

import typer
from common.bash import bash_check_stream

from .projects import load_unity_projects
from .unity import prepare_unity_project, unity_batchmode_command

app = typer.Typer(add_completion=False, pretty_exceptions_show_locals=False)


@app.command()
def lock_unity(project: Annotated[str | None, typer.Option(help="Limit to a specific project.")] = None) -> None:
    config = load_unity_projects()

    if project is not None and project not in config.projects:
        raise typer.BadParameter(f"Unknown project '{project}'. Valid: {', '.join(config.projects)}")

    all_projects = {name: project_config.path for name, project_config in config.projects.items()}
    projects = {project: all_projects[project]} if project else all_projects

    for name, path in projects.items():
        project_path = Path.cwd() / path
        lock_file = project_path / "Packages" / "packages-lock.json"
        print(f"Resolving {name} ({lock_file})...")

        prepare_unity_project(project_path)
        succeeded = bash_check_stream(f"{unity_batchmode_command(project_path)} -logFile /dev/stdout")
        if not succeeded:
            print(f"  WARNING: Unity exited non-zero for {name} (package resolution may still have succeeded)")

        print("  Done")
