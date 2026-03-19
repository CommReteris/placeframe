from __future__ import annotations

import sys
import tempfile
from pathlib import Path


def get_cesium_build_paths() -> tuple[Path, Path]:
    # On Windows, tempfile.gettempdir() returns a long path like
    # C:\Users\runneradmin\AppData\Local\Temp, which combined with Cesium's deeply
    # nested CMake build tree exceeds the 260-character MAX_PATH limit. MSVC fails with
    # "fatal error C1083: Cannot open compiler generated file: '': Invalid argument"
    # when the object file path is too long. Using a short root on Windows avoids this.
    if sys.platform == "win32":
        build_directory = Path("C:/cb")
    else:
        build_directory = Path(tempfile.gettempdir()) / "cesium-build"
    package_directory = build_directory / "CesiumForUnityBuildProject" / "Packages" / "com.cesium.unity"
    return build_directory, package_directory
