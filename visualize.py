#!/usr/bin/env python3
"""
Network Monitor Data Visualization
Creates charts and graphs from collected network monitoring data
"""

import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
import seaborn as sns
import argparse
import sys
from pathlib import Path
from datetime import datetime, timedelta
import numpy as np

class NetworkDataVisualizer:
    def __init__(self, data_dir="/var/lib/network-monitor"):
        self.data_dir = Path(data_dir)
        self.speed_csv = self.data_dir / "speed_tests.csv"
        self.ping_csv = self.data_dir / "ping_tests.csv"

        # Set style
        plt.style.use('seaborn-v0_8')
        sns.set_palette("husl")

    def load_speed_data(self):
        """Load speed test data"""
        if not self.speed_csv.exists():
            print(f"Speed test data not found: {self.speed_csv}")
            return None

        try:
            df = pd.read_csv(self.speed_csv)
            df['timestamp'] = pd.to_datetime(df['timestamp'])
            return df
        except Exception as e:
            print(f"Error loading speed data: {e}")
            return None

    def load_ping_data(self):
        """Load ping test data"""
        if not self.ping_csv.exists():
            print(f"Ping test data not found: {self.ping_csv}")
            return None

        try:
            df = pd.read_csv(self.ping_csv)
            df['timestamp'] = pd.to_datetime(df['timestamp'])
            return df
        except Exception as e:
            print(f"Error loading ping data: {e}")
            return None

    def plot_speed_over_time(self, output_file=None, days=7):
        """Plot internet speed over time"""
        df = self.load_speed_data()
        if df is None or df.empty:
            print("No speed data available")
            return

        # Filter to recent data
        cutoff_date = datetime.now() - timedelta(days=days)
        df = df[df['timestamp'] >= cutoff_date]

        if df.empty:
            print(f"No speed data available for the last {days} days")
            return

        fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(12, 10))

        # Download/Upload speeds
        ax1.plot(df['timestamp'], df['download_mbps'], label='Download', linewidth=2, alpha=0.8)
        ax1.plot(df['timestamp'], df['upload_mbps'], label='Upload', linewidth=2, alpha=0.8)
        ax1.set_ylabel('Speed (Mbps)')
        ax1.set_title(f'Internet Speed Over Time (Last {days} Days)')
        ax1.legend()
        ax1.grid(True, alpha=0.3)

        # Format x-axis
        ax1.xaxis.set_major_formatter(mdates.DateFormatter('%m/%d %H:%M'))
        ax1.xaxis.set_major_locator(mdates.HourLocator(interval=6))

        # Ping/Latency
        ax2.plot(df['timestamp'], df['ping_ms'], label='Ping', color='red', linewidth=2, alpha=0.8)
        ax2.set_ylabel('Latency (ms)')
        ax2.set_xlabel('Time')
        ax2.set_title('Ping Latency Over Time')
        ax2.legend()
        ax2.grid(True, alpha=0.3)

        # Format x-axis
        ax2.xaxis.set_major_formatter(mdates.DateFormatter('%m/%d %H:%M'))
        ax2.xaxis.set_major_locator(mdates.HourLocator(interval=6))

        plt.xticks(rotation=45)
        plt.tight_layout()

        if output_file:
            plt.savefig(output_file, dpi=300, bbox_inches='tight')
            print(f"Speed chart saved to: {output_file}")
        else:
            plt.show()

    def plot_ping_by_target(self, output_file=None, days=7):
        """Plot ping latency by target"""
        df = self.load_ping_data()
        if df is None or df.empty:
            print("No ping data available")
            return

        # Filter to recent data
        cutoff_date = datetime.now() - timedelta(days=days)
        df = df[df['timestamp'] >= cutoff_date]

        if df.empty:
            print(f"No ping data available for the last {days} days")
            return

        fig, ax = plt.subplots(figsize=(12, 6))

        # Plot each target separately
        targets = df['target'].unique()
        for target in targets:
            target_data = df[df['target'] == target]
            ax.plot(target_data['timestamp'], target_data['avg_latency_ms'],
                   label=target, linewidth=2, alpha=0.8)

        ax.set_ylabel('Latency (ms)')
        ax.set_xlabel('Time')
        ax.set_title(f'Ping Latency by Target (Last {days} Days)')
        ax.legend()
        ax.grid(True, alpha=0.3)

        # Format x-axis
        ax.xaxis.set_major_formatter(mdates.DateFormatter('%m/%d %H:%M'))
        ax.xaxis.set_major_locator(mdates.HourLocator(interval=6))

        plt.xticks(rotation=45)
        plt.tight_layout()

        if output_file:
            plt.savefig(output_file, dpi=300, bbox_inches='tight')
            print(f"Ping chart saved to: {output_file}")
        else:
            plt.show()

    def plot_speed_distribution(self, output_file=None):
        """Plot speed distribution histograms"""
        df = self.load_speed_data()
        if df is None or df.empty:
            print("No speed data available")
            return

        fig, ((ax1, ax2), (ax3, ax4)) = plt.subplots(2, 2, figsize=(12, 10))

        # Download speed histogram
        ax1.hist(df['download_mbps'], bins=30, alpha=0.7, edgecolor='black')
        ax1.set_xlabel('Download Speed (Mbps)')
        ax1.set_ylabel('Frequency')
        ax1.set_title('Download Speed Distribution')
        ax1.axvline(df['download_mbps'].mean(), color='red', linestyle='--',
                   label=f'Mean: {df["download_mbps"].mean():.1f} Mbps')
        ax1.legend()
        ax1.grid(True, alpha=0.3)

        # Upload speed histogram
        ax2.hist(df['upload_mbps'], bins=30, alpha=0.7, edgecolor='black', color='orange')
        ax2.set_xlabel('Upload Speed (Mbps)')
        ax2.set_ylabel('Frequency')
        ax2.set_title('Upload Speed Distribution')
        ax2.axvline(df['upload_mbps'].mean(), color='red', linestyle='--',
                   label=f'Mean: {df["upload_mbps"].mean():.1f} Mbps')
        ax2.legend()
        ax2.grid(True, alpha=0.3)

        # Ping histogram
        ax3.hist(df['ping_ms'], bins=30, alpha=0.7, edgecolor='black', color='green')
        ax3.set_xlabel('Ping (ms)')
        ax3.set_ylabel('Frequency')
        ax3.set_title('Ping Distribution')
        ax3.axvline(df['ping_ms'].mean(), color='red', linestyle='--',
                   label=f'Mean: {df["ping_ms"].mean():.1f} ms')
        ax3.legend()
        ax3.grid(True, alpha=0.3)

        # Speed ratio (upload/download)
        speed_ratio = df['upload_mbps'] / df['download_mbps']
        ax4.hist(speed_ratio, bins=30, alpha=0.7, edgecolor='black', color='purple')
        ax4.set_xlabel('Upload/Download Ratio')
        ax4.set_ylabel('Frequency')
        ax4.set_title('Upload/Download Speed Ratio')
        ax4.axvline(speed_ratio.mean(), color='red', linestyle='--',
                   label=f'Mean: {speed_ratio.mean():.2f}')
        ax4.legend()
        ax4.grid(True, alpha=0.3)

        plt.tight_layout()

        if output_file:
            plt.savefig(output_file, dpi=300, bbox_inches='tight')
            print(f"Distribution charts saved to: {output_file}")
        else:
            plt.show()

    def plot_daily_summary(self, output_file=None, days=30):
        """Plot daily summary statistics"""
        df = self.load_speed_data()
        if df is None or df.empty:
            print("No speed data available")
            return

        # Filter to recent data
        cutoff_date = datetime.now() - timedelta(days=days)
        df = df[df['timestamp'] >= cutoff_date]

        if df.empty:
            print(f"No speed data available for the last {days} days")
            return

        # Group by date
        df['date'] = df['timestamp'].dt.date
        daily_stats = df.groupby('date').agg({
            'download_mbps': ['mean', 'min', 'max'],
            'upload_mbps': ['mean', 'min', 'max'],
            'ping_ms': ['mean', 'min', 'max']
        }).round(2)

        fig, (ax1, ax2, ax3) = plt.subplots(3, 1, figsize=(12, 12))

        dates = daily_stats.index

        # Download speeds
        ax1.plot(dates, daily_stats[('download_mbps', 'mean')], 'b-', linewidth=2, label='Average')
        ax1.fill_between(dates,
                        daily_stats[('download_mbps', 'min')],
                        daily_stats[('download_mbps', 'max')],
                        alpha=0.3, label='Min-Max Range')
        ax1.set_ylabel('Download Speed (Mbps)')
        ax1.set_title('Daily Download Speed Summary')
        ax1.legend()
        ax1.grid(True, alpha=0.3)

        # Upload speeds
        ax2.plot(dates, daily_stats[('upload_mbps', 'mean')], 'r-', linewidth=2, label='Average')
        ax2.fill_between(dates,
                        daily_stats[('upload_mbps', 'min')],
                        daily_stats[('upload_mbps', 'max')],
                        alpha=0.3, label='Min-Max Range')
        ax2.set_ylabel('Upload Speed (Mbps)')
        ax2.set_title('Daily Upload Speed Summary')
        ax2.legend()
        ax2.grid(True, alpha=0.3)

        # Ping
        ax3.plot(dates, daily_stats[('ping_ms', 'mean')], 'g-', linewidth=2, label='Average')
        ax3.fill_between(dates,
                        daily_stats[('ping_ms', 'min')],
                        daily_stats[('ping_ms', 'max')],
                        alpha=0.3, label='Min-Max Range')
        ax3.set_ylabel('Ping (ms)')
        ax3.set_xlabel('Date')
        ax3.set_title('Daily Ping Summary')
        ax3.legend()
        ax3.grid(True, alpha=0.3)

        plt.xticks(rotation=45)
        plt.tight_layout()

        if output_file:
            plt.savefig(output_file, dpi=300, bbox_inches='tight')
            print(f"Daily summary chart saved to: {output_file}")
        else:
            plt.show()

    def generate_report(self, output_dir="./reports"):
        """Generate a complete set of charts"""
        output_path = Path(output_dir)
        output_path.mkdir(exist_ok=True)

        print("Generating network monitoring charts...")

        # Speed over time
        self.plot_speed_over_time(output_path / "speed_over_time.png")

        # Ping by target
        self.plot_ping_by_target(output_path / "ping_by_target.png")

        # Speed distributions
        self.plot_speed_distribution(output_path / "speed_distributions.png")

        # Daily summary
        self.plot_daily_summary(output_path / "daily_summary.png")

        print(f"\nAll charts saved to: {output_path}")
        print("Generated files:")
        print("- speed_over_time.png")
        print("- ping_by_target.png")
        print("- speed_distributions.png")
        print("- daily_summary.png")

def main():
    parser = argparse.ArgumentParser(description='Network Monitor Data Visualization')
    parser.add_argument('--data-dir', default='/var/lib/network-monitor',
                       help='Directory containing data files')
    parser.add_argument('--output-dir', default='./reports',
                       help='Directory to save chart files')
    parser.add_argument('--days', type=int, default=7,
                       help='Number of days to include in time-based charts')
    parser.add_argument('--chart', choices=['speed', 'ping', 'distribution', 'daily', 'all'],
                       default='all', help='Which chart(s) to generate')

    args = parser.parse_args()

    # Check if matplotlib is available
    try:
        import matplotlib.pyplot as plt
        import seaborn as sns
    except ImportError:
        print("Error: matplotlib and seaborn are required for visualization")
        print("Install with: pip3 install matplotlib seaborn")
        sys.exit(1)

    visualizer = NetworkDataVisualizer(args.data_dir)

    output_path = Path(args.output_dir)
    output_path.mkdir(exist_ok=True)

    if args.chart == 'all':
        visualizer.generate_report(args.output_dir)
    elif args.chart == 'speed':
        visualizer.plot_speed_over_time(output_path / "speed_over_time.png", args.days)
    elif args.chart == 'ping':
        visualizer.plot_ping_by_target(output_path / "ping_by_target.png", args.days)
    elif args.chart == 'distribution':
        visualizer.plot_speed_distribution(output_path / "speed_distributions.png")
    elif args.chart == 'daily':
        visualizer.plot_daily_summary(output_path / "daily_summary.png", 30)

if __name__ == '__main__':
    main()