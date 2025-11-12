#!/usr/bin/env python3
"""
Local development server for API endpoints
Only used for local development - Vercel uses serverless functions directly
"""

from http.server import HTTPServer, BaseHTTPRequestHandler
import sys
import os

# Add current directory to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# Import handlers
from process_product import handler as process_handler
from health import handler as health_handler
from login_tracking import handler as login_handler

class LocalAPIHandler(BaseHTTPRequestHandler):
    """Local development handler that routes to Vercel-style handlers"""
    
    def do_GET(self):
        """Handle GET requests"""
        if self.path == '/api/health':
            health_handler.do_GET(self)
        else:
            self.send_error(404, "Not Found")
    
    def do_POST(self):
        """Handle POST requests"""
        if self.path == '/api/process_product':
            process_handler.do_POST(self)
        elif self.path == '/api/login_tracking':
            login_handler.do_POST(self)
        else:
            self.send_error(404, "Not Found")
    
    def do_OPTIONS(self):
        """Handle CORS preflight"""
        self.send_response(200)
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Access-Control-Allow-Methods', 'GET, POST, OPTIONS')
        self.send_header('Access-Control-Allow-Headers', 'Content-Type')
        self.end_headers()
    
    def log_message(self, format, *args):
        """Suppress default logging"""
        pass

def main():
    """Start local development server"""
    port = int(os.getenv('API_PORT', 5001))
    server = HTTPServer(('localhost', port), LocalAPIHandler)
    
    print("=" * 60)
    print("🚀 Local API Server (Development Only)")
    print("=" * 60)
    print(f"📍 Running on: http://localhost:{port}")
    print("📝 Endpoints:")
    print("   GET  /api/health")
    print("   POST /api/process_product")
    print("   POST /api/login_tracking")
    print("=" * 60)
    print("💡 This server is only for local development.")
    print("   On Vercel, serverless functions handle these routes automatically.")
    print("=" * 60)
    
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\n🛑 Stopping server...")
        server.shutdown()
        print("✅ Server stopped")

if __name__ == '__main__':
    main()

