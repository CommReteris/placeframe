#!/bin/bash
set -e

echo "Provisioning Code on Incus (COI) - minimal"

# 1) System deps
sudo apt update
sudo apt install -y curl git firewalld btrfs-progs uidmap

# 2) Firewall (COI restricted mode depends on this)
sudo ufw disable || true
sudo systemctl enable --now firewalld

# Allow COI to run firewall-cmd without sudo prompts (fixes "next day firewalld not running" error)
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

# 6) Trust the Incus bridge
sudo firewall-cmd --permanent --zone=trusted --add-interface=incusbr0 || true
sudo firewall-cmd --reload || true

# 7) COI repo + binary (cloning the repo is a workaround for https://github.com/mensfeld/code-on-incus/issues/50)
echo "Fetching COI repository and binary..."
COI_DIR="/opt/code-on-incus"
if [ ! -d "$COI_DIR" ]; then
  sudo git clone --depth 1 https://github.com/mensfeld/code-on-incus.git "$COI_DIR"
else
  sudo git -C "$COI_DIR" pull
fi

sudo curl -fsSL -o /usr/local/bin/coi \
  https://github.com/mensfeld/code-on-incus/releases/latest/download/coi-linux-amd64
sudo chmod +x /usr/local/bin/coi

# 8) Build base image
echo "Ensuring COI base image exists..."
if ! sg incus-admin -c "incus image info coi >/dev/null 2>&1"; then
  echo "Building COI base image..."
  cd "$COI_DIR"
  sg incus-admin -c "coi build"
else
  echo "COI base image already exists. Skipping build."
fi

# 9) COI config
echo "Writing COI config..."
mkdir -p "$HOME/.config/coi"

cat > "$HOME/.config/coi/config.toml" <<'EOF'
[defaults]
persistent = true
mount_claude_config = true
EOF