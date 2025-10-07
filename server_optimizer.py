#!/usr/bin/env python3
"""
Speedtest Server Optimizer
A utility to find and test the best speedtest servers for your location
"""

import subprocess
import json
import sys
import time
from datetime import datetime

def run_speedtest_with_server(server_id):
    """Run speedtest with specific server"""
    try:
        result = subprocess.run(
            ['speedtest', '--server-id', str(server_id), '--format=json',
             '--accept-license', '--accept-gdpr'],
            capture_output=True, text=True, timeout=120
        )

        if result.returncode == 0:
            data = json.loads(result.stdout)
            return {
                'server_id': server_id,
                'server_name': data['server']['name'],
                'location': f"{data['server']['location']}, {data['server']['country']}",
                'distance': data['server']['distance'],
                'download_mbps': round(data['download']['bandwidth'] * 8 / 1_000_000, 2),
                'upload_mbps': round(data['upload']['bandwidth'] * 8 / 1_000_000, 2),
                'ping_ms': round(data['ping']['latency'], 2),
                'jitter_ms': round(data['ping']['jitter'], 2) if 'jitter' in data['ping'] else 0
            }
    except Exception as e:
        print(f"Error testing server {server_id}: {e}")
    return None

def get_servers():
    """Get available servers"""
    try:
        result = subprocess.run(
            ['speedtest', '--servers', '--format=json'],
            capture_output=True, text=True, timeout=30
        )

        if result.returncode == 0:
            data = json.loads(result.stdout)
            return data.get('servers', [])
    except Exception as e:
        print(f"Error getting servers: {e}")
    return []

def main():
    print("🚀 Speedtest Server Optimizer")
    print("=" * 50)

    # Check if speedtest CLI is available
    try:
        subprocess.run(['speedtest', '--version'], capture_output=True, timeout=5)
    except:
        print("❌ Speedtest CLI not found. Please install it first.")
        sys.exit(1)

    # Get available servers
    print("📡 Getting available servers...")
    servers = get_servers()

    if not servers:
        print("❌ No servers found")
        sys.exit(1)

    print(f"✅ Found {len(servers)} servers")
    print("\n📋 Top 10 closest servers:")
    print("-" * 70)
    print(f"{'ID':<8} {'Name':<25} {'Location':<30} {'Distance':<10}")
    print("-" * 70)

    for i, server in enumerate(servers[:10]):
        print(f"{server['id']:<8} {server['name'][:24]:<25} {server['location'][:29]:<30} {server['distance']:.1f} km")

    # Ask user which servers to test
    print(f"\n🔬 Which servers would you like to test?")
    print("Options:")
    print("1. Test top 5 servers (quick)")
    print("2. Test top 10 servers (thorough)")
    print("3. Test specific server IDs")
    print("4. Exit")

    choice = input("\nEnter your choice (1-4): ").strip()

    servers_to_test = []

    if choice == "1":
        servers_to_test = servers[:5]
    elif choice == "2":
        servers_to_test = servers[:10]
    elif choice == "3":
        server_ids = input("Enter server IDs separated by commas (e.g., 48238,1270,21325): ").strip()
        try:
            ids = [int(x.strip()) for x in server_ids.split(',')]
            servers_to_test = [s for s in servers if s['id'] in ids]
            if not servers_to_test:
                print("❌ No valid server IDs found")
                sys.exit(1)
        except ValueError:
            print("❌ Invalid server IDs")
            sys.exit(1)
    elif choice == "4":
        print("👋 Goodbye!")
        sys.exit(0)
    else:
        print("❌ Invalid choice")
        sys.exit(1)

    # Test servers
    print(f"\n🧪 Testing {len(servers_to_test)} servers...")
    print("This may take a few minutes...\n")

    results = []

    for i, server in enumerate(servers_to_test):
        print(f"Testing {i+1}/{len(servers_to_test)}: {server['name']} (ID: {server['id']})...")

        result = run_speedtest_with_server(server['id'])
        if result:
            # Calculate performance score
            score = result['download_mbps'] - (result['ping_ms'] / 10)
            result['score'] = round(score, 2)
            results.append(result)

            print(f"  ✅ Download: {result['download_mbps']} Mbps, "
                  f"Upload: {result['upload_mbps']} Mbps, "
                  f"Ping: {result['ping_ms']} ms, Score: {result['score']}")
        else:
            print(f"  ❌ Test failed")

        # Small delay between tests
        if i < len(servers_to_test) - 1:
            time.sleep(2)

    if not results:
        print("❌ No successful tests")
        sys.exit(1)

    # Sort by score
    results.sort(key=lambda x: x['score'], reverse=True)

    # Display results
    print(f"\n🏆 TEST RESULTS (sorted by performance score)")
    print("=" * 100)
    print(f"{'Rank':<6} {'Server Name':<25} {'ID':<8} {'Download':<12} {'Upload':<12} {'Ping':<10} {'Score':<8}")
    print("-" * 100)

    for i, result in enumerate(results):
        rank = f"#{i+1}"
        print(f"{rank:<6} {result['server_name'][:24]:<25} {result['server_id']:<8} "
              f"{result['download_mbps']} Mbps{'':<4} {result['upload_mbps']} Mbps{'':<5} "
              f"{result['ping_ms']} ms{'':<4} {result['score']}")

    # Best server recommendation
    best = results[0]
    print(f"\n🎯 RECOMMENDATION:")
    print(f"Best server: {best['server_name']} (ID: {best['server_id']})")
    print(f"Location: {best['location']}")
    print(f"Performance: {best['download_mbps']} Mbps down, {best['upload_mbps']} Mbps up, {best['ping_ms']} ms ping")
    print(f"Distance: {best['distance']:.1f} km")

    print(f"\n💡 To use this server in your network monitor:")
    print(f"python network_monitor.py --server-id {best['server_id']}")
    print(f"Or to cache it as the default best server:")
    print(f"python network_monitor.py --find-best-server")

if __name__ == '__main__':
    main()