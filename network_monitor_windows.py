#!/usr/bin/env python3
"""
Network Monitor - Windows Version
Periodic Internet Speed and Latency Monitoring for Windows
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
import platform
from datetime import datetime
from pathlib import Path
import statistics
import signal
import ctypes
import threading

class NetworkMonitorWindows:
    def __init__(self, log_dir=None, data_dir=None):
        # Set Windows-appropriate default directories
        if log_dir is None:
            log_dir = Path.home() / "AppData" / "Local" / "NetworkMonitor" / "logs"
        if data_dir is None:
            data_dir = Path.home() / "AppData" / "Local" / "NetworkMonitor" / "data"

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

        # Windows-specific signal handling
        if platform.system() == "Windows":
            signal.signal(signal.SIGINT, self._signal_handler)
            signal.signal(signal.SIGTERM, self._signal_handler)
            # Also handle Windows console events
            self._setup_windows_console_handler()

    def _setup_windows_console_handler(self):
        """Setup Windows console event handler for graceful shutdown"""
        try:
            def console_handler(event):
                if event in (0, 2):  # CTRL_C_EVENT, CTRL_CLOSE_EVENT
                    self.logger.info("Received Windows console event, shutting down...")
                    self.running = False
                    return True
                return False

            # Set console control handler
            kernel32 = ctypes.windll.kernel32
            kernel32.SetConsoleCtrlHandler(console_handler, True)
        except Exception as e:
            self.logger.warning(f"Could not set Windows console handler: {e}")

    def _signal_handler(self, signum, frame):
        """Handle shutdown signals gracefully"""
        self.logger.info(f"Received signal {signum}, shutting down...")
        self.running = False

    def _init_csv_files(self):
        """Initialize CSV files with headers if they don't exist"""
        # Speed test CSV with enhanced metrics
        if not self.speed_csv.exists():
            with open(self.speed_csv, 'w', newline='', encoding='utf-8') as csvfile:
                writer = csv.writer(csvfile)
                writer.writerow([
                    'timestamp', 'download_mbps', 'upload_mbps', 'ping_ms',
                    'server_name', 'server_location', 'server_id', 'isp', 'external_ip',
                    'idle_latency_ms', 'idle_jitter_ms',
                    'download_latency_low_ms', 'download_latency_high_ms', 'download_latency_iqm_ms', 'download_jitter_ms',
                    'upload_latency_low_ms', 'upload_latency_high_ms', 'upload_latency_iqm_ms', 'upload_jitter_ms',
                    'packet_loss_percent', 'download_bytes', 'upload_bytes', 'result_url'
                ])
        else:
            # Check if CSV needs to be migrated to new format
            self._migrate_csv_if_needed()

        # Ping test CSV
        if not self.ping_csv.exists():
            with open(self.ping_csv, 'w', newline='', encoding='utf-8') as csvfile:
                writer = csv.writer(csvfile)
                writer.writerow([
                    'timestamp', 'target', 'avg_latency_ms',
                    'min_latency_ms', 'max_latency_ms', 'packet_loss_percent'
                ])

    def _migrate_csv_if_needed(self):
        """Migrate old CSV format to new enhanced format if needed"""
        try:
            # Read the first line to check current format
            with open(self.speed_csv, 'r', newline='', encoding='utf-8') as csvfile:
                reader = csv.reader(csvfile)
                header = next(reader)

                # Check if we need to migrate (old format has 8 columns, new has 23)
                if len(header) < 23:
                    self.logger.info("Migrating CSV to enhanced format...")

                    # Read all existing data
                    csvfile.seek(0)
                    reader = csv.reader(csvfile)
                    rows = list(reader)

                    # Create backup
                    backup_file = self.speed_csv.with_suffix('.bak')
                    with open(backup_file, 'w', newline='', encoding='utf-8') as backup:
                        writer = csv.writer(backup)
                        writer.writerows(rows)

                    # Write new format
                    with open(self.speed_csv, 'w', newline='', encoding='utf-8') as csvfile:
                        writer = csv.writer(csvfile)
                        # Write new header
                        writer.writerow([
                            'timestamp', 'download_mbps', 'upload_mbps', 'ping_ms',
                            'server_name', 'server_location', 'server_id', 'isp', 'external_ip',
                            'idle_latency_ms', 'idle_jitter_ms',
                            'download_latency_low_ms', 'download_latency_high_ms', 'download_latency_iqm_ms', 'download_jitter_ms',
                            'upload_latency_low_ms', 'upload_latency_high_ms', 'upload_latency_iqm_ms', 'upload_jitter_ms',
                            'packet_loss_percent', 'download_bytes', 'upload_bytes', 'result_url'
                        ])

                        # Migrate existing data (skip header)
                        for row in rows[1:]:
                            if len(row) >= 8:  # Ensure we have at least the old format
                                # Fill missing columns with default values
                                migrated_row = row[:9] if len(row) >= 9 else row + ['']  # Add server_id if missing
                                migrated_row.extend([0] * 14)  # Add all new metric columns with default values
                                writer.writerow(migrated_row)

                    self.logger.info(f"CSV migration complete. Backup saved as {backup_file}")

        except Exception as e:
            self.logger.error(f"Error migrating CSV: {e}")

    def check_speedtest_cli(self):
        """Check if speedtest CLI is installed"""
        try:
            # Try both 'speedtest' and 'speedtest.exe'
            for cmd in ['speedtest', 'speedtest.exe']:
                try:
                    result = subprocess.run([cmd, '--version'],
                                          capture_output=True, text=True, timeout=10)
                    if result.returncode == 0:
                        self.logger.info(f"Speedtest CLI version: {result.stdout.strip()}")
                        self.speedtest_cmd = cmd
                        return True
                except FileNotFoundError:
                    continue

            self.logger.error("Speedtest CLI not found. Please install it first.")
            self.logger.info("Download from: https://www.speedtest.net/apps/cli")
            return False

        except subprocess.TimeoutExpired:
            self.logger.error("Speedtest CLI check timed out")
            return False

    def run_speedtest(self):
        """Run internet speed test using Ookla Speedtest CLI"""
        try:
            self.logger.info("Running speed test...")

            # Run speedtest with JSON output
            result = subprocess.run(
                [self.speedtest_cmd, '--format=json', '--accept-license', '--accept-gdpr'],
                capture_output=True, text=True, timeout=120
            )

            if result.returncode != 0:
                self.logger.error(f"Speedtest failed: {result.stderr}")
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
            with open(self.speed_csv, 'a', newline='', encoding='utf-8') as csvfile:
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
        """Run ping test to measure latency (Windows version)"""
        try:
            self.logger.debug(f"Pinging {target}...")

            # Windows ping command
            result = subprocess.run(
                ['ping', '-n', str(count), target],
                capture_output=True, text=True, timeout=30
            )

            if result.returncode != 0:
                self.logger.warning(f"Ping to {target} failed: {result.stderr}")
                return None

            # Parse Windows ping output
            lines = result.stdout.split('\n')

            # Extract latency values from Windows ping output
            latencies = []
            for line in lines:
                if 'time=' in line or 'time<' in line:
                    try:
                        # Handle both "time=XXXms" and "time<1ms" formats
                        if 'time<' in line:
                            # For very fast pings, assume 0.5ms
                            latencies.append(0.5)
                        else:
                            time_part = line.split('time=')[1].split('ms')[0]
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

            # Calculate packet loss from Windows ping output
            packet_loss = 0
            for line in lines:
                if 'Lost = ' in line:
                    try:
                        # Extract loss from format like "Lost = 0 (0% loss)"
                        loss_part = line.split('(')[1].split('%')[0]
                        packet_loss = float(loss_part)
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
                with open(self.ping_csv, 'a', newline='', encoding='utf-8') as csvfile:
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

        # Run speed test
        speed_result = self.run_speedtest()

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
                    for _ in range(interval_seconds):
                        if not self.running:
                            break
                        time.sleep(1)

            except KeyboardInterrupt:
                self.logger.info("Received interrupt signal, stopping...")
                break
            except Exception as e:
                self.logger.error(f"Unexpected error: {e}")
                self.logger.info("Waiting 60 seconds before retrying...")
                for _ in range(60):
                    if not self.running:
                        break
                    time.sleep(1)

        self.logger.info("Network monitoring stopped")

def main():
    parser = argparse.ArgumentParser(description='Network Monitor - Track internet speed and latency (Windows)')
    parser.add_argument('--interval', '-i', type=int, default=10,
                       help='Monitoring interval in minutes (default: 10)')
    parser.add_argument('--single', '-s', action='store_true',
                       help='Run a single test and exit')
    parser.add_argument('--log-dir',
                       help='Directory for log files (default: %USERPROFILE%\\AppData\\Local\\NetworkMonitor\\logs)')
    parser.add_argument('--data-dir',
                       help='Directory for data files (default: %USERPROFILE%\\AppData\\Local\\NetworkMonitor\\data)')

    args = parser.parse_args()

    # Create monitor instance
    monitor = NetworkMonitorWindows(log_dir=args.log_dir, data_dir=args.data_dir)

    # Check if speedtest CLI is available
    if not monitor.check_speedtest_cli():
        input("Press Enter to exit...")
        sys.exit(1)

    try:
        if args.single:
            monitor.run_single_test()
        else:
            monitor.run_continuous(args.interval)
    except KeyboardInterrupt:
        print("\nShutting down...")

    if not args.single:
        input("Press Enter to exit...")

if __name__ == '__main__':
    main()