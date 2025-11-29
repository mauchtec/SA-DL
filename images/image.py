from sadl import parse_file
import cv2
import numpy as np

def extract_license_photo(license_image_path, license_key):
    """Extract the photo from the license image"""
    
    # First, get the license data to know the image dimensions
    license_data = parse_file(license_image_path, encrypted=True, license=license_key)
    
    if not license_data:
        print("❌ Could not parse license data")
        return None
    
    width, height = license_data.image_width, license_data.image_height
    print(f"📐 License photo dimensions: {width}x{height} pixels")
    
    # Load the original license image
    img = cv2.imread(license_image_path)
    if img is None:
        print("❌ Could not load license image")
        return None
    
    original_height, original_width = img.shape[:2]
    print(f"📐 Original image size: {original_width}x{original_height}")
    
    # Common photo locations on South African licenses
    # Try different areas where the photo might be located
    
    photo_locations = [
        # Format: (x_start, y_start, width, height, description)
        (original_width - width - 50, 100, width, height, "Right side"),
        (50, 100, width, height, "Left side"), 
        (original_width // 2 - width // 2, 100, width, height, "Center top"),
        (original_width - 300, 150, width, height, "Right side adjusted"),
    ]
    
    for i, (x, y, w, h, description) in enumerate(photo_locations):
        # Ensure the area is within image bounds
        x = max(0, x)
        y = max(0, y)
        w = min(w, original_width - x)
        h = min(h, original_height - y)
        
        if w > 0 and h > 0:
            # Extract the photo area
            photo = img[y:y+h, x:x+w]
            filename = f"license_photo_{i+1}_{description.replace(' ', '_')}.jpg"
            cv2.imwrite(filename, photo)
            print(f"✅ Extracted: {filename} - {description}")
    
    # Also try manual selection
    print("\n🎯 Manual selection mode:")
    print("Click and drag to select the photo area, then press SPACE or ENTER")
    from_center = False
    roi = cv2.selectROI("Select Photo Area (Press SPACE/ENTER when done)", img, from_center)
    
    if roi[2] > 0 and roi[3] > 0:  # Valid selection
        x, y, w, h = roi
        manual_photo = img[y:y+h, x:x+w]
        cv2.imwrite("manual_selection_photo.jpg", manual_photo)
        print(f"✅ Manual selection saved: manual_selection_photo.jpg ({w}x{h})")
    
    cv2.destroyAllWindows()
    return True

def auto_detect_face_photo(license_image_path):
    """Try to automatically detect and extract face photo"""
    img = cv2.imread(license_image_path)
    if img is None:
        return None
    
    # Convert to grayscale for face detection
    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    
    # Load face detection classifier
    face_cascade = cv2.CascadeClassifier(cv2.data.haarcascades + 'haarcascade_frontalface_default.xml')
    
    # Detect faces
    faces = face_cascade.detectMultiScale(gray, scaleFactor=1.1, minNeighbors=5, minSize=(100, 100))
    
    print(f"🤖 Auto-detected {len(faces)} face(s) in the image")
    
    for i, (x, y, w, h) in enumerate(faces):
        # Expand the area a bit to include hair and shoulders
        padding = 30
        x = max(0, x - padding)
        y = max(0, y - padding)
        w = min(w + 2 * padding, img.shape[1] - x)
        h = min(h + 2 * padding, img.shape[0] - y)
        
        face_photo = img[y:y+h, x:x+w]
        filename = f"auto_detected_face_{i+1}.jpg"
        cv2.imwrite(filename, face_photo)
        print(f"✅ Auto-detected face: {filename} ({w}x{h})")
    
    return len(faces) > 0

# Your license key
license_key = "DLS2eyJoYW5kc2hha2VDb2RlIjoiMTA0NjIyMzU3LU1UQTBOakl5TXpVM0xWUnlhV0ZzVUhKdmFnIiwibWFpblNlcnZlclVSTCI6Imh0dHBzOi8vbWRscy5keW5hbXNvZnRvbmxpbmUuY29tIiwib3JnYW5pemF0aW9uSUQiOiIxMDQ2MjIzNTciLCJzdGFuZGJ5U2VydmVyVVJMIjoiaHR0cHM6Ly9zZGxzLmR5bmFtc29mdG9ubGluZS5jb20iLCJjaGVja0NvZGUiOjEzNzMwMDIxNDB9"

# Your license image file
license_image = "dl.png"  # Change this to your actual file name if different

print("🖼️ Extracting Photo from License Image")
print("=" * 50)

# Method 1: Extract based on known dimensions and common locations
extract_license_photo(license_image, license_key)

print("\n" + "=" * 50)

# Method 2: Try automatic face detection
print("🤖 Attempting automatic face detection...")
auto_detect_face_photo(license_image)

print("\n🎉 Check the generated JPG files for your license photo!")