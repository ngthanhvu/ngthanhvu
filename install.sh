#!/bin/bash

set -e

APP_NAME="docke-manager-panel"
APP_DIR="/opt/docker-manager"

BACKEND_IMAGE="ngthanhvu/docker-manager-backend:latest"
FRONTEND_IMAGE="ngthanhvu/docker-manager-frontend:latest"

DEFAULT_PORT=8088

echo "=============================="
echo " Dock Manager Panel Installer"
echo "=============================="

# -----------------------------
# check docker
# -----------------------------
if ! command -v docker &> /dev/null
then
    echo "Docker not found. Installing Docker..."
    curl -fsSL https://get.docker.com | sh
fi

# -----------------------------
# check docker compose
# -----------------------------
if ! docker compose version &> /dev/null
then
    echo "Docker Compose not found."
    echo "Please install Docker Compose v2."
    exit 1
fi

# -----------------------------
# choose port
# -----------------------------
read -p "Enter port for Docker Panel [${DEFAULT_PORT}]: " PORT
PORT=${PORT:-$DEFAULT_PORT}

# -----------------------------
# check port
# -----------------------------
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

# -----------------------------
# create directory
# -----------------------------
mkdir -p $APP_DIR
cd $APP_DIR

# -----------------------------
# create compose file
# -----------------------------
cat > docker-compose.yml <<EOF
version: "3.8"

services:

  backend:
    image: $BACKEND_IMAGE
    container_name: docker-panel-backend
    restart: unless-stopped
    volumes:
      - /var/run/docker.sock:/var/run/docker.sock
    ports:
      - "127.0.0.1:8080:8080"

  frontend:
    image: $FRONTEND_IMAGE
    container_name: docker-panel-frontend
    restart: unless-stopped
    depends_on:
      - backend
    ports:
      - "$PORT:80"
EOF

echo "Pulling images..."
docker compose pull

echo "Starting Docker Panel..."
docker compose up -d

IP=$(hostname -I | awk '{print $1}')

echo ""
echo "===================================="
echo " Dock Manager Panel Installed Successfully"
echo "===================================="
echo ""
echo "Access URL:"
echo "http://$IP:$PORT"
echo ""
echo "Install directory:"
echo "$APP_DIR"
echo ""
