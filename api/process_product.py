from http.server import BaseHTTPRequestHandler
import json
import os
import base64
from PIL import Image, ImageFilter, ImageEnhance
import piexif
import io
import zipfile
import google.generativeai as genai
from dotenv import load_dotenv
import traceback
import random
import datetime
import time
import urllib.parse

# Load environment variables
load_dotenv()

# Configure Gemini API
GEMINI_API_KEY = os.getenv('GEMINI_API_KEY')
if GEMINI_API_KEY:
    genai.configure(api_key=GEMINI_API_KEY)
    model = genai.GenerativeModel('gemini-2.0-flash')
else:
    model = None

# Session data for consistent processing
session_data = {}

def reset_session():
    """Reset session data for new batch"""
    global session_data
    session_data = {}

def get_session_data(gps_location="usa"):
    """Get or create session data for consistent processing"""
    if not session_data:
        # Random iPhone selection per batch
        iphone_models = [
            {"name": "iPhone 14 Pro Max", "megapixels": 48.0, "base_resolution": (4032, 3024)},
            {"name": "iPhone 16 Pro Max", "megapixels": 48.0, "base_resolution": (5712, 4284)}
        ]
        session_data['iphone'] = random.choice(iphone_models)
        
        # GPS locations
        gps_locations = {
            "usa": (37.7749, -122.4194, "United States"),
            "germany": (52.5200, 13.4050, "Germany"),
            "canada": (43.6532, -79.3832, "Canada"),
            "australia": (-33.8688, 151.2093, "Australia"),
            "france": (48.8566, 2.3522, "France")
        }
        
        lat, lon, country = gps_locations.get(gps_location.lower(), gps_locations["usa"])
        session_data['base_lat'] = lat + random.uniform(-0.01, 0.01)
        session_data['base_lon'] = lon + random.uniform(-0.01, 0.01)
        session_data['country'] = country
        
    return session_data

def convert_to_jpg(image_bytes, preserve_original_size=True):
    """Convert any image format to JPG while preserving original dimensions and aesthetics."""
    img = Image.open(io.BytesIO(image_bytes)).convert("RGB")
    
    # Preserve original image dimensions and aspect ratio
    original_size = img.size
    print(f"Original image size: {original_size[0]}x{original_size[1]}")
    
    # Only convert format, don't resize or modify aesthetics
    img_processed = img
    
    # Very subtle enhancements that don't change appearance
    img_processed = img_processed.filter(ImageFilter.UnsharpMask(radius=0.1, percent=10, threshold=3))
    enhancer = ImageEnhance.Contrast(img_processed)
    img_processed = enhancer.enhance(1.01)  # Barely noticeable
    
    # Save as JPEG with high quality
    output = io.BytesIO()
    img_processed.save(output, format='JPEG', quality=95, optimize=True)
    return output.getvalue()

def generate_apple_filename(team_member_token, index):
    """Generate Apple-style filename"""
    timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
    return f"IMG_{timestamp}_{index:04d}.jpg"

def add_exif_data(img, team_member_token, session):
    """Add realistic iPhone EXIF data to image"""
    try:
        # Random iPhone model selection (per batch consistency)
        iphone_models = [
            ("iPhone 14 Pro Max", "Apple", 48.0),
            ("iPhone 16 Pro Max", "Apple", 48.0)
        ]
        model_name, make, megapixels = random.choice(iphone_models)
        
        # Use session GPS data for consistency
        lat, lon = session['base_lat'], session['base_lon']
        
        # EXIF structure
        exif_dict = {
            "0th": {
                piexif.ImageIFD.Make: make,
                piexif.ImageIFD.Model: model_name,
                piexif.ImageIFD.Software: "iOS 18.0",
                piexif.ImageIFD.DateTime: datetime.datetime.now().strftime("%Y:%m:%d %H:%M:%S"),
                piexif.ImageIFD.Orientation: 1,  # Normal orientation (no rotation)
            },
            "Exif": {
                piexif.ExifIFD.DateTimeOriginal: datetime.datetime.now().strftime("%Y:%m:%d %H:%M:%S"),
                piexif.ExifIFD.FocalLength: (26, 1),
                piexif.ExifIFD.ISOSpeedRatings: random.randint(50, 400),
                piexif.ExifIFD.ExposureTime: (1, random.randint(100, 2000)),
                piexif.ExifIFD.PixelXDimension: img.size[0],
                piexif.ExifIFD.PixelYDimension: img.size[1],
            },
            "GPS": {
                piexif.GPSIFD.GPSLatitude: _decimal_to_dms(abs(lat)),
                piexif.GPSIFD.GPSLatitudeRef: 'N' if lat >= 0 else 'S',
                piexif.GPSIFD.GPSLongitude: _decimal_to_dms(abs(lon)),
                piexif.GPSIFD.GPSLongitudeRef: 'E' if lon >= 0 else 'W',
            }
        }
        
        # Save with EXIF
        exif_bytes = piexif.dump(exif_dict)
        output = io.BytesIO()
        img.save(output, format='JPEG', exif=exif_bytes, quality=95)
        return output.getvalue()
        
    except Exception as e:
        print(f"Error adding EXIF data: {e}")
        # Return image without EXIF if there's an error
        output = io.BytesIO()
        img.save(output, format='JPEG', quality=95)
        return output.getvalue()

def _decimal_to_dms(decimal):
    """Convert decimal coordinates to DMS format"""
    degrees = int(decimal)
    minutes = int((decimal - degrees) * 60)
    seconds = int(((decimal - degrees) * 60 - minutes) * 60 * 100)
    return [(degrees, 1), (minutes, 1), (seconds, 100)]

def call_gemini_api(text):
    """Call Google Gemini API to rewrite the product description."""
    try:
        if not model:
            return text  # Return original text if no model available
        
        prompt = f"""SYSTEM / CONFIG:
You are a smart product description writer for Happydeel — a store that buys, inspects, and resells top-quality used and new gear at honest prices. You receive unfiltered text copied from marketplaces (like eBay, Etsy, etc.) that may include titles, conditions, prices, seller names, and unrelated UI or policy text.

Your job:
1. Extract only what matters:
   - Product title
   - Condition (new, used, like new, etc.)
   - Key attributes (size, color, specs, model, capacity, etc.)
   - Price if present
   - Shipping info (only if it's mentioned in the input)
2. Ignore completely:
   - Seller names, usernames, or store names
   - Mentions of eBay, Etsy, or platform-specific text
   - UI words like "See all definitions," "opens in new tab," etc.
   - Any HTML, emojis, or formatting symbols
3. Create comprehensive product descriptions with the following structure:
   - SEO-optimized title (60-80 characters max)
   - Short description (500 characters max)
   - Extended description (1000 characters max)
   - Smart tags (6-8 keywords, comma-separated)
   - Hashtags (6-8 keywords with # prefix)
   - Calculated price (40% off original if price present)
4. Writing logic:
   - Tone: confident, chill, lightly emotional — as if a person is casually explaining why they're selling it
   - Style: realistic, not robotic; never use generic AI words like "unleash", "groundbreaking", "crafted", "unravel", "premium quality", "innovative", or "cutting-edge"
   - Mention we sell it at a lower price because of something personal or practical (e.g., "we upgraded", "switched brands", "needed cash", etc.)
   - If shipping mentioned, rewrite to: "Ships same day with FedEx"
   - Create light urgency with limited availability
   - Mention testing and verification when appropriate
5. Output format (use exact separators):
——————————————————————————————————————————————————————
   TITLE : 

   [SEO-optimized title with vital keywords]
   
—————————————————————————————————————————————————————— 

SLUG :

[URL-friendly slug based on title]

   
—————————————————————————————————————————————————————— 
   SHORT DESCRIPTION : 

   [500 character max description]
   
——————————————————————————————————————————————————————
   EXTENDED DESCRIPTION :

   [1000 character max detailed description]
   
——————————————————————————————————————————————————————
   TAGS : 

   [6-8 keywords, comma-separated]
   
——————————————————————————————————————————————————————
   HASHTAGS :

   [6-8 hashtags with # prefix]
   
——————————————————————————————————————————————————————

   PRICE :

   [Calculated price: 40% off original if price present, or "Price on request" if no price]
   
——————————————————————————————————————————————————————

USER INPUT (text to process):
{text}"""

        # Generate content with proper configuration
        response = model.generate_content(
            prompt,
            generation_config=genai.types.GenerationConfig(
                temperature=0.7,
                max_output_tokens=1000,
                top_p=0.8,
                top_k=40
            )
        )
        
        if response.text:
            return response.text.strip()
        else:
            print("Warning: Empty response from Gemini API")
            return text
    except Exception as e:
        print(f"Error calling Gemini API: {e}")
        return text  # Return original text if API fails

