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
if ! grep -q "root:1000000" /etc/subuid; then
  echo "root:1000000:1000000000" | sudo tee -a /etc/subuid >/dev/null
  echo "root:1000000:1000000000" | sudo tee -a /etc/subgid >/dev/null
fi

# 4) Install Incus
if ! command -v incus >/dev/null; then
  sudo mkdir -p /etc/apt/keyrings
  sudo curl -fsSL https://pkgs.zabbly.com/key.asc -o /etc/apt/keyrings/zabbly.asc
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

# Docker-in-container needs nesting in most Incus setups
sudo incus profile set default security.nesting true || true

# GPU passthrough: add a gpu device to the default profile if missing
# (Idempotent: command will fail if already present; ignore)
sudo incus profile device add default gpu gpu >/dev/null 2>&1 || true

# 6) Trust the Incus bridge
sudo firewall-cmd --permanent --zone=trusted --add-interface=incusbr0 || true
sudo firewall-cmd --reload || true

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
#    (b) disables Claude "bypass permissions / yolo" mode via managed settings (highest precedence)
#    Bug reference: https://github.com/lxc/incus/issues/2623
CONTAINERD_FIX="$(mktemp)"
cat > "$CONTAINERD_FIX" <<'FIXEOF'
#!/bin/bash
set -e
export DEBIAN_FRONTEND=noninteractive

apt-get update -y

# --- (a) containerd pin (nested Docker workaround)
# Docker repo is already present in the COI base image build environment (see logs).
# Prefer a downgrade that likely bundles older runc (workaround for Incus #2623).
apt-get install -y --allow-downgrades containerd.io=1.7.18-1 || \
apt-get install -y --allow-downgrades containerd.io=1.7.28-2~ubuntu.22.04~jammy
apt-mark hold containerd.io

# --- (b) disable Claude bypassPermissions mode (managed settings override CLI flags)
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
FIXEOF
chmod +x "$CONTAINERD_FIX"

cd "$COI_DIR"
sg incus-admin -c "coi build --force custom coi-fixed --base coi --script $CONTAINERD_FIX" || \
  echo "WARNING: custom image build failed; nested Docker may still be broken"
rm -f "$CONTAINERD_FIX"

# 10) Claude settings: disable bypassPermissions mode by default
# This is Claude's official setting. COI copies ~/.claude settings into the container.
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

# 11) COI config: use the fixed image by default
echo "Writing COI config..."
mkdir -p "$HOME/.config/coi"
cat > "$HOME/.config/coi/config.toml" <<'EOF'
[defaults]
image = "coi-fixed"
persistent = true
mount_claude_config = false
EOF

echo ""
echo "Done."
echo "Open a NEW terminal (incus-admin group membership won’t apply to the current shell)."
echo ""
echo "Usage (from your repo root):"
echo "  coi shell"