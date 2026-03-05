from __future__ import annotations

import multiprocessing
import os
import sys
from pathlib import Path

import typer
from common.run_command import check_command, run_command

CESIUM_SAMPLES_REPO = "https://github.com/CesiumGS/cesium-unity-samples.git"
CESIUM_UNITY_REPO = "https://github.com/CesiumGS/cesium-unity.git"
GENERATED_HEADER = "native~/Runtime/generated-Editor/include/DotNet/System/Action1.h"
VCPKG_TRIPLET_CONTENT = """\
include("${CMAKE_CURRENT_LIST_DIR}/shared/common.cmake")
set(VCPKG_TARGET_ARCHITECTURE x64)
set(VCPKG_CRT_LINKAGE static)
set(VCPKG_LIBRARY_LINKAGE static)
set(VCPKG_CMAKE_SYSTEM_NAME Linux)
"""

DEFAULT_UNITY_PATH = Path("/opt/unity")

app = typer.Typer(add_completion=False, pretty_exceptions_show_locals=False)


def find_unity_editor(unity_version: str) -> str:
    override = os.environ.get("UNITY_EDITOR")
    if override:
        return override
    editor_path = DEFAULT_UNITY_PATH / unity_version / "Editor" / "Unity"
    if not editor_path.exists():
        print(f"FATAL: Unity editor not found at {editor_path}")
        print("Set UNITY_EDITOR env var or install Unity at the expected path.")
        sys.exit(1)
    return str(editor_path)


def build_native_library(package_path: Path, variant: str, editor_mode: bool) -> None:
    if variant == "Editor":
        output_file = package_path / "Editor" / "libCesiumForUnityNative-Editor.so"
        install_prefix = package_path / "Editor"
    else:
        output_file = package_path / "Plugins" / "Standalone" / "libCesiumForUnityNative-Runtime.so"
        install_prefix = package_path / "Plugins" / "Standalone"

    if output_file.exists():
        print(f"{variant} native library already built.")
        return

    native_directory = package_path / "native~"
    build_directory_name = f"build-{variant}"

    print(f"\nBuilding {variant} native library...")
    if variant == "Editor":
        print("(First run may take 30-60 minutes for vcpkg dependency compilation)")

    run_command(
        f"cmake -B {build_directory_name} -S . "
        f"-DCMAKE_BUILD_TYPE=RelWithDebInfo "
        f"-DCMAKE_INSTALL_PREFIX={install_prefix} "
        f"-DVCPKG_TRIPLET=x64-linux-unity "
        f"-DVCPKG_OVERLAY_TRIPLETS={native_directory / 'vcpkg' / 'triplets'} "
        f"-DEDITOR={'ON' if editor_mode else 'OFF'}",
        cwd=native_directory,
        stream_log=True,
    )
    run_command(
        f"cmake --build {build_directory_name} --target install --parallel {multiprocessing.cpu_count()}",
        cwd=native_directory,
        stream_log=True,
    )


def phase_clone(build_directory: Path, cesium_version: str) -> None:
    project_path = build_directory / "cesium-unity-samples"
    if not (project_path / ".git").is_dir():
        print("Cloning cesium-unity-samples...")
        run_command(f"git clone --recurse-submodules {CESIUM_SAMPLES_REPO} {project_path}", stream_log=True)
    else:
        print(f"cesium-unity-samples already cloned at {project_path}")

    package_path = project_path / "Packages" / "com.cesium.unity"
    if not (package_path / ".git").is_dir():
        print(f"Cloning cesium-unity {cesium_version}...")
        if package_path.exists():
            run_command(f"rm -rf {package_path}")
        run_command(
            f"git clone --recurse-submodules -b {cesium_version} {CESIUM_UNITY_REPO} {package_path}", stream_log=True
        )
    else:
        print(f"cesium-unity already cloned at {package_path}")


