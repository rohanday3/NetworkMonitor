#!/bin/bash

# Network Monitor Data Analysis Script
# This script provides basic analysis of collected network monitoring data

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Default data directory
DATA_DIR="/var/lib/network-monitor"

# Check if data directory exists
if [ ! -d "$DATA_DIR" ]; then
    echo -e "${RED}Data directory not found: $DATA_DIR${NC}"
    echo "Make sure the network monitor is installed and has run at least once."
    exit 1
fi

SPEED_CSV="$DATA_DIR/speed_tests.csv"
PING_CSV="$DATA_DIR/ping_tests.csv"

echo -e "${GREEN}Network Monitor Data Analysis${NC}"
echo "============================="

# Function to check if file exists and has data
check_file() {
    local file=$1
    local name=$2

    if [ ! -f "$file" ]; then
        echo -e "${RED}$name file not found: $file${NC}"
        return 1
    fi

    local lines=$(wc -l < "$file")
    if [ "$lines" -le 1 ]; then
        echo -e "${YELLOW}$name file has no data yet${NC}"
        return 1
    fi

    return 0
}

# Speed test analysis
if check_file "$SPEED_CSV" "Speed test"; then
    echo -e "\n${BLUE}Speed Test Analysis:${NC}"
    echo "===================="

    # Count total tests
    total_tests=$(($(wc -l < "$SPEED_CSV") - 1))
    echo "Total speed tests: $total_tests"

    # Latest test
    echo -e "\nLatest test:"
    tail -n 1 "$SPEED_CSV" | awk -F',' '{
        print "  Date/Time: " $1
        print "  Download: " $2 " Mbps"
        print "  Upload: " $3 " Mbps"
        print "  Ping: " $4 " ms"
        print "  Server: " $5 " (" $6 ")"
        print "  ISP: " $7
    }'

    # Basic statistics using awk
    echo -e "\nSpeed Test Statistics:"
    tail -n +2 "$SPEED_CSV" | awk -F',' '
    BEGIN {
        count = 0
        sum_down = 0
        sum_up = 0
        sum_ping = 0
        min_down = 999999
        max_down = 0
        min_up = 999999
        max_up = 0
        min_ping = 999999
        max_ping = 0
    }
    {
        count++
        sum_down += $2
        sum_up += $3
        sum_ping += $4

        if ($2 < min_down) min_down = $2
        if ($2 > max_down) max_down = $2
        if ($3 < min_up) min_up = $3
        if ($3 > max_up) max_up = $3
        if ($4 < min_ping) min_ping = $4
        if ($4 > max_ping) max_ping = $4
    }
    END {
        if (count > 0) {
            printf "  Download - Avg: %.2f Mbps, Min: %.2f Mbps, Max: %.2f Mbps\n", sum_down/count, min_down, max_down
            printf "  Upload   - Avg: %.2f Mbps, Min: %.2f Mbps, Max: %.2f Mbps\n", sum_up/count, min_up, max_up
            printf "  Ping     - Avg: %.2f ms, Min: %.2f ms, Max: %.2f ms\n", sum_ping/count, min_ping, max_ping
        }
    }'

    # Recent performance (last 24 hours if available)
    echo -e "\nRecent Tests (last 10):"
    tail -n 10 "$SPEED_CSV" | tail -n +2 | awk -F',' '{
        # Extract just the date part (first 10 characters)
        date_part = substr($1, 1, 10)
        time_part = substr($1, 12, 8)
        printf "  %s %s - Down: %6.2f Mbps, Up: %6.2f Mbps, Ping: %6.2f ms\n",
               date_part, time_part, $2, $3, $4
    }'
fi

# Ping test analysis
if check_file "$PING_CSV" "Ping test"; then
    echo -e "\n${BLUE}Ping Test Analysis:${NC}"
    echo "=================="

    # Count total tests
    total_ping_tests=$(($(wc -l < "$PING_CSV") - 1))
    echo "Total ping tests: $total_ping_tests"

    # Latest ping tests by target
    echo -e "\nLatest ping results by target:"
    tail -n 20 "$PING_CSV" | awk -F',' '
    {
        target = $2
        avg_latency = $3
        packet_loss = $6
        latest[target] = avg_latency
        loss[target] = packet_loss
    }
    END {
        for (target in latest) {
            printf "  %-15s: %6.2f ms (loss: %s%%)\n", target, latest[target], loss[target]
        }
    }'

    # Ping statistics by target
    echo -e "\nPing statistics by target:"
    tail -n +2 "$PING_CSV" | awk -F',' '
    {
        target = $2
        avg_latency = $3
        packet_loss = $6

        count[target]++
        sum_latency[target] += avg_latency
        sum_loss[target] += packet_loss

        if (count[target] == 1 || avg_latency < min_latency[target]) min_latency[target] = avg_latency
        if (count[target] == 1 || avg_latency > max_latency[target]) max_latency[target] = avg_latency
    }
    END {
        for (target in count) {
            avg_lat = sum_latency[target] / count[target]
            avg_loss = sum_loss[target] / count[target]
            printf "  %-15s: Avg: %6.2f ms, Min: %6.2f ms, Max: %6.2f ms, Loss: %5.2f%%\n",
                   target, avg_lat, min_latency[target], max_latency[target], avg_loss
        }
    }'
fi

# Service status
echo -e "\n${BLUE}Service Status:${NC}"
echo "=============="
if systemctl is-active --quiet network-monitor; then
    echo -e "Service status: ${GREEN}RUNNING${NC}"
    echo "Next test in: $(systemctl show network-monitor --property=InactiveEnterTimestamp | cut -d= -f2)"
else
    echo -e "Service status: ${RED}STOPPED${NC}"
fi

# Disk usage
echo -e "\nData directory size: $(du -sh $DATA_DIR | cut -f1)"

# Show data file locations
echo -e "\n${BLUE}Data Files:${NC}"
echo "==========="
echo "Speed tests: $SPEED_CSV"
echo "Ping tests:  $PING_CSV"

if [ -f "$SPEED_CSV" ]; then
    echo "Speed test entries: $(($(wc -l < "$SPEED_CSV") - 1))"
fi

if [ -f "$PING_CSV" ]; then
    echo "Ping test entries: $(($(wc -l < "$PING_CSV") - 1))"
fi

echo -e "\n${YELLOW}Commands:${NC}"
echo "View live logs: journalctl -u network-monitor -f"
echo "Manual test:    sudo -u network-monitor python3 /opt/network-monitor/network_monitor.py --single"
echo "Service start:  sudo systemctl start network-monitor"
echo "Service stop:   sudo systemctl stop network-monitor"