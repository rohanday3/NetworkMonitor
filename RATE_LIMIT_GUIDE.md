# Rate Limit Safe Usage Guide

## 🚨 Avoiding Rate Limits

To avoid getting rate limited by Speedtest.net, the network monitor now:

### **Default Behavior (No Server Testing)**
```bash
# ✅ SAFE - Uses speedtest's automatic server selection (no rate limit risk)
python network_monitor.py --single

# ✅ SAFE - Continuous monitoring with automatic server selection
python network_monitor.py --interval 10
```

### **Using Your Known Good Server (Recommended)**
Since you know server 48238 (Atomic Access) works well:

```bash
# ✅ SAFE - Set your preferred server once (no testing)
python network_monitor.py --set-preferred-server 48238

# ✅ SAFE - Use specific server for single test
python network_monitor.py --server-id 48238 --single

# ✅ SAFE - Continuous monitoring with your preferred server
python network_monitor.py --interval 10
```

After setting preferred server, all future tests will use it automatically.

### **Server Testing (Use Sparingly)**
```bash
# ⚠️ RATE LIMIT RISK - Only use when you really need to find best server
python network_monitor.py --find-best-server

# ⚠️ RATE LIMIT RISK - Interactive server testing
python server_optimizer.py
```

## 🔧 Quick Setup for Your Raspberry Pi

Based on your message, here's the safest approach:

```bash
# 1. Set your known good server (no testing, no rate limits)
sudo -u network-monitor python3 /opt/network-monitor/network_monitor.py --set-preferred-server 48238

# 2. Run normal tests (will use server 48238 automatically)
sudo -u network-monitor python3 /opt/network-monitor/network_monitor.py --single

# 3. Start continuous monitoring
sudo systemctl start network-monitor
```

## 📊 What Changed

**Before**: Automatically tested multiple servers → Rate limits
**Now**: Uses speedtest default OR cached preferred server → No rate limits

## 🎯 Error Fix

Also fixed the `'distance'` field error you encountered by using safe field access.

## 🏃‍♂️ Quick Commands

```bash
# Just run a test (safe, no server testing)
python network_monitor.py --single

# Set your good server as default
python network_monitor.py --set-preferred-server 48238

# List available servers (if you need to see options)
python network_monitor.py --list-servers

# Force use speedtest's default (ignore any cached server)
python network_monitor.py --no-server-optimization --single
```

The system now respects rate limits and won't automatically test servers unless explicitly requested! 🚀