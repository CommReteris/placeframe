from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest
from scripts.build_unity import build_project, find_unity_editor


@pytest.fixture()
def unity_project(tmp_path: Path) -> Path:
    project = tmp_path / "TestProject"
    project.mkdir()
    settings = project / "ProjectSettings"
    settings.mkdir()
    (settings / "ProjectVersion.txt").write_text("m_EditorVersion: 6000.0.66f1\n")
    return project


@pytest.fixture()
def fake_editor(tmp_path: Path) -> Path:
    editor = tmp_path / "unity-editor"
    editor.touch()
    editor.chmod(0o755)
    return editor


class TestBuildCommandLinux64:
    @patch("scripts.build_unity.run_command")
    def test_should_use_build_linux64_player_flag(
        self, mock_run: MagicMock, unity_project: Path, fake_editor: Path, tmp_path: Path
    ):
        build_project(unity_project, "linux64", tmp_path / "output", fake_editor)

        command = mock_run.call_args[0][0]
        assert "-buildLinux64Player" in command

    @patch("scripts.build_unity.run_command")
    def test_should_set_output_path_under_output_directory(
        self, mock_run: MagicMock, unity_project: Path, fake_editor: Path, tmp_path: Path
    ):
        build_project(unity_project, "linux64", tmp_path / "output", fake_editor)

        command = mock_run.call_args[0][0]
        expected_output = str(tmp_path / "output" / "TestProject" / "linux64" / "TestProject")
        assert expected_output in command


class TestBuildCommandWin64:
    @patch("scripts.build_unity.run_command")
    def test_should_use_build_windows64_player_flag(
        self, mock_run: MagicMock, unity_project: Path, fake_editor: Path, tmp_path: Path
    ):
        build_project(unity_project, "win64", tmp_path / "output", fake_editor)

        command = mock_run.call_args[0][0]
        assert "-buildWindows64Player" in command

    @patch("scripts.build_unity.run_command")
    def test_should_append_exe_extension(
        self, mock_run: MagicMock, unity_project: Path, fake_editor: Path, tmp_path: Path
    ):
        build_project(unity_project, "win64", tmp_path / "output", fake_editor)

        command = mock_run.call_args[0][0]
        assert "TestProject.exe" in command


class TestBuildCommandAndroidMobile:
    @patch("scripts.build_unity.run_command")
    def test_should_use_execute_method_flag(
        self, mock_run: MagicMock, unity_project: Path, fake_editor: Path, tmp_path: Path
    ):
        build_project(
            unity_project,
            "android-mobile",
            tmp_path / "output",
            fake_editor,
            execute_method="Test.Build.BuildForAndroidMobile",
        )

        command = mock_run.call_args[0][0]
        assert "-executeMethod Test.Build.BuildForAndroidMobile" in command

    @patch("scripts.build_unity.run_command")
    def test_should_include_build_target_android(
        self, mock_run: MagicMock, unity_project: Path, fake_editor: Path, tmp_path: Path
    ):
        build_project(
            unity_project,
            "android-mobile",
            tmp_path / "output",
            fake_editor,
            execute_method="Test.Build.BuildForAndroidMobile",
        )

        command = mock_run.call_args[0][0]
        assert "-buildTarget Android" in command

    @patch("scripts.build_unity.run_command")
    def test_should_not_include_standalone_build_flags(
        self, mock_run: MagicMock, unity_project: Path, fake_editor: Path, tmp_path: Path
    ):
        build_project(
            unity_project,
            "android-mobile",
            tmp_path / "output",
            fake_editor,
            execute_method="Test.Build.BuildForAndroidMobile",
        )

        command = mock_run.call_args[0][0]
        assert "-buildLinux64Player" not in command
        assert "-buildWindows64Player" not in command


class TestBuildCommandMagicLeap:
    @patch("scripts.build_unity.run_command")
    def test_should_use_execute_method_flag(
        self, mock_run: MagicMock, unity_project: Path, fake_editor: Path, tmp_path: Path
    ):
        build_project(
            unity_project, "magicleap", tmp_path / "output", fake_editor, execute_method="Test.Build.BuildForMagicLeap"
        )

        command = mock_run.call_args[0][0]
        assert "-executeMethod Test.Build.BuildForMagicLeap" in command

    @patch("scripts.build_unity.run_command")
    def test_should_include_build_target_android(
        self, mock_run: MagicMock, unity_project: Path, fake_editor: Path, tmp_path: Path
    ):
        build_project(
            unity_project, "magicleap", tmp_path / "output", fake_editor, execute_method="Test.Build.BuildForMagicLeap"
        )

        command = mock_run.call_args[0][0]
        assert "-buildTarget Android" in command


class TestEditorDiscovery:
    def test_should_use_unity_editor_env_var_when_set(self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch):
        editor = tmp_path / "Editor" / "Unity"
        editor.parent.mkdir(parents=True)
        editor.touch()
        monkeypatch.setenv("UNITY_EDITOR", str(tmp_path))

        result = find_unity_editor("6000.0.66f1")
        assert result == editor

    def test_should_use_default_path_when_env_var_not_set(self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch):
        monkeypatch.delenv("UNITY_EDITOR", raising=False)
        editor = tmp_path / "6000.0.66f1" / "Editor" / "Unity"
        editor.parent.mkdir(parents=True)
        editor.touch()
        monkeypatch.setattr("scripts.build_unity.DEFAULT_UNITY_PATH", tmp_path)

        result = find_unity_editor("6000.0.66f1")
        assert result == editor

    def test_should_exit_when_editor_not_found(self, monkeypatch: pytest.MonkeyPatch):
        monkeypatch.delenv("UNITY_EDITOR", raising=False)
        monkeypatch.setattr("scripts.build_unity.DEFAULT_UNITY_PATH", Path("/nonexistent"))

        with pytest.raises(SystemExit):
            find_unity_editor("6000.0.66f1")


class TestBuildProjectReturnValue:
    @patch("scripts.build_unity.run_command")
    def test_should_return_true_on_success(
        self, mock_run: MagicMock, unity_project: Path, fake_editor: Path, tmp_path: Path
    ):
        result = build_project(unity_project, "linux64", tmp_path / "output", fake_editor)
        assert result is True

    @patch("scripts.build_unity.run_command", side_effect=Exception("build failed"))
    def test_should_return_false_on_failure(
        self, mock_run: MagicMock, unity_project: Path, fake_editor: Path, tmp_path: Path
    ):
        result = build_project(unity_project, "linux64", tmp_path / "output", fake_editor)
        assert result is False
