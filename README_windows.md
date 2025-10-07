# Network Monitor for Windows

A comprehensive Windows application for monitoring internet speed and latency over time using Ookla Speedtest CLI.

## 🚀 Windows-Specific Features

- **Native Windows Integration**: Uses Windows-appropriate file paths and processes
- **Windows Service Support**: Can run as a Windows service (with optional service scripts)
- **Desktop Shortcuts**: Easy access through desktop shortcuts
- **Windows-Style UI**: Enhanced web dashboard with Windows design elements
- **Automatic Browser Launch**: Dashboard opens automatically in your default browser
- **Windows Ping Compatibility**: Handles Windows ping command output format

## 📋 Requirements

### System Requirements
- **Windows 10/11** or **Windows Server 2016+**
- **Python 3.7+** (from python.org)
- **Administrator privileges** (for installation only)
- **Internet connection**

### Dependencies
- **Ookla Speedtest CLI** (downloaded separately)
- **Python packages**: pandas, matplotlib, seaborn, numpy

## 🛠 Installation

### Quick Install

1. **Download Speedtest CLI**:
   - Go to https://www.speedtest.net/apps/cli
   - Download the Windows version
   - Extract `speedtest.exe` to a folder in your PATH or to the same folder as the scripts

2. **Run Installation**:
   ```cmd
   # Right-click Command Prompt and "Run as administrator"
   cd path\to\NetworkMonitor
   install_windows.bat
   ```

### Manual Installation

If automatic installation fails:

1. **Install Python 3.7+** from https://python.org
   - ✅ Check "Add Python to PATH" during installation

2. **Install Python packages**:
   ```cmd
   pip install pandas matplotlib seaborn numpy
   ```

3. **Download Speedtest CLI** and ensure it's accessible

4. **Run the installation script**

## 🎯 Usage

### Option 1: Desktop Shortcuts (Recommended)
After installation, use the desktop shortcuts:
- **"Network Monitor"** - Run monitoring manually
- **"Network Monitor Dashboard"** - Start web dashboard

### Option 2: Command Line

**Run Single Test**:
```cmd
python network_monitor_windows.py --single
```

**Continuous Monitoring**:
```cmd
python network_monitor_windows.py --interval 10
```

**Web Dashboard**:
```cmd
python dashboard_windows.py
```

### Option 3: Windows Service (Advanced)
```cmd
# Install as service (from install directory)
install_service.bat

# Service management
sc start NetworkMonitor
sc stop NetworkMonitor
sc query NetworkMonitor
```

## 📊 Data Storage

All data is stored in Windows user directories:

- **Data Files**: `%USERPROFILE%\AppData\Local\NetworkMonitor\data\`
  - `speed_tests.csv` - Speed test results
  - `ping_tests.csv` - Ping test results

- **Log Files**: `%USERPROFILE%\AppData\Local\NetworkMonitor\logs\`
  - `network_monitor.log` - Application logs

### Example Paths
```
C:\Users\YourUsername\AppData\Local\NetworkMonitor\data\speed_tests.csv
C:\Users\YourUsername\AppData\Local\NetworkMonitor\logs\network_monitor.log
```

## 🖥 Web Dashboard

The Windows dashboard includes:
- **Modern Windows-style UI** with gradients and effects
- **Real-time monitoring** with auto-refresh
- **Responsive design** for different screen sizes
- **Automatic browser launch**
- **Windows-specific file paths** and instructions

**Access**: http://localhost:8080

## 📈 Data Analysis

### Quick Analysis
```cmd
analyze_windows.bat
```

### Generate Charts
```cmd
# From installation directory
analyze_data.bat
```

### Python Analysis
```python
import pandas as pd
from pathlib import Path

# Load speed data
data_dir = Path.home() / "AppData" / "Local" / "NetworkMonitor" / "data"
df = pd.read_csv(data_dir / "speed_tests.csv")
df['timestamp'] = pd.to_datetime(df['timestamp'])

