from http.server import BaseHTTPRequestHandler
import json
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

class handler(BaseHTTPRequestHandler):
    def do_GET(self):
        if self.path == '/api/health':
            self.handle_health()
        else:
            self.send_error(404, "Not Found")
    
    def handle_health(self):
        try:
            GEMINI_API_KEY = os.getenv('GEMINI_API_KEY')
            
            response_data = {
                "status": "healthy",
                "gemini_configured": bool(GEMINI_API_KEY),
                "environment": "production" if os.getenv('VERCEL') else "development"
            }
            
            self.send_response(200)
            self.send_header('Content-Type', 'application/json')
            self.send_header('Access-Control-Allow-Origin', '*')
            self.end_headers()
            
            self.wfile.write(json.dumps(response_data).encode('utf-8'))
            
        except Exception as e:
            self.send_response(500)
            self.send_header('Content-Type', 'application/json')
            self.send_header('Access-Control-Allow-Origin', '*')
            self.end_headers()
            
            error_response = {
                "error": f"Health check failed: {str(e)}",
                "status": "unhealthy"
            }
            
            self.wfile.write(json.dumps(error_response).encode('utf-8'))
    
    def do_OPTIONS(self):
        # Handle CORS preflight
        self.send_response(200)
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Access-Control-Allow-Methods', 'GET, OPTIONS')
        self.send_header('Access-Control-Allow-Headers', 'Content-Type')
        self.end_headers()