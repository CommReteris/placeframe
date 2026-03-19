import shutil
import sys
from pathlib import Path

from common.bash import bash


def find_unity_editor(project_path: Path) -> str:
    if shutil.which("unity-editor"):
        return "unity-editor"

    version_file = project_path / "ProjectSettings" / "ProjectVersion.txt"
    if not version_file.exists():
        raise SystemExit(f"Cannot find {version_file} — is this a Unity project?")

    version = None
    for line in version_file.read_text().splitlines():
        if line.startswith("m_EditorVersion:"):
            version = line.split(":", 1)[1].strip()
            break
    if not version:
        raise SystemExit(f"Cannot parse editor version from {version_file}")

    if sys.platform == "win32":
        candidates = [Path(f"C:/Program Files/Unity/Hub/Editor/{version}/Editor/Unity.exe")]
    else:
        candidates = [
            Path(f"/opt/unity/{version}/Editor/Unity"),
            Path.home() / f"Unity/Hub/Editor/{version}/Editor/Unity",
        ]

    for candidate in candidates:
        if candidate.exists():
            return str(candidate)

    searched = ", ".join(str(c) for c in candidates)
    raise SystemExit(f"Cannot find Unity {version} editor. Searched: {searched}")


def prepare_unity_project(project_path: Path) -> None:
    stale_lockfile = project_path / "Temp" / "UnityLockfile"
    if stale_lockfile.exists():
        stale_lockfile.unlink()

    bash("dotnet tool restore")
    bash(f"dotnet nugetforunity restore {project_path}")


def unity_batchmode_command(project_path: Path) -> str:
    editor = find_unity_editor(project_path)
    command = f"{editor} -batchmode -nographics -quit -projectPath {project_path.resolve()}"
    if sys.platform != "win32" and shutil.which("xvfb-run"):
        command = f"xvfb-run {command}"
    return command
