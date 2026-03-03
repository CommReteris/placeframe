import re
import sys
import tempfile
from pathlib import Path
from subprocess import CalledProcessError

import typer
from common.run_command import run_command

UNITY_PROJECTS = [
    Path("apps/AndroidMobile"),
    Path("apps/MapRegistrationTool"),
    Path("apps/MakeItSing"),
    Path("legacy/Outernet.Client"),
]

BUILD_TARGETS = ["android", "linux64"]

UNITY_INSTALL_PATH = Path("/opt/unity")

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
    editor_path = UNITY_INSTALL_PATH / version / "Editor" / "Unity"
    if not editor_path.exists():
        print(f"ERROR: Unity editor not found at {editor_path}")
        print("Rebuild the COI image: uv run setup-agent-sandbox --rebuild")
        sys.exit(1)
    return editor_path


def build_project(project_path: Path, build_target: str, output_directory: Path) -> bool:
    version = read_editor_version(project_path)
    editor = find_unity_editor(version)

    if build_target == "linux64":
        output_path = output_directory / project_path.name / "linux64" / project_path.name
        output_path.parent.mkdir(parents=True, exist_ok=True)
        print(f"\nBuilding {project_path.name} [{build_target}] (Unity {version})")
        print(f"  Output: {output_path}")
        command = (
            f"xvfb-run {editor} -batchmode -nographics -quit"
            f" -projectPath {project_path.resolve()}"
            f" -buildLinux64Player {output_path}"
            f" -logFile /dev/stdout"
        )
    else:
        print(f"\nCompiling {project_path.name} [{build_target}] (Unity {version})")
        print(f"  (compilation check only — no {build_target} toolchain available)")
        command = (
            f"xvfb-run {editor} -batchmode -nographics -quit"
            f" -projectPath {project_path.resolve()}"
            f" -buildTarget {build_target}"
            f" -logFile /dev/stdout"
        )

    try:
        run_command(command, stream_log=True)
        print(f"  PASS: {project_path.name} [{build_target}]")
        return True
    except CalledProcessError:
        print(f"  FAIL: {project_path.name} [{build_target}]")
        return False


@app.command()
def build_unity(
    project: str | None = typer.Option(None, "--project", "-p", help="Build a specific project by directory name."),
    target: str | None = typer.Option(None, "--target", "-t", help="Build for a specific target (android, linux64)."),
    output: Path = typer.Option(
        Path(tempfile.gettempdir()) / "unity-builds", "--output", "-o", help="Output directory for build artifacts."
    ),
) -> None:
    projects = UNITY_PROJECTS
    if project:
        projects = [path for path in UNITY_PROJECTS if path.name == project]
        if not projects:
            print(f"ERROR: Unknown project '{project}'. Available: {', '.join(path.name for path in UNITY_PROJECTS)}")
            sys.exit(1)

    targets = BUILD_TARGETS
    if target:
        if target not in BUILD_TARGETS:
            print(f"ERROR: Unknown target '{target}'. Available: {', '.join(BUILD_TARGETS)}")
            sys.exit(1)
        targets = [target]

    results: list[tuple[str, str, bool]] = []
    for project_path in projects:
        if not project_path.exists():
            print(f"WARNING: Project not found: {project_path}")
            continue
        for build_target in targets:
            passed = build_project(project_path, build_target, output)
            results.append((project_path.name, build_target, passed))

    print("\nResults:")
    for project_name, build_target, passed in results:
        status = "PASS" if passed else "FAIL"
        mode = "build" if build_target == "linux64" else "compile"
        print(f"  {status}: {project_name} [{build_target}] ({mode})")

    failures = [result for result in results if not result[2]]
    if failures:
        print(f"\n{len(failures)} build(s) failed.")
        sys.exit(1)
    print(f"\nAll {len(results)} build(s) passed.")


def main() -> None:
    app()


if __name__ == "__main__":
    main()