def send_notification(notification_type, data):
    """Send notification to Telegram (simplified for Vercel)"""
    try:
        # This is a simplified version - in production you'd implement proper async calls
        print(f"📱 Notification: {notification_type} - {data}")
    except Exception as e:
        print(f"⚠️ Notification failed: {e}")

class handler(BaseHTTPRequestHandler):
    def do_POST(self):
        if self.path == '/api/process_product':
            self.handle_process_product()
        else:
            self.send_error(404, "Not Found")
    
    def handle_process_product(self):
        try:
            # Parse form data
            content_length = int(self.headers['Content-Length'])
            post_data = self.rfile.read(content_length)
            
            # Parse multipart form data
            boundary = self.headers['Content-Type'].split('boundary=')[1]
            parts = post_data.split(f'--{boundary}'.encode())
            
            form_data = {}
            images = []
            
            for part in parts:
                if b'Content-Disposition: form-data' in part:
                    if b'name="text"' in part:
                        # Extract text
                        text_start = part.find(b'\r\n\r\n') + 4
                        text_end = part.rfind(b'\r\n')
                        form_data['text'] = part[text_start:text_end].decode('utf-8')
                    elif b'name="team_member_token"' in part:
                        # Extract team member token
                        token_start = part.find(b'\r\n\r\n') + 4
                        token_end = part.rfind(b'\r\n')
                        form_data['team_member_token'] = part[token_start:token_end].decode('utf-8')
                    elif b'name="gps_location"' in part:
                        # Extract GPS location
                        gps_start = part.find(b'\r\n\r\n') + 4
                        gps_end = part.rfind(b'\r\n')
                        form_data['gps_location'] = part[gps_start:gps_end].decode('utf-8')
                    elif b'name="images"' in part and b'filename=' in part:
                        # Extract image
                        filename_start = part.find(b'filename="') + 10
                        filename_end = part.find(b'"', filename_start)
                        filename = part[filename_start:filename_end].decode('utf-8')
                        
                        image_start = part.find(b'\r\n\r\n') + 4
                        image_end = part.rfind(b'\r\n')
                        image_data = part[image_start:image_end]
                        
                        images.append({
                            'filename': filename,
                            'data': image_data
                        })
            
            # Validate required fields
            if 'text' not in form_data or 'team_member_token' not in form_data or not images:
                self.send_error(400, "Missing required fields")
                return
            
            text = form_data['text']
            team_member_token = form_data['team_member_token']
            gps_location = form_data.get('gps_location', 'usa')
            
            print(f"Processing product for {team_member_token}: {len(images)} images, text length: {len(text)}, GPS location: {gps_location}")
            
            # Send notifications
            send_notification('product_submit', {
                'user_id': team_member_token,
                'user_name': team_member_token,
                'product_count': len(images),
                'description_length': len(text),
                'gps_location': gps_location
            })
            
            send_notification('process_click', {
                'user_id': team_member_token,
                'user_name': team_member_token,
                'product_count': len(images),
                'description_length': len(text)
            })
            
            # Reset session for new batch
            reset_session()
            session = get_session_data(gps_location)
            print(f"New session started with {session['iphone']['name']} at GPS: {session['base_lat']:.4f}, {session['base_lon']:.4f} in {session['country'].upper()}")
            
            # Call Gemini API
            print("Calling Gemini API to rewrite text...")
            rewritten_text = call_gemini_api(text)
            print(f"Gemini API response length: {len(rewritten_text)} characters")
            
            # Process images
            processed_images = []
            for i, image_data in enumerate(images):
                print(f"Processing image {i+1}/{len(images)}...")
                
                # Convert to JPG
                jpg_data = convert_to_jpg(image_data['data'])
                
                # Create PIL Image for EXIF data
                img = Image.open(io.BytesIO(jpg_data))
                
                # Add EXIF data
                img_with_exif = add_exif_data(img, team_member_token, session)
                
                # Generate filename
                filename = generate_apple_filename(team_member_token, i+1)
                
                processed_images.append({
                    'filename': filename,
                    'data': img_with_exif
                })
                
                print(f"Image {i+1} processed: {filename}")
            
            # Create zip file
            print("Creating zip file...")
            zip_buffer = io.BytesIO()
            
            with zipfile.ZipFile(zip_buffer, 'w', zipfile.ZIP_DEFLATED) as zip_file:
                # Add processed images
                for img_data in processed_images:
                    zip_file.writestr(img_data['filename'], img_data['data'])
                
                # Add rewritten description
                zip_file.writestr("description.txt", rewritten_text.encode('utf-8'))
                
                # Add original text for reference
                zip_file.writestr("original_text.txt", text.encode('utf-8'))
            
            zip_buffer.seek(0)
            zip_data = zip_buffer.getvalue()
            
            # Convert to base64 for JSON response
            zip_base64 = base64.b64encode(zip_data).decode('utf-8')
            
            # Prepare response
            response_data = {
                "message": "Product processed successfully",
                "images_processed": len(images),
                "zip_file": zip_base64,
                "filename": f"{team_member_token}_product.zip"
            }
            
            print(f"Processing complete for {team_member_token}: {len(images)} images processed, zip size: {len(zip_data)} bytes")
            
            # Send completion notification
            send_notification('processing_complete', {
                'user_id': team_member_token,
                'user_name': team_member_token,
                'processing_time': 0,  # Simplified for Vercel
                'success': True
            })
            
            # Send response
            self.send_response(200)
            self.send_header('Content-Type', 'application/json')
            self.send_header('Access-Control-Allow-Origin', '*')
            self.send_header('Access-Control-Allow-Methods', 'POST, OPTIONS')
            self.send_header('Access-Control-Allow-Headers', 'Content-Type')
            self.end_headers()
            
            response_json = json.dumps(response_data)
            self.wfile.write(response_json.encode('utf-8'))
            
        except Exception as e:
            print(f"Error processing product: {e}")
            traceback.print_exc()
            
            # Send error notification
            send_notification('processing_complete', {
                'user_id': form_data.get('team_member_token', 'unknown'),
                'user_name': form_data.get('team_member_token', 'unknown'),
                'processing_time': 0,
                'success': False,
                'error_message': str(e)
            })
            
            # Send error response
            self.send_response(500)
            self.send_header('Content-Type', 'application/json')
            self.send_header('Access-Control-Allow-Origin', '*')
            self.end_headers()
            
            error_response = {
                "error": f"Failed to process product: {str(e)}",
                "error_type": type(e).__name__
            }
            
            self.wfile.write(json.dumps(error_response).encode('utf-8'))
    
    def do_OPTIONS(self):
        # Handle CORS preflight
        self.send_response(200)
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Access-Control-Allow-Methods', 'POST, OPTIONS')
        self.send_header('Access-Control-Allow-Headers', 'Content-Type')
        self.end_headers()