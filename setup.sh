#!/bin/bash

# Quick setup script to make all shell scripts executable
# Run this script after downloading the files

echo "Setting up Network Monitor..."

# Make shell scripts executable
chmod +x install.sh
chmod +x uninstall.sh
chmod +x analyze.sh

# Make Python scripts executable
chmod +x network_monitor.py
chmod +x visualize.py
chmod +x dashboard.py

echo "Setup complete!"
echo ""
echo "Next steps:"
echo "1. Install: sudo ./install.sh"
echo "2. Start service: sudo systemctl start network-monitor"
echo "3. Check status: sudo systemctl status network-monitor"
echo "4. Analyze data: ./analyze.sh"
echo "5. Web dashboard: python3 dashboard.py"