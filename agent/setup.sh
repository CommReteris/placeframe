#!/bin/bash
set -euo pipefail

echo "Provisioning COI (code-on-incus) on Ubuntu: Incus + firewalld restricted networking + nested Docker + GPU (no patches, no wrappers)"

# ----------------------------
# 1) Host dependencies
# ----------------------------
sudo apt update
sudo apt install -y \
  ca-certificates \
  curl \
  git \
  firewalld \
  btrfs-progs \
  uidmap

# ----------------------------
# 2) firewalld + passwordless firewall-cmd (COI uses this in restricted mode)
# ----------------------------
sudo ufw disable || true
sudo systemctl enable --now firewalld

# Avoid non-interactive sudo failures/timestamp expiry when COI runs firewall-cmd.
sudo tee /etc/sudoers.d/coi-firewalld >/dev/null <<EOF
$USER ALL=(root) NOPASSWD: /usr/bin/firewall-cmd
EOF
sudo chmod 440 /etc/sudoers.d/coi-firewalld
sudo visudo -cf /etc/sudoers.d/coi-firewalld >/dev/null

# Dedicated zone for Incus bridge (do NOT put incusbr0 in "trusted")
sudo firewall-cmd --permanent --new-zone=incus >/dev/null 2>&1 || true

# ----------------------------
# 3) Ensure subuid/subgid mapping exists (unprivileged containers)
# ----------------------------
if ! awk -F: '$1=="root"{found=1} END{exit found?0:1}' /etc/subuid; then
  echo "root:100000:65536" | sudo tee -a /etc/subuid >/dev/null
fi
if ! awk -F: '$1=="root"{found=1} END{exit found?0:1}' /etc/subgid; then
  echo "root:100000:65536" | sudo tee -a /etc/subgid >/dev/null
fi

# ----------------------------
# 4) Install Incus (Zabbly repo) + add user to incus-admin
# ----------------------------
if ! command -v incus >/dev/null; then
  sudo mkdir -p /etc/apt/keyrings
  sudo curl -fsSL https://pkgs.zabbly.com/key.asc -o /etc/apt/keyrings/zabbly.asc
  echo "deb [signed-by=/etc/apt/keyrings/zabbly.asc] https://pkgs.zabbly.com/incus/stable $(lsb_release -cs) main" \
    | sudo tee /etc/apt/sources.list.d/zabbly.list >/dev/null
  sudo apt update
  sudo apt install -y incus
fi

sudo usermod -aG incus-admin "$USER"

# Group membership won't apply in this shell if we just added it.
if ! id -nG | tr ' ' '\n' | grep -qx incus-admin; then
  echo "Added $USER to incus-admin. Open a NEW terminal and re-run this script."
  exit 0
fi

# ----------------------------
# 5) Initialize Incus (only if not already initialized with a default pool)
# ----------------------------
if ! incus storage list 2>/dev/null | grep -qE '^\|\s+default\s+\|'; then
  cat <<EOF | incus admin init --preseed
config: {}
networks:
- config:
    ipv4.address: 10.250.250.1/24
    ipv4.nat: "true"
    ipv6.address: none
  name: incusbr0
  type: bridge
storage_pools:
- name: default
  driver: btrfs
  config:
    size: 50GiB
profiles:
- name: default
  devices:
    eth0:
      name: eth0
      network: incusbr0
      type: nic
    root:
      path: /
      pool: default
      type: disk
EOF
fi

# Attach incusbr0 to the dedicated zone and enable NAT there.
if incus network show incusbr0 >/dev/null 2>&1; then
  sudo firewall-cmd --permanent --zone=incus --add-interface=incusbr0 >/dev/null 2>&1 || true
  sudo firewall-cmd --permanent --zone=incus --set-target=ACCEPT >/dev/null 2>&1 || true
  sudo firewall-cmd --permanent --zone=incus --add-service=dhcp >/dev/null 2>&1 || true
  sudo firewall-cmd --permanent --zone=incus --add-service=dns  >/dev/null 2>&1 || true
  sudo firewall-cmd --permanent --zone=incus --add-masquerade   >/dev/null 2>&1 || true
  sudo firewall-cmd --reload >/dev/null 2>&1 || true
fi

# ----------------------------
# 6) Nested Docker + GPU passthrough
# NOTE: simplest reliable approach is to apply these to the Incus "default" profile.
# This affects all containers that use the default profile.
# ----------------------------
incus profile set default security.nesting true >/dev/null 2>&1 || true
if ! incus profile device show default | grep -qE '^\s*gpu:\s*$'; then
  incus profile device add default gpu gpu >/dev/null 2>&1 || true