# Basic statistics
print(df[['download_mbps', 'upload_mbps', 'ping_ms']].describe())
```

## 🔧 Configuration

### Change Monitoring Interval
Edit the desktop shortcut or run:
```cmd
python network_monitor_windows.py --interval 5  # 5 minutes
```

### Custom Data Directory
```cmd
python network_monitor_windows.py --data-dir "C:\MyNetworkData"
```

### Custom Log Directory
```cmd
python network_monitor_windows.py --log-dir "C:\MyLogs"
```

## 🛠 Troubleshooting

### Common Issues

**1. "Python not found"**
- Install Python from python.org
- Ensure "Add Python to PATH" was checked during installation
- Restart Command Prompt after installation

**2. "Speedtest not found"**
- Download from https://www.speedtest.net/apps/cli
- Place `speedtest.exe` in same folder as scripts, or
- Add speedtest.exe location to Windows PATH

**3. "Permission denied"**
- Run Command Prompt as Administrator for installation
- Regular user permissions are fine for running

**4. Dashboard won't open**
- Check if port 8080 is available
- Try different port: `python dashboard_windows.py --port 8081`

**5. Service won't start**
- Ensure Python path is correct in service configuration
- Check Windows Event Viewer for service errors

### Debug Mode
```cmd
python network_monitor_windows.py --single -v
```

### Check Installation
```cmd
# Test Speedtest CLI
speedtest --version

# Test Python packages
python -c "import pandas, matplotlib, seaborn, numpy; print('All packages OK')"

# View data files
dir "%USERPROFILE%\AppData\Local\NetworkMonitor\data"
```

## 📁 File Structure

```
NetworkMonitor\
├── network_monitor_windows.py    # Main monitoring script
├── dashboard_windows.py          # Web dashboard
├── visualize.py                  # Chart generation
├── install_windows.bat           # Installation script
├── analyze_windows.bat           # Data analysis
├── requirements_windows.txt      # Dependencies
└── README_windows.md            # This file

After Installation:
%ProgramFiles%\NetworkMonitor\
├── network_monitor.py           # Installed monitor script
├── dashboard.py                 # Installed dashboard
├── visualize.py                 # Chart generator
├── run_monitor.bat              # Manual run script
├── start_dashboard.bat          # Dashboard launcher
├── analyze_data.bat             # Analysis script
└── install_service.bat          # Service installer
```

## 🎨 Dashboard Features

The Windows dashboard provides:

### Real-time Monitoring
- **Live speed metrics** with color-coded displays
- **Ping latency tracking** for multiple targets
- **Auto-refresh** every 2 minutes
- **Modern UI** with Windows design language

### Data Visualization
- **Recent test history** in tabular format
- **Server information** and ISP details
- **Packet loss monitoring**
- **Responsive layout** for all screen sizes

### Windows Integration
- **File system links** to data directories
- **Windows-style notifications**
- **Proper Unicode handling** for international users

## 🔒 Security

- **User-level permissions** (no admin required for operation)
- **Local data storage** (no cloud dependency)
- **Sandboxed operation** (doesn't modify system files)
- **HTTPS ready** (can be configured for SSL)

## ⚡ Performance

- **Efficient data storage** using CSV format
- **Minimal system impact** during testing
- **Configurable intervals** to balance monitoring vs. resources
- **Automatic cleanup** of old log files (optional)

## 🔄 Updates

To update the application:
1. Download new version
2. Run `install_windows.bat` again
3. Existing data and settings are preserved

## 📞 Support

For Windows-specific issues:
- Check Windows Event Viewer for service errors
- Verify Python installation: `python --version`
- Test network connectivity: `ping 8.8.8.8`
- Ensure Speedtest CLI works: `speedtest --version`

This Windows version provides the same comprehensive network monitoring capabilities as the Linux version, but with native Windows integration and user-friendly installation!