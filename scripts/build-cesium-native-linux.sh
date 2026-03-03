#!/bin/bash
set -euo pipefail

# Build Cesium for Unity native plugin for Linux.
# Idempotent: safe to run from any starting state.
# Follows: https://github.com/JOHNI1/CesiumSetupLinuxGuide

BUILD_DIR="${1:-/tmp/cesium-build}"
OUTPUT_DIR="${2:-/tmp/cesium-output}"
CESIUM_VERSION="${CESIUM_VERSION:-v1.15.4}"
UNITY_VERSION="${UNITY_VERSION:-6000.0.66f1}"
UNITY_EDITOR="/opt/unity/${UNITY_VERSION}/Editor/Unity"

echo "=== Cesium for Unity Linux build ==="
echo "Build dir:  $BUILD_DIR"
echo "Output dir: $OUTPUT_DIR"
echo "Version:    $CESIUM_VERSION"
echo "Unity:      $UNITY_VERSION"
echo ""

# ── Install build dependencies ──────────────────────────────────────

install_if_missing() {
    if command -v "$1" &>/dev/null; then return; fi
    echo "Installing $2..."
    apt-get install -y -qq "$2"
}

if ! command -v cmake &>/dev/null || ! command -v ninja &>/dev/null || \
   ! command -v nasm &>/dev/null || ! command -v dotnet &>/dev/null || \
   ! command -v zip &>/dev/null; then
    echo "Installing build dependencies..."
    apt-get update -qq
fi

install_if_missing cmake cmake
install_if_missing ninja ninja-build
install_if_missing nasm nasm
install_if_missing g++ g++
install_if_missing zip zip
install_if_missing unzip unzip
install_if_missing curl curl

if ! command -v dotnet &>/dev/null; then
    echo "Installing .NET SDK 8.0..."
    apt-get install -y -qq wget
    wget -q "https://packages.microsoft.com/config/ubuntu/22.04/packages-microsoft-prod.deb" \
        -O /tmp/packages-microsoft-prod.deb
    dpkg -i /tmp/packages-microsoft-prod.deb
    rm /tmp/packages-microsoft-prod.deb
    apt-get update -qq
    apt-get install -y -qq dotnet-sdk-8.0
fi

mkdir -p "$BUILD_DIR" "$OUTPUT_DIR"

# ── Create minimal Unity project ────────────────────────────────────

UNITY_PROJECT="$BUILD_DIR/unity-project"
if [ ! -d "$UNITY_PROJECT/ProjectSettings" ]; then
    echo "Creating minimal Unity project..."
    mkdir -p "$UNITY_PROJECT/Assets" "$UNITY_PROJECT/ProjectSettings" "$UNITY_PROJECT/Packages"
    cat > "$UNITY_PROJECT/ProjectSettings/ProjectVersion.txt" <<EOF
m_EditorVersion: $UNITY_VERSION
EOF
    cat > "$UNITY_PROJECT/Packages/manifest.json" <<'EOF'
{
  "dependencies": {}
}
EOF
fi

# ── Clone cesium-unity ───────────────────────────────────────────────

CESIUM_PKG="$UNITY_PROJECT/Packages/com.cesium.unity"
if [ ! -d "$CESIUM_PKG/.git" ]; then
    echo "Cloning cesium-unity $CESIUM_VERSION (with submodules)..."
    rm -rf "$CESIUM_PKG"
    git clone --recurse-submodules -b "$CESIUM_VERSION" \
        https://github.com/CesiumGS/cesium-unity.git \
        "$CESIUM_PKG"
fi

cd "$CESIUM_PKG"

# ── Add LinuxStandalone64 to CesiumRuntime.asmdef ───────────────────

if ! grep -q "LinuxStandalone64" Runtime/CesiumRuntime.asmdef; then
    echo "Adding LinuxStandalone64 to CesiumRuntime.asmdef..."
    sed -i 's/"WindowsStandalone64"/"WindowsStandalone64",\n        "LinuxStandalone64"/' \
        Runtime/CesiumRuntime.asmdef
fi

# ── Build Reinterop ─────────────────────────────────────────────────

if [ ! -f Reinterop.dll ]; then
    echo "Building Reinterop..."
    dotnet publish Reinterop~ -o .
    git restore Reinterop.dll.meta 2>/dev/null || true
fi

# ── Open Unity to trigger Reinterop code generation ─────────────────

GENERATED_CHECK="native~/Runtime/generated-Editor/src/DotNet"
if [ ! -d "$GENERATED_CHECK" ]; then
    if [ ! -x "$UNITY_EDITOR" ]; then
        echo "FATAL: Unity editor not found at $UNITY_EDITOR"
        exit 1
    fi
    echo "Opening Unity to trigger Reinterop code generation..."
    echo "(DllNotFoundException warnings are expected — no native library yet)"
    echo ""
    xvfb-run "$UNITY_EDITOR" \
        -batchmode -nographics -quit \
        -projectPath "$UNITY_PROJECT" \
        -logFile /dev/stdout || true
    echo ""
    if [ ! -d "$GENERATED_CHECK" ]; then
        echo "FATAL: Code generation failed — $GENERATED_CHECK not found."
        echo "Check Unity log above for errors."
        exit 1
    fi
    echo "Code generation succeeded."
fi

# ── Create vcpkg triplet ────────────────────────────────────────────

TRIPLET_DIR="native~/vcpkg/triplets"
TRIPLET_FILE="$TRIPLET_DIR/x64-linux-unity.cmake"
if [ ! -f "$TRIPLET_FILE" ]; then
    echo "Creating vcpkg triplet..."
    mkdir -p "$TRIPLET_DIR"
    cat > "$TRIPLET_FILE" <<'EOF'
include("${CMAKE_CURRENT_LIST_DIR}/shared/common.cmake")
set(VCPKG_TARGET_ARCHITECTURE x64)
set(VCPKG_CRT_LINKAGE static)
set(VCPKG_LIBRARY_LINKAGE static)
set(VCPKG_CMAKE_SYSTEM_NAME Linux)
set(VCPKG_LIBRARY_PREFIX "")
EOF
fi

# ── Build Runtime .so ────────────────────────────────────────────────

cd native~

RUNTIME_SO="libCesiumForUnityNative-Runtime.so"
if [ ! -f "../Plugins/Standalone/$RUNTIME_SO" ]; then
    echo ""
    echo "Building Runtime native library..."
    echo "(First run may take 30-60 minutes for vcpkg dependency compilation)"
    cmake -B build-Standalone -S . \
        -DCMAKE_BUILD_TYPE=RelWithDebInfo \
        -DVCPKG_TRIPLET=x64-linux-unity \
        -DVCPKG_OVERLAY_TRIPLETS="$(pwd)/vcpkg/triplets" \
        -DEDITOR=OFF
    cmake --build build-Standalone --target install --parallel "$(nproc)"
fi

# ── Build Editor .so ─────────────────────────────────────────────────

EDITOR_SO="libCesiumForUnityNative-Editor.so"
if [ ! -f "../Editor/$EDITOR_SO" ]; then
    echo ""
    echo "Building Editor native library..."
    cmake -B build-Editor -S . \
        -DCMAKE_BUILD_TYPE=RelWithDebInfo \
        -DVCPKG_TRIPLET=x64-linux-unity \
        -DVCPKG_OVERLAY_TRIPLETS="$(pwd)/vcpkg/triplets" \
        -DEDITOR=ON
    cmake --build build-Editor --target install --parallel "$(nproc)"
fi

cd ..

# ── Copy outputs ─────────────────────────────────────────────────────

echo ""
echo "Copying build outputs to $OUTPUT_DIR..."

cp -f "Plugins/Standalone/$RUNTIME_SO" "$OUTPUT_DIR/" 2>/dev/null || true
cp -f "Editor/$EDITOR_SO" "$OUTPUT_DIR/" 2>/dev/null || true

echo ""
echo "=== Build complete ==="
echo "Package directory: $CESIUM_PKG"
echo ""
echo "Outputs in $OUTPUT_DIR:"
ls -lh "$OUTPUT_DIR/"*.so 2>/dev/null || echo "  (no .so files — check build log for errors)"
