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

# Artifact directory prefixes to skip (not release deliverables)
SKIP_PREFIXES = ("env-lock-", "versions")
SKIP_SUFFIXES = ("-build-report",)


def _bump_patch(version: str) -> str:
    major, minor, patch = version.split(".")
    return f"{major}.{minor}.{int(patch) + 1}"


def _package_artifacts() -> list[Path]:
    """Prepare release assets from downloaded CI artifacts.

    Single-file artifacts (.apk, .exe, etc.) are attached directly.
    Multi-file artifacts (e.g. linux64 builds) are zipped.
    """
    assets: list[Path] = []
    if not ARTIFACT_DIR.is_dir():
        print("No release artifacts directory found")
        return assets

    for entry in sorted(ARTIFACT_DIR.iterdir()):
        if not entry.is_dir():
            continue
        if any(entry.name.startswith(p) for p in SKIP_PREFIXES):
            print(f"  Skipping: {entry.name} (not a release artifact)")
            continue
        if any(entry.name.endswith(s) for s in SKIP_SUFFIXES):
            print(f"  Skipping: {entry.name} (not a release artifact)")
            continue

        files = [f for f in entry.rglob("*") if f.is_file()]
        if not files:
            print(f"  Skipping: {entry.name} (empty)")
            continue

        if len(files) == 1:
            # Single file — attach directly
            asset = ARTIFACT_DIR / files[0].name
            shutil.copy2(files[0], asset)
            assets.append(asset)
            print(f"  Asset: {files[0].name}")
        else:
            # Multiple files — zip the directory
            zip_path = ARTIFACT_DIR / entry.name
            shutil.make_archive(str(zip_path), "zip", entry)
            assets.append(zip_path.with_suffix(".zip"))
            print(f"  Asset: {entry.name}.zip ({len(files)} files)")

    return assets


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
        assets = _package_artifacts()
        if assets:
            print(f"  {len(assets)} asset(s) ready for upload")
        else:
            print("  No build artifacts to attach")

    with ci_step("Create GitHub Release"):
        asset_args = " ".join(f'"{a}"' for a in assets)
        bash(f"gh release create {tag} --title {tag} --generate-notes {asset_args}")
        print(f"  Release created: {tag}")
