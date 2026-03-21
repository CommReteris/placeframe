from __future__ import annotations

import os
import subprocess
from pathlib import Path
from tempfile import TemporaryDirectory

import pathspec


def compute_context_sha(repo_root: Path) -> str:
    repo_root = repo_root.resolve()
    all_files = subprocess.run(
        ["git", "ls-files"], cwd=str(repo_root), capture_output=True, text=True, check=True
    ).stdout.splitlines()

    dockerignore = repo_root / ".dockerignore"
    spec = pathspec.PathSpec.from_lines("gitignore", dockerignore.read_text().splitlines())
    visible_files = [f for f in all_files if not spec.match_file(f)]

    with TemporaryDirectory() as tmpdir:
        env = {**os.environ, "GIT_INDEX_FILE": str(Path(tmpdir) / "index")}
        pathspec_file = Path(tmpdir) / "pathspec"
        pathspec_file.write_text("\n".join(visible_files) + "\n")
        subprocess.run(
            ["git", "add", "--force", f"--pathspec-from-file={pathspec_file}"],
            cwd=str(repo_root),
            env=env,
            capture_output=True,
            check=True,
        )
        result = subprocess.run(
            ["git", "write-tree"], cwd=str(repo_root), env=env, capture_output=True, text=True, check=True
        )
        return f"tree-{result.stdout.strip()}"
