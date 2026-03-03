#!/bin/bash
set -euo pipefail
export DEBIAN_FRONTEND=noninteractive

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

# System dependencies for Unity headless batch builds (X11/Mesa libs, xvfb, IL2CPP toolchain).
# libasound2 was renamed to libasound2t64 in Ubuntu 24.04; try both.
apt-get install -y \
  xvfb \
  libgtk2.0-0 libglib2.0-0 \
  libxinerama1 libxcursor1 libxrandr2 libxext6 libxrender1 libxi6 libx11-6 \
  libglu1-mesa libgl1-mesa-dev mesa-common-dev \
  libpulse0 libnss3 libcap2 libnotify4 libunwind-dev \
  build-essential clang lld
apt-get install -y libasound2t64 || apt-get install -y libasound2

# Unity Hub
install -d /etc/apt/keyrings
curl -fsSL https://hub.unity3d.com/linux/keys/public | gpg --dearmor -o /etc/apt/keyrings/unityhub.gpg
echo "deb [arch=amd64 signed-by=/etc/apt/keyrings/unityhub.gpg] https://hub.unity3d.com/linux/repos/deb stable main" \
  > /etc/apt/sources.list.d/unityhub.list
apt-get update
apt-get install -y unityhub

# Unity 6000.0.66f1 with Android and Linux IL2CPP modules
xvfb-run unityhub --headless install-path --set /opt/unity
xvfb-run unityhub --headless install \
  --version 6000.0.66f1 \
  --changeset e7adf66625be \
  --module android android-sdk-ndk-tools android-open-jdk linux-il2cpp \
  --childModules

# The workspace is mounted as code:code but the container runs as root.
# Git refuses to operate on repos owned by a different user without this.
git config --system --add safe.directory /workspace
