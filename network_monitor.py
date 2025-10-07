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
                    'ping_ms', 'server_name', 'server_location',
                    'isp', 'external_ip'
                ])

        # Ping test CSV
        if not self.ping_csv.exists():
            with open(self.ping_csv, 'w', newline='') as csvfile:
                writer = csv.writer(csvfile)
                writer.writerow([
                    'timestamp', 'target', 'avg_latency_ms',
                    'min_latency_ms', 'max_latency_ms', 'packet_loss_percent'
                ])

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

    def run_speedtest(self):
        """Run internet speed test using Ookla Speedtest CLI"""
        try:
            self.logger.info("Running speed test...")

            # Run speedtest with JSON output
            result = subprocess.run(
                ['speedtest', '--format=json', '--accept-license', '--accept-gdpr'],
                capture_output=True, text=True, timeout=120
            )

            if result.returncode != 0:
                self.logger.error(f"Speedtest failed: {result.stderr}")
                return None

            # Parse JSON output
            data = json.loads(result.stdout)

            # Extract relevant data
            speed_data = {
                'timestamp': datetime.now().isoformat(),
                'download_mbps': round(data['download']['bandwidth'] * 8 / 1_000_000, 2),
                'upload_mbps': round(data['upload']['bandwidth'] * 8 / 1_000_000, 2),
                'ping_ms': round(data['ping']['latency'], 2),
                'server_name': data['server']['name'],
                'server_location': f"{data['server']['location']}, {data['server']['country']}",
                'isp': data['isp'],
                'external_ip': data['interface']['externalIp']
            }

            # Log the results
            self.logger.info(
                f"Speed test completed - "
                f"Download: {speed_data['download_mbps']} Mbps, "
                f"Upload: {speed_data['upload_mbps']} Mbps, "
                f"Ping: {speed_data['ping_ms']} ms"
            )

            # Save to CSV
            with open(self.speed_csv, 'a', newline='') as csvfile:
                writer = csv.writer(csvfile)
                writer.writerow([
                    speed_data['timestamp'], speed_data['download_mbps'],
                    speed_data['upload_mbps'], speed_data['ping_ms'],
                    speed_data['server_name'], speed_data['server_location'],
                    speed_data['isp'], speed_data['external_ip']
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

    args = parser.parse_args()

    # Create monitor instance
    monitor = NetworkMonitor(log_dir=args.log_dir, data_dir=args.data_dir)

    # Check if speedtest CLI is available
    if not monitor.check_speedtest_cli():
        sys.exit(1)

    if args.single:
        monitor.run_single_test()
    else:
        monitor.run_continuous(args.interval)

if __name__ == '__main__':
    main()