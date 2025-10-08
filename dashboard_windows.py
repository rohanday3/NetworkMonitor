#!/usr/bin/env python3
"""
Network Monitor Dashboard - Windows Version
Simple Web Dashboard for Network Monitor on Windows
"""

import json
import csv
from datetime import datetime, timedelta
from pathlib import Path
from http.server import HTTPServer, BaseHTTPRequestHandler
import urllib.parse
import argparse
import os
import webbrowser
import threading

class NetworkDashboardHandler(BaseHTTPRequestHandler):
    def __init__(self, *args, data_dir=None, **kwargs):
        if data_dir is None:
            data_dir = Path.home() / "AppData" / "Local" / "NetworkMonitor" / "data"
        self.data_dir = Path(data_dir)
        super().__init__(*args, **kwargs)

    def log_message(self, format, *args):
        """Override to reduce console spam"""
        pass

    def do_GET(self):
        if self.path == '/' or self.path == '/index.html':
            self.serve_dashboard()
        elif self.path == '/api/speed':
            self.serve_speed_data()
        elif self.path == '/api/ping':
            self.serve_ping_data()
        elif self.path == '/api/status':
            self.serve_status()
        elif self.path == '/favicon.ico':
            self.send_error(404)
        else:
            self.send_error(404)

    def serve_dashboard(self):
        html = """
<!DOCTYPE html>
<html>
<head>
    <title>Network Monitor Dashboard - Windows</title>
    <meta charset="utf-8">
    <meta name="viewport" content="width=device-width, initial-scale=1">
    <style>
        body {
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
            margin: 0;
            padding: 20px;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            min-height: 100vh;
            color: #333;
        }
        .container {
            max-width: 1200px;
            margin: 0 auto;
            background: rgba(255,255,255,0.95);
            border-radius: 15px;
            padding: 30px;
            box-shadow: 0 10px 30px rgba(0,0,0,0.2);
        }
        .header {
            text-align: center;
            margin-bottom: 30px;
            padding-bottom: 20px;
            border-bottom: 2px solid #e0e0e0;
        }
        .header h1 {
            color: #2c3e50;
            margin: 0;
            font-size: 2.5em;
            font-weight: 300;
        }
        .header .subtitle {
            color: #7f8c8d;
            font-size: 1.1em;
            margin-top: 10px;
        }
        .card {
            background: white;
            padding: 25px;
            margin: 20px 0;
            border-radius: 10px;
            box-shadow: 0 5px 15px rgba(0,0,0,0.1);
            border-left: 4px solid #3498db;
        }
        .card h2 {
            margin-top: 0;
            color: #2c3e50;
            font-size: 1.4em;
        }
        .metric {
            display: inline-block;
            margin: 15px 30px 15px 0;
            text-align: center;
            padding: 20px;
            background: #f8f9fa;
            border-radius: 8px;
            min-width: 120px;
        }
        .metric-value {
            font-size: 2.5em;
            font-weight: bold;
            line-height: 1;
        }
        .metric-label {
            color: #666;
            font-size: 0.9em;
            margin-top: 5px;
            text-transform: uppercase;
            letter-spacing: 1px;
        }
        .download { color: #3498db; }
        .upload { color: #e67e22; }
        .ping { color: #27ae60; }

        table {
            width: 100%;
            border-collapse: collapse;
            margin-top: 15px;
        }
        th, td {
            padding: 12px 8px;
            text-align: left;
            border-bottom: 1px solid #ecf0f1;
        }
        th {
            background: linear-gradient(135deg, #f8f9fa 0%, #e9ecef 100%);
            font-weight: 600;
            color: #2c3e50;
            text-transform: uppercase;
            font-size: 0.85em;
            letter-spacing: 0.5px;
        }
        tr:hover {
            background-color: #f8f9fa;
        }

        .refresh-btn {
            background: linear-gradient(135deg, #3498db 0%, #2980b9 100%);
            color: white;
            padding: 12px 25px;
            border: none;
            border-radius: 25px;
            cursor: pointer;
            font-size: 1em;
            transition: transform 0.2s, box-shadow 0.2s;
            margin: 10px 10px 10px 0;
        }
        .refresh-btn:hover {
            transform: translateY(-2px);
            box-shadow: 0 5px 15px rgba(52, 152, 219, 0.4);
        }

        .status-info {
            background: #e8f5e8;
            border: 1px solid #c3e6c3;
            padding: 15px;
            border-radius: 8px;
            margin: 15px 0;
        }

        .loading {
            text-align: center;
            color: #7f8c8d;
            font-style: italic;
            padding: 20px;
        }

        .error {
            color: #e74c3c;
            background: #fdf2f2;
            border: 1px solid #f5c6cb;
            padding: 15px;
            border-radius: 8px;
            margin: 10px 0;
        }

        .server-info {
            background: #f8f9fa;
            padding: 15px;
            border-radius: 8px;
            margin: 15px 0;
            border-left: 4px solid #17a2b8;
        }

        .timestamp {
            color: #6c757d;
            font-size: 0.9em;
        }

        @media (max-width: 768px) {
            .container { padding: 15px; }
            .metric { margin: 10px 10px 10px 0; }
            .metric-value { font-size: 2em; }
            table { font-size: 0.9em; }
        }
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>🌐 Network Monitor</h1>
            <div class="subtitle">Real-time Internet Speed & Latency Monitoring for Windows</div>
        </div>

        <div class="card">
            <h2>📊 System Status</h2>
            <div id="status" class="loading">Loading system status...</div>
            <button class="refresh-btn" onclick="refreshData()">🔄 Refresh Data</button>
            <button class="refresh-btn" onclick="openDataFolder()" style="background: linear-gradient(135deg, #27ae60 0%, #229954 100%);">📁 Open Data Folder</button>
        </div>

        <div class="card">
            <h2>⚡ Latest Speed Test</h2>
            <div id="latest-speed" class="loading">Loading latest speed test...</div>
        </div>

        <div class="card">
            <h2>📈 Recent Speed Tests</h2>
            <div id="speed-history" class="loading">Loading speed test history...</div>
        </div>

        <div class="card">
            <h2>📡 Latest Ping Results</h2>
            <div id="ping-results" class="loading">Loading ping results...</div>
        </div>
    </div>

    <script>
        function formatDate(dateString) {
            const date = new Date(dateString);
            return date.toLocaleString('en-US', {
                month: '2-digit',
                day: '2-digit',
                year: 'numeric',
                hour: '2-digit',
                minute: '2-digit',
                second: '2-digit',
                hour12: false
            });
        }

        function openDataFolder() {
            const userProfile = '%USERPROFILE%';
            const dataPath = userProfile + '\\\\AppData\\\\Local\\\\NetworkMonitor\\\\data';
            // This won't work directly from browser, but we can show the path
            alert('Data folder location:\\n' + dataPath.replace('%USERPROFILE%', 'C:\\\\Users\\\\[YourUsername]'));
        }

        function loadStatus() {
            fetch('/api/status')
                .then(response => response.json())
                .then(data => {
                    document.getElementById('status').innerHTML = `
                        <div class="status-info">
                            <p><strong>Last updated:</strong> ${formatDate(data.last_updated)}</p>
                            <p><strong>Total speed tests:</strong> ${data.total_speed_tests}</p>
                            <p><strong>Total ping tests:</strong> ${data.total_ping_tests}</p>
                            <p><strong>Data location:</strong> %USERPROFILE%\\\\AppData\\\\Local\\\\NetworkMonitor\\\\data</p>
                        </div>
                    `;
                })
                .catch(error => {
                    document.getElementById('status').innerHTML = '<div class="error">⚠️ Error loading system status</div>';
                });
        }

        function loadSpeedData() {
            fetch('/api/speed')
                .then(response => response.json())
                .then(data => {
                    if (data.length === 0) {
                        document.getElementById('latest-speed').innerHTML = '<div class="error">No speed test data available. Run a test first!</div>';
                        document.getElementById('speed-history').innerHTML = '<div class="error">No speed test data available</div>';
                        return;
                    }

                    // Latest test
                    const latest = data[data.length - 1];
                    document.getElementById('latest-speed').innerHTML = `
                        <div style="display: flex; flex-wrap: wrap; align-items: center;">
                            <div class="metric download">
                                <div class="metric-value">${latest.download_mbps}</div>
                                <div class="metric-label">Mbps Down</div>
                            </div>
                            <div class="metric upload">
                                <div class="metric-value">${latest.upload_mbps}</div>
                                <div class="metric-label">Mbps Up</div>
                            </div>
                            <div class="metric ping">
                                <div class="metric-value">${latest.ping_ms}</div>
                                <div class="metric-label">ms Ping</div>
                            </div>
                        </div>
                        <div class="server-info">
                            <p><strong>🖥️ Server:</strong> ${latest.server_name}</p>
                            <p><strong>📍 Location:</strong> ${latest.server_location}</p>
                            <p><strong>🌐 ISP:</strong> ${latest.isp}</p>
                            <p><strong>🔗 External IP:</strong> ${latest.external_ip}</p>
                            <p class="timestamp"><strong>⏰ Test Time:</strong> ${formatDate(latest.timestamp)}</p>
                        </div>
                    `;

                    // Recent history
                    const recent = data.slice(-10).reverse();
                    let tableHtml = `
                        <table>
                            <tr>
                                <th>⏰ Time</th>
                                <th>⬇️ Download</th>
                                <th>⬆️ Upload</th>
                                <th>📡 Ping</th>
                                <th>🖥️ Server</th>
                            </tr>
                    `;

                    recent.forEach(test => {
                        tableHtml += `
                            <tr>
                                <td class="timestamp">${formatDate(test.timestamp)}</td>
                                <td class="download"><strong>${test.download_mbps} Mbps</strong></td>
                                <td class="upload"><strong>${test.upload_mbps} Mbps</strong></td>
                                <td class="ping"><strong>${test.ping_ms} ms</strong></td>
                                <td>${test.server_name}</td>
                            </tr>
                        `;
                    });

                    tableHtml += '</table>';
                    document.getElementById('speed-history').innerHTML = tableHtml;
                })
                .catch(error => {
                    document.getElementById('latest-speed').innerHTML = '<div class="error">⚠️ Error loading speed data</div>';
                    document.getElementById('speed-history').innerHTML = '<div class="error">⚠️ Error loading speed data</div>';
                });
        }

        function loadPingData() {
            fetch('/api/ping')
                .then(response => response.json())
                .then(data => {
                    if (data.length === 0) {
                        document.getElementById('ping-results').innerHTML = '<div class="error">No ping data available</div>';
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
                                <th>🎯 Target</th>
                                <th>📊 Avg Latency</th>
                                <th>⬇️ Min</th>
                                <th>⬆️ Max</th>
                                <th>📉 Packet Loss</th>
                                <th>⏰ Time</th>
                            </tr>
                    `;

                    Object.values(byTarget).forEach(ping => {
                        const lossClass = ping.packet_loss_percent > 0 ? 'style="color: #e74c3c;"' : '';
                        tableHtml += `
                            <tr>
                                <td><strong>${ping.target}</strong></td>
                                <td class="ping"><strong>${ping.avg_latency_ms} ms</strong></td>
                                <td>${ping.min_latency_ms} ms</td>
                                <td>${ping.max_latency_ms} ms</td>
                                <td ${lossClass}><strong>${ping.packet_loss_percent}%</strong></td>
                                <td class="timestamp">${formatDate(ping.timestamp)}</td>
                            </tr>
                        `;
                    });

                    tableHtml += '</table>';
                    document.getElementById('ping-results').innerHTML = tableHtml;
                })
                .catch(error => {
                    document.getElementById('ping-results').innerHTML = '<div class="error">⚠️ Error loading ping data</div>';
                });
        }

        function refreshData() {
            document.getElementById('status').innerHTML = '<div class="loading">Refreshing...</div>';
            document.getElementById('latest-speed').innerHTML = '<div class="loading">Refreshing...</div>';
            document.getElementById('speed-history').innerHTML = '<div class="loading">Refreshing...</div>';
            document.getElementById('ping-results').innerHTML = '<div class="loading">Refreshing...</div>';

            loadStatus();
            loadSpeedData();
            loadPingData();
        }

        // Load data on page load
        window.onload = refreshData;

        // Auto-refresh every 2 minutes
        setInterval(refreshData, 120000);
    </script>
</body>
</html>
        """

        self.send_response(200)
        self.send_header('Content-type', 'text/html; charset=utf-8')
        self.end_headers()
        self.wfile.write(html.encode('utf-8'))

    def serve_speed_data(self):
        speed_csv = self.data_dir / "speed_tests.csv"
        data = []

        try:
            with open(speed_csv, 'r', encoding='utf-8') as file:
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
                        'isp': row['isp'],
                        'external_ip': row['external_ip']
                    }

                    # Add enhanced metrics if available
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

        except (FileNotFoundError, ValueError, UnicodeDecodeError):
            pass

        self.send_json_response(data)

    def serve_ping_data(self):
        ping_csv = self.data_dir / "ping_tests.csv"
        data = []

        try:
            with open(ping_csv, 'r', encoding='utf-8') as file:
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
        except (FileNotFoundError, ValueError, UnicodeDecodeError):
            pass

        self.send_json_response(data)

    def serve_status(self):
        speed_csv = self.data_dir / "speed_tests.csv"
        ping_csv = self.data_dir / "ping_tests.csv"

        status = {
            'last_updated': datetime.now().isoformat(),
            'total_speed_tests': 0,
            'total_ping_tests': 0,
            'data_directory': str(self.data_dir)
        }

        try:
            with open(speed_csv, 'r', encoding='utf-8') as file:
                status['total_speed_tests'] = max(0, len(file.readlines()) - 1)
        except (FileNotFoundError, UnicodeDecodeError):
            pass

        try:
            with open(ping_csv, 'r', encoding='utf-8') as file:
                status['total_ping_tests'] = max(0, len(file.readlines()) - 1)
        except (FileNotFoundError, UnicodeDecodeError):
            pass

        self.send_json_response(status)

    def send_json_response(self, data):
        self.send_response(200)
        self.send_header('Content-type', 'application/json; charset=utf-8')
        self.send_header('Access-Control-Allow-Origin', '*')
        self.end_headers()
        self.wfile.write(json.dumps(data, ensure_ascii=False).encode('utf-8'))

