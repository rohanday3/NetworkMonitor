# Network Monitor

A comprehensive Linux application for monitoring internet speed and latency over time using Ookla Speedtest CLI.

## Features

- **Automated Speed Testing**: Periodic internet speed measurements using Ookla Speedtest CLI
- **Latency Monitoring**: Regular ping tests to multiple targets (Google DNS, Cloudflare, OpenDNS)
- **Data Logging**: All results saved to CSV files for analysis
- **Systemd Integration**: Runs as a system service with automatic startup
- **Data Analysis**: Built-in tools for analyzing collected data
- **Visualization**: Generate charts and graphs from monitoring data
- **Easy Installation**: Automated installation script for major Linux distributions

## Quick Start

1. **Download and Install**:
   ```bash
   # Clone or download the files to a directory
   chmod +x install.sh
   sudo ./install.sh
   ```

2. **Start Monitoring**:
   ```bash
   sudo systemctl start network-monitor
   ```

3. **View Status**:
   ```bash
   sudo systemctl status network-monitor
   ```

4. **Analyze Data**:
   ```bash
   chmod +x analyze.sh
   sudo ./analyze.sh
   ```

## Installation

### Prerequisites

The installation script will automatically install:
- Python 3
- Ookla Speedtest CLI
- Required system packages

### Supported Distributions

- Ubuntu 18.04+
- Debian 9+
- CentOS 7+
- RHEL 7+
- Fedora 28+

### Manual Installation

If automatic installation fails, you can install dependencies manually:

1. **Install Python 3**:
   ```bash
   # Ubuntu/Debian
   sudo apt update && sudo apt install python3 python3-pip

   # CentOS/RHEL/Fedora
   sudo yum install python3 python3-pip  # or dnf
   ```

2. **Install Speedtest CLI**:
   ```bash
   # Ubuntu/Debian
   curl -s https://packagecloud.io/install/repositories/ookla/speedtest-cli/script.deb.sh | sudo bash
   sudo apt install speedtest

   # CentOS/RHEL/Fedora
   curl -s https://packagecloud.io/install/repositories/ookla/speedtest-cli/script.rpm.sh | sudo bash
   sudo yum install speedtest  # or dnf
   ```

3. **Run Installation Script**:
   ```bash
   sudo ./install.sh
   ```

## Configuration

### Default Settings

- **Test Interval**: 10 minutes
- **Ping Targets**: Google DNS (8.8.8.8), Cloudflare (1.1.1.1), OpenDNS (208.67.222.222)
- **Data Location**: `/var/lib/network-monitor/`
- **Logs Location**: `/var/log/network-monitor/`

### Changing Test Interval

Edit the systemd service:
```bash
sudo systemctl edit network-monitor
```

Add:
```ini
[Service]
ExecStart=
ExecStart=/usr/bin/python3 /opt/network-monitor/network_monitor.py --interval 5
```

Then restart:
```bash
sudo systemctl restart network-monitor
```

## Usage

### Service Management

```bash
# Start the service
sudo systemctl start network-monitor

# Stop the service
sudo systemctl stop network-monitor

# Check status
sudo systemctl status network-monitor

# View logs
journalctl -u network-monitor -f

# Enable auto-start on boot (done automatically during install)
sudo systemctl enable network-monitor
```

### Manual Testing

Run a single test:
```bash
sudo -u network-monitor python3 /opt/network-monitor/network_monitor.py --single
```

Run with custom interval:
```bash
sudo -u network-monitor python3 /opt/network-monitor/network_monitor.py --interval 5
```

### Data Analysis

Use the analysis script:
```bash
./analyze.sh
```

This shows:
- Total number of tests
- Latest test results
- Statistical summaries (min, max, average)
- Recent test history
- Service status

### Data Visualization

Generate charts (requires matplotlib and seaborn):
```bash
# Install visualization dependencies
pip3 install matplotlib seaborn pandas

# Generate all charts
python3 visualize.py --output-dir ./reports

# Generate specific chart
python3 visualize.py --chart speed --days 7
```

Available chart types:
- `speed`: Speed over time
- `ping`: Ping latency by target
- `distribution`: Speed/latency distributions
- `daily`: Daily summary statistics
- `all`: Generate all charts

## Data Files

### Speed Test Data (`speed_tests.csv`)

