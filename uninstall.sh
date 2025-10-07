#!/bin/bash

# Network Monitor Uninstall Script
# This script removes the network monitoring application from Linux systems

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

echo -e "${YELLOW}Network Monitor Uninstall Script${NC}"
echo "================================="

# Check if running as root
if [ "$EUID" -ne 0 ]; then
    echo -e "${RED}Please run this script as root (use sudo)${NC}"
    exit 1
fi

# Confirm uninstallation
echo -e "${YELLOW}This will completely remove the Network Monitor service and its data.${NC}"
read -p "Are you sure you want to continue? (y/N): " -n 1 -r
echo
if [[ ! $REPLY =~ ^[Yy]$ ]]; then
    echo "Uninstallation cancelled."
    exit 0
fi

# Stop and disable service
echo "Stopping and disabling service..."
if systemctl is-active --quiet $SERVICE_NAME; then
    systemctl stop $SERVICE_NAME
fi

if systemctl is-enabled --quiet $SERVICE_NAME; then
    systemctl disable $SERVICE_NAME
fi

# Remove systemd service file
if [ -f "/etc/systemd/system/${SERVICE_NAME}.service" ]; then
    echo "Removing systemd service file..."
    rm -f "/etc/systemd/system/${SERVICE_NAME}.service"
    systemctl daemon-reload
fi

# Backup data option
if [ -d "$DATA_DIR" ] && [ "$(ls -A $DATA_DIR 2>/dev/null)" ]; then
    echo -e "\n${YELLOW}Data directory contains monitoring data.${NC}"
    read -p "Do you want to backup the data before removing? (y/N): " -n 1 -r
    echo
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        BACKUP_DIR="/tmp/network-monitor-backup-$(date +%Y%m%d-%H%M%S)"
        mkdir -p "$BACKUP_DIR"
        cp -r "$DATA_DIR"/* "$BACKUP_DIR"/ 2>/dev/null || true
        echo -e "${GREEN}Data backed up to: $BACKUP_DIR${NC}"
    fi
fi

# Remove directories
echo "Removing application directories..."
[ -d "$INSTALL_DIR" ] && rm -rf "$INSTALL_DIR"
[ -d "$LOG_DIR" ] && rm -rf "$LOG_DIR"
[ -d "$DATA_DIR" ] && rm -rf "$DATA_DIR"

# Remove user
if id "$USER" &>/dev/null; then
    echo "Removing service user..."
    userdel "$USER" 2>/dev/null || true
fi

echo -e "\n${GREEN}Network Monitor has been successfully uninstalled.${NC}"

# Note about Speedtest CLI
echo -e "\n${YELLOW}Note: Ookla Speedtest CLI was not removed.${NC}"
echo "If you want to remove it as well, run:"
echo "  Ubuntu/Debian: sudo apt remove speedtest"
echo "  RHEL/CentOS/Fedora: sudo yum remove speedtest (or dnf remove speedtest)"