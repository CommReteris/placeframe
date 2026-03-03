#!/bin/bash
set -euo pipefail

# Build Cesium for Unity native plugin for Linux.
# Follows the official Cesium developer setup:
#   https://cesium.com/learn/cesium-unity/ref-doc/developer-setup.html
# Idempotent: safe to run from any starting state.

BUILD_DIR="${1:-/tmp/cesium-build}"
CESIUM_VERSION="${CESIUM_VERSION:-v1.15.3}"
UNITY_VERSION="${UNITY_VERSION:-6000.0.66f1}"
UNITY_EDITOR="/opt/unity/${UNITY_VERSION}/Editor/Unity"

echo "=== Cesium for Unity Linux build ==="
echo "Build dir: $BUILD_DIR"
echo "Version:   $CESIUM_VERSION"
echo "Unity:     $UNITY_VERSION"
echo ""

# ── Install build dependencies ──────────────────────────────────────

install_if_missing() {
    if command -v "$1" &>/dev/null; then return; fi
    echo "Installing $2..."
    apt-get install -y -qq "$2"
}

if ! command -v cmake &>/dev/null || ! command -v ninja &>/dev/null || \
   ! command -v nasm &>/dev/null || ! command -v dotnet &>/dev/null; then
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
install_if_missing pkg-config pkg-config

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

mkdir -p "$BUILD_DIR"

# ── Clone cesium-unity-samples (the Unity project) ──────────────────

UNITY_PROJECT="$BUILD_DIR/cesium-unity-samples"
if [ ! -d "$UNITY_PROJECT/.git" ]; then
    echo "Cloning cesium-unity-samples..."
    git clone --recurse-submodules \
        https://github.com/CesiumGS/cesium-unity-samples.git \
        "$UNITY_PROJECT"
fi

# ── Clone cesium-unity into Packages/ ────────────────────────────────

CESIUM_PKG="$UNITY_PROJECT/Packages/com.cesium.unity"
if [ ! -d "$CESIUM_PKG/.git" ]; then
    echo "Cloning cesium-unity $CESIUM_VERSION..."
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

# ── Build Reinterop (Roslyn source generator) ───────────────────────

if [ ! -f Reinterop.dll ]; then
    echo "Building Reinterop..."
    dotnet publish Reinterop~ -o .
    git restore Reinterop.dll.meta 2>/dev/null || true
fi

# ── Open Unity to trigger Reinterop code generation ─────────────────

GENERATED_HEADER="native~/Runtime/generated-Editor/include/DotNet/System/Action1.h"

run_unity_codegen() {
    if [ ! -x "$UNITY_EDITOR" ]; then
        echo "FATAL: Unity editor not found at $UNITY_EDITOR"
        exit 1
    fi
    echo "Opening Unity to trigger Reinterop code generation (pass $1)..."
    echo "(DllNotFoundException warnings are expected — no native library yet)"
    echo ""
    xvfb-run "$UNITY_EDITOR" \
        -batchmode -nographics -quit \
        -projectPath "$UNITY_PROJECT" \
        -logFile /dev/stdout || true
    echo ""
}

if [ ! -f "$GENERATED_HEADER" ]; then
    run_unity_codegen 1
    if [ ! -f "$GENERATED_HEADER" ]; then
        echo "Incomplete generation after pass 1. Running second pass..."
        run_unity_codegen 2
    fi
    if [ ! -f "$GENERATED_HEADER" ]; then
        echo "FATAL: Code generation incomplete after two passes."
        echo "Missing: $GENERATED_HEADER"
        echo "Check Unity log above for errors."
        exit 1
    fi
    echo "Code generation succeeded."
fi

# ── Create vcpkg triplet for Linux ──────────────────────────────────

TRIPLET_FILE="native~/vcpkg/triplets/x64-linux-unity.cmake"
if [ ! -f "$TRIPLET_FILE" ]; then
    echo "Creating x64-linux-unity vcpkg triplet..."
    cat > "$TRIPLET_FILE" <<'EOF'
include("${CMAKE_CURRENT_LIST_DIR}/shared/common.cmake")
set(VCPKG_TARGET_ARCHITECTURE x64)
set(VCPKG_CRT_LINKAGE static)
set(VCPKG_LIBRARY_LINKAGE static)
set(VCPKG_CMAKE_SYSTEM_NAME Linux)
EOF
fi

# ── Build Editor native library ──────────────────────────────────────

cd native~

if [ ! -f "../Editor/libCesiumForUnityNative-Editor.so" ]; then
    echo ""
    echo "Building Editor native library..."
    echo "(First run may take 30-60 minutes for vcpkg dependency compilation)"
    cmake -B build-Editor -S . \
        -DCMAKE_BUILD_TYPE=RelWithDebInfo \
        -DCMAKE_INSTALL_PREFIX="$(pwd)/../Editor" \
        -DVCPKG_TRIPLET=x64-linux-unity \
        -DVCPKG_OVERLAY_TRIPLETS="$(pwd)/vcpkg/triplets" \
        -DEDITOR=ON
    cmake --build build-Editor --target install --parallel "$(nproc)"
fi

# ── Build Runtime (Standalone) native library ────────────────────────

if [ ! -f "../Plugins/Standalone/libCesiumForUnityNative-Runtime.so" ]; then
    echo ""
    echo "Building Runtime native library..."
    cmake -B build-Standalone -S . \
        -DCMAKE_BUILD_TYPE=RelWithDebInfo \
        -DCMAKE_INSTALL_PREFIX="$(pwd)/../Plugins/Standalone" \
        -DVCPKG_TRIPLET=x64-linux-unity \
        -DVCPKG_OVERLAY_TRIPLETS="$(pwd)/vcpkg/triplets" \
        -DEDITOR=OFF
    cmake --build build-Standalone --target install --parallel "$(nproc)"
fi

cd ..

echo ""
echo "=== Build complete ==="
echo "Package directory: $CESIUM_PKG"
echo ""
echo "Editor .so:"
ls -lh "Editor/libCesiumForUnityNative-Editor.so" 2>/dev/null || echo "  (not found)"
echo "Runtime .so:"
ls -lh "Plugins/Standalone/libCesiumForUnityNative-Runtime.so" 2>/dev/null || echo "  (not found)"
