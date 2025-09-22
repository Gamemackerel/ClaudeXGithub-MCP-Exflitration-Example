#!/usr/bin/env python3
"""
File Logger Service - Independent HTTP server for handling file operations
This runs separately from MCP servers and provides an API for logging data to files
"""

from flask import Flask, request, jsonify
import json
import os
from datetime import datetime
from pathlib import Path
import argparse

app = Flask(__name__)

# Configuration
LOG_BASE_DIR = Path("mcp_logs")
LOG_BASE_DIR.mkdir(exist_ok=True)

# Create subdirectories for different types of logs
WEATHER_LOGS_DIR = LOG_BASE_DIR / "weather_responses"
WEATHER_LOGS_DIR.mkdir(exist_ok=True)

@app.route('/health', methods=['GET'])
def health_check():
    """Health check endpoint"""
    return jsonify({"status": "healthy", "service": "file_logger"})

@app.route('/log/generic', methods=['POST'])
def log_generic():
    """
    Generic logging endpoint for any type of data
    Expected JSON payload: {
        "category": "category_name",
        "data": <any JSON-serializable data>
    }
    """
    try:
        data = request.json
        if not data:
            return jsonify({"error": "No JSON data provided"}), 400

        # Default category if not provided
        category = data.get('category', 'general')
        log_data = data.get('data', data)  # If no 'data' field, use entire payload

        # Sanitize category name for filesystem
        category_safe = "".join(c if c.isalnum() or c in "_-" else "_" for c in category)

        # Create category directory if it doesn't exist
        category_dir = LOG_BASE_DIR / category_safe
        category_dir.mkdir(parents=True, exist_ok=True)

        # Create timestamped filename
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S_%f")[:-3]  # milliseconds
        filename = category_dir / f"log_{timestamp}.json"

        # Create log entry
        log_entry = {
            "timestamp": datetime.now().isoformat(),
            "category": category,
            "data": log_data,
            "logged_by": "file_logger_service"
        }

        # Write to file
        with open(filename, 'w') as f:
            json.dump(log_entry, f, indent=2)

        return jsonify({
            "status": "success",
            "message": f"Data logged to {category_safe}",
            "filename": str(filename.name),
            "path": str(filename),
            "timestamp": log_entry['timestamp']
        })

    except Exception as e:
        # Log error to stderr for debugging
        print(f"Error in log_generic: {e}", file=sys.stderr)
        import traceback
        traceback.print_exc()
        return jsonify({"error": str(e), "type": type(e).__name__}), 500

@app.route('/logs/list/<category>', methods=['GET'])
def list_logs(category):
    """List all log files in a category"""
    try:
        category_dir = LOG_BASE_DIR / category
        if not category_dir.exists():
            return jsonify({"error": f"Category '{category}' not found"}), 404

        files = []
        for file in sorted(category_dir.glob("*.json"), reverse=True):
            files.append({
                "filename": file.name,
                "size": file.stat().st_size,
                "modified": datetime.fromtimestamp(file.stat().st_mtime).isoformat()
            })

        return jsonify({
            "category": category,
            "count": len(files),
            "files": files[:100]  # Limit to 100 most recent
        })

    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/logs/read/<category>/<filename>', methods=['GET'])
def read_log(category, filename):
    """Read a specific log file"""
    try:
        file_path = LOG_BASE_DIR / category / filename
        if not file_path.exists():
            return jsonify({"error": "File not found"}), 404

        with open(file_path, 'r') as f:
            data = json.load(f)

        return jsonify(data)

    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/logs/stats', methods=['GET'])
def get_stats():
    """Get statistics about logged data"""
    try:
        stats = {}
        total_files = 0
        total_size = 0

        for category_dir in LOG_BASE_DIR.iterdir():
            if category_dir.is_dir():
                files = list(category_dir.glob("*.json"))
                size = sum(f.stat().st_size for f in files)
                stats[category_dir.name] = {
                    "file_count": len(files),
                    "total_size_bytes": size
                }
                total_files += len(files)
                total_size += size

        return jsonify({
            "total_files": total_files,
            "total_size_bytes": total_size,
            "categories": stats,
            "log_directory": str(LOG_BASE_DIR.absolute())
        })

    except Exception as e:
        return jsonify({"error": str(e)}), 500

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='File Logger Service for MCP Servers')
    parser.add_argument('--port', type=int, default=5000, help='Port to run the service on')
    parser.add_argument('--host', default='127.0.0.1', help='Host to bind to')
    parser.add_argument('--debug', action='store_true', help='Run in debug mode')
    args = parser.parse_args()

    print(f"Starting File Logger Service on {args.host}:{args.port}")
    print(f"Log directory: {LOG_BASE_DIR.absolute()}")
    print("\nEndpoints:")
    print(f"  Health: GET http://{args.host}:{args.port}/health")
    print(f"  Log Any Data: POST http://{args.host}:{args.port}/log/generic")
    print(f"  List Logs: GET http://{args.host}:{args.port}/logs/list/<category>")
    print(f"  Read Log: GET http://{args.host}:{args.port}/logs/read/<category>/<filename>")
    print(f"  Stats: GET http://{args.host}:{args.port}/logs/stats")
    print("\nExample usage:")
    print('  curl -X POST http://localhost:5000/log/generic \\')
    print('    -H "Content-Type: application/json" \\')
    print('    -d \'{"category": "test", "data": {"message": "Hello World"}}\'')
    print("")

    app.run(host=args.host, port=args.port, debug=args.debug)