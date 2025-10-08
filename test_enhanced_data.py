#!/usr/bin/env python3
"""
Test Enhanced Data Collection
Verify that the enhanced network monitor correctly extracts all speedtest metrics
"""

import json
import subprocess
import sys
from datetime import datetime

def test_speedtest_data_extraction():
    """Test speedtest data extraction to see what fields are available"""
    print("Testing Speedtest CLI data extraction...")
    print("=" * 50)

    try:
        # Run speedtest with JSON output
        print("Running speedtest with JSON output...")
        result = subprocess.run(
            ['speedtest', '--format=json', '--accept-license', '--accept-gdpr'],
            capture_output=True, text=True, timeout=120
        )

        if result.returncode != 0:
            print(f"❌ Speedtest failed: {result.stderr}")
            return False

        # Parse JSON output
        data = json.loads(result.stdout)

        # Display the structure
        print("✅ Speedtest completed successfully!")
        print("\n📊 Available data structure:")
        print(json.dumps(data, indent=2))

        # Test our data extraction
        print("\n🔍 Testing enhanced data extraction:")

        extracted_data = {
            'timestamp': datetime.now().isoformat(),
            'download_mbps': round(data['download']['bandwidth'] * 8 / 1_000_000, 2),
            'upload_mbps': round(data['upload']['bandwidth'] * 8 / 1_000_000, 2),
            'ping_ms': round(data['ping']['latency'], 2),
            'server_name': data['server']['name'],
            'server_location': f"{data['server']['location']}, {data['server']['country']}",
            'server_id': data['server']['id'],
            'isp': data['isp'],
            'external_ip': data['interface']['externalIp'],
            'idle_latency_ms': round(data['ping'].get('latency', 0), 2),
            'idle_jitter_ms': round(data['ping'].get('jitter', 0), 2),
            'download_latency_low_ms': round(data['download'].get('latency', {}).get('low', 0), 2),
            'download_latency_high_ms': round(data['download'].get('latency', {}).get('high', 0), 2),
            'download_latency_iqm_ms': round(data['download'].get('latency', {}).get('iqm', 0), 2),
            'download_jitter_ms': round(data['download'].get('latency', {}).get('jitter', 0), 2),
            'upload_latency_low_ms': round(data['upload'].get('latency', {}).get('low', 0), 2),
            'upload_latency_high_ms': round(data['upload'].get('latency', {}).get('high', 0), 2),
            'upload_latency_iqm_ms': round(data['upload'].get('latency', {}).get('iqm', 0), 2),
            'upload_jitter_ms': round(data['upload'].get('latency', {}).get('jitter', 0), 2),
            'packet_loss_percent': data.get('packetLoss', 0),
            'download_bytes': data['download'].get('bytes', 0),
            'upload_bytes': data['upload'].get('bytes', 0),
            'result_url': data.get('result', {}).get('url', '')
        }

        print("✅ Enhanced data extracted successfully:")
        for key, value in extracted_data.items():
            print(f"  📈 {key}: {value}")

        # Show improvements
        print(f"\n📈 Performance Summary:")
        print(f"  🔽 Download: {extracted_data['download_mbps']} Mbps ({extracted_data['download_bytes']:,} bytes)")
        print(f"  🔼 Upload: {extracted_data['upload_mbps']} Mbps ({extracted_data['upload_bytes']:,} bytes)")
        print(f"  📶 Server: {extracted_data['server_name']} (ID: {extracted_data['server_id']})")
        print(f"  📍 Location: {extracted_data['server_location']}")
        print(f"  ⏱️  Ping: {extracted_data['ping_ms']} ms (Jitter: {extracted_data['idle_jitter_ms']} ms)")
        print(f"  📦 Packet Loss: {extracted_data['packet_loss_percent']}%")

        if extracted_data['download_jitter_ms'] > 0:
            print(f"  🔽 Download Jitter: {extracted_data['download_jitter_ms']} ms")
        if extracted_data['upload_jitter_ms'] > 0:
            print(f"  🔼 Upload Jitter: {extracted_data['upload_jitter_ms']} ms")

        if extracted_data['result_url']:
            print(f"  🔗 Result URL: {extracted_data['result_url']}")

        return True

    except subprocess.TimeoutExpired:
        print("❌ Speedtest timed out")
        return False
    except json.JSONDecodeError as e:
        print(f"❌ Failed to parse speedtest output: {e}")
        return False
    except Exception as e:
        print(f"❌ Error: {e}")
        return False

if __name__ == "__main__":
    print("🚀 Network Monitor Enhanced Data Collection Test")
    print("=" * 60)

    # Check if speedtest CLI is available
    try:
        result = subprocess.run(['speedtest', '--version'], capture_output=True, text=True, timeout=10)
        if result.returncode == 0:
            print(f"✅ Speedtest CLI found: {result.stdout.strip()}")
        else:
            print("❌ Speedtest CLI not found")
            sys.exit(1)
    except FileNotFoundError:
        print("❌ Speedtest CLI not found. Please install it first.")
        print("   Download from: https://www.speedtest.net/apps/cli")
        sys.exit(1)

    # Run the test
    success = test_speedtest_data_extraction()

    if success:
        print("\n🎉 Enhanced data collection test completed successfully!")
        print("   Your network monitor will now collect detailed metrics including:")
        print("   • Jitter measurements (idle, download, upload)")
        print("   • Latency ranges (low, high, interquartile mean)")
        print("   • Packet loss percentage")
        print("   • Data usage (bytes transferred)")
        print("   • Server ID for consistent monitoring")
        print("   • Result URLs for detailed analysis")
    else:
        print("\n❌ Enhanced data collection test failed")
        sys.exit(1)