#!/bin/bash
set -e

echo "Provisioning Code on Incus (COI) - minimal (+ containerd pin for nested Docker + GPU + no-yolo)"

# 1) System deps
sudo apt update
sudo apt install -y curl git firewalld btrfs-progs uidmap

# 2) Firewall (COI restricted mode depends on this)
sudo ufw disable || true
sudo systemctl enable --now firewalld

# Allow COI to run firewall-cmd without sudo prompts (fixes "next day" sudo timestamp issues)
sudo tee /etc/sudoers.d/coi-firewalld >/dev/null <<EOF
$USER ALL=(root) NOPASSWD: /usr/bin/firewall-cmd
EOF
sudo chmod 440 /etc/sudoers.d/coi-firewalld
sudo visudo -cf /etc/sudoers.d/coi-firewalld >/dev/null

# 3) UID/GID mapping (unprivileged containers)
# Ensure root has a range (only if missing). Avoid appending massive ranges repeatedly.
if ! awk -F: '$1=="root"{found=1} END{exit found?0:1}' /etc/subuid; then
  echo "root:100000:65536" | sudo tee -a /etc/subuid >/dev/null
fi
if ! awk -F: '$1=="root"{found=1} END{exit found?0:1}' /etc/subgid; then
  echo "root:100000:65536" | sudo tee -a /etc/subgid >/dev/null
fi

# 4) Install Incus
if ! command -v incus >/dev/null; then
  sudo mkdir -p /etc/apt/keyrings
  sudo curl -fsSL https://pkgs.zabbly.com/incus/stable/gpg.key -o /etc/apt/keyrings/zabbly.asc
  echo "deb [signed-by=/etc/apt/keyrings/zabbly.asc] https://pkgs.zabbly.com/incus/stable $(lsb_release -cs) main" \
    | sudo tee /etc/apt/sources.list.d/zabbly.list >/dev/null
  sudo apt update
  sudo apt install -y incus
fi
sudo usermod -aG incus-admin "$USER"

# 5) Initialize Incus (only if default pool not present)
if ! sudo incus storage list | grep -q "^| default"; then
  cat <<EOF | sudo incus admin init --preseed
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

# COI profile (avoid modifying the global default profile)
# - security.nesting: Docker-in-container needs this in most Incus setups
# - gpu device: pass through all GPUs
sudo incus profile create coi >/dev/null 2>&1 || true
sudo incus profile set coi security.nesting true >/dev/null 2>&1 || true
sudo incus profile device add coi gpu gpu >/dev/null 2>&1 || true

# 6) Firewall zone for Incus bridge (do NOT blanket-trust incusbr0)
# Putting incusbr0 in "trusted" can accidentally weaken COI restricted networking.
# Create a dedicated zone with masquerade enabled and let COI add per-container rules.
sudo firewall-cmd --permanent --new-zone=incus >/dev/null 2>&1 || true
sudo firewall-cmd --permanent --zone=incus --add-interface=incusbr0 >/dev/null 2>&1 || true
sudo firewall-cmd --permanent --zone=incus --add-masquerade >/dev/null 2>&1 || true
sudo firewall-cmd --reload >/dev/null 2>&1 || true

# 7) COI repo + binary
# Repo clone is a workaround for https://github.com/mensfeld/code-on-incus/issues/50
echo "Fetching COI repository..."
COI_DIR="/opt/code-on-incus"
if [ ! -d "$COI_DIR" ]; then
  sudo git clone --depth 1 https://github.com/mensfeld/code-on-incus.git "$COI_DIR"
else
  sudo git -C "$COI_DIR" pull
fi

echo "Installing COI binary..."
TMP_COI="$(mktemp)"
curl -fsSL -o "$TMP_COI" https://github.com/mensfeld/code-on-incus/releases/latest/download/coi-linux-amd64
chmod +x "$TMP_COI"
sudo mv "$TMP_COI" /usr/local/bin/coi

# 8) Build base image (if missing)
echo "Ensuring COI base image exists..."
if ! sg incus-admin -c "incus image info coi >/dev/null 2>&1"; then
  echo "Building COI base image..."
  cd "$COI_DIR"
  sg incus-admin -c "coi build"
else
  echo "COI base image already exists. Skipping build."
fi

# 9) Build a custom image that:
#    (a) pins containerd.io to avoid nested-Docker sysctl bug (Incus #2623)
#    (b) disables Claude "bypass permissions / yolo" mode via managed settings (defense-in-depth)
#    (c) forces human-in-the-loop by wrapping Claude to strip COI's hardcoded bypass flags
#    Bug reference: https://github.com/lxc/incus/issues/2623
CUSTOM_FIX="$(mktemp)"
cat > "$CUSTOM_FIX" <<'FIXEOF'
#!/bin/bash
set -e
export DEBIAN_FRONTEND=noninteractive

apt-get update -y

# --- (a) containerd pin (nested Docker workaround)
# COI base build container is Ubuntu 22.04 jammy.
apt-get install -y --allow-downgrades containerd.io=1.7.18-1 || \
apt-get install -y --allow-downgrades containerd.io=1.7.28-2~ubuntu.22.04~jammy
apt-mark hold containerd.io

# --- (b) disable Claude bypassPermissions mode (managed settings; highest precedence layer)
install -d -m 0755 /etc/claude-code
cat > /etc/claude-code/managed-settings.json <<'JSON'
{
  "$schema": "https://json.schemastore.org/claude-code-settings.json",
  "permissions": {
    "disableBypassPermissionsMode": "disable",
    "defaultMode": "default"
  }
}
JSON
chmod 0644 /etc/claude-code/managed-settings.json

# --- (c) wrapper: COI hardcodes bypassPermissions at launch; strip those args and force default permission mode
cat > /usr/local/bin/claude-safe <<'SH'
#!/usr/bin/env bash
set -euo pipefail
real_claude="$(command -v claude)"

args=()
while (($#)); do
  case "$1" in
    --dangerously-skip-permissions|--allow-dangerously-skip-permissions) shift ;;
    --permission-mode) shift; (($#)) && shift || true ;;   # drop flag + its value (if present)
    bypassPermissions) shift ;;                             # drop stray value if it appears alone
    *) args+=("$1"); shift ;;
  esac
done

exec "$real_claude" --permission-mode default "${args[@]}"
SH
chmod 0755 /usr/local/bin/claude-safe
FIXEOF
chmod +x "$CUSTOM_FIX"

cd "$COI_DIR"
# NOTE: --force belongs to the 'custom' subcommand
sg incus-admin -c "coi build custom coi-fixed --force --base coi --script $CUSTOM_FIX" || \
  echo "WARNING: custom image build failed; nested Docker / no-yolo may not work"
rm -f "$CUSTOM_FIX"

# 10) Claude settings: disable bypassPermissions mode by default (nice-to-have; wrapper enforces behavior)
mkdir -p "$HOME/.claude"
cat > "$HOME/.claude/settings.json" <<'EOF'
{
  "$schema": "https://json.schemastore.org/claude-code-settings.json",
  "permissions": {
    "disableBypassPermissionsMode": "disable",
    "defaultMode": "default"
  }
}
EOF
chmod 600 "$HOME/.claude/settings.json" || true

# 11) COI config:
# - Use coi-fixed only if it exists (avoid pointing defaults at a missing image)
# - Use dedicated Incus profile "coi" (nesting+gpu) without modifying default
echo "Writing COI config..."
if sg incus-admin -c "incus image info coi-fixed >/dev/null 2>&1"; then
  DEFAULT_IMAGE="coi-fixed"
else
  DEFAULT_IMAGE="coi"
fi

mkdir -p "$HOME/.config/coi"
cat > "$HOME/.config/coi/config.toml" <<EOF
[defaults]
image = "$DEFAULT_IMAGE"
persistent = true
mount_claude_config = false
profile = "coi"

[tool]
name = "claude"
binary = "claude-safe"
EOF

echo ""
echo "Done."
echo "Open a NEW terminal (incus-admin group membership won’t apply to the current shell)."
echo ""
echo "Usage (from your repo root):"
echo "  coi shell"