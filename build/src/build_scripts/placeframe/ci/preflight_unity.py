from pathlib import Path

import typer
from common.bash import bash
from pydantic_settings import BaseSettings

from ...shared.ci_step import ci_step
from ...shared.license_restore import restore_license
from ...shared.setup import configure_git, install_dotnet
from ...shared.setup_oras import install_oras
from ..lock_unity import lock_unity


class Settings(BaseSettings):
    github_workspace: str


settings = Settings.model_validate({})
app = typer.Typer(add_completion=False, pretty_exceptions_show_locals=False)


@app.command()
def main(
    project: str = typer.Option(help="Project name"),
    project_path: Path = typer.Option(help="Path to Unity project"),
    registry: str = typer.Option(help="OCI registry path"),
) -> None:
    with ci_step("Setup"):
        configure_git(settings.github_workspace)
        install_oras()
        install_dotnet("8.0")
        restore_license()

    with ci_step("Restore packages"):
        bash("dotnet tool restore")
        bash(f"dotnet nugetforunity restore {project_path}")

    with ci_step("Check Unity lock files"):
        lock_unity(check=True, project=project)
