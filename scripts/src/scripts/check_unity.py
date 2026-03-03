import re
import sys
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


def check_compilation(project_path: Path, build_target: str) -> bool:
    version = read_editor_version(project_path)
    editor = find_unity_editor(version)
    print(f"\nChecking {project_path.name} [{build_target}] (Unity {version})")
    try:
        run_command(
            f"xvfb-run {editor} -batchmode -nographics -quit"
            f" -projectPath {project_path.resolve()}"
            f" -buildTarget {build_target}"
            f" -logFile /dev/stdout",
            stream_log=True,
        )
        print(f"  PASS: {project_path.name} [{build_target}]")
        return True
    except CalledProcessError:
        print(f"  FAIL: {project_path.name} [{build_target}]")
        return False


@app.command()
def check_unity(
    project: str | None = typer.Option(None, "--project", "-p", help="Check a specific project directory name."),
    target: str | None = typer.Option(None, "--target", "-t", help="Check a specific build target (android, linux64)."),
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
            passed = check_compilation(project_path, build_target)
            results.append((project_path.name, build_target, passed))

    print("\nResults:")
    for project_name, build_target, passed in results:
        status = "PASS" if passed else "FAIL"
        print(f"  {status}: {project_name} [{build_target}]")

    failures = [result for result in results if not result[2]]
    if failures:
        print(f"\n{len(failures)} check(s) failed.")
        sys.exit(1)
    print(f"\nAll {len(results)} check(s) passed.")


def main() -> None:
    app()


if __name__ == "__main__":
    main()
