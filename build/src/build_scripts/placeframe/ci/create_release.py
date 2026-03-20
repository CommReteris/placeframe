from __future__ import annotations

import shutil
from pathlib import Path

import typer
from common.bash import bash

from ...shared.ci_step import ci_step
from .git_tags import create_and_push_tag, get_latest_tag_version

app = typer.Typer(add_completion=False, pretty_exceptions_show_locals=False)

ARTIFACT_DIR = Path("/tmp/release-artifacts")

# Artifact directory prefixes to skip (not release deliverables)
SKIP_PREFIXES = ("env-lock-", "versions")
SKIP_SUFFIXES = ("-build-report",)


def _bump_patch(version: str) -> str:
    major, minor, patch = version.split(".")
    return f"{major}.{minor}.{int(patch) + 1}"


def _package_artifacts() -> list[Path]:
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
            asset = ARTIFACT_DIR / files[0].name
            shutil.copy2(files[0], asset)
            assets.append(asset)
            print(f"  Asset: {files[0].name}")
        else:
            zip_path = ARTIFACT_DIR / entry.name
            shutil.make_archive(str(zip_path), "zip", entry)
            assets.append(zip_path.with_suffix(".zip"))
            print(f"  Asset: {entry.name}.zip ({len(files)} files)")

    return assets


@app.command()
def main(run_number: int = typer.Option(..., help="GitHub Actions run number")) -> None:
    with ci_step("Read release version"):
        current_version = get_latest_tag_version("release-v") or "0.0.0"
        new_version = _bump_patch(current_version)
        tag = f"v{new_version}"
        print(f"  Current: {current_version}")
        print(f"  New:     {new_version} (run #{run_number})")

    with ci_step("Create release tag"):
        create_and_push_tag(tag)
        create_and_push_tag(f"release-v{new_version}")

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
