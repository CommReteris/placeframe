from unittest.mock import MagicMock, call, patch

import pytest
from pydantic import ValidationError
from scripts.tidy_commits_wrapper import Commit, Committer, TidyCommitsPlan, execute_plan


def make_committer() -> Committer:
    return Committer(name="Test User", email="test@example.com")


def make_plan(commits: list[Commit]) -> TidyCommitsPlan:
    return TidyCommitsPlan(committer=make_committer(), commits=commits)


class TestCommitValidator:
    def test_should_accept_commit_with_only_rename(self):
        commit = Commit(message="rename files", author="Test <test@example.com>", rename={"old/path.md": "new/path.md"})
        assert commit.rename == {"old/path.md": "new/path.md"}

    def test_should_accept_commit_with_only_checkout_ref(self):
        commit = Commit(
            message="restore from ref", author="Test <test@example.com>", checkout_ref={"abc123": ["file.md"]}
        )
        assert commit.checkout_ref == {"abc123": ["file.md"]}

    def test_should_reject_commit_with_no_operations(self):
        with pytest.raises(ValidationError, match="no file operations"):
            Commit(message="empty", author="Test <test@example.com>")

    def test_should_accept_commit_with_existing_checkout_field(self):
        commit = Commit(message="checkout files", author="Test <test@example.com>", checkout=["file.md"])
        assert commit.checkout == ["file.md"]

    def test_should_accept_commit_with_existing_delete_field(self):
        commit = Commit(message="delete files", author="Test <test@example.com>", delete=["file.md"])
        assert commit.delete == ["file.md"]

    def test_should_accept_commit_with_existing_content_field(self):
        commit = Commit(message="write content", author="Test <test@example.com>", content={"file.md": "hello"})
        assert commit.content == {"file.md": "hello"}


class TestExecutePlanRename:
    @patch("scripts.tidy_commits_wrapper.Path")
    @patch("scripts.tidy_commits_wrapper.run_command")
    def test_should_checkout_from_backup_then_git_mv(self, mock_run: MagicMock, mock_path: MagicMock):
        plan = make_plan([
            Commit(message="rename file", author="Test <test@example.com>", rename={"old/file.md": "new/file.md"})
        ])

        execute_plan(plan, branch="feature", base="abc000", backup="feature-backup")

        assert call(["git", "checkout", "feature-backup", "--", "old/file.md"]) in mock_run.call_args_list
        assert call(["git", "mv", "old/file.md", "new/file.md"]) in mock_run.call_args_list

    @patch("scripts.tidy_commits_wrapper.Path")
    @patch("scripts.tidy_commits_wrapper.run_command")
    def test_should_create_parent_directories_for_new_path(self, mock_run: MagicMock, mock_path: MagicMock):
        mock_path_instance = MagicMock()
        mock_path.return_value = mock_path_instance
        mock_parent = MagicMock()
        mock_path_instance.parent = mock_parent

        plan = make_plan([
            Commit(
                message="rename to nested dir",
                author="Test <test@example.com>",
                rename={"file.md": "deep/nested/dir/file.md"},
            )
        ])

        execute_plan(plan, branch="feature", base="abc000", backup="feature-backup")

        mock_path.assert_any_call("deep/nested/dir/file.md")
        mock_parent.mkdir.assert_called_with(parents=True, exist_ok=True)

    @patch("scripts.tidy_commits_wrapper.Path")
    @patch("scripts.tidy_commits_wrapper.run_command")
    def test_should_handle_multiple_renames_in_one_commit(self, mock_run: MagicMock, mock_path: MagicMock):
        plan = make_plan([
            Commit(message="rename multiple", author="Test <test@example.com>", rename={"a.md": "x.md", "b.md": "y.md"})
        ])

        execute_plan(plan, branch="feature", base="abc000", backup="feature-backup")

        assert call(["git", "checkout", "feature-backup", "--", "a.md"]) in mock_run.call_args_list
        assert call(["git", "mv", "a.md", "x.md"]) in mock_run.call_args_list
        assert call(["git", "checkout", "feature-backup", "--", "b.md"]) in mock_run.call_args_list
        assert call(["git", "mv", "b.md", "y.md"]) in mock_run.call_args_list


class TestExecutePlanCheckoutRef:
    @patch("scripts.tidy_commits_wrapper.Path")
    @patch("scripts.tidy_commits_wrapper.run_command")
    def test_should_git_checkout_from_ref(self, mock_run: MagicMock, mock_path: MagicMock):
        plan = make_plan([
            Commit(message="restore from ref", author="Test <test@example.com>", checkout_ref={"abc123": ["file.md"]})
        ])

        execute_plan(plan, branch="feature", base="abc000", backup="feature-backup")

        assert call(["git", "checkout", "abc123", "--", "file.md"]) in mock_run.call_args_list

    @patch("scripts.tidy_commits_wrapper.Path")
    @patch("scripts.tidy_commits_wrapper.run_command")
    def test_should_handle_multiple_files_per_ref(self, mock_run: MagicMock, mock_path: MagicMock):
        plan = make_plan([
            Commit(
                message="restore multiple",
                author="Test <test@example.com>",
                checkout_ref={"abc123": ["file1.md", "file2.md"]},
            )
        ])

        execute_plan(plan, branch="feature", base="abc000", backup="feature-backup")

        assert call(["git", "checkout", "abc123", "--", "file1.md", "file2.md"]) in mock_run.call_args_list

    @patch("scripts.tidy_commits_wrapper.Path")
    @patch("scripts.tidy_commits_wrapper.run_command")
    def test_should_handle_multiple_refs_in_one_commit(self, mock_run: MagicMock, mock_path: MagicMock):
        plan = make_plan([
            Commit(
                message="restore from multiple refs",
                author="Test <test@example.com>",
                checkout_ref={"abc123": ["file1.md"], "def456": ["file2.md"]},
            )
        ])

        execute_plan(plan, branch="feature", base="abc000", backup="feature-backup")

        assert call(["git", "checkout", "abc123", "--", "file1.md"]) in mock_run.call_args_list
        assert call(["git", "checkout", "def456", "--", "file2.md"]) in mock_run.call_args_list


class TestExecutePlanOperationOrdering:
    @patch("scripts.tidy_commits_wrapper.Path")
    @patch("scripts.tidy_commits_wrapper.run_command")
    def test_should_execute_operations_in_correct_order(self, mock_run: MagicMock, mock_path: MagicMock):
        mock_path_instance = MagicMock()
        mock_path.return_value = mock_path_instance
        mock_path_instance.parent = MagicMock()

        plan = make_plan([
            Commit(
                message="all operations",
                author="Test <test@example.com>",
                checkout=["checked_out.md"],
                checkout_ref={"ref123": ["from_ref.md"]},
                rename={"old.md": "new.md"},
                delete=["deleted.md"],
                content={"written.md": "content"},
            )
        ])

        execute_plan(plan, branch="feature", base="abc000", backup="feature-backup")

        git_calls = [c for c in mock_run.call_args_list if isinstance(c[0][0], list)]
        # Filter to the operation calls (skip the initial branch checkout and final commit/branch ops)
        operation_calls = git_calls[1:-4]  # skip "git checkout -b" and final commit + 3 branch ops

        # Find indices of each operation type
        checkout_index = next(
            i
            for i, c in enumerate(operation_calls)
            if c == call(["git", "checkout", "feature-backup", "--", "checked_out.md"])
        )
        checkout_ref_index = next(
            i for i, c in enumerate(operation_calls) if c == call(["git", "checkout", "ref123", "--", "from_ref.md"])
        )
        rename_checkout_index = next(
            i for i, c in enumerate(operation_calls) if c == call(["git", "checkout", "feature-backup", "--", "old.md"])
        )
        rename_mv_index = next(i for i, c in enumerate(operation_calls) if c == call(["git", "mv", "old.md", "new.md"]))
        delete_index = next(i for i, c in enumerate(operation_calls) if c == call(["git", "rm", "deleted.md"]))
        content_add_index = next(i for i, c in enumerate(operation_calls) if c == call(["git", "add", "written.md"]))

        assert checkout_index < checkout_ref_index
        assert checkout_ref_index < rename_checkout_index
        assert rename_checkout_index < rename_mv_index
        assert rename_mv_index < delete_index
        assert delete_index < content_add_index


class TestExecutePlanExistingFields:
    @patch("scripts.tidy_commits_wrapper.Path")
    @patch("scripts.tidy_commits_wrapper.run_command")
    def test_should_still_handle_checkout_field(self, mock_run: MagicMock, mock_path: MagicMock):
        plan = make_plan([Commit(message="checkout only", author="Test <test@example.com>", checkout=["file.md"])])

        execute_plan(plan, branch="feature", base="abc000", backup="feature-backup")

        assert call(["git", "checkout", "feature-backup", "--", "file.md"]) in mock_run.call_args_list

    @patch("scripts.tidy_commits_wrapper.Path")
    @patch("scripts.tidy_commits_wrapper.run_command")
    def test_should_still_handle_delete_field(self, mock_run: MagicMock, mock_path: MagicMock):
        plan = make_plan([Commit(message="delete only", author="Test <test@example.com>", delete=["file.md"])])

        execute_plan(plan, branch="feature", base="abc000", backup="feature-backup")

        assert call(["git", "rm", "file.md"]) in mock_run.call_args_list

    @patch("scripts.tidy_commits_wrapper.Path")
    @patch("scripts.tidy_commits_wrapper.run_command")
    def test_should_still_handle_content_field(self, mock_run: MagicMock, mock_path: MagicMock):
        mock_path_instance = MagicMock()
        mock_path.return_value = mock_path_instance
        mock_path_instance.parent = MagicMock()

        plan = make_plan([
            Commit(message="content only", author="Test <test@example.com>", content={"file.md": "hello world"})
        ])

        execute_plan(plan, branch="feature", base="abc000", backup="feature-backup")

        mock_path_instance.write_text.assert_called_with("hello world")
        assert call(["git", "add", "file.md"]) in mock_run.call_args_list
