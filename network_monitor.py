#!/usr/bin/env python3
"""
Network Monitor - Periodic Internet Speed and Latency Monitoring
Monitors internet speed using Speedtest CLI and latency using ping
"""

import subprocess
import csv
import json
import time
import logging
import argparse
import os
import sys
from datetime import datetime
from pathlib import Path
import statistics
import signal

class NetworkMonitor:
    def __init__(self, log_dir="/var/log/network-monitor", data_dir="/var/lib/network-monitor"):
        self.log_dir = Path(log_dir)
        self.data_dir = Path(data_dir)
        self.running = True

        # Create directories if they don't exist
        self.log_dir.mkdir(parents=True, exist_ok=True)
        self.data_dir.mkdir(parents=True, exist_ok=True)

        # Setup logging
        log_file = self.log_dir / "network_monitor.log"
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(levelname)s - %(message)s',
            handlers=[
                logging.FileHandler(log_file),
                logging.StreamHandler(sys.stdout)
            ]
        )
        self.logger = logging.getLogger(__name__)

        # CSV files for data storage
        self.speed_csv = self.data_dir / "speed_tests.csv"
        self.ping_csv = self.data_dir / "ping_tests.csv"

        # Initialize CSV files with headers if they don't exist
        self._init_csv_files()

        # Default ping targets
        self.ping_targets = [
            "8.8.8.8",      # Google DNS
            "1.1.1.1",      # Cloudflare DNS
            "208.67.222.222" # OpenDNS
        ]

        # Server selection settings
        self.preferred_server_id = None
        self.server_test_results = {}
        self.best_server_cache_file = self.data_dir / "best_server.json"

        # Load cached best server if available
        self._load_best_server_cache()

        # Signal handlers for graceful shutdown
        signal.signal(signal.SIGINT, self._signal_handler)
        signal.signal(signal.SIGTERM, self._signal_handler)

    def _signal_handler(self, signum, frame):
        """Handle shutdown signals gracefully"""
        self.logger.info(f"Received signal {signum}, shutting down...")
        self.running = False

    def _init_csv_files(self):
        """Initialize CSV files with headers if they don't exist"""
        # Speed test CSV
        if not self.speed_csv.exists():
            with open(self.speed_csv, 'w', newline='') as csvfile:
                writer = csv.writer(csvfile)
                writer.writerow([
                    'timestamp', 'download_mbps', 'upload_mbps',
                    'idle_latency_ms', 'idle_jitter_ms', 'idle_low_ms', 'idle_high_ms',
                    'download_latency_ms', 'download_jitter_ms', 'download_low_ms', 'download_high_ms',
                    'upload_latency_ms', 'upload_jitter_ms', 'upload_low_ms', 'upload_high_ms',
                    'packet_loss_percent', 'download_bytes', 'upload_bytes',
                    'server_name', 'server_location', 'server_id', 'isp', 'external_ip', 'result_url'
                ])

        # Ping test CSV
        if not self.ping_csv.exists():
            with open(self.ping_csv, 'w', newline='') as csvfile:
                writer = csv.writer(csvfile)
                writer.writerow([
                    'timestamp', 'target', 'avg_latency_ms',
                    'min_latency_ms', 'max_latency_ms', 'packet_loss_percent'
                ])

    def _ensure_csv_has_server_id(self):
        """Ensure CSV file has all new columns (for backward compatibility)"""
        try:
            if not self.speed_csv.exists():
                return

            # Read first line to check headers
            with open(self.speed_csv, 'r') as csvfile:
                first_line = csvfile.readline().strip()
                headers = first_line.split(',')

                # Check if we have the new extended format
                new_headers = [
                    'timestamp', 'download_mbps', 'upload_mbps',
                    'idle_latency_ms', 'idle_jitter_ms', 'idle_low_ms', 'idle_high_ms',
                    'download_latency_ms', 'download_jitter_ms', 'download_low_ms', 'download_high_ms',
                    'upload_latency_ms', 'upload_jitter_ms', 'upload_low_ms', 'upload_high_ms',
                    'packet_loss_percent', 'download_bytes', 'upload_bytes',
                    'server_name', 'server_location', 'server_id', 'isp', 'external_ip', 'result_url'
                ]

                needs_update = False

                # Check if we need to update to new format
                if len(headers) < len(new_headers) or 'idle_latency_ms' not in headers:
                    needs_update = True
                    self.logger.info("Updating CSV file to include extended metrics...")

                if needs_update:
                    # Read all data
                    csvfile.seek(0)
                    reader = csv.reader(csvfile)
                    all_rows = list(reader)

                    # Update header
                    if all_rows:
                        all_rows[0] = new_headers

                        # Extend existing data rows with empty values for new columns
                        for i in range(1, len(all_rows)):
                            row = all_rows[i]
                            # Pad row to new length
                            while len(row) < len(new_headers):
                                row.append('')

                    # Write updated data back
                    with open(self.speed_csv, 'w', newline='') as csvfile:
                        writer = csv.writer(csvfile)
                        writer.writerows(all_rows)

        except Exception as e:
            self.logger.warning(f"Could not update CSV format: {e}")

    def check_speedtest_cli(self):
        """Check if speedtest CLI is installed"""
        try:
            result = subprocess.run(['speedtest', '--version'],
                                  capture_output=True, text=True, timeout=10)
            if result.returncode == 0:
                self.logger.info(f"Speedtest CLI version: {result.stdout.strip()}")
                return True
        except (subprocess.TimeoutExpired, FileNotFoundError):
            pass

        self.logger.error("Speedtest CLI not found. Please install it first.")
        return False

    def _load_best_server_cache(self):
        """Load cached best server information"""
        try:
            if self.best_server_cache_file.exists():
                with open(self.best_server_cache_file, 'r') as f:
                    cache_data = json.load(f)
                    self.preferred_server_id = cache_data.get('server_id')
                    self.server_test_results = cache_data.get('test_results', {})
                    self.logger.info(f"Loaded cached best server: ID {self.preferred_server_id}")
        except Exception as e:
            self.logger.warning(f"Could not load server cache: {e}")

    def _save_best_server_cache(self):
        """Save best server information to cache"""
        try:
            cache_data = {
                'server_id': self.preferred_server_id,
                'test_results': self.server_test_results,
                'last_updated': datetime.now().isoformat()
            }
            with open(self.best_server_cache_file, 'w') as f:
                json.dump(cache_data, f, indent=2)
        except Exception as e:
            self.logger.warning(f"Could not save server cache: {e}")

    def get_available_servers(self):
        """Get list of available speedtest servers"""
        try:
            self.logger.info("Getting available speedtest servers...")

            result = subprocess.run(
                ['speedtest', '--servers', '--format=json'],
                capture_output=True, text=True, timeout=30
            )

            if result.returncode != 0:
                self.logger.error(f"Failed to get servers: {result.stderr}")
                return []

            data = json.loads(result.stdout)
            servers = data.get('servers', [])

            self.logger.info(f"Found {len(servers)} available servers")
            return servers

        except subprocess.TimeoutExpired:
            self.logger.error("Server list request timed out")
            return []
        except json.JSONDecodeError as e:
            self.logger.error(f"Failed to parse server list: {e}")
            return []
        except Exception as e:
            self.logger.error(f"Error getting servers: {e}")
            return []

    def test_server_performance(self, server_id, server_name=None):
        """Test performance of a specific server"""
        try:
            if server_name:
                self.logger.info(f"Testing server: {server_name} (ID: {server_id})")
            else:
                self.logger.info(f"Testing server ID: {server_id}")

            result = subprocess.run(
                ['speedtest', '--server-id', str(server_id), '--format=json',
                 '--accept-license', '--accept-gdpr'],
                capture_output=True, text=True, timeout=120
            )

            if result.returncode != 0:
                self.logger.warning(f"Server {server_id} test failed: {result.stderr}")
                return None

            data = json.loads(result.stdout)

            # Calculate a performance score based on download speed and ping
            download_mbps = data['download']['bandwidth'] * 8 / 1_000_000
            ping_ms = data['ping']['latency']

            # Score formula: prioritize download speed, penalize high ping
            # Higher score is better
            score = download_mbps - (ping_ms / 10)

            performance = {
                'server_id': server_id,
                'server_name': data['server']['name'],
                'location': f"{data['server']['location']}, {data['server']['country']}",
                'distance': data['server'].get('distance', 0),  # Use .get() with default value
                'download_mbps': round(download_mbps, 2),
                'upload_mbps': round(data['upload']['bandwidth'] * 8 / 1_000_000, 2),
                'ping_ms': round(ping_ms, 2),
                'score': round(score, 2),
                'jitter': round(data['ping']['jitter'], 2) if 'jitter' in data['ping'] else 0,
                'test_time': datetime.now().isoformat()
            }

            self.logger.info(
                f"Server {server_id} results - "
                f"Download: {performance['download_mbps']} Mbps, "
                f"Ping: {performance['ping_ms']} ms, "
                f"Score: {performance['score']}"
            )

            return performance

        except subprocess.TimeoutExpired:
            self.logger.warning(f"Server {server_id} test timed out")
            return None
        except json.JSONDecodeError as e:
            self.logger.warning(f"Failed to parse results for server {server_id}: {e}")
            return None
        except Exception as e:
            self.logger.error(f"Error testing server {server_id}: {e}")
            return None

    def find_best_server(self, max_servers_to_test=5, force_retest=False):
        """Find the best performing server by testing multiple servers"""

        if not force_retest and self.preferred_server_id:
            self.logger.info(f"Using cached best server: {self.preferred_server_id}")
            return self.preferred_server_id

        self.logger.info("Finding best speedtest server...")

        # Get available servers
        servers = self.get_available_servers()
        if not servers:
            self.logger.error("No servers available")
            return None

        # Test top servers (closest by distance)
        servers_to_test = servers[:max_servers_to_test]
        self.logger.info(f"Testing {len(servers_to_test)} servers for best performance...")

        test_results = []

        for server in servers_to_test:
            performance = self.test_server_performance(
                server['id'],
                server['name']
            )

            if performance:
                test_results.append(performance)
                self.server_test_results[str(server['id'])] = performance

            # Small delay between tests
            time.sleep(2)

        if not test_results:
            self.logger.error("No servers responded successfully")
            return None

        # Sort by score (higher is better)
        test_results.sort(key=lambda x: x['score'], reverse=True)

        # Log results
        self.logger.info("Server test results (sorted by performance score):")
        for i, result in enumerate(test_results):
            self.logger.info(
                f"  {i+1}. {result['server_name']} (ID: {result['server_id']}) - "
                f"Score: {result['score']}, Download: {result['download_mbps']} Mbps, "
                f"Ping: {result['ping_ms']} ms"
            )

        # Select best server
        best_server = test_results[0]
        self.preferred_server_id = best_server['server_id']

        self.logger.info(
            f"Best server selected: {best_server['server_name']} "
            f"(ID: {self.preferred_server_id}) with score {best_server['score']}"
        )

        # Save to cache
        self._save_best_server_cache()

        return self.preferred_server_id

    def run_speedtest(self, use_best_server=True):
        """Run internet speed test using Ookla Speedtest CLI"""
        try:
            # Determine which server to use
            server_id = None
            if use_best_server:
                if not self.preferred_server_id:
                    self.logger.info("No preferred server set, finding best server...")
                    server_id = self.find_best_server()
                else:
                    server_id = self.preferred_server_id

            if server_id:
                self.logger.info(f"Running speed test with server ID: {server_id}")
                cmd = ['speedtest', '--server-id', str(server_id), '--format=json',
                       '--accept-license', '--accept-gdpr']
            else:
                self.logger.info("Running speed test with automatic server selection...")
                cmd = ['speedtest', '--format=json', '--accept-license', '--accept-gdpr']

            # Run speedtest
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=120)

            if result.returncode != 0:
                self.logger.error(f"Speedtest failed: {result.stderr}")
                # If specific server failed, try automatic selection as fallback
                if server_id:
                    self.logger.info("Retrying with automatic server selection...")
                    cmd = ['speedtest', '--format=json', '--accept-license', '--accept-gdpr']
                    result = subprocess.run(cmd, capture_output=True, text=True, timeout=120)
                    if result.returncode != 0:
                        return None
                else:
                    return None

            # Parse JSON output
            data = json.loads(result.stdout)

            # Extract relevant data with enhanced metrics
            speed_data = {
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

            # Log the results with enhanced metrics
            self.logger.info(
                f"Speed test completed - "
                f"Server: {speed_data['server_name']} (ID: {speed_data['server_id']}), "
                f"Download: {speed_data['download_mbps']} Mbps, "
                f"Upload: {speed_data['upload_mbps']} Mbps, "
                f"Ping: {speed_data['ping_ms']} ms, "
                f"Jitter: {speed_data['idle_jitter_ms']} ms, "
                f"Packet Loss: {speed_data['packet_loss_percent']}%"
            )

            # Save to CSV with all enhanced metrics
            self._ensure_csv_has_server_id()
            with open(self.speed_csv, 'a', newline='') as csvfile:
                writer = csv.writer(csvfile)
                writer.writerow([
                    speed_data['timestamp'], speed_data['download_mbps'],
                    speed_data['upload_mbps'], speed_data['ping_ms'],
                    speed_data['server_name'], speed_data['server_location'],
                    speed_data['server_id'], speed_data['isp'], speed_data['external_ip'],
                    speed_data['idle_latency_ms'], speed_data['idle_jitter_ms'],
                    speed_data['download_latency_low_ms'], speed_data['download_latency_high_ms'],
                    speed_data['download_latency_iqm_ms'], speed_data['download_jitter_ms'],
                    speed_data['upload_latency_low_ms'], speed_data['upload_latency_high_ms'],
                    speed_data['upload_latency_iqm_ms'], speed_data['upload_jitter_ms'],
                    speed_data['packet_loss_percent'], speed_data['download_bytes'],
                    speed_data['upload_bytes'], speed_data['result_url']
                ])

            return speed_data

        except subprocess.TimeoutExpired:
            self.logger.error("Speed test timed out")
            return None
        except json.JSONDecodeError as e:
            self.logger.error(f"Failed to parse speedtest output: {e}")
            return None
        except Exception as e:
            self.logger.error(f"Speed test error: {e}")
            return None

    def run_ping_test(self, target, count=10):
        """Run ping test to measure latency"""
        try:
            self.logger.debug(f"Pinging {target}...")

            # Run ping command
            result = subprocess.run(
                ['ping', '-c', str(count), target],
                capture_output=True, text=True, timeout=30
            )

            if result.returncode != 0:
                self.logger.warning(f"Ping to {target} failed: {result.stderr}")
                return None

            # Parse ping output
            lines = result.stdout.split('\n')

            # Extract latency values
            latencies = []
            for line in lines:
                if 'time=' in line:
                    try:
                        time_part = line.split('time=')[1].split()[0]
                        latency = float(time_part)
                        latencies.append(latency)
                    except (IndexError, ValueError):
                        continue

            if not latencies:
                self.logger.warning(f"No latency data found for {target}")
                return None

            # Calculate statistics
            avg_latency = round(statistics.mean(latencies), 2)
            min_latency = round(min(latencies), 2)
            max_latency = round(max(latencies), 2)

            # Calculate packet loss
            packet_loss = 0
            for line in lines:
                if 'packet loss' in line:
                    try:
                        loss_str = line.split(',')[2].strip()
                        packet_loss = float(loss_str.split('%')[0])
                        break
                    except (IndexError, ValueError):
                        continue

            ping_data = {
                'timestamp': datetime.now().isoformat(),
                'target': target,
                'avg_latency_ms': avg_latency,
                'min_latency_ms': min_latency,
                'max_latency_ms': max_latency,
                'packet_loss_percent': packet_loss
            }

            self.logger.debug(
                f"Ping to {target} - Avg: {avg_latency}ms, "
                f"Loss: {packet_loss}%"
            )

            return ping_data

        except subprocess.TimeoutExpired:
            self.logger.warning(f"Ping to {target} timed out")
            return None
        except Exception as e:
            self.logger.error(f"Ping test error for {target}: {e}")
            return None

    def run_all_ping_tests(self):
        """Run ping tests for all targets"""
        ping_results = []

        for target in self.ping_targets:
            result = self.run_ping_test(target)
            if result:
                ping_results.append(result)

                # Save to CSV
                with open(self.ping_csv, 'a', newline='') as csvfile:
                    writer = csv.writer(csvfile)
                    writer.writerow([
                        result['timestamp'], result['target'],
                        result['avg_latency_ms'], result['min_latency_ms'],
                        result['max_latency_ms'], result['packet_loss_percent']
                    ])

        if ping_results:
            avg_latencies = [r['avg_latency_ms'] for r in ping_results]
            overall_avg = round(statistics.mean(avg_latencies), 2)
            self.logger.info(f"Ping tests completed - Overall average: {overall_avg}ms")

        return ping_results

    def run_single_test(self):
        """Run a single round of tests"""
        self.logger.info("Starting network monitoring cycle...")

        # Run speed test - only use best server if one is already set/cached
        use_server_optimization = bool(self.preferred_server_id)
        speed_result = self.run_speedtest(use_best_server=use_server_optimization)

        # Run ping tests
        ping_results = self.run_all_ping_tests()

        self.logger.info("Network monitoring cycle completed")
        return speed_result, ping_results

    def run_continuous(self, interval_minutes=10):
        """Run continuous monitoring"""
        interval_seconds = interval_minutes * 60

        self.logger.info(f"Starting continuous monitoring (interval: {interval_minutes} minutes)")

        while self.running:
            try:
                self.run_single_test()

                if self.running:  # Check if we should continue
                    self.logger.info(f"Waiting {interval_minutes} minutes until next test...")
                    time.sleep(interval_seconds)

            except KeyboardInterrupt:
                self.logger.info("Received interrupt signal, stopping...")
                break
            except Exception as e:
                self.logger.error(f"Unexpected error: {e}")
                self.logger.info("Waiting 60 seconds before retrying...")
                time.sleep(60)

        self.logger.info("Network monitoring stopped")

def main():
    parser = argparse.ArgumentParser(description='Network Monitor - Track internet speed and latency')
    parser.add_argument('--interval', '-i', type=int, default=10,
                       help='Monitoring interval in minutes (default: 10)')
    parser.add_argument('--single', '-s', action='store_true',
                       help='Run a single test and exit')
    parser.add_argument('--log-dir', default='/var/log/network-monitor',
                       help='Directory for log files')
    parser.add_argument('--data-dir', default='/var/lib/network-monitor',
                       help='Directory for data files')
    parser.add_argument('--find-best-server', action='store_true',
                       help='Find and cache the best server, then exit')
    parser.add_argument('--list-servers', action='store_true',
                       help='List available servers and exit')
    parser.add_argument('--server-id', type=int,
                       help='Use specific server ID for tests')
    parser.add_argument('--test-servers', type=int, default=5,
                       help='Number of servers to test when finding best (default: 5)')
    parser.add_argument('--no-server-optimization', action='store_true',
                       help='Disable automatic server selection, use speedtest default')
    parser.add_argument('--set-preferred-server', type=int,
                       help='Set and cache a preferred server ID without testing')

    args = parser.parse_args()

    # Create monitor instance
    monitor = NetworkMonitor(log_dir=args.log_dir, data_dir=args.data_dir)

    # Check if speedtest CLI is available
    if not monitor.check_speedtest_cli():
        sys.exit(1)

    # Handle server-related commands
    if args.list_servers:
        print("Available Speedtest Servers:")
        print("=" * 50)
        servers = monitor.get_available_servers()
        for server in servers[:20]:  # Show top 20
            print(f"ID: {server['id']:>6} | {server['name']:<25} | {server['location']}, {server['country']}")
        print(f"\nShowing top 20 of {len(servers)} available servers")
        return

    if args.find_best_server:
        print("Finding best speedtest server...")
        print("=" * 40)
        best_server_id = monitor.find_best_server(max_servers_to_test=args.test_servers, force_retest=True)
        if best_server_id:
            print(f"\nBest server found and cached: ID {best_server_id}")
            print("This server will be used for future tests.")
        else:
            print("Failed to find best server.")
        return

    # Set specific server if provided
    if args.server_id:
        monitor.preferred_server_id = args.server_id
        print(f"Using server ID: {args.server_id}")

    # Set and cache preferred server
    if args.set_preferred_server:
        monitor.preferred_server_id = args.set_preferred_server
        monitor._save_best_server_cache()
        print(f"Preferred server set and cached: ID {args.set_preferred_server}")
        print("This server will be used for future tests.")
        return

    # Only use server optimization if explicitly enabled or if server is already cached
    use_best_server = not args.no_server_optimization and (args.server_id or monitor.preferred_server_id or args.find_best_server)

    if args.single:
        # Only find best server if explicitly requested, not automatically
        monitor.run_single_test()
    else:
        # Only find best server if explicitly requested, not automatically
        monitor.run_continuous(args.interval)

if __name__ == '__main__':
    main()