from __future__ import annotations

import shutil
from pathlib import Path

import typer
from common.bash import bash

from ...shared.ci_step import ci_step

app = typer.Typer(add_completion=False, pretty_exceptions_show_locals=False)

ARTIFACT_DIR = Path("/tmp/release-artifacts")

# Artifact directory prefixes to skip (not release deliverables)
SKIP_PREFIXES = ("env-lock-", "versions")
SKIP_SUFFIXES = ("-build-report",)


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
            asset = ARTIFACT_DIR / f"{entry.name}{files[0].suffix}"
            shutil.copy2(files[0], asset)
            assets.append(asset)
            print(f"  Asset: {asset.name}")
        else:
            zip_path = ARTIFACT_DIR / entry.name
            shutil.make_archive(str(zip_path), "zip", entry)
            asset = zip_path.parent / f"{zip_path.name}.zip"
            assets.append(asset)
            print(f"  Asset: {asset.name} ({len(files)} files)")

    return assets


@app.command()
def main(run_number: int = typer.Option(..., help="GitHub Actions run number")) -> None:
    tag = f"build-{run_number}"

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
