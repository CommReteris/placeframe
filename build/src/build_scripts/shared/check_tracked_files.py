import shlex
from pathlib import Path

from common.bash import bash, bash_output


def check_tracked_files(project_path: Path, intended_output: set[str] | None = None) -> list[str]:
    relative_project = project_path.relative_to(Path.cwd()) if project_path.is_absolute() else project_path
    diff_output = bash_output(f"git diff --name-only -- {relative_project}").strip()

    if not diff_output:
        return []

    changed_files = set(diff_output.splitlines())

    intended = {str(relative_project / file) for file in intended_output} if intended_output else set[str]()

    unexpected = [file for file in changed_files if file not in intended]

    if unexpected:
        restore_args = " ".join(shlex.quote(file) for file in unexpected)
        bash(f"git checkout -- {restore_args}")

    return sorted(unexpected)