def phase_codegen(editor: str, project_path: Path, package_path: Path) -> None:
    if not check_command("which dotnet"):
        print("Installing .NET SDK 8.0...")
        run_command(
            "wget -q https://packages.microsoft.com/config/ubuntu/22.04/packages-microsoft-prod.deb"
            " -O /tmp/packages-microsoft-prod.deb",
            stream_log=True,
        )
        run_command("dpkg -i /tmp/packages-microsoft-prod.deb", stream_log=True)
        run_command("rm /tmp/packages-microsoft-prod.deb")
        run_command("apt-get update -qq", stream_log=True)
        run_command("apt-get install -y -qq dotnet-sdk-8.0", stream_log=True)

    asmdef_file = package_path / "Runtime" / "CesiumRuntime.asmdef"
    asmdef_content = asmdef_file.read_text()
    if "LinuxStandalone64" not in asmdef_content:
        print("Adding LinuxStandalone64 to CesiumRuntime.asmdef...")
        asmdef_file.write_text(
            asmdef_content.replace('"WindowsStandalone64"', '"WindowsStandalone64",\n        "LinuxStandalone64"')
        )

    if not (package_path / "Reinterop.dll").exists():
        print("Building Reinterop...")
        run_command("dotnet publish Reinterop~ -o .", cwd=package_path, stream_log=True)
        check_command("git restore Reinterop.dll.meta", cwd=package_path)

    generated_header = package_path / GENERATED_HEADER
    if not generated_header.exists():
        for pass_number in range(1, 3):
            print(f"Opening Unity to trigger Reinterop code generation (pass {pass_number})...")
            print("(DllNotFoundException warnings are expected — no native library yet)")
            check_command(
                f"xvfb-run {editor} -batchmode -nographics -quit -projectPath {project_path} -logFile /dev/stdout",
                stream_output=True,
            )
            if generated_header.exists():
                print("Code generation succeeded.")
                break
        else:
            print(f"FATAL: Code generation incomplete after two passes. Missing: {generated_header}")
            sys.exit(1)
    else:
        print("Reinterop code generation already complete.")


def phase_native_build(package_path: Path) -> None:
    dependencies = [
        ("cmake", "cmake"),
        ("ninja", "ninja-build"),
        ("nasm", "nasm"),
        ("g++", "g++"),
        ("zip", "zip"),
        ("unzip", "unzip"),
        ("curl", "curl"),
        ("pkg-config", "pkg-config"),
    ]
    missing = [(command, package) for command, package in dependencies if not check_command(f"which {command}")]
    if missing:
        print(f"Installing {len(missing)} missing build dependencies...")
        run_command("apt-get update -qq", stream_log=True)
        for _, package in missing:
            run_command(f"apt-get install -y -qq {package}", stream_log=True)

    triplet_file = package_path / "native~" / "vcpkg" / "triplets" / "x64-linux-unity.cmake"
    if not triplet_file.exists():
        print("Creating x64-linux-unity vcpkg triplet...")
        triplet_file.write_text(VCPKG_TRIPLET_CONTENT)

    build_native_library(package_path, "Editor", editor_mode=True)
    build_native_library(package_path, "Standalone", editor_mode=False)

    binaries_to_strip = [
        str(path)
        for path in [
            package_path / "Editor" / "libCesiumForUnityNative-Editor.so",
            package_path / "Editor" / "libCesiumForUnityNative-Runtime.so",
            package_path / "Plugins" / "Standalone" / "libCesiumForUnityNative-Runtime.so",
        ]
        if path.exists()
    ]
    if binaries_to_strip:
        print("Stripping debug symbols...")
        run_command(f"strip {' '.join(binaries_to_strip)}", stream_log=True)

    print(f"\nPackage directory: {package_path}")
    for label, path in [
        ("Editor .so", package_path / "Editor" / "libCesiumForUnityNative-Editor.so"),
        ("Runtime .so", package_path / "Plugins" / "Standalone" / "libCesiumForUnityNative-Runtime.so"),
    ]:
        if path.exists():
            print(f"  {label}: {path.stat().st_size / (1024 * 1024):.1f} MB")
        else:
            print(f"  {label}: (not found)")


@app.command()
def build_cesium_native_linux(
    build_directory: Path = typer.Option(Path("/tmp/cesium-build"), "--build-dir", help="Build working directory."),
    cesium_version: str = typer.Option("v1.15.3", "--cesium-version", help="Cesium for Unity git tag to build."),
    unity_version: str = typer.Option("6000.0.66f1", "--unity-version", help="Unity editor version."),
    phase: str = typer.Option("all", "--phase", help="Build phase: 'clone', 'codegen', 'native-build', or 'all'."),
) -> None:
    if phase not in ("all", "clone", "codegen", "native-build"):
        print(f"FATAL: Unknown phase '{phase}'. Use 'clone', 'codegen', 'native-build', or 'all'.")
        sys.exit(1)

    editor = find_unity_editor(unity_version)
    print(f"Build dir: {build_directory}")
    print(f"Version:   {cesium_version}")
    print(f"Unity:     {unity_version}")
    print(f"Editor:    {editor}")
    print(f"Phase:     {phase}")
    print()

    build_directory.mkdir(parents=True, exist_ok=True)
    project_path = build_directory / "cesium-unity-samples"
    package_path = project_path / "Packages" / "com.cesium.unity"

    if phase in ("all", "clone"):
        phase_clone(build_directory, cesium_version)
        if phase == "clone":
            return

    if phase in ("all", "codegen"):
        phase_codegen(editor, project_path, package_path)

    if phase in ("all", "native-build"):
        phase_native_build(package_path)


def main() -> None:
    app()


if __name__ == "__main__":
    main()
