#!/bin/bash
set -e

### ===== CONFIG =====
AAPANEL_PORT=2005
AAPANEL_USER=ngthanhvu
AAPANEL_PASS="AaPanel@123456"
### ==================

echo "===== aaPanel Silent Installer (NO MySQL) ====="

# Check root
if [ "$EUID" -ne 0 ]; then
  echo "❌ Vui lòng chạy bằng root"
  exit 1
fi

# Detect OS
if command -v apt >/dev/null 2>&1; then
  OS="debian"
elif command -v yum >/dev/null 2>&1; then
  OS="centos"
else
  echo "❌ Không hỗ trợ OS này"
  exit 1
fi

echo "👉 OS: $OS"

# Update system
if [ "$OS" = "debian" ]; then
  apt update -y
  apt install -y curl wget sudo ca-certificates gnupg
else
  yum update -y
  yum install -y curl wget sudo
fi

# Disable SELinux (CentOS)
if [ -f /etc/selinux/config ]; then
  setenforce 0 || true
  sed -i 's/^SELINUX=.*/SELINUX=disabled/' /etc/selinux/config
fi

# Install aaPanel (silent)
echo "👉 Cài aaPanel..."
curl -sSO http://www.aapanel.com/script/install-ubuntu_6.0_en.sh \
|| curl -sSO http://www.aapanel.com/script/install.sh

bash install*.sh <<EOF
y
EOF

sleep 15

AAPANEL_PATH="/www/server/panel"

# Change aaPanel port
echo "👉 Đổi port aaPanel..."
echo "$AAPANEL_PORT" > $AAPANEL_PATH/data/port.pl
$AAPANEL_PATH/init.sh reload

# Set aaPanel user/password
echo "👉 Set user/password aaPanel..."
btpip install requests >/dev/null 2>&1 || true

python3 <<EOF
import hashlib, json, time

user="$AAPANEL_USER"
pwd="$AAPANEL_PASS"

pwd_md5 = hashlib.md5(pwd.encode()).hexdigest()

conf = {
  "username": user,
  "password": pwd_md5,
  "login": True,
  "time": int(time.time())
}

open("$AAPANEL_PATH/data/admin.json","w").write(json.dumps(conf))
EOF

# Install Docker
echo "👉 Cài Docker..."
if [ "$OS" = "debian" ]; then
  curl -fsSL https://get.docker.com | sh
else
  yum install -y docker
  systemctl enable docker
  systemctl start docker
fi

# Install Nginx via aaPanel
echo "👉 Cài Nginx..."
btpip install psutil >/dev/null 2>&1 || true
python3 $AAPANEL_PATH/install/install_soft.py install nginx

echo "========================================"
echo "✅ CÀI ĐẶT HOÀN TẤT"
echo "----------------------------------------"
echo "aaPanel URL : http://IP:$AAPANEL_PORT"
echo "User        : $AAPANEL_USER"
echo "Password    : $AAPANEL_PASS"
echo "========================================"
