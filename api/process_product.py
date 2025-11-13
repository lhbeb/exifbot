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
import math

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

def generate_device_serial():
    """Generate realistic Apple device serial number"""
    # Format: F2LXXXXXXXXX (12 characters, alphanumeric)
    chars = '0123456789ABCDEFGHJKLMNPQRSTUVWXYZ'  # Exclude I, O for clarity
    return 'F2L' + ''.join(random.choice(chars) for _ in range(9))

def generate_lens_serial():
    """Generate realistic lens serial number"""
    return f"L{random.randint(100000, 999999)}"

def get_session_data(gps_location="usa"):
    """Get or create session data for consistent processing"""
    if not session_data:
        # Random iPhone selection per batch with iOS version mapping
        # Based on real iPhone EXIF data analysis
        iphone_models = [
            {
                "name": "iPhone 14",
                "megapixels": 12.2,
                "base_resolution": (4032, 3024),
                "ios_version": random.choice(["16.5", "16.6", "16.7", "17.0", "17.1"]),
                "lens_model": "iPhone 14 back dual wide camera 5.7mm f/1.5",
                "lens_id": "iPhone 14 back dual wide camera 5.7mm f/1.5",
                "lens_info": "1.539999962-5.699999809mm f/1.5-2.4",
                "focal_length": (57, 10),  # 5.7mm in tenths
                "focal_length_35mm": 26,
                "aperture": (15, 10),  # f/1.5
                "fov": 69.4
            },
            {
                "name": "iPhone 14 Pro Max",
                "megapixels": 48.0,
                "base_resolution": (4032, 3024),
                "ios_version": random.choice(["17.6.1", "17.7", "18.0", "18.0.1", "18.1"]),
                "lens_model": "iPhone 14 Pro Max back triple camera 6.86mm f/1.78",
                "lens_id": "iPhone 14 Pro Max back triple camera 6.86mm f/1.78",
                "lens_info": "1.539999962-6.859999657mm f/1.78-2.8",
                "focal_length": (686, 100),  # 6.86mm in hundredths
                "focal_length_35mm": 24,
                "aperture": (178, 100),  # f/1.78
                "fov": 77.0
            },
            {
                "name": "iPhone 16 Pro Max",
                "megapixels": 48.0,
                "base_resolution": (5712, 4284),
                "ios_version": random.choice(["18.0", "18.0.1", "18.1", "18.2"]),
                "lens_model": "iPhone 16 Pro Max back triple camera 6.86mm f/1.78",
                "lens_id": "iPhone 16 Pro Max back triple camera 6.86mm f/1.78",
                "lens_info": "1.539999962-6.859999657mm f/1.78-2.8",
                "focal_length": (686, 100),
                "focal_length_35mm": 24,
                "aperture": (178, 100),
                "fov": 77.0
            }
        ]
        selected_iphone = random.choice(iphone_models)
        session_data['iphone'] = selected_iphone
        
        # Generate unique device identifiers for this session
        session_data['device_serial'] = generate_device_serial()
        session_data['lens_serial'] = generate_lens_serial()
        
        # GPS locations with more realistic variation
        gps_locations = {
            "usa": [
                (37.7749, -122.4194, "San Francisco, United States"),
                (40.7128, -74.0060, "New York, United States"),
                (34.0522, -118.2437, "Los Angeles, United States"),
                (41.8781, -87.6298, "Chicago, United States"),
            ],
            "germany": [
                (52.5200, 13.4050, "Berlin, Germany"),
                (48.1351, 11.5820, "Munich, Germany"),
                (53.5511, 9.9937, "Hamburg, Germany"),
            ],
            "canada": [
                (43.6532, -79.3832, "Toronto, Canada"),
                (45.5017, -73.5673, "Montreal, Canada"),
                (49.2827, -123.1207, "Vancouver, Canada"),
            ],
            "australia": [
                (-33.8688, 151.2093, "Sydney, Australia"),
                (-37.8136, 144.9631, "Melbourne, Australia"),
                (-27.4698, 153.0251, "Brisbane, Australia"),
            ],
            "france": [
                (48.8566, 2.3522, "Paris, France"),
                (45.7640, 4.8357, "Lyon, France"),
                (43.2965, 5.3698, "Marseille, France"),
            ]
        }
        
        # Select random city from location
        city_options = gps_locations.get(gps_location.lower(), gps_locations["usa"])
        base_lat, base_lon, city_name = random.choice(city_options)
        
        # Add realistic variation (walking distance ~100-500m)
        session_data['base_lat'] = base_lat + random.uniform(-0.005, 0.005)
        session_data['base_lon'] = base_lon + random.uniform(-0.005, 0.005)
        session_data['country'] = city_name
        
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
    
    # Save as JPEG with high quality (optimize=False to prevent over-compression)
    # Quality 95 ensures good file size while maintaining quality
    output = io.BytesIO()
    img_processed.save(output, format='JPEG', quality=95, optimize=False, subsampling='4:4:4')
    output.seek(0)
    jpg_data = output.getvalue()
    print(f"Converted to JPG: {len(jpg_data)} bytes ({len(jpg_data)/1024:.1f} KB)")
    return jpg_data

