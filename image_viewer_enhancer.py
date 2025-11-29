# Create: image_viewer_enhancer.py

from PIL import Image, ImageFilter, ImageEnhance
import os

def display_image_info(filename):
    """Display information about decoded images"""
    if os.path.exists(filename):
        img = Image.open(filename)
        print(f"📊 {filename}:")
        print(f"   Size: {img.size}")
        print(f"   Mode: {img.mode}")
        print(f"   Format: {img.format}")
        
        # Get image statistics
        img_array = img.getdata()
        min_val = min(img_array)
        max_val = max(img_array)
        avg_val = sum(img_array) / len(img_array)
        
        print(f"   Pixel range: {min_val} - {max_val}")
        print(f"   Average value: {avg_val:.1f}")
        
        return img
    else:
        print(f"❌ {filename} not found")
        return None

def enhance_decoded_images():
    """Enhance and improve the decoded images"""
    print("\n🎨 ENHANCING DECODED IMAGES")
    print("=" * 50)
    
    enhanced_files = []
    
    # Check which files exist and enhance them
    base_files = ["license_photo_differential.png", "license_photo_histogram.png"]
    
    for filename in base_files:
        if os.path.exists(filename):
            print(f"\n🔄 Enhancing {filename}...")
            img = Image.open(filename)
            
            # Apply various enhancements
            enhancements = [
                ("contrast", ImageEnhance.Contrast(img).enhance(2.0)),
                ("brightness", ImageEnhance.Brightness(img).enhance(1.2)),
                ("sharpness", ImageEnhance.Sharpness(img).enhance(2.0)),
                ("inverted", Image.eval(img, lambda x: 255 - x)),
            ]
            
            for name, enhanced_img in enhancements:
                enhanced_filename = f"enhanced_{name}_{filename}"
                enhanced_img.save(enhanced_filename)
                enhanced_files.append(enhanced_filename)
                print(f"   💾 {enhanced_filename}")
            
            # Also try edge detection to see structure
            edges = img.filter(ImageFilter.FIND_EDGES)
            edges_filename = f"enhanced_edges_{filename}"
            edges.save(edges_filename)
            enhanced_files.append(edges_filename)
            print(f"   💾 {edges_filename}")
    
    return enhanced_files

def analyze_decoding_quality():
    """Analyze how good our decoding was"""
    print("\n🔍 ANALYZING DECODING QUALITY")
    print("=" * 50)
    
    # Check file sizes to see if we got reasonable images
    for filename in ["license_photo_differential.png", "license_photo_histogram.png"]:
        if os.path.exists(filename):
            file_size = os.path.getsize(filename)
            print(f"📁 {filename}: {file_size} bytes")
            
            # A proper 250x200 grayscale PNG should be > 10KB
            if file_size < 10000:
                print("   ⚠️  File size suggests incomplete or poor decoding")
            else:
                print("   ✅ File size looks reasonable")

def create_comparison_grid():
    """Create a comparison grid of all decoded images"""
    print("\n🖼️ CREATING COMPARISON GRID")
    print("=" * 50)
    
    image_files = []
    
    # Find all PNG files in current directory
    for file in os.listdir('.'):
        if file.endswith('.png') and ('license_photo' in file or 'enhanced' in file):
            image_files.append(file)
    
    if not image_files:
        print("❌ No decoded images found")
        return
    
    print(f"Found {len(image_files)} images for comparison")
    
    # Open all images
    images = []
    for filename in image_files:
        try:
            img = Image.open(filename)
            # Resize to same size for comparison
            img = img.resize((250, 200))
            images.append((filename, img))
        except Exception as e:
            print(f"❌ Could not open {filename}: {e}")
    
    if len(images) < 2:
        print("❌ Need at least 2 images for comparison")
        return
    
    # Create comparison grid
    cols = min(3, len(images))
    rows = (len(images) + cols - 1) // cols
    
    grid_width = 250 * cols
    grid_height = 200 * rows
    
    grid = Image.new('L', (grid_width, grid_height), color=255)  # White background
    
    for idx, (filename, img) in enumerate(images):
        row = idx // cols
        col = idx % cols
        x = col * 250
        y = row * 200
        
        grid.paste(img, (x, y))
    
    grid.save("decoding_comparison.png")
    print("💾 Comparison grid saved: decoding_comparison.png")

def improve_differential_decoding(raw_data, width=250, height=200):
    """Improve the differential decoding that worked"""
    print("\n🔄 IMPROVING DIFFERENTIAL DECODING")
    print("=" * 50)
    
    # The differential method worked best, let's refine it
    output = bytearray(width * height)
    
    # Start with different backgrounds to see what works best
    backgrounds = [255, 0, 128]  # White, black, gray
    
    for bg_val in backgrounds:
        print(f"  Trying background: {bg_val} ({'white' if bg_val == 255 else 'black' if bg_val == 0 else 'gray'})")
        
        # Initialize with background
        for i in range(len(output)):
            output[i] = bg_val
        
        ptr = 0
        pixel_pos = 0
        
        # Improved decoding logic
        while ptr < len(raw_data) and pixel_pos < len(output):
            current_byte = raw_data[ptr]
            
            # Try different interpretations
            if current_byte < 0x20:  # Control codes
                # Skip or special handling
                ptr += 1
                continue
            elif current_byte < 0x80:  # Likely data
                output[pixel_pos] = current_byte
                pixel_pos += 1
                ptr += 1
            else:  # Potential command
                if ptr + 1 < len(raw_data):
                    next_byte = raw_data[ptr + 1]
                    # Interpret as [command, data]
                    output[pixel_pos] = next_byte
                    pixel_pos += 1
                    ptr += 2
                else:
                    ptr += 1
        
        # Save this version
        filename = f"improved_bg_{bg_val}.png"
        save_grayscale_image(bytes(output), width, height, filename)
        print(f"    💾 {filename}")

def save_grayscale_image(data, width, height, filename):
    """Save grayscale image with proper size"""
    from PIL import Image
    # Ensure correct size
    if len(data) < width * height:
        data = data + b'\xFF' * (width * height - len(data))
    elif len(data) > width * height:
        data = data[:width * height]
    
    img = Image.frombytes('L', (width, height), bytes(data))
    img.save(filename)

# Main analysis function
def comprehensive_image_review(license_data):
    """Comprehensive review of all decoded images"""
    if not license_data or not license_data.image_bytes:
        return
    
    raw_data = license_data.image_bytes
    width = license_data.image_width
    height = license_data.image_height
    
    print("🎯 COMPREHENSIVE IMAGE REVIEW")
    print("=" * 60)
    
    # 1. Display info about decoded images
    print("\n1. 📊 DECODED IMAGE ANALYSIS")
    for filename in ["license_photo_differential.png", "license_photo_histogram.png"]:
        display_image_info(filename)
    
    # 2. Analyze decoding quality
    analyze_decoding_quality()
    
    # 3. Enhance images
    enhanced_files = enhance_decoded_images()
    
    # 4. Improve the working decoding method
    improve_differential_decoding(raw_data, width, height)
    
    # 5. Create comparison
    create_comparison_grid()
    
    print(f"\n🎉 REVIEW COMPLETE!")
    print("Check all the generated PNG files to see which decoding looks best!")
    print("The 'enhanced_' files may reveal more details.")