from __future__ import annotations

import os
import subprocess
from pathlib import Path
from tempfile import TemporaryDirectory

import pathspec


def compute_context_sha(repo_root: Path) -> str:
    repo_root = repo_root.resolve()

    tree_entries = subprocess.run(
        ["git", "ls-tree", "-r", "HEAD"], cwd=str(repo_root), capture_output=True, text=True, check=True
    ).stdout.splitlines()

    dockerignore = repo_root / ".dockerignore"
    spec = pathspec.PathSpec.from_lines("gitignore", dockerignore.read_text().splitlines())

    index_info_lines: list[str] = []
    for entry in tree_entries:
        meta, path = entry.split("\t", 1)
        if spec.match_file(path):
            continue
        mode, _type, obj_hash = meta.split()
        index_info_lines.append(f"{mode} {obj_hash}\t{path}")

    index_input = "\n".join(index_info_lines) + "\n" if index_info_lines else ""

    with TemporaryDirectory() as tmpdir:
        env = {**os.environ, "GIT_INDEX_FILE": str(Path(tmpdir) / "index")}
        subprocess.run(
            ["git", "update-index", "--index-info"],
            cwd=str(repo_root),
            env=env,
            input=index_input.encode(),
            capture_output=True,
            check=True,
        )
        result = subprocess.run(
            ["git", "write-tree"], cwd=str(repo_root), env=env, capture_output=True, text=True, check=True
        )
        return f"tree-{result.stdout.strip()}"
