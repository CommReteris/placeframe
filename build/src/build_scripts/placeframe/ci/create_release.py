from __future__ import annotations

import shutil
from pathlib import Path
from tempfile import NamedTemporaryFile

import typer
from common.bash import bash
from pydantic_settings import BaseSettings

from ...shared.ci_step import ci_step
from ..context_sha import compute_context_sha
from .git_tags import APP_TAG_PREFIXES, get_latest_tag_version

app = typer.Typer(add_completion=False, pretty_exceptions_show_locals=False)

ARTIFACT_DIR = Path("/tmp/release-artifacts")
SKIP_PREFIXES = ("env-lock-", "versions")
SKIP_SUFFIXES = ("-build-report",)

GHCR_BASE = "ghcr.io/outernet-foundation/placeframe"
GHCR_URL = "https://github.com/orgs/outernet-foundation/packages?repo_name=placeframe"

NUGET_PACKAGES: dict[str, str] = {
    "placeframe-api-client": "PlaceframeApiClient",
    "placeframe-zed-client": "PlaceframeZedClient",
}
NPM_PACKAGES: dict[str, str] = {
    "placeframe-core": "org.outernet.placeframe",
    "placeframe-arfoundation": "org.outernet.placeframe.arfoundation",
    "placeframe-magicleap": "org.outernet.placeframe.magicleap",
}

DOCKER_SERVICES = [
    "api",
    "state-sync",
    "auth-initializer",
    "cloudbeaver-initializer",
    "database-manager",
    "database-migrator",
    "gateway",
    "localizer-cuda",
    "localizer-rocm",
    "reconstructor-cuda",
    "reconstructor-rocm",
]


class Settings(BaseSettings):
    github_repository: str = "outernet-foundation/placeframe"


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


def _build_release_notes(context_sha: str) -> str:
    lines: list[str] = []

    lines.append("## Docker images")
    lines.append("")
    lines.append(f"All images tagged `{context_sha}` on [GHCR]({GHCR_URL}).")
    lines.append("")
    for service in DOCKER_SERVICES:
        lines.append(f"- `{GHCR_BASE}/{service}:{context_sha}`")
    lines.append("")

    lines.append("## Packages")
    lines.append("")
    lines.append("| Package | Version | Registry |")
    lines.append("|---|---|---|")
    for tag_prefix, nuget_name in NUGET_PACKAGES.items():
        version = get_latest_tag_version(f"{tag_prefix}-v") or "—"
        url = f"https://www.nuget.org/packages/{nuget_name}/{version}" if version != "—" else ""
        link = f"[NuGet]({url})" if url else "NuGet"
        lines.append(f"| {nuget_name} | {version} | {link} |")
    for tag_prefix, npm_name in NPM_PACKAGES.items():
        version = get_latest_tag_version(f"{tag_prefix}-v") or "—"
        url = f"https://www.npmjs.com/package/{npm_name}/v/{version}" if version != "—" else ""
        link = f"[npm]({url})" if url else "npm"
        lines.append(f"| {npm_name} | {version} | {link} |")

    for app_name, tag_prefix in APP_TAG_PREFIXES.items():
        version = get_latest_tag_version(f"{tag_prefix}-v")
        if version:
            lines.append(f"| {app_name} | {version} | — |")

    lines.append("")
    return "\n".join(lines)


@app.command()
def main(run_number: int = typer.Option(..., help="GitHub Actions run number")) -> None:
    settings = Settings.model_validate({})
    tag = f"build-{run_number}"

    with ci_step("Compute context SHA"):
        context_sha = compute_context_sha(Path.cwd())
        print(f"  {context_sha}")

    with ci_step("Package artifacts"):
        assets = _package_artifacts()
        if assets:
            print(f"  {len(assets)} asset(s) ready for upload")
        else:
            print("  No build artifacts to attach")

    with ci_step("Create GitHub Release"):
        notes = _build_release_notes(context_sha)
        print(notes)

        asset_args = " ".join(f'"{a}"' for a in assets)
        with NamedTemporaryFile(mode="w", suffix=".md", delete=False) as f:
            f.write(notes)
            notes_path = f.name
        bash(
            f"gh release create {tag} --title {tag}"
            f" --notes-file {notes_path}"
            f" --repo {settings.github_repository}"
            f" {asset_args}"
        )
        Path(notes_path).unlink()
        print(f"  Release created: {tag}")
