from http.server import BaseHTTPRequestHandler
import json
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

class handler(BaseHTTPRequestHandler):
    def do_POST(self):
        if self.path == '/api/login_tracking':
            self.handle_login_tracking()
        else:
            self.send_error(404, "Not Found")
    
    def handle_login_tracking(self):
        try:
            # Parse JSON data
            content_length = int(self.headers['Content-Length'])
            post_data = self.rfile.read(content_length)
            data = json.loads(post_data.decode('utf-8'))
            
            # Extract login information
            user_id = data.get('user_id', 'unknown')
            user_name = data.get('user_name', 'Unknown User')
            ip_address = data.get('ip_address', 'Unknown')
            user_agent = data.get('user_agent', 'Unknown')
            
            print(f"Login tracking: {user_name} ({user_id}) from {ip_address}")
            
            # Send notification (simplified for Vercel)
            print(f"📱 Login notification: {user_name} ({user_id}) logged in")
            
            response_data = {
                "status": "success",
                "message": "Login tracked successfully",
                "user_id": user_id,
                "user_name": user_name
            }
            
            self.send_response(200)
            self.send_header('Content-Type', 'application/json')
            self.send_header('Access-Control-Allow-Origin', '*')
            self.end_headers()
            
            self.wfile.write(json.dumps(response_data).encode('utf-8'))
            
        except Exception as e:
            print(f"Error tracking login: {e}")
            
            self.send_response(500)
            self.send_header('Content-Type', 'application/json')
            self.send_header('Access-Control-Allow-Origin', '*')
            self.end_headers()
            
            error_response = {
                "error": f"Failed to track login: {str(e)}",
                "status": "failed"
            }
            
            self.wfile.write(json.dumps(error_response).encode('utf-8'))
    
    def do_OPTIONS(self):
        # Handle CORS preflight
        self.send_response(200)
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Access-Control-Allow-Methods', 'POST, OPTIONS')
        self.send_header('Access-Control-Allow-Headers', 'Content-Type')
        self.end_headers()