def create_handler_class(data_dir):
    class CustomHandler(NetworkDashboardHandler):
        def __init__(self, *args, **kwargs):
            super().__init__(*args, data_dir=data_dir, **kwargs)
    return CustomHandler

def main():
    parser = argparse.ArgumentParser(description='Network Monitor Web Dashboard - Windows')
    parser.add_argument('--port', type=int, default=8080,
                       help='Port to run the web server on (default: 8080)')
    parser.add_argument('--host', default='localhost',
                       help='Host to bind to (default: localhost)')
    parser.add_argument('--data-dir',
                       help='Directory containing data files (default: %USERPROFILE%\\AppData\\Local\\NetworkMonitor\\data)')
    parser.add_argument('--no-browser', action='store_true',
                       help='Don\'t automatically open browser')

    args = parser.parse_args()

    # Use default Windows data directory if not specified
    if args.data_dir is None:
        args.data_dir = Path.home() / "AppData" / "Local" / "NetworkMonitor" / "data"

    handler_class = create_handler_class(args.data_dir)
    server = HTTPServer((args.host, args.port), handler_class)

    url = f"http://{args.host}:{args.port}"
    print(f"🌐 Network Monitor Dashboard starting...")
    print(f"📍 Server: {url}")
    print(f"📁 Data directory: {args.data_dir}")
    print(f"🛑 Press Ctrl+C to stop")

    # Auto-open browser
    if not args.no_browser:
        def open_browser():
            import time
            time.sleep(1)  # Give server time to start
            try:
                webbrowser.open(url)
                print(f"🌍 Browser opened: {url}")
            except Exception:
                print(f"⚠️  Could not open browser automatically. Please open: {url}")

        threading.Thread(target=open_browser, daemon=True).start()

    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\n🛑 Shutting down dashboard...")
        server.shutdown()
        print("✅ Dashboard stopped")

if __name__ == '__main__':
    main()