#!/bin/bash

# Network Monitor Installation Script
# This script installs the network monitoring application on Linux systems

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Configuration
INSTALL_DIR="/opt/network-monitor"
SERVICE_NAME="network-monitor"
USER="network-monitor"
LOG_DIR="/var/log/network-monitor"
DATA_DIR="/var/lib/network-monitor"

echo -e "${GREEN}Network Monitor Installation Script${NC}"
echo "=================================="

# Check if running as root
if [ "$EUID" -ne 0 ]; then
    echo -e "${RED}Please run this script as root (use sudo)${NC}"
    exit 1
fi

# Detect Linux distribution
if [ -f /etc/os-release ]; then
    . /etc/os-release
    OS=$NAME
    VER=$VERSION_ID
else
    echo -e "${RED}Cannot detect Linux distribution${NC}"
    exit 1
fi

echo -e "${YELLOW}Detected OS: $OS${NC}"

# Function to install packages on Ubuntu/Debian
install_packages_debian() {
    echo "Installing packages for Debian/Ubuntu..."
    apt update
    apt install -y python3 python3-pip curl gnupg lsb-release

    # Install Speedtest CLI
    echo "Installing Ookla Speedtest CLI..."
    curl -s https://packagecloud.io/install/repositories/ookla/speedtest-cli/script.deb.sh | bash
    apt install -y speedtest
}

# Function to install packages on CentOS/RHEL/Fedora
install_packages_rhel() {
    echo "Installing packages for RHEL/CentOS/Fedora..."

    if command -v dnf &> /dev/null; then
        PKG_MANAGER="dnf"
    else
        PKG_MANAGER="yum"
    fi

    $PKG_MANAGER update -y
    $PKG_MANAGER install -y python3 python3-pip curl gnupg

    # Install Speedtest CLI
    echo "Installing Ookla Speedtest CLI..."
    curl -s https://packagecloud.io/install/repositories/ookla/speedtest-cli/script.rpm.sh | bash
    $PKG_MANAGER install -y speedtest
}

# Install packages based on distribution
case $OS in
    *"Ubuntu"*|*"Debian"*)
        install_packages_debian
        ;;
    *"CentOS"*|*"Red Hat"*|*"Fedora"*)
        install_packages_rhel
        ;;
    *)
        echo -e "${YELLOW}Unsupported distribution. Please install manually:${NC}"
        echo "- python3 and python3-pip"
        echo "- Ookla Speedtest CLI from https://www.speedtest.net/apps/cli"
        exit 1
        ;;
esac

# Create user for the service
echo "Creating service user..."
if ! id "$USER" &>/dev/null; then
    useradd --system --shell /bin/false --home-dir /nonexistent --no-create-home $USER
fi

# Create directories
echo "Creating directories..."
mkdir -p $INSTALL_DIR
mkdir -p $LOG_DIR
mkdir -p $DATA_DIR

# Copy files
echo "Installing application files..."
cp network_monitor.py $INSTALL_DIR/
chmod +x $INSTALL_DIR/network_monitor.py

# Set ownership and permissions
chown -R $USER:$USER $LOG_DIR
chown -R $USER:$USER $DATA_DIR
chown root:root $INSTALL_DIR/network_monitor.py

# Create systemd service file
echo "Creating systemd service..."
cat > /etc/systemd/system/${SERVICE_NAME}.service << EOF
[Unit]
Description=Network Monitor - Internet Speed and Latency Monitoring
After=network-online.target
Wants=network-online.target

[Service]
Type=simple
User=$USER
Group=$USER
ExecStart=/usr/bin/python3 $INSTALL_DIR/network_monitor.py --interval 10
Restart=always
RestartSec=30
StandardOutput=journal
StandardError=journal
SyslogIdentifier=network-monitor

# Security settings
NoNewPrivileges=true
PrivateTmp=true
ProtectSystem=strict
ProtectHome=true
ReadWritePaths=$LOG_DIR $DATA_DIR

[Install]
WantedBy=multi-user.target
EOF

# Reload systemd and enable service
echo "Configuring systemd service..."
systemctl daemon-reload
systemctl enable $SERVICE_NAME

# Test speedtest CLI
echo "Testing Speedtest CLI installation..."
if sudo -u $USER speedtest --version &>/dev/null; then
    echo -e "${GREEN}Speedtest CLI installed successfully${NC}"
else
    echo -e "${RED}Speedtest CLI test failed${NC}"
    exit 1
fi

# Create a basic configuration file
cat > $INSTALL_DIR/config.txt << EOF
# Network Monitor Configuration
#
# Data files location: $DATA_DIR
# Log files location: $LOG_DIR
#
# Service commands:
# - Start: sudo systemctl start $SERVICE_NAME
# - Stop: sudo systemctl stop $SERVICE_NAME
# - Status: sudo systemctl status $SERVICE_NAME
# - Logs: journalctl -u $SERVICE_NAME -f
#
# Data files:
# - Speed tests: $DATA_DIR/speed_tests.csv
# - Ping tests: $DATA_DIR/ping_tests.csv
EOF

echo ""
echo -e "${GREEN}Installation completed successfully!${NC}"
echo ""
echo "Next steps:"
echo "1. Start the service: sudo systemctl start $SERVICE_NAME"
echo "2. Check status: sudo systemctl status $SERVICE_NAME"
echo "3. View logs: journalctl -u $SERVICE_NAME -f"
echo ""
echo "Data files will be saved to:"
echo "- Speed tests: $DATA_DIR/speed_tests.csv"
echo "- Ping tests: $DATA_DIR/ping_tests.csv"
echo ""
echo "To run a single test manually:"
echo "sudo -u $USER python3 $INSTALL_DIR/network_monitor.py --single"
echo ""
echo -e "${YELLOW}The service will run tests every 10 minutes by default.${NC}"