def generate_apple_filename(team_member_token, index):
    """Generate Apple-style filename"""
    timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
    return f"IMG_{timestamp}_{index:04d}.jpg"

def calculate_realistic_camera_settings(img, aperture_value):
    """Calculate realistic ISO, exposure, and brightness based on image characteristics"""
    # Analyze image brightness to determine realistic settings
    img_gray = img.convert('L')
    avg_brightness = sum(img_gray.getdata()) / (img.size[0] * img.size[1])
    
    # Brightness ranges from 0-255
    if avg_brightness < 50:  # Dark scene
        iso = random.randint(400, 1600)
        exposure_denominator = random.randint(30, 200)
    elif avg_brightness < 100:  # Low light
        iso = random.randint(200, 800)
        exposure_denominator = random.randint(50, 400)
    elif avg_brightness < 150:  # Normal light
        iso = random.randint(50, 400)
        exposure_denominator = random.randint(100, 1000)
    else:  # Bright scene
        iso = random.randint(25, 200)
        exposure_denominator = random.randint(500, 2000)
    
    # Calculate BrightnessValue (APEX system)
    # BrightnessValue = log2((FNumber^2) / (ExposureTime * ISO))
    f_number = aperture_value
    exposure_time = 1.0 / exposure_denominator if exposure_denominator > 0 else 1.0
    
    if exposure_time > 0 and iso > 0:
        # APEX formula: BV = log2((F^2) / (T * S))
        # Where F = f-number, T = exposure time, S = ISO
        brightness_apex = math.log2((f_number ** 2) / (exposure_time * iso))
        # Convert to rational number format (numerator, denominator)
        brightness_rational = (int(brightness_apex * 1000), 1000)
    else:
        brightness_rational = (0, 1)
    
    # Calculate ShutterSpeedValue (APEX)
    # ShutterSpeedValue = -log2(T) where T is exposure time in seconds
    if exposure_time > 0:
        shutter_speed_value = -math.log2(exposure_time)
        shutter_speed_rational = (int(shutter_speed_value * 1000), 1000)
    else:
        shutter_speed_rational = (0, 1)
    
    return iso, exposure_denominator, brightness_rational, shutter_speed_rational

def generate_thumbnail(img, max_size=(160, 160)):
    """Generate thumbnail for EXIF"""
    try:
        # Create thumbnail maintaining aspect ratio
        img.thumbnail(max_size, Image.Resampling.LANCZOS)
        thumb_output = io.BytesIO()
        img.save(thumb_output, format='JPEG', quality=85)
        return thumb_output.getvalue()
    except:
        return None

def add_safe_exif_field(exif_dict, ifd, tag, value):
    """Safely add EXIF field, skipping if tag doesn't exist"""
    try:
        if hasattr(piexif, ifd) and hasattr(getattr(piexif, ifd), tag):
            tag_id = getattr(getattr(piexif, ifd), tag)
            exif_dict[ifd][tag_id] = value
    except (AttributeError, KeyError):
        pass  # Field not supported, skip it

