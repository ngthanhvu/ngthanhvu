#!/bin/bash

set -e

APP_DIR="/opt/docker-manager"

BACKEND_IMAGE="ngthanhvu/docker-manager-backend:v1.0.0"
FRONTEND_IMAGE="ngthanhvu/docker-manager-frontend:v1.0.0"

DEFAULT_PORT=8088

echo "================================="
echo " Docker Manager Installer"
echo "================================="
echo ""
echo "1) Install Docker Manager"
echo "2) Uninstall Docker Manager"
echo ""

read -p "Choose option [1-2]: " OPTION

# -------------------------
# INSTALL
# -------------------------

install_app() {

echo "Installing Docker Manager..."

# check docker
if ! command -v docker &> /dev/null
then
    echo "Docker not found. Installing..."
    curl -fsSL https://get.docker.com | sh
fi

# check compose
if ! docker compose version &> /dev/null
then
    echo "Docker Compose v2 is required."
    exit 1
fi

# choose port
read -p "Enter port for Docker Manager [${DEFAULT_PORT}]: " PORT
PORT=${PORT:-$DEFAULT_PORT}

# check port
check_port() {
    if lsof -i:$1 >/dev/null 2>&1; then
        return 1
    else
        return 0
    fi
}

while ! check_port $PORT; do
    echo "Port $PORT is already in use."
    read -p "Choose another port: " PORT
done

echo "Using port: $PORT"

# create install dir
mkdir -p $APP_DIR
cd $APP_DIR

# create compose file
cat > docker-compose.yml <<EOF
version: "3.8"

services:

  backend:
    image: $BACKEND_IMAGE
    container_name: docker-manager-backend
    restart: unless-stopped
    volumes:
      - /var/run/docker.sock:/var/run/docker.sock
    ports:
      - "127.0.0.1:8080:8080"

  frontend:
    image: $FRONTEND_IMAGE
    container_name: docker-manager-frontend
    restart: unless-stopped
    depends_on:
      - backend
    ports:
      - "$PORT:80"
EOF

echo "Pulling images..."
docker compose pull

echo "Starting Docker Manager..."
docker compose up -d

IP=$(hostname -I | awk '{print $1}')

echo ""
echo "================================="
echo " Docker Manager Installed"
echo "================================="
echo ""
echo "Access URL:"
echo "http://$IP:$PORT"
echo ""
echo "Install directory:"
echo "$APP_DIR"
echo ""

}

# -------------------------
# UNINSTALL
# -------------------------

uninstall_app() {

if [ ! -d "$APP_DIR" ]; then
    echo "Docker Manager is not installed."
    exit 0
fi

read -p "Are you sure you want to uninstall Docker Manager? (y/n): " CONFIRM

if [ "$CONFIRM" != "y" ]; then
    echo "Cancelled."
    exit 0
fi

cd $APP_DIR

echo "Stopping containers..."
docker compose down

echo "Removing images..."
docker image rm $BACKEND_IMAGE 2>/dev/null || true
docker image rm $FRONTEND_IMAGE 2>/dev/null || true

echo "Removing install directory..."
rm -rf $APP_DIR

echo ""
echo "Docker Manager removed successfully."
echo ""

}

# -------------------------
# MENU
# -------------------------

case $OPTION in
1)
    install_app
    ;;
2)
    uninstall_app
    ;;
*)
    echo "Invalid option."
    ;;
esac
