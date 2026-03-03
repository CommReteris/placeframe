#!/bin/bash
set -euo pipefail
export DEBIAN_FRONTEND=noninteractive

# Unity editor + modules via direct download (bypasses Unity Hub, which segfaults in the
# build container — see agent/research/unity-hub-segfault-in-coi-build.md).
# Download URLs from: https://download.unity3d.com/download_unity/$CHANGESET/unity-$VERSION-linux.ini
CHANGESET=e7adf66625be
VERSION=6000.0.66f1
CDN=https://download.unity3d.com/download_unity/$CHANGESET
UNITY_PATH=/opt/unity/$VERSION
ANDROID_DIR=$UNITY_PATH/Editor/Data/PlaybackEngines/AndroidPlayer

# System dependencies for Unity headless batch builds (X11/Mesa libs, xvfb, IL2CPP toolchain)
# plus extraction tools for direct downloads (p7zip-full for .pkg, cpio for Payload, unzip for .zip).
# libasound2 was renamed to libasound2t64 in Ubuntu 24.04; try both.
apt-get update
apt-get install -y \
  xvfb \
  libgtk2.0-0 libglib2.0-0 \
  libxinerama1 libxcursor1 libxrandr2 libxext6 libxrender1 libxi6 libx11-6 \
  libglu1-mesa libgl1-mesa-dev mesa-common-dev \
  libpulse0 libnss3 libcap2 libnotify4 libunwind-dev \
  build-essential clang lld \
  p7zip-full cpio unzip
apt-get install -y libasound2t64 || apt-get install -y libasound2

# Unity editor (4.5 GB). Extracts to Editor/ at the target path.
mkdir -p "$UNITY_PATH"
echo "Downloading Unity $VERSION editor..."
curl -fSL "$CDN/LinuxEditorInstaller/Unity-$VERSION.tar.xz" | tar xJ -C "$UNITY_PATH"

# Linux IL2CPP build support (66 MB). Extracts to Editor/Data/PlaybackEngines/LinuxStandaloneSupport/.
echo "Downloading Linux IL2CPP module..."
curl -fSL "$CDN/LinuxEditorTargetInstaller/UnitySetup-Linux-IL2CPP-Support-for-Editor-$VERSION.tar.xz" \
  | tar xJ -C "$UNITY_PATH"

# Android build support (.pkg — no Linux-native tar.xz available).
# The .pkg is an Apple xar archive containing a plain cpio Payload that extracts flat
# to the AndroidPlayer directory level.
echo "Downloading Android build support module..."
curl -fSL "$CDN/MacEditorTargetInstaller/UnitySetup-Android-Support-for-Editor-$VERSION.pkg" \
  -o /tmp/android-support.pkg
mkdir -p /tmp/android-extract
cd /tmp/android-extract
7z x -y -bd /tmp/android-support.pkg > /dev/null
mkdir -p "$ANDROID_DIR"
cpio -idmu < Payload~ 2>/dev/null
cp -a . "$ANDROID_DIR/"
rm "$ANDROID_DIR/Payload~"
cd /
rm -rf /tmp/android-extract /tmp/android-support.pkg

# OpenJDK 17.0.9 for Android builds
echo "Downloading OpenJDK..."
mkdir -p "$ANDROID_DIR/OpenJDK"
# OpenJDK is hosted at a version-independent path (no changeset prefix) — see T62 reopened (4).
curl -fSL "https://download.unity3d.com/download_unity/open-jdk/open-jdk-linux-x64/jdk17.0.9-9_8d1cbcce56285f3146cf7761353a643fe573b39e45bd94f35590dca39277f667.zip" \
  -o /tmp/jdk.zip
unzip -q /tmp/jdk.zip -d "$ANDROID_DIR/OpenJDK"
rm /tmp/jdk.zip

# Android NDK r27c (664 MB). ZIP extracts to android-ndk-r27c/; move contents up.
echo "Downloading Android NDK..."
curl -fSL "https://dl.google.com/android/repository/android-ndk-r27c-linux.zip" \
  -o /tmp/ndk.zip
