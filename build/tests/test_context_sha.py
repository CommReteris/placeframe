import subprocess
from pathlib import Path

import pytest
from build_scripts.placeframe.context_sha import compute_context_sha


def _init_repo(path: Path) -> None:
    subprocess.run(["git", "init"], cwd=str(path), capture_output=True, check=True)
    subprocess.run(["git", "config", "user.email", "test@test.com"], cwd=str(path), capture_output=True, check=True)
    subprocess.run(["git", "config", "user.name", "Test"], cwd=str(path), capture_output=True, check=True)


def _commit_all(path: Path) -> None:
    subprocess.run(["git", "add", "-A"], cwd=str(path), capture_output=True, check=True)
    subprocess.run(["git", "commit", "-m", "init", "--allow-empty"], cwd=str(path), capture_output=True, check=True)


@pytest.fixture()
def repo(tmp_path: Path) -> Path:
    _init_repo(tmp_path)
    (tmp_path / ".dockerignore").write_text("*\n!docker/\n!packages/\n")
    (tmp_path / "docker").mkdir()
    (tmp_path / "docker" / "app.py").write_text("print('hello')")
    (tmp_path / "packages").mkdir()
    (tmp_path / "packages" / "lib.py").write_text("x = 1")
    (tmp_path / "README.md").write_text("ignored")
    _commit_all(tmp_path)
    return tmp_path


class TestComputeContextSha:
    def test_should_return_deterministic_hash(self, repo: Path):
        sha1 = compute_context_sha(repo)
        sha2 = compute_context_sha(repo)

        assert sha1 == sha2

    def test_should_have_tree_prefix(self, repo: Path):
        sha = compute_context_sha(repo)

        assert sha.startswith("tree-")

    def test_should_change_when_visible_file_changes(self, repo: Path):
        sha_before = compute_context_sha(repo)

        (repo / "docker" / "app.py").write_text("print('changed')")
        _commit_all(repo)

        sha_after = compute_context_sha(repo)
        assert sha_before != sha_after

    def test_should_not_change_when_ignored_file_changes(self, repo: Path):
        sha_before = compute_context_sha(repo)

        (repo / "README.md").write_text("changed readme")
        _commit_all(repo)

        sha_after = compute_context_sha(repo)
        assert sha_before == sha_after

    def test_should_include_files_in_allowlisted_subdirectories(self, repo: Path):
        sha_before = compute_context_sha(repo)

        (repo / "packages" / "new.py").write_text("new file")
        _commit_all(repo)

        sha_after = compute_context_sha(repo)
        assert sha_before != sha_after

    def test_should_exclude_files_not_in_allowlist(self, repo: Path):
        sha_before = compute_context_sha(repo)

        (repo / "scripts").mkdir()
        (repo / "scripts" / "tool.py").write_text("tool")
        _commit_all(repo)

        sha_after = compute_context_sha(repo)
        assert sha_before == sha_after

    def test_should_not_change_from_uncommitted_edits(self, repo: Path):
        sha_before = compute_context_sha(repo)

        (repo / "docker" / "app.py").write_text("print('uncommitted')")

        sha_after = compute_context_sha(repo)
        assert sha_before == sha_after

    def test_should_preserve_file_modes(self, repo: Path):
        subprocess.run(
            ["git", "update-index", "--chmod=+x", "docker/app.py"], cwd=str(repo), capture_output=True, check=True
        )
        subprocess.run(["git", "commit", "-m", "chmod"], cwd=str(repo), capture_output=True, check=True)

        sha_with_exec = compute_context_sha(repo)

        subprocess.run(
            ["git", "update-index", "--chmod=-x", "docker/app.py"], cwd=str(repo), capture_output=True, check=True
        )
        subprocess.run(["git", "commit", "-m", "unchmod"], cwd=str(repo), capture_output=True, check=True)

        sha_without_exec = compute_context_sha(repo)
        assert sha_with_exec != sha_without_exec
