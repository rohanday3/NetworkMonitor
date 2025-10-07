# Server Selection Feature Usage Guide

## 🎯 New Server Selection Capabilities

Your network monitor now includes intelligent server selection to get the most consistent and fastest speed test results!

## 🚀 Quick Start

### Find the Best Server (Recommended)
```bash
# Test multiple servers and cache the best one
python network_monitor.py --find-best-server

# Test more servers for better accuracy (tests top 10 instead of 5)
python network_monitor.py --find-best-server --test-servers 10
```

### Use a Specific Server
```bash
# Use the Atomic Access server that gave you 105 Mbps
python network_monitor.py --server-id 48238 --single

# Run continuous monitoring with specific server
python network_monitor.py --server-id 48238 --interval 10
```

### List Available Servers
```bash
# See all available servers in your area
python network_monitor.py --list-servers
```

## 🛠 Server Optimizer Tool

I've also created a dedicated server testing tool:

```bash
# Interactive server testing and optimization
python server_optimizer.py
```

This tool will:
- Show you the closest servers
- Let you test specific servers or groups
- Rank servers by performance
- Give recommendations

## 📊 How Server Selection Works

### Performance Scoring
The system scores servers based on:
- **Download Speed** (primary factor)
- **Ping Latency** (lower is better)
- **Consistency** (based on jitter)

**Score Formula**: `Download Speed (Mbps) - (Ping ms / 10)`

### Automatic Best Server Selection
1. Gets list of closest servers
2. Tests top 5 servers (configurable)
3. Ranks by performance score
4. Caches the best server for future use
5. Falls back to automatic selection if cached server fails

## 🔧 Command Line Options

### New Arguments:
- `--find-best-server` - Find and cache best server, then exit
- `--list-servers` - List available servers and exit
- `--server-id ID` - Use specific server ID for tests
- `--test-servers N` - Number of servers to test when finding best (default: 5)
- `--no-server-optimization` - Disable automatic server selection

### Examples:

```bash
# Find best server first time
python network_monitor.py --find-best-server

# Run single test with automatic best server
python network_monitor.py --single

# Run with specific server (your good one)
python network_monitor.py --server-id 48238 --single

# Continuous monitoring with best server
python network_monitor.py --interval 10

# Disable server optimization (use speedtest default)
python network_monitor.py --no-server-optimization --single

# Test 10 servers to find the best one
python network_monitor.py --find-best-server --test-servers 10
```

## 📈 What This Solves

Your original issue:
- **Problem**: 33 Mbps with random servers vs 105 Mbps with server 48238
- **Solution**: Automatically test and cache the best server
- **Result**: Consistent high-speed results without manual server selection

## 💾 Server Caching

The best server is cached in:
- **Linux**: `/var/lib/network-monitor/best_server.json`
- **Windows**: `%USERPROFILE%\AppData\Local\NetworkMonitor\data\best_server.json`

Cache includes:
- Best server ID
- Test results for all tested servers
- Last update timestamp

## 🔄 Updated CSV Format

Speed test CSV now includes server information:
```
timestamp,download_mbps,upload_mbps,ping_ms,server_name,server_location,server_id,isp,external_ip
```

This helps you track which server was used for each test.

## 🎛 Dashboard Updates

The web dashboard now shows:
- Server ID and name for each test
- Performance consistency tracking
- Server-specific analysis

## 🤖 Automatic Behavior

1. **First Run**: Will find best server automatically
2. **Subsequent Runs**: Uses cached best server
3. **Server Failure**: Falls back to automatic selection
4. **Periodic Re-testing**: Can be forced with `--find-best-server`

## 🔍 Troubleshooting Server Issues

If you're getting inconsistent speeds:

1. **Find best server**:
   ```bash
   python network_monitor.py --find-best-server --test-servers 10
   ```

2. **Test specific servers**:
   ```bash
   python server_optimizer.py
   ```

3. **Check server consistency**:
   ```bash
   # Run multiple tests with same server
   for i in {1..5}; do
     python network_monitor.py --server-id 48238 --single
     sleep 30
   done
   ```

4. **Force re-discovery**:
   ```bash
   # Remove cache and find new best server
   rm /var/lib/network-monitor/best_server.json  # Linux
   # or delete %USERPROFILE%\AppData\Local\NetworkMonitor\data\best_server.json  # Windows
   python network_monitor.py --find-best-server
   ```

This should give you much more consistent and reliable speed test results! 🚀