Columns:
- `timestamp`: Test time (ISO format)
- `download_mbps`: Download speed in Mbps
- `upload_mbps`: Upload speed in Mbps
- `ping_ms`: Ping latency in milliseconds
- `server_name`: Speedtest server name
- `server_location`: Server location
- `isp`: Internet Service Provider
- `external_ip`: Your external IP address

### Ping Test Data (`ping_tests.csv`)

Columns:
- `timestamp`: Test time (ISO format)
- `target`: Target IP address
- `avg_latency_ms`: Average latency in milliseconds
- `min_latency_ms`: Minimum latency
- `max_latency_ms`: Maximum latency
- `packet_loss_percent`: Packet loss percentage

## Data Analysis Examples

### Using Command Line Tools

View recent speed tests:
```bash
tail -10 /var/lib/network-monitor/speed_tests.csv
```

Calculate average download speed:
```bash
tail -n +2 /var/lib/network-monitor/speed_tests.csv | \
awk -F',' '{sum+=$2; count++} END {print "Average download:", sum/count, "Mbps"}'
```

Find minimum/maximum speeds:
```bash
tail -n +2 /var/lib/network-monitor/speed_tests.csv | \
awk -F',' 'NR==1{min=$2; max=$2} {if($2<min) min=$2; if($2>max) max=$2} END {print "Min:", min, "Mbps, Max:", max, "Mbps"}'
```

### Using Python/Pandas

```python
import pandas as pd

# Load data
df = pd.read_csv('/var/lib/network-monitor/speed_tests.csv')
df['timestamp'] = pd.to_datetime(df['timestamp'])

# Basic statistics
print(df[['download_mbps', 'upload_mbps', 'ping_ms']].describe())

# Performance over time
daily_avg = df.groupby(df['timestamp'].dt.date)['download_mbps'].mean()
print(daily_avg)
```

## Troubleshooting

### Service Won't Start

1. Check logs:
   ```bash
   journalctl -u network-monitor -n 50
   ```

2. Test manually:
   ```bash
   sudo -u network-monitor python3 /opt/network-monitor/network_monitor.py --single
   ```

3. Check Speedtest CLI:
   ```bash
   speedtest --version
   ```

### Permission Issues

Ensure correct ownership:
```bash
sudo chown -R network-monitor:network-monitor /var/lib/network-monitor
sudo chown -R network-monitor:network-monitor /var/log/network-monitor
```

### High CPU Usage

If the service is using too much CPU:
1. Increase the test interval
2. Check for network connectivity issues
3. Monitor system resources during tests

### Data Not Being Saved

1. Check disk space:
   ```bash
   df -h /var/lib/network-monitor
   ```

2. Check file permissions:
   ```bash
   ls -la /var/lib/network-monitor/
   ```

3. Test write access:
   ```bash
   sudo -u network-monitor touch /var/lib/network-monitor/test.txt
   ```

## Uninstallation

To completely remove the network monitor:

```bash
sudo ./uninstall.sh
```

This will:
- Stop and disable the service
- Remove all files and directories
- Optionally backup your data
- Remove the service user

Note: Speedtest CLI will remain installed and must be removed separately if desired.

## Advanced Usage

### Custom Ping Targets

Edit the script to add custom ping targets:
```python
self.ping_targets = [
    "8.8.8.8",           # Google DNS
    "1.1.1.1",           # Cloudflare DNS
    "your.custom.server", # Your custom server
]
```

### Integration with Monitoring Systems

The CSV data can be easily imported into:
- **Grafana**: Use CSV or convert to InfluxDB
- **Prometheus**: Use node_exporter with textfile collector
- **Zabbix**: Use Zabbix sender to import data
- **Nagios**: Create custom scripts to check thresholds

### API Integration

Example script to send data to external API:
```python
import requests
import pandas as pd

df = pd.read_csv('/var/lib/network-monitor/speed_tests.csv')
latest = df.iloc[-1]

# Send to your API
requests.post('https://your-api.com/metrics', json={
    'timestamp': latest['timestamp'],
    'download_mbps': latest['download_mbps'],
    'upload_mbps': latest['upload_mbps'],
    'ping_ms': latest['ping_ms']
})
```

## License

This project is open source and available under the MIT License.

## Contributing

Contributions are welcome! Please feel free to submit pull requests or open issues for bugs and feature requests.