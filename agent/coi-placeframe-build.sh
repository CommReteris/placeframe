#!/bin/bash
set -euo pipefail
export DEBIAN_FRONTEND=noninteractive

# Install uv system-wide (default installs to ~/.local/bin which is root-only)
curl -LsSf https://astral.sh/uv/install.sh | env UV_INSTALL_DIR=/usr/local/bin sh
