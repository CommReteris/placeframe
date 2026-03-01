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

# The workspace is mounted as code:code but the container runs as root.
# Git refuses to operate on repos owned by a different user without this.
git config --global --add safe.directory /workspace
