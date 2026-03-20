from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass, field
from pathlib import Path
from subprocess import CalledProcessError

import typer
from common.bash import bash, bash_output
from pydantic_settings import BaseSettings

from ...shared.ci_step import ci_step
from ...shared.setup import configure_git, free_disk_space, install_dotnet, install_node
from ..projects import load_unity_projects


class Settings(BaseSettings):
    github_workspace: str
    github_step_summary: str | None = None
    github_output: str | None = None
    nuget_api_key: str = ""


settings = Settings.model_validate({})

app = typer.Typer(add_completion=False, pretty_exceptions_show_locals=False)

REPO_ROOT = Path.cwd()
STATE_FILE = REPO_ROOT / "build" / "versions.json"
UNITY_PACKAGE_ROOT = REPO_ROOT / "packages" / "unity" / "Placeframe" / "Assets" / "Package"


@dataclass
class PackageConfig:
    path: Path
    hash_glob: str = "**/*"
    hash_exclude: set[str] = field(default_factory=set)
    depends_on: str | None = None


PACKAGES: dict[str, PackageConfig] = {
    "api-client": PackageConfig(
        path=REPO_ROOT / "packages" / "generated" / "csharp" / "api-client" / "src" / "PlaceframeApiClient",
        hash_glob="**/*.cs",
        hash_exclude={"bin", "obj"},
    ),
    "core": PackageConfig(path=UNITY_PACKAGE_ROOT / "Core"),
    "arfoundation": PackageConfig(path=UNITY_PACKAGE_ROOT / "ARFoundation", depends_on="core"),
    "magicleap": PackageConfig(path=UNITY_PACKAGE_ROOT / "MagicLeap", depends_on="core"),
}


def npm_publish(cwd: Path) -> None:
    """Run npm publish, tolerating 'already exists' errors for idempotency."""
    try:
        bash_output("npm publish --access public --provenance", cwd=cwd)
    except CalledProcessError as e:
        stderr = e.stderr or ""
        if "EPUBLISHCONFLICT" in stderr or "cannot publish over existing version" in stderr:
            print("  Version already published, skipping (idempotent)")
        else:
            raise


def patch_package_json(package_path: Path, version: str, dependency_updates: dict[str, str] | None = None) -> None:
    # These package.json files serve dual roles: they're the UPM package
    # definitions that Unity resolves via file: references (where the version
    # field is ignored), and the source of truth for npm publish (where the
    # version field is the only thing that matters). We patch versions in-place
    # here and commit them back; the "stale" version in subsequent builds is
    # harmless because local file: resolution never reads it.
    package_json = package_path / "package.json"
    package = json.loads(package_json.read_text())
    package["version"] = version
    for dependency_name, dependency_version in (dependency_updates or {}).items():
        package["dependencies"][dependency_name] = dependency_version
    package_json.write_text(json.dumps(package, indent=2) + "\n")


@app.command()
def main(dry_run: bool = typer.Option(False, help="Plan publishes without executing them")) -> None:
    with ci_step("Setup"):
        configure_git(settings.github_workspace)
        free_disk_space()
        install_dotnet("8.0")
        install_node("24", "https://registry.npmjs.org")

    with ci_step("Compute publish plan"):
        state = json.loads(STATE_FILE.read_text())
        package_state = state["packages"]

        hashes: dict[str, str] = {}
        for name, config in PACKAGES.items():
            hasher = hashlib.sha256()
            exclude = config.hash_exclude or set()
            for file in sorted(config.path.rglob(config.hash_glob)):
                if not file.is_file() or file.name == "package.json" or any(part in exclude for part in file.parts):
                    continue
                hasher.update(str(file.relative_to(config.path)).encode())
                hasher.update(file.read_bytes())
            hashes[name] = hasher.hexdigest()

        publish: dict[str, bool] = {}
        versions: dict[str, str] = {}
        for name, config in PACKAGES.items():
            old_hash = package_state[name]["hash"]
            old_version: str = package_state[name]["version"]
            changed = hashes[name] != old_hash or (
                config.depends_on is not None and publish.get(config.depends_on, False)
            )
            publish[name] = changed
            if changed:
                major, minor, patch = old_version.split(".")
                versions[name] = f"{major}.{minor}.{int(patch) + 1}"
            else:
                versions[name] = old_version

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
            patch_package_json(
                PACKAGES["core"].path, versions["core"], {"org.nuget.placeframeapiclient": versions["api-client"]}
            )
            npm_publish(PACKAGES["core"].path)

    if publish["arfoundation"]:
        with ci_step("Publish ARFoundation"):
            dependency_updates = {"org.outernet.placeframe": versions["core"]} if publish["core"] else {}
            patch_package_json(PACKAGES["arfoundation"].path, versions["arfoundation"], dependency_updates)
            npm_publish(PACKAGES["arfoundation"].path)

    if publish["magicleap"]:
        with ci_step("Publish MagicLeap"):
            dependency_updates = {"org.outernet.placeframe": versions["core"]} if publish["core"] else {}
            patch_package_json(PACKAGES["magicleap"].path, versions["magicleap"], dependency_updates)
            npm_publish(PACKAGES["magicleap"].path)

    app_state: dict[str, dict[str, str]] = dict(state.get("apps", {}))
    with ci_step("Compute app versions"):
        app_exclude_dirs = {"Library", "Temp", "Logs", "Build", "Builds", "obj", "UserSettings"}
        app_exclude_extensions = {".csproj", ".sln"}
        projects = load_unity_projects()

        for name, project in projects.projects.items():
            if not project.builds or name not in app_state:
                continue

            hasher = hashlib.sha256()
            for file in sorted(REPO_ROOT.joinpath(project.path).rglob("*")):
                if not file.is_file():
                    continue
                if any(part in app_exclude_dirs for part in file.parts):
                    continue
                if file.suffix in app_exclude_extensions:
                    continue
                if file.name == "ProjectSettings.asset":
                    continue
                hasher.update(str(file.relative_to(REPO_ROOT / project.path)).encode())
                hasher.update(file.read_bytes())

            for package_name in sorted(hashes):
                hasher.update(hashes[package_name].encode())

            app_hash = hasher.hexdigest()
            old_app = app_state[name]
            if app_hash != old_app["hash"]:
                major, minor, patch = old_app["version"].split(".")
                app_state[name] = {"version": f"{major}.{minor}.{int(patch) + 1}", "hash": app_hash}
                print(f"  {name}: {old_app['version']} -> {app_state[name]['version']}")
            else:
                print(f"  {name}: {old_app['version']} (unchanged)")

    with ci_step("Save publish state"):
        new_state = {
            "packages": {name: {"version": versions[name], "hash": hashes[name]} for name in PACKAGES},
            "apps": app_state,
        }
        STATE_FILE.write_text(json.dumps(new_state, indent=2) + "\n")

        if settings.github_output:
            with open(settings.github_output, "a") as file:
                file.write("published=true\n")