def add_exif_data(img, team_member_token, session):
    """
    Add comprehensive, realistic iPhone EXIF data that passes fraud detection.
    
    This function creates EXIF metadata that closely matches real iPhone images:
    - Realistic timestamp variations (not perfectly identical)
    - Correlated ISO/exposure based on image brightness
    - Complete camera metadata (aperture, flash, metering, etc.)
    - Device-specific information (iOS version, lens model)
    - GPS coordinates with realistic variation
    - Thumbnail generation
    
    Note: Apple MakerNotes (proprietary binary format) are not fully supported
    by piexif library. Real iPhones include extensive MakerNotes with processing
    parameters, HDR info, etc. This is a limitation of the library, not the implementation.
    """
    try:
        # Use session iPhone model for consistency
        iphone_info = session['iphone']
        model_name = iphone_info['name']
        make = "Apple"
        ios_version = iphone_info['ios_version']
        lens_model = iphone_info['lens_model']
        focal_length_tuple = iphone_info['focal_length']
        aperture_tuple = iphone_info['aperture']
        
        # Use session GPS data for consistency
        lat, lon = session['base_lat'], session['base_lon']
        device_serial = session['device_serial']
        lens_serial = session['lens_serial']
        
        # Get timestamps with realistic variations (not perfectly identical)
        now = datetime.datetime.now()
        base_datetime = now
        
        # DateTime (file modification) - can be slightly after capture
        datetime_file = base_datetime + datetime.timedelta(milliseconds=random.randint(0, 500))
        datetime_str_file = datetime_file.strftime("%Y:%m:%d %H:%M:%S")
        
        # DateTimeOriginal (capture time) - base time
        datetime_str_original = base_datetime.strftime("%Y:%m:%d %H:%M:%S")
        
        # DateTimeDigitized (digitization) - can be same or slightly after original
        datetime_digitized = base_datetime + datetime.timedelta(milliseconds=random.randint(0, 200))
        datetime_str_digitized = datetime_digitized.strftime("%Y:%m:%d %H:%M:%S")
        
        # Calculate aperture value from f-number (matches FNumber exactly in real iPhone)
        f_number = aperture_tuple[0] / aperture_tuple[1]
        aperture_value = aperture_tuple  # ApertureValue should match FNumber in real iPhone
        
        # Calculate realistic camera settings based on image
        iso, exposure_denominator, brightness_rational, shutter_speed_rational = calculate_realistic_camera_settings(img, f_number)
        exposure_numerator = 1
        
        # Get timezone offset (realistic timezone based on GPS location)
        # Calculate timezone offset based on longitude (simplified)
        # Real iPhones use actual timezone, but we'll use a reasonable approximation
        timezone_hours = int(lon / 15)  # Rough timezone calculation
        timezone_offset_str = f"{timezone_hours:+03d}:00"
        
        # Add OffsetTime fields (timezone offsets) - use raw tag IDs
        # These are EXIF tags 0x9010, 0x9011, 0x9012
        offset_time_original = timezone_offset_str.encode('utf-8')
        offset_time_digitized = timezone_offset_str.encode('utf-8')
        offset_time = timezone_offset_str.encode('utf-8')
        
        # SubSecTime should match across all fields (real iPhone behavior)
        subsec_time = str(random.randint(0, 999)).zfill(3)
        
        # Standard iPhone resolution (72 DPI is most common)
        resolution = 72
        resolution_unit = 2  # 2 = inches
        
        # Generate thumbnail
        thumbnail_data = generate_thumbnail(img.copy())
        
        # Get additional iPhone info
        lens_id = iphone_info.get('lens_id', lens_model)
        lens_info = iphone_info.get('lens_info', '')
        focal_length_35mm = iphone_info.get('focal_length_35mm', 26)
        fov = iphone_info.get('fov', 69.4)
        
        # Build comprehensive EXIF structure matching real iPhone data
        exif_dict = {
            "0th": {
                piexif.ImageIFD.Make: make.encode('utf-8'),
                piexif.ImageIFD.Model: model_name.encode('utf-8'),
                piexif.ImageIFD.Software: ios_version.encode('utf-8'),  # Just version number, no "iOS" prefix
                piexif.ImageIFD.DateTime: datetime_str_file,
                piexif.ImageIFD.Orientation: 1,  # Normal orientation (can be 6 for rotated, but 1 is common)
                piexif.ImageIFD.XResolution: (resolution, 1),
                piexif.ImageIFD.YResolution: (resolution, 1),
                piexif.ImageIFD.ResolutionUnit: resolution_unit,
                piexif.ImageIFD.Artist: "Apple".encode('utf-8'),
            },
            "Exif": {
                # ExifVersion (0232 in real iPhone)
                piexif.ExifIFD.ExifVersion: b"0232",
                
                # Date/Time fields with variations
                piexif.ExifIFD.DateTimeOriginal: datetime_str_original,
                piexif.ExifIFD.DateTimeDigitized: datetime_str_digitized,
                
                # SubSecTime fields - should match across all (real iPhone behavior)
                piexif.ExifIFD.SubSecTime: subsec_time.encode('utf-8'),
                piexif.ExifIFD.SubSecTimeOriginal: subsec_time.encode('utf-8'),
                piexif.ExifIFD.SubSecTimeDigitized: subsec_time.encode('utf-8'),
                
                # OffsetTime fields (timezone offsets) - added via raw tags below
                
                # Camera settings
                piexif.ExifIFD.FocalLength: focal_length_tuple,
                piexif.ExifIFD.FocalLengthIn35mmFilm: focal_length_35mm,
                piexif.ExifIFD.FNumber: aperture_tuple,
                piexif.ExifIFD.ApertureValue: aperture_value,  # Matches FNumber in real iPhone
                piexif.ExifIFD.ISOSpeedRatings: iso,
                piexif.ExifIFD.ExposureTime: (exposure_numerator, exposure_denominator),
                piexif.ExifIFD.ShutterSpeedValue: shutter_speed_rational,  # APEX value
                piexif.ExifIFD.ExposureBiasValue: (0, 1),  # No exposure compensation
                piexif.ExifIFD.ExposureMode: 0,  # 0 = Auto exposure
                piexif.ExifIFD.ExposureProgram: 2,  # 2 = Program AE (matches real iPhone)
                piexif.ExifIFD.MeteringMode: 5,  # 5 = Multi-segment (matches real iPhone)
                
                # BrightnessValue (calculated from exposure settings)
                piexif.ExifIFD.BrightnessValue: brightness_rational,
                
                # Image characteristics
                piexif.ExifIFD.PixelXDimension: img.size[0],
                piexif.ExifIFD.PixelYDimension: img.size[1],
                piexif.ExifIFD.ColorSpace: 65535,  # Uncalibrated (CRITICAL: matches real iPhone, not sRGB!)
                piexif.ExifIFD.WhiteBalance: 0,  # 0 = Auto
                piexif.ExifIFD.SceneCaptureType: 0,  # 0 = Standard
                piexif.ExifIFD.SceneType: 1,  # 1 = Directly photographed
                piexif.ExifIFD.CustomRendered: 0,  # 0 = Normal process
                piexif.ExifIFD.DigitalZoomRatio: (1, 1),  # No digital zoom
                
                # Flash information
                piexif.ExifIFD.Flash: 16,  # 16 = Flash did not fire, auto mode
                piexif.ExifIFD.FlashPixVersion: b"0100",  # FlashPix Version 1.0
                
                # Light source
                piexif.ExifIFD.LightSource: 0,  # 0 = Unknown (auto)
                
                # SensingMethod
                piexif.ExifIFD.SensingMethod: 2,  # 2 = One-chip color area sensor
            },
            "GPS": {
                piexif.GPSIFD.GPSVersionID: (2, 2, 0, 0),
                piexif.GPSIFD.GPSLatitude: _decimal_to_dms(abs(lat)),
                piexif.GPSIFD.GPSLatitudeRef: 'N' if lat >= 0 else 'S',
                piexif.GPSIFD.GPSLongitude: _decimal_to_dms(abs(lon)),
                piexif.GPSIFD.GPSLongitudeRef: 'E' if lon >= 0 else 'W',
                piexif.GPSIFD.GPSDateStamp: base_datetime.strftime("%Y:%m:%d"),
                piexif.GPSIFD.GPSTimeStamp: (
                    (base_datetime.hour, 1),
                    (base_datetime.minute, 1),
                    (base_datetime.second, 1)
                ),
                piexif.GPSIFD.GPSAltitudeRef: 0,  # 0 = Above sea level
                piexif.GPSIFD.GPSAltitude: (random.randint(0, 500), 1),  # Random altitude 0-500m
                piexif.GPSIFD.GPSMapDatum: "WGS-84".encode('utf-8'),
            },
            "1st": {}  # Thumbnail IFD
        }
        
        # Add unofficial but commonly used tags AFTER initial dump attempt
        # These will be added to a copy if the first dump succeeds
        unofficial_tags = {}
        try:
            unofficial_tags[0xA432] = lens_model.encode('utf-8')  # LensModel
            unofficial_tags[0xA433] = make.encode('utf-8')  # LensMake
            if lens_info:
                unofficial_tags[0xA434] = lens_info.encode('utf-8')  # LensInfo
            unofficial_tags[0xA435] = lens_id.encode('utf-8')  # LensID (unofficial)
            unofficial_tags[0x013C] = model_name.encode('utf-8')  # HostComputer
            
            # OffsetTime fields (timezone offsets) - EXIF tags 0x9010, 0x9011, 0x9012
            unofficial_tags[0x9010] = offset_time_original  # OffsetTimeOriginal
            unofficial_tags[0x9011] = offset_time_digitized  # OffsetTimeDigitized
            unofficial_tags[0x9012] = offset_time  # OffsetTime
        except Exception as e:
            print(f"Warning: Failed to prepare unofficial tags: {e}")
            unofficial_tags = {}
        
        # Add thumbnail if generated
        if thumbnail_data:
            try:
                exif_dict["1st"] = {
                    piexif.ImageIFD.JPEGInterchangeFormat: 0,  # Offset will be set by piexif
                    piexif.ImageIFD.JPEGInterchangeFormatLength: len(thumbnail_data),
                }
            except:
                pass  # Thumbnail addition is optional
        
        # Convert EXIF dict to bytes with proper error handling
        # First try without unofficial tags (they might cause issues)
        exif_bytes = None
        exif_dict_clean = {
            "0th": exif_dict["0th"],
            "Exif": {k: v for k, v in exif_dict["Exif"].items() if k not in unofficial_tags},
            "GPS": exif_dict["GPS"],
            "1st": exif_dict.get("1st", {})
        }
        
        try:
            exif_bytes = piexif.dump(exif_dict_clean)
            print(f"EXIF dump successful (clean): {len(exif_bytes)} bytes")
            
            # If successful, try adding unofficial tags
            if unofficial_tags:
                try:
                    exif_dict_with_unofficial = exif_dict_clean.copy()
                    exif_dict_with_unofficial["Exif"] = exif_dict_with_unofficial["Exif"].copy()
                    exif_dict_with_unofficial["Exif"].update(unofficial_tags)
                    exif_bytes = piexif.dump(exif_dict_with_unofficial)
                    print(f"EXIF dump successful (with unofficial tags): {len(exif_bytes)} bytes")
                except Exception as e_unofficial:
                    print(f"Warning: Could not add unofficial tags, using clean EXIF: {e_unofficial}")
                    # Continue with clean EXIF
        except Exception as e:
            print(f"ERROR: piexif.dump() failed: {e}")
            print(f"EXIF dict keys: 0th={list(exif_dict.get('0th', {}).keys())}, Exif={list(exif_dict.get('Exif', {}).keys())[:10]}...")
            traceback.print_exc()
            
            # Try again with a minimal set (remove problematic fields)
            try:
                minimal_exif = {
                    "0th": {
                        piexif.ImageIFD.Make: make.encode('utf-8'),
                        piexif.ImageIFD.Model: model_name.encode('utf-8'),
                        piexif.ImageIFD.Software: ios_version.encode('utf-8'),
                        piexif.ImageIFD.DateTime: datetime_str_file,
                        piexif.ImageIFD.XResolution: (resolution, 1),
                        piexif.ImageIFD.YResolution: (resolution, 1),
                        piexif.ImageIFD.ResolutionUnit: resolution_unit,
                    },
                    "Exif": {
                        piexif.ExifIFD.ExifVersion: b"0232",
                        piexif.ExifIFD.DateTimeOriginal: datetime_str_original,
                        piexif.ExifIFD.DateTimeDigitized: datetime_str_digitized,
                        piexif.ExifIFD.FocalLength: focal_length_tuple,
                        piexif.ExifIFD.FocalLengthIn35mmFilm: focal_length_35mm,
                        piexif.ExifIFD.FNumber: aperture_tuple,
                        piexif.ExifIFD.ApertureValue: aperture_value,
                        piexif.ExifIFD.ISOSpeedRatings: iso,
                        piexif.ExifIFD.ExposureTime: (exposure_numerator, exposure_denominator),
                        piexif.ExifIFD.PixelXDimension: img.size[0],
                        piexif.ExifIFD.PixelYDimension: img.size[1],
                        piexif.ExifIFD.ColorSpace: 65535,
                    },
                    "GPS": exif_dict["GPS"],
                    "1st": {}
                }
                exif_bytes = piexif.dump(minimal_exif)
                print(f"Minimal EXIF dump successful: {len(exif_bytes)} bytes")
            except Exception as e2:
                print(f"ERROR: Minimal EXIF dump also failed: {e2}")
                traceback.print_exc()
                # Last resort: basic EXIF only
                try:
                    basic_exif = {
                        "0th": {
                            piexif.ImageIFD.Make: make.encode('utf-8'),
                            piexif.ImageIFD.Model: model_name.encode('utf-8'),
                        },
                        "Exif": {
                            piexif.ExifIFD.DateTimeOriginal: datetime_str_original,
                        },
                    }
                    exif_bytes = piexif.dump(basic_exif)
                    print(f"Basic EXIF dump successful: {len(exif_bytes)} bytes")
                except Exception as e3:
                    print(f"ERROR: Even basic EXIF failed: {e3}")
                    exif_bytes = None
        
        # Save image with EXIF data
        # Ensure image is in RGB mode (required for JPEG with EXIF)
        if img.mode != 'RGB':
            img = img.convert('RGB')
        
        output = io.BytesIO()
        if exif_bytes:
            try:
                # Method 1: Use exif parameter (PIL/Pillow standard)
                img.save(output, format='JPEG', exif=exif_bytes, quality=95, optimize=False)
                output.seek(0)
                test_data = output.getvalue()
                
                # Verify EXIF was actually embedded
                test_img = Image.open(io.BytesIO(test_data))
                has_exif = False
                if hasattr(test_img, '_getexif') and test_img._getexif():
                    has_exif = True
                elif 'exif' in test_img.info:
                    has_exif = True
                elif hasattr(test_img, 'getexif'):
                    try:
                        exif_data = test_img.getexif()
                        if exif_data:
                            has_exif = True
                    except:
                        pass
                
                if has_exif:
                    print(f"✓ Image saved with EXIF data (verified)")
                else:
                    print(f"⚠ WARNING: EXIF parameter used but verification failed, trying alternative method")
                    # Method 2: Use piexif.insert() to inject EXIF into JPEG bytes
                    output = io.BytesIO()
                    img.save(output, format='JPEG', quality=95, optimize=False)
                    jpeg_bytes = output.getvalue()
                    try:
                        image_data = piexif.insert(exif_bytes, jpeg_bytes)
                        print(f"✓ EXIF inserted using piexif.insert()")
                        output = io.BytesIO(image_data)
                    except Exception as e2:
                        print(f"ERROR: piexif.insert() also failed: {e2}")
                        # Fall back to image without EXIF
                        output = io.BytesIO(jpeg_bytes)
                        print(f"Image saved WITHOUT EXIF (all methods failed)")
            except Exception as e:
                print(f"ERROR: Failed to save image with EXIF: {e}")
                traceback.print_exc()
                # Try alternative: save first, then inject EXIF
                try:
                    output_temp = io.BytesIO()
                    img.save(output_temp, format='JPEG', quality=95, optimize=False)
                    jpeg_bytes = output_temp.getvalue()
                    image_data = piexif.insert(exif_bytes, jpeg_bytes)
                    output = io.BytesIO(image_data)
                    print(f"✓ EXIF inserted using piexif.insert() (fallback method)")
                except Exception as e2:
                    print(f"ERROR: piexif.insert() fallback also failed: {e2}")
                    # Final fallback: image without EXIF
                    output = io.BytesIO()
                    img.save(output, format='JPEG', quality=95, optimize=False)
                    print(f"Image saved WITHOUT EXIF (all methods failed)")
        else:
            # No EXIF data available
            print(f"WARNING: No EXIF data to embed, saving image without EXIF")
            img.save(output, format='JPEG', quality=95, optimize=False)
        
        output.seek(0)
        image_data = output.getvalue()
        
        # Verify EXIF was embedded by trying to read it back
        try:
            verify_img = Image.open(io.BytesIO(image_data))
            if hasattr(verify_img, '_getexif') and verify_img._getexif():
                print(f"✓ EXIF verified: Image contains EXIF data")
            elif 'exif' in verify_img.info:
                print(f"✓ EXIF verified: Image contains EXIF in info")
            else:
                print(f"✗ WARNING: EXIF verification failed - no EXIF found in saved image")
        except Exception as e:
            print(f"EXIF verification error: {e}")
        
        print(f"EXIF processing complete: {model_name} (iOS {ios_version}), GPS: {lat:.4f}, {lon:.4f}, ISO: {iso}, Exposure: 1/{exposure_denominator}, Size: {len(image_data)} bytes")
        
        return image_data
        
    except Exception as e:
        print(f"CRITICAL ERROR in add_exif_data: {e}")
        traceback.print_exc()
        # Return image without EXIF if there's a critical error
        # But log it clearly so we know what went wrong
        output = io.BytesIO()
        img.save(output, format='JPEG', quality=95, optimize=False)
        print(f"Returned image WITHOUT EXIF due to error")
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