from __future__ import annotations

import json
import shutil
from pathlib import Path

import typer
from common.bash import bash

from ...shared.ci_step import ci_step

app = typer.Typer(add_completion=False, pretty_exceptions_show_locals=False)

REPO_ROOT = Path.cwd()
STATE_FILE = REPO_ROOT / "build" / "versions.json"
ARTIFACT_DIR = Path("/tmp/release-artifacts")


def _bump_patch(version: str) -> str:
    major, minor, patch = version.split(".")
    return f"{major}.{minor}.{int(patch) + 1}"


def _zip_artifacts() -> list[Path]:
    """Zip each artifact directory into a .zip archive. Returns list of zip paths."""
    zips: list[Path] = []
    if not ARTIFACT_DIR.is_dir():
        print("No release artifacts directory found")
        return zips

    for entry in sorted(ARTIFACT_DIR.iterdir()):
        if not entry.is_dir():
            continue
        zip_path = ARTIFACT_DIR / entry.name
        shutil.make_archive(str(zip_path), "zip", entry)
        zips.append(zip_path.with_suffix(".zip"))
        print(f"  Zipped: {entry.name}.zip")

    return zips


@app.command()
def main(run_number: int = typer.Option(..., help="GitHub Actions run number")) -> None:
    with ci_step("Read release version"):
        state = json.loads(STATE_FILE.read_text())
        current_version = state["release"]["version"]
        new_version = _bump_patch(current_version)
        tag = f"v{new_version}"
        print(f"  Current: {current_version}")
        print(f"  New:     {new_version} (run #{run_number})")

    with ci_step("Bump version and tag"):
        state["release"]["version"] = new_version
        STATE_FILE.write_text(json.dumps(state, indent=2) + "\n")

        bash('git config user.name "github-actions[bot]"')
        bash('git config user.email "github-actions[bot]@users.noreply.github.com"')
        bash(f"git add {STATE_FILE}")
        bash(f'git commit -m "release: {tag}"')
        bash(f"git tag {tag}")
        bash("git push")
        bash(f"git push origin {tag}")

    with ci_step("Package artifacts"):
        zips = _zip_artifacts()
        if zips:
            print(f"  {len(zips)} artifact(s) ready for upload")
        else:
            print("  No Unity build artifacts to attach")

    with ci_step("Create GitHub Release"):
        zip_args = " ".join(f'"{z}"' for z in zips)
        bash(f"gh release create {tag} --title {tag} --generate-notes {zip_args}")
        print(f"  Release created: {tag}")
