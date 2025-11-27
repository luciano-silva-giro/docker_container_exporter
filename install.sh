#!/bin/bash
set -e

# Configuration
INSTALL_DIR="/opt/docker_container_exporter"
SERVICE_NAME="docker-container-exporter"
REPO_URL="https://github.com/luciano-silva-giro/docker_container_exporter.git"
PORT="${PORT:-9102}"
USER="${SUDO_USER:-$USER}"

echo "=== Docker Container Exporter Installation ==="
echo "Install directory: $INSTALL_DIR"
echo "Service user: $USER"
echo "Port: $PORT"
echo ""

# Check if running as root
if [ "$EUID" -ne 0 ]; then 
    echo "Please run as root or with sudo"
    exit 1
fi

# Install dependencies
echo "Installing system dependencies..."
if command -v apt-get &> /dev/null; then
    apt-get update
    apt-get install -y python3 python3-pip python3-venv git
else
    echo "Unsupported package manager. Please install python3, pip, and git manually."
    exit 1
fi

# Clone or update repository
if [ -d "$INSTALL_DIR" ]; then
    echo "Updating existing installation..."
    cd "$INSTALL_DIR"
    git pull
else
    echo "Cloning repository..."
    git clone "$REPO_URL" "$INSTALL_DIR"
    cd "$INSTALL_DIR"
fi

# Create virtual environment and install Python dependencies
echo "Setting up Python virtual environment..."
python3 -m venv venv
source venv/bin/activate
pip install --upgrade pip
pip install -r requirements.txt
deactivate

# Add user to docker group
echo "Adding user $USER to docker group..."
usermod -aG docker "$USER"

# Create systemd service file
echo "Creating systemd service..."
cat > /etc/systemd/system/${SERVICE_NAME}.service <<EOF
[Unit]
Description=Docker Container Prometheus Exporter
After=docker.service
Requires=docker.service

[Service]
Type=simple
User=$USER
Group=docker
WorkingDirectory=$INSTALL_DIR
Environment="PORT=$PORT"
ExecStart=$INSTALL_DIR/venv/bin/python $INSTALL_DIR/containers_running.py
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
EOF

# Reload systemd and enable service
echo "Enabling and starting service..."
systemctl daemon-reload
systemctl enable ${SERVICE_NAME}
systemctl restart ${SERVICE_NAME}

# Wait a moment for service to start
sleep 2

# Check service status
echo ""
echo "=== Installation Complete ==="
echo ""
systemctl status ${SERVICE_NAME} --no-pager
echo ""
echo "Metrics available at: http://localhost:$PORT/metrics"
echo ""
echo "Useful commands:"
echo "  sudo systemctl status ${SERVICE_NAME}"
echo "  sudo systemctl restart ${SERVICE_NAME}"
echo "  sudo journalctl -u ${SERVICE_NAME} -f"
echo "  curl http://localhost:$PORT/metrics"
