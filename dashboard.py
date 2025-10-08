#!/usr/bin/env python3
"""
Simple Web Dashboard for Network Monitor
Provides a basic web interface to view monitoring data
"""

import json
import csv
from datetime import datetime, timedelta
from pathlib import Path
from http.server import HTTPServer, BaseHTTPRequestHandler
import urllib.parse
import argparse

class NetworkDashboardHandler(BaseHTTPRequestHandler):
    def __init__(self, *args, data_dir="/var/lib/network-monitor", **kwargs):
        self.data_dir = Path(data_dir)
        super().__init__(*args, **kwargs)

    def do_GET(self):
        if self.path == '/' or self.path == '/index.html':
            self.serve_dashboard()
        elif self.path == '/api/speed':
            self.serve_speed_data()
        elif self.path == '/api/ping':
            self.serve_ping_data()
        elif self.path == '/api/status':
            self.serve_status()
        else:
            self.send_error(404)

    def serve_dashboard(self):
        html = """
<!DOCTYPE html>
<html>
<head>
    <title>Network Monitor Dashboard</title>
    <meta charset="utf-8">
    <meta name="viewport" content="width=device-width, initial-scale=1">
    <style>
        body { font-family: Arial, sans-serif; margin: 20px; background-color: #f5f5f5; }
        .container { max-width: 1200px; margin: 0 auto; }
        .card { background: white; padding: 20px; margin: 20px 0; border-radius: 8px; box-shadow: 0 2px 4px rgba(0,0,0,0.1); }
        .metric { display: inline-block; margin: 10px 20px 10px 0; }
        .metric-value { font-size: 2em; font-weight: bold; }
        .metric-label { color: #666; font-size: 0.9em; }
        .download { color: #2196F3; }
        .upload { color: #FF9800; }
        .ping { color: #4CAF50; }
        table { width: 100%; border-collapse: collapse; }
        th, td { padding: 8px; text-align: left; border-bottom: 1px solid #ddd; }
        th { background-color: #f2f2f2; }
        .refresh-btn { background: #2196F3; color: white; padding: 10px 20px; border: none; border-radius: 4px; cursor: pointer; }
        .status-running { color: #4CAF50; }
        .status-stopped { color: #f44336; }
    </style>
</head>
<body>
    <div class="container">
        <h1>Network Monitor Dashboard</h1>

        <div class="card">
            <h2>Current Status</h2>
            <div id="status">Loading...</div>
            <button class="refresh-btn" onclick="refreshData()">Refresh Data</button>
        </div>

        <div class="card">
            <h2>Latest Speed Test</h2>
            <div id="latest-speed">Loading...</div>
        </div>

        <div class="card">
            <h2>Recent Speed Tests</h2>
            <div id="speed-history">Loading...</div>
        </div>

        <div class="card">
            <h2>Latest Ping Results</h2>
            <div id="ping-results">Loading...</div>
        </div>
    </div>

    <script>
        function formatDate(dateString) {
            return new Date(dateString).toLocaleString();
        }

        function loadStatus() {
            fetch('/api/status')
                .then(response => response.json())
                .then(data => {
                    document.getElementById('status').innerHTML = `
                        <p>Last updated: ${formatDate(data.last_updated)}</p>
                        <p>Total speed tests: ${data.total_speed_tests}</p>
                        <p>Total ping tests: ${data.total_ping_tests}</p>
                    `;
                })
                .catch(error => {
                    document.getElementById('status').innerHTML = '<p style="color: red;">Error loading status</p>';
                });
        }

        function loadSpeedData() {
            fetch('/api/speed')
                .then(response => response.json())
                .then(data => {
                    if (data.length === 0) {
                        document.getElementById('latest-speed').innerHTML = '<p>No speed test data available</p>';
                        document.getElementById('speed-history').innerHTML = '<p>No speed test data available</p>';
                        return;
                    }

                    // Latest test
                    const latest = data[data.length - 1];
                    document.getElementById('latest-speed').innerHTML = `
                        <div class="metric download">
                            <div class="metric-value">${latest.download_mbps}</div>
                            <div class="metric-label">Mbps Download</div>
                        </div>
                        <div class="metric upload">
                            <div class="metric-value">${latest.upload_mbps}</div>
                            <div class="metric-label">Mbps Upload</div>
                        </div>
                        <div class="metric ping">
                            <div class="metric-value">${latest.ping_ms}</div>
                            <div class="metric-label">ms Ping</div>
                        </div>
                        <p>Server: ${latest.server_name} (${latest.server_location})</p>
                        <p>ISP: ${latest.isp}</p>
                        <p>Time: ${formatDate(latest.timestamp)}</p>
                    `;

                    // Recent history
                    const recent = data.slice(-10).reverse();
                    let tableHtml = `
                        <table>
                            <tr>
                                <th>Time</th>
                                <th>Download (Mbps)</th>
                                <th>Upload (Mbps)</th>
                                <th>Ping (ms)</th>
                                <th>Server</th>
                            </tr>
                    `;

                    recent.forEach(test => {
                        tableHtml += `
                            <tr>
                                <td>${formatDate(test.timestamp)}</td>
                                <td class="download">${test.download_mbps}</td>
                                <td class="upload">${test.upload_mbps}</td>
                                <td class="ping">${test.ping_ms}</td>
                                <td>${test.server_name}</td>
                            </tr>
                        `;
                    });

                    tableHtml += '</table>';
                    document.getElementById('speed-history').innerHTML = tableHtml;
                })
                .catch(error => {
                    document.getElementById('latest-speed').innerHTML = '<p style="color: red;">Error loading speed data</p>';
                    document.getElementById('speed-history').innerHTML = '<p style="color: red;">Error loading speed data</p>';
                });
        }

        function loadPingData() {
            fetch('/api/ping')
                .then(response => response.json())
                .then(data => {
                    if (data.length === 0) {
                        document.getElementById('ping-results').innerHTML = '<p>No ping data available</p>';
                        return;
                    }

                    // Group by target and get latest for each
                    const byTarget = {};
                    data.forEach(ping => {
                        if (!byTarget[ping.target] || ping.timestamp > byTarget[ping.target].timestamp) {
                            byTarget[ping.target] = ping;
                        }
                    });

                    let tableHtml = `
                        <table>
                            <tr>
                                <th>Target</th>
                                <th>Avg Latency (ms)</th>
                                <th>Min (ms)</th>
                                <th>Max (ms)</th>
                                <th>Packet Loss (%)</th>
                                <th>Time</th>
                            </tr>
                    `;

                    Object.values(byTarget).forEach(ping => {
                        tableHtml += `
                            <tr>
                                <td>${ping.target}</td>
                                <td class="ping">${ping.avg_latency_ms}</td>
                                <td>${ping.min_latency_ms}</td>
                                <td>${ping.max_latency_ms}</td>
                                <td>${ping.packet_loss_percent}</td>
                                <td>${formatDate(ping.timestamp)}</td>
                            </tr>
                        `;
                    });

                    tableHtml += '</table>';
                    document.getElementById('ping-results').innerHTML = tableHtml;
                })
                .catch(error => {
                    document.getElementById('ping-results').innerHTML = '<p style="color: red;">Error loading ping data</p>';
                });
        }

        function refreshData() {
            loadStatus();
            loadSpeedData();
            loadPingData();
        }

        // Load data on page load
        window.onload = refreshData;

        // Auto-refresh every 5 minutes
        setInterval(refreshData, 300000);
    </script>
</body>
</html>
        """

        self.send_response(200)
        self.send_header('Content-type', 'text/html')
        self.end_headers()
        self.wfile.write(html.encode())

    def serve_speed_data(self):
        speed_csv = self.data_dir / "speed_tests.csv"
        data = []

        try:
            with open(speed_csv, 'r') as file:
                reader = csv.DictReader(file)
                for row in reader:
                    # Handle both old and new CSV formats
                    entry = {
                        'timestamp': row['timestamp'],
                        'download_mbps': float(row['download_mbps']),
                        'upload_mbps': float(row['upload_mbps']),
                        'ping_ms': float(row['ping_ms']),
                        'server_name': row['server_name'],
                        'server_location': row['server_location'],
                        'isp': row['isp']
                    }

                    # Add enhanced metrics if available
                    if 'external_ip' in row:
                        entry['external_ip'] = row['external_ip']
                    if 'server_id' in row:
                        entry['server_id'] = row['server_id']
                    if 'idle_jitter_ms' in row:
                        entry['idle_jitter_ms'] = float(row.get('idle_jitter_ms', 0))
                    if 'packet_loss_percent' in row:
                        entry['packet_loss_percent'] = float(row.get('packet_loss_percent', 0))
                    if 'download_jitter_ms' in row:
                        entry['download_jitter_ms'] = float(row.get('download_jitter_ms', 0))
                    if 'upload_jitter_ms' in row:
                        entry['upload_jitter_ms'] = float(row.get('upload_jitter_ms', 0))
                    if 'download_bytes' in row:
                        entry['download_bytes'] = int(row.get('download_bytes', 0))
                    if 'upload_bytes' in row:
                        entry['upload_bytes'] = int(row.get('upload_bytes', 0))
                    if 'result_url' in row:
                        entry['result_url'] = row.get('result_url', '')

                    data.append(entry)

        except (FileNotFoundError, ValueError):
            pass

        self.send_json_response(data)

    def serve_ping_data(self):
        ping_csv = self.data_dir / "ping_tests.csv"
        data = []

        try:
            with open(ping_csv, 'r') as file:
                reader = csv.DictReader(file)
                for row in reader:
                    data.append({
                        'timestamp': row['timestamp'],
                        'target': row['target'],
                        'avg_latency_ms': float(row['avg_latency_ms']),
                        'min_latency_ms': float(row['min_latency_ms']),
                        'max_latency_ms': float(row['max_latency_ms']),
                        'packet_loss_percent': float(row['packet_loss_percent'])
                    })
        except (FileNotFoundError, ValueError):
            pass

        self.send_json_response(data)

    def serve_status(self):
        speed_csv = self.data_dir / "speed_tests.csv"
        ping_csv = self.data_dir / "ping_tests.csv"

        status = {
            'last_updated': datetime.now().isoformat(),
            'total_speed_tests': 0,
            'total_ping_tests': 0
        }

        try:
            with open(speed_csv, 'r') as file:
                status['total_speed_tests'] = max(0, len(file.readlines()) - 1)
        except FileNotFoundError:
            pass

        try:
            with open(ping_csv, 'r') as file:
                status['total_ping_tests'] = max(0, len(file.readlines()) - 1)
        except FileNotFoundError:
            pass

        self.send_json_response(status)

    def send_json_response(self, data):
        self.send_response(200)
        self.send_header('Content-type', 'application/json')
        self.send_header('Access-Control-Allow-Origin', '*')
        self.end_headers()
        self.wfile.write(json.dumps(data).encode())

def create_handler_class(data_dir):
    class CustomHandler(NetworkDashboardHandler):
        def __init__(self, *args, **kwargs):
            super().__init__(*args, data_dir=data_dir, **kwargs)
    return CustomHandler

def main():
    parser = argparse.ArgumentParser(description='Network Monitor Web Dashboard')
    parser.add_argument('--port', type=int, default=8080,
                       help='Port to run the web server on (default: 8080)')
    parser.add_argument('--host', default='localhost',
                       help='Host to bind to (default: localhost)')
    parser.add_argument('--data-dir', default='/var/lib/network-monitor',
                       help='Directory containing data files')

    args = parser.parse_args()

    handler_class = create_handler_class(args.data_dir)
    server = HTTPServer((args.host, args.port), handler_class)

    print(f"Starting Network Monitor Dashboard on http://{args.host}:{args.port}")
    print("Press Ctrl+C to stop the server")

    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\nShutting down the server...")
        server.shutdown()

if __name__ == '__main__':
    main()