unzip -q /tmp/ndk.zip -d "$ANDROID_DIR/NDK"
mv "$ANDROID_DIR/NDK/android-ndk-r27c"/* "$ANDROID_DIR/NDK/"
rmdir "$ANDROID_DIR/NDK/android-ndk-r27c"
rm /tmp/ndk.zip

# Android SDK components
mkdir -p "$ANDROID_DIR/SDK"

# Build Tools 36.0.0 (ZIP extracts to android-16/; rename to 36.0.0)
echo "Downloading Android SDK build tools..."
curl -fSL "https://dl.google.com/android/repository/build-tools_r36_linux.zip" \
  -o /tmp/build-tools.zip
unzip -q /tmp/build-tools.zip -d "$ANDROID_DIR/SDK/build-tools"
mv "$ANDROID_DIR/SDK/build-tools/android-16" "$ANDROID_DIR/SDK/build-tools/36.0.0"
rm /tmp/build-tools.zip

# Platform Tools 36.0.0
echo "Downloading Android SDK platform tools..."
curl -fSL "https://dl.google.com/android/repository/platform-tools_r36.0.0-linux.zip" \
  -o /tmp/platform-tools.zip
unzip -q /tmp/platform-tools.zip -d "$ANDROID_DIR/SDK"
rm /tmp/platform-tools.zip

# SDK Platforms 34, 35, 36
echo "Downloading Android SDK platforms..."
mkdir -p "$ANDROID_DIR/SDK/platforms"
for platform_url in \
  "https://dl.google.com/android/repository/platform-34-ext7_r02.zip" \
  "https://dl.google.com/android/repository/platform-35_r01.zip" \
  "https://dl.google.com/android/repository/platform-36_r02.zip"; do
  curl -fSL "$platform_url" -o /tmp/platform.zip
  unzip -q /tmp/platform.zip -d "$ANDROID_DIR/SDK/platforms"
  rm /tmp/platform.zip
done

# Command Line Tools 16.0 (ZIP extracts to cmdline-tools/; rename to 16.0)
echo "Downloading Android SDK command line tools..."
mkdir -p "$ANDROID_DIR/SDK/cmdline-tools"
curl -fSL "https://dl.google.com/android/repository/commandlinetools-linux-12266719_latest.zip" \
  -o /tmp/cmdline-tools.zip
unzip -q /tmp/cmdline-tools.zip -d "$ANDROID_DIR/SDK/cmdline-tools"
mv "$ANDROID_DIR/SDK/cmdline-tools/cmdline-tools" "$ANDROID_DIR/SDK/cmdline-tools/16.0"
rm /tmp/cmdline-tools.zip

# CMake 3.22.1 (ZIP extracts flat — bin/, share/ — with no parent directory)
echo "Downloading CMake for Android..."
mkdir -p "$ANDROID_DIR/SDK/cmake/3.22.1"
curl -fSL "https://dl.google.com/android/repository/cmake-3.22.1-linux.zip" \
  -o /tmp/cmake.zip
unzip -q /tmp/cmake.zip -d "$ANDROID_DIR/SDK/cmake/3.22.1"
rm /tmp/cmake.zip

# Accept Android SDK licenses
yes 2>/dev/null | "$ANDROID_DIR/SDK/cmdline-tools/16.0/bin/sdkmanager" \
  --sdk_root="$ANDROID_DIR/SDK" --licenses > /dev/null 2>&1 || true

# Ensure executables have +x (ZIP extraction may not preserve permissions)
chmod +x "$UNITY_PATH/Editor/Unity"
chmod -R +x "$ANDROID_DIR/SDK/build-tools/36.0.0/" 2>/dev/null || true
chmod -R +x "$ANDROID_DIR/SDK/platform-tools/" 2>/dev/null || true
chmod -R +x "$ANDROID_DIR/SDK/cmdline-tools/16.0/bin/" 2>/dev/null || true

# Install uv system-wide (default installs to ~/.local/bin which is root-only)
curl -LsSf https://astral.sh/uv/install.sh | env UV_INSTALL_DIR=/usr/local/bin sh

# Install Node.js 20 LTS + pnpm (needed for SvelteKit board app)
curl -fsSL https://deb.nodesource.com/setup_20.x | bash -
apt-get install -y nodejs
npm install -g pnpm

# COI installs Claude Code for the `code` user at container launch.
# The container runs as root, so Claude's startup self-check looks for
# /root/.local/bin/claude (the native install path for root) and errors
# when it doesn't exist. Pre-create a symlink chain so root's path
# resolves to the code user's install once COI populates it.
mkdir -p /root/.local/bin
ln -sf /home/code/.local/bin/claude /root/.local/bin/claude

# Install Playwright's Chromium and its OS-level dependencies (for E2E tests).
# Uses npx so we don't need @playwright/test installed globally.
npx playwright install --with-deps chromium

# The workspace is mounted as code:code but the container runs as root.
# Git refuses to operate on repos owned by a different user without this.
git config --system --add safe.directory /workspace
