import os
import re
import sys
import tempfile
from pathlib import Path

import typer
from common.run_command import run_command

UNITY_PROJECTS = [Path("apps/AndroidMobile"), Path("apps/MapRegistrationTool"), Path("legacy/Outernet.Client")]

PLATFORMS = ["android-mobile", "magicleap", "linux64", "win64"]

BUILD_MATRIX: dict[str, list[str]] = {
    "Outernet.Client": ["android-mobile", "magicleap", "linux64", "win64"],
    "MapRegistrationTool": ["linux64", "win64"],
    "AndroidMobile": ["android-mobile"],
}

EXECUTE_METHODS: dict[str, dict[str, str]] = {
    "Outernet.Client": {
        "android-mobile": "Outernet.Client.Build.BuildForAndroidMobile",
        "magicleap": "Outernet.Client.Build.BuildForMagicLeap",
    },
    "AndroidMobile": {"android-mobile": "Placeframe.Client.Build.BuildForAndroidMobile"},
}

DEFAULT_UNITY_PATH = Path("/opt/unity")

app = typer.Typer(add_completion=False, pretty_exceptions_show_locals=False)


def read_editor_version(project_path: Path) -> str:
    version_file = project_path / "ProjectSettings" / "ProjectVersion.txt"
    for line in version_file.read_text().splitlines():
        match = re.match(r"m_EditorVersion:\s+(.+)", line)
        if match:
            return match.group(1).strip()
    print(f"ERROR: Could not parse editor version from {version_file}")
    sys.exit(1)


def find_unity_editor(version: str) -> Path:
    unity_editor_override = os.environ.get("UNITY_EDITOR")
    if unity_editor_override:
        editor_path = Path(unity_editor_override) / "Editor" / "Unity"
    else:
        editor_path = DEFAULT_UNITY_PATH / version / "Editor" / "Unity"
    if not editor_path.exists():
        print(f"ERROR: Unity editor not found at {editor_path}")
        print("Set UNITY_EDITOR env var or rebuild the COI image: uv run setup-agent-sandbox --rebuild")
        sys.exit(1)
    return editor_path


def build_project(
    project_path: Path, platform: str, output_directory: Path, editor: Path, execute_method: str | None = None
) -> bool:
    print(f"\nBuilding {project_path.name} [{platform}]")

    base_command = f"xvfb-run {editor} -batchmode -nographics -quit -projectPath {project_path.resolve()}"

    if platform in ("android-mobile", "magicleap"):
        if not execute_method:
            print(f"ERROR: No execute method specified for {project_path.name} [{platform}]")
            return False
        command = f"{base_command} -buildTarget Android -executeMethod {execute_method} -logFile /dev/stdout"
    elif platform == "linux64":
        output_path = output_directory / project_path.name / "linux64" / project_path.name
        output_path.parent.mkdir(parents=True, exist_ok=True)
        print(f"  Output: {output_path}")
        command = f"{base_command} -buildLinux64Player {output_path} -logFile /dev/stdout"
    elif platform == "win64":
        output_path = output_directory / project_path.name / "win64" / (project_path.name + ".exe")
        output_path.parent.mkdir(parents=True, exist_ok=True)
        print(f"  Output: {output_path}")
        command = f"{base_command} -buildWindows64Player {output_path} -logFile /dev/stdout"
    else:
        print(f"ERROR: Unknown platform '{platform}'")
        return False

    try:
        run_command(command, stream_log=True)
        print(f"  PASS: {project_path.name} [{platform}]")
        return True
    except Exception:
        print(f"  FAIL: {project_path.name} [{platform}]")
        return False


@app.command()
def build_unity(
    project: str | None = typer.Option(None, "--project", "-p", help="Build a specific project by directory name."),
    platform: str | None = typer.Option(
        None, "--platform", "-t", help=f"Build for a specific platform ({', '.join(PLATFORMS)})."
    ),
    output: Path = typer.Option(
        Path(tempfile.gettempdir()) / "unity-builds", "--output", "-o", help="Output directory for build artifacts."
    ),
) -> None:
    if platform and platform not in PLATFORMS:
        print(f"ERROR: Unknown platform '{platform}'. Available: {', '.join(PLATFORMS)}")
        sys.exit(1)

    projects = UNITY_PROJECTS
    if project:
        projects = [path for path in UNITY_PROJECTS if path.name == project]
        if not projects:
            print(f"ERROR: Unknown project '{project}'. Available: {', '.join(path.name for path in UNITY_PROJECTS)}")
            sys.exit(1)

    results: list[tuple[str, str, bool]] = []
    for project_path in projects:
        if not project_path.exists():
            print(f"WARNING: Project not found: {project_path}")
            continue

        version = read_editor_version(project_path)
        editor = find_unity_editor(version)
        valid_platforms = BUILD_MATRIX.get(project_path.name, [])
        platforms_to_build = [platform] if platform else valid_platforms

        for build_platform in platforms_to_build:
            if build_platform not in valid_platforms:
                print(f"WARNING: {project_path.name} does not support platform '{build_platform}', skipping")
                continue
            execute_method = EXECUTE_METHODS.get(project_path.name, {}).get(build_platform)
            passed = build_project(project_path, build_platform, output, editor, execute_method)
            results.append((project_path.name, build_platform, passed))

    if not results:
        print("No builds were executed.")
        sys.exit(1)

    print("\nResults:")
    for project_name, build_platform, passed in results:
        status = "PASS" if passed else "FAIL"
        print(f"  {status}: {project_name} [{build_platform}]")

    failures = [result for result in results if not result[2]]
    if failures:
        print(f"\n{len(failures)} build(s) failed.")
        sys.exit(1)
    print(f"\nAll {len(results)} build(s) passed.")


def main() -> None:
    app()


if __name__ == "__main__":
    main()