fi

# ----------------------------
# 7) Install COI binary (prebuilt)
# ----------------------------
TMP_COI="$(mktemp)"
curl -fsSL -o "$TMP_COI" https://github.com/mensfeld/code-on-incus/releases/latest/download/coi-linux-amd64
chmod +x "$TMP_COI"
sudo mv "$TMP_COI" /usr/local/bin/coi

# ----------------------------
# 8) Clone COI repo (workaround for build script issues) + build base image if needed
# ----------------------------
COI_DIR="/opt/code-on-incus"
if [ ! -d "$COI_DIR" ]; then
  sudo git clone --depth 1 https://github.com/mensfeld/code-on-incus.git "$COI_DIR"
else
  sudo git -C "$COI_DIR" pull --ff-only
fi

# Ensure base COI image exists (this is the one you want to use if you're accepting default behavior)
if ! incus image info coi >/dev/null 2>&1; then
  (cd "$COI_DIR" && coi build)
fi

# ----------------------------
# 9) Build project-specific COI image with uv + Java pre-installed
# ----------------------------
PLACEFRAME_IMAGE="coi-placeframe"
if ! incus image info "$PLACEFRAME_IMAGE" >/dev/null 2>&1; then
  echo "Building $PLACEFRAME_IMAGE image (base coi + uv + Java)..."
  TEMP_CONTAINER="coi-placeframe-build-$$"

  incus launch coi "$TEMP_CONTAINER"
  # Wait for container to be ready
  sleep 5

  incus exec "$TEMP_CONTAINER" -- bash -c '
    set -euo pipefail
    export DEBIAN_FRONTEND=noninteractive

    apt-get update -qq
    apt-get install -y -qq --no-install-recommends default-jre-headless

    # Install uv system-wide (default installs to ~/.local/bin which is root-only)
    curl -LsSf https://astral.sh/uv/install.sh | env UV_INSTALL_DIR=/usr/local/bin sh

    # Install openapi-generator-cli
    npm install -g @openapitools/openapi-generator-cli

    apt-get clean
    rm -rf /var/lib/apt/lists/*
  '

  incus stop "$TEMP_CONTAINER"
  incus publish "$TEMP_CONTAINER" --alias "$PLACEFRAME_IMAGE"
  incus delete "$TEMP_CONTAINER"
  echo "$PLACEFRAME_IMAGE image published."
fi

# ----------------------------
# 10) Reset COI user config to avoid any wrapper/tool overrides from prior experiments
# ----------------------------
mkdir -p "$HOME/.config/coi"
cat > "$HOME/.config/coi/config.toml" <<EOF
[defaults]
persistent = true
image = "$PLACEFRAME_IMAGE"
EOF

# ----------------------------
# 11) Pass host git identity into containers via Incus default profile
# ----------------------------
HOST_GIT_NAME="$(git config user.name 2>/dev/null || true)"
HOST_GIT_EMAIL="$(git config user.email 2>/dev/null || true)"
if [ -n "$HOST_GIT_NAME" ] && [ -n "$HOST_GIT_EMAIL" ]; then
  incus profile set default environment.GIT_AUTHOR_NAME="$HOST_GIT_NAME"
  incus profile set default environment.GIT_AUTHOR_EMAIL="$HOST_GIT_EMAIL"
  incus profile set default environment.GIT_COMMITTER_NAME="$HOST_GIT_NAME"
  incus profile set default environment.GIT_COMMITTER_EMAIL="$HOST_GIT_EMAIL"
  echo "Git identity set in Incus default profile: $HOST_GIT_NAME <$HOST_GIT_EMAIL>"

# Keep the container's venv outside the mounted workspace so it doesn't
# overwrite the host's .venv (venvs contain absolute paths and aren't portable).
incus profile set default environment.UV_PROJECT_ENVIRONMENT="/home/code/.venvs/placeframe"
else
  echo "WARNING: Could not read git user.name/user.email from host. Set them and re-run, or set manually:"
  echo "  incus profile set default environment.GIT_AUTHOR_NAME='Your Name'"
  echo "  incus profile set default environment.GIT_AUTHOR_EMAIL='you@example.com'"
  echo "  incus profile set default environment.GIT_COMMITTER_NAME='Your Name'"
  echo "  incus profile set default environment.GIT_COMMITTER_EMAIL='you@example.com'"
fi

echo "Done."
echo "Run: coi shell"