from __future__ import annotations

import json
from collections.abc import Iterator
from contextlib import contextmanager
from dataclasses import dataclass
from pathlib import Path
from subprocess import CalledProcessError

import typer
from common.bash import bash, bash_output
from pydantic_settings import BaseSettings

from ...shared.ci_step import ci_step
from ...shared.setup import configure_git, free_disk_space, install_dotnet, install_node
from ..projects import load_unity_projects
from .git_tags import APP_TAG_PREFIXES, create_and_push_tag, get_latest_tag_version, has_changes_since_tag


class Settings(BaseSettings):
    github_workspace: str
    github_step_summary: str | None = None
    github_output: str | None = None
    nuget_api_key: str = ""


settings = Settings.model_validate({})

app = typer.Typer(add_completion=False, pretty_exceptions_show_locals=False)

REPO_ROOT = Path.cwd()
UNITY_PACKAGE_ROOT = REPO_ROOT / "packages" / "unity" / "Placeframe" / "Assets" / "Package"


@dataclass
class PackageConfig:
    path: Path
    depends_on: str | None = None


PACKAGES: dict[str, PackageConfig] = {
    "api-client": PackageConfig(
        path=REPO_ROOT / "packages" / "generated" / "csharp" / "api-client" / "src" / "PlaceframeApiClient"
    ),
    "core": PackageConfig(path=UNITY_PACKAGE_ROOT / "Core"),
    "arfoundation": PackageConfig(path=UNITY_PACKAGE_ROOT / "ARFoundation", depends_on="core"),
    "magicleap": PackageConfig(path=UNITY_PACKAGE_ROOT / "MagicLeap", depends_on="core"),
}


def npm_publish(cwd: Path) -> None:
    try:
        bash_output("npm publish --access public --provenance", cwd=cwd)
    except CalledProcessError as e:
        stderr = e.stderr or ""
        if "EPUBLISHCONFLICT" in stderr or "cannot publish over existing version" in stderr:
            print("  Version already published, skipping (idempotent)")
        else:
            raise


def patch_package_json(package_path: Path, version: str, dependency_updates: dict[str, str] | None = None) -> None:
    package_json = package_path / "package.json"
    package = json.loads(package_json.read_text())
    package["version"] = version
    for dependency_name, dependency_version in (dependency_updates or {}).items():
        package["dependencies"][dependency_name] = dependency_version
    package_json.write_text(json.dumps(package, indent=2) + "\n")


@contextmanager
def ephemeral_patch(
    package_path: Path, version: str, dependency_updates: dict[str, str] | None = None
) -> Iterator[None]:
    package_json = package_path / "package.json"
    original = package_json.read_text()
    try:
        patch_package_json(package_path, version, dependency_updates)
        yield
    finally:
        package_json.write_text(original)


@app.command()
def main(dry_run: bool = typer.Option(False, help="Plan publishes without executing them")) -> None:
    with ci_step("Setup"):
        configure_git(settings.github_workspace)
        free_disk_space()
        install_dotnet("8.0")
        install_node("24", "https://registry.npmjs.org")

    with ci_step("Compute publish plan"):
        publish: dict[str, bool] = {}
        versions: dict[str, str] = {}
        for name, config in PACKAGES.items():
            last_version = get_latest_tag_version(f"{name}-v")
            changed = has_changes_since_tag(f"{name}-v{last_version}" if last_version else None, config.path)
            if config.depends_on and publish.get(config.depends_on, False):
                changed = True
            publish[name] = changed
            if changed:
                if last_version:
                    major, minor, patch = last_version.split(".")
                    versions[name] = f"{major}.{minor}.{int(patch) + 1}"
                else:
                    versions[name] = "0.1.0"
            else:
                versions[name] = last_version or "0.0.0"

        summary_lines = [
            "### Publish Plan",
            "| Package | Publish | Version |",
            "|---|---|---|",
            f"| NuGet (PlaceframeApiClient) | {publish['api-client']} | {versions['api-client']} |",
            f"| Core | {publish['core']} | {versions['core']} |",
            f"| ARFoundation | {publish['arfoundation']} | {versions['arfoundation']} |",
            f"| MagicLeap | {publish['magicleap']} | {versions['magicleap']} |",
        ]
        summary = "\n".join(summary_lines)
        print(summary)

        if settings.github_step_summary:
            with open(settings.github_step_summary, "a") as file:
                file.write(summary + "\n")

        if not any(publish.values()):
            print("Nothing to publish")
            return

        if dry_run:
            print("Dry run — skipping publish")
            return

    if publish["api-client"]:
        with ci_step("Publish NuGet"):
            nuget_path = PACKAGES["api-client"].path
            bash(f"dotnet pack -c Release -p:Version={versions['api-client']} -o ./nupkg", cwd=nuget_path)
            nuget_api_key = settings.nuget_api_key
            bash(
                f"dotnet nuget push ./nupkg/*.nupkg --api-key {nuget_api_key}"
                " --source https://api.nuget.org/v3/index.json"
                " --skip-duplicate",
                cwd=nuget_path,
            )

    if publish["core"]:
        with ci_step("Publish Core"):
            with ephemeral_patch(
                PACKAGES["core"].path, versions["core"], {"org.nuget.placeframeapiclient": versions["api-client"]}
            ):
                npm_publish(PACKAGES["core"].path)

    if publish["arfoundation"]:
        with ci_step("Publish ARFoundation"):
            dependency_updates = {"org.outernet.placeframe": versions["core"]} if publish["core"] else {}
            with ephemeral_patch(PACKAGES["arfoundation"].path, versions["arfoundation"], dependency_updates):
                npm_publish(PACKAGES["arfoundation"].path)

    if publish["magicleap"]:
        with ci_step("Publish MagicLeap"):
            dependency_updates = {"org.outernet.placeframe": versions["core"]} if publish["core"] else {}
            with ephemeral_patch(PACKAGES["magicleap"].path, versions["magicleap"], dependency_updates):
                npm_publish(PACKAGES["magicleap"].path)

    app_publish: dict[str, str] = {}
    with ci_step("Compute app versions"):
        projects = load_unity_projects()
        for name, project in projects.projects.items():
            if not project.builds or name not in APP_TAG_PREFIXES:
                continue
            prefix = APP_TAG_PREFIXES[name]
            last_version = get_latest_tag_version(f"{prefix}-v")
            changed = has_changes_since_tag(
                f"{prefix}-v{last_version}" if last_version else None, REPO_ROOT / project.path
            )
            # Apps depend on packages — bump if any package changed
            if any(publish.values()):
                changed = True
            if changed:
                if last_version:
                    major, minor, patch = last_version.split(".")
                    new_version = f"{major}.{minor}.{int(patch) + 1}"
                else:
                    new_version = "0.1.0"
                app_publish[name] = new_version
                print(f"  {name}: {last_version or '(none)'} -> {new_version}")
            else:
                print(f"  {name}: {last_version or '0.0.0'} (unchanged)")

    with ci_step("Create version tags"):
        for name in PACKAGES:
            if publish[name]:
                tag = f"{name}-v{versions[name]}"
                create_and_push_tag(tag)
                print(f"  Tagged: {tag}")

        for name, new_version in app_publish.items():
            tag = f"{APP_TAG_PREFIXES[name]}-v{new_version}"
            create_and_push_tag(tag)
            print(f"  Tagged: {tag}")

        if settings.github_output:
            with open(settings.github_output, "a") as file:
                file.write("published=true\n")
