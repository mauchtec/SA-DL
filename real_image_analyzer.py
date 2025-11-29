# Create: fixed_image_analyzer.py
from PIL import Image
import struct

def analyze_actual_image_data(raw_data, width=250, height=200):
    """Actually figure out what the 611 bytes represent"""
    print("🔍 REAL IMAGE DATA ANALYSIS")
    print("=" * 60)
    
    print(f"Data size: {len(raw_data)} bytes")
    print(f"Expected for {width}x{height} grayscale: {width * height} bytes")
    print(f"Compression ratio: {len(raw_data) / (width * height):.4%}")
    print()
    
    # This compression ratio is impossibly high for normal images
    # Let's check what the data actually contains
    
    # 1. Check if it's a sparse image (mostly one color)
    from collections import Counter
    byte_counts = Counter(raw_data)
    most_common = byte_counts.most_common(10)
    
    print("Most common bytes:")
    for byte_val, count in most_common:
        percentage = (count / len(raw_data)) * 100
        print(f"  {byte_val:3d} (0x{byte_val:02x}): {count:4d} times ({percentage:5.1f}%)")
    
    # 2. Check for patterns that might indicate data type
    print(f"\nPattern analysis:")
    
    # Check for coordinate patterns (pairs of bytes that could be x,y coordinates)
    coord_pairs = 0
    for i in range(0, len(raw_data)-1, 2):
        if raw_data[i] < width and raw_data[i+1] < height:
            coord_pairs += 1
    
    print(f"  Potential coordinate pairs: {coord_pairs}")
    
    # Check if bytes are mostly in printable ASCII range (might be text)
    printable = sum(1 for b in raw_data if 32 <= b <= 126)
    print(f"  Printable ASCII characters: {printable} ({printable/len(raw_data)*100:.1f}%)")
    
    # Check for sequential patterns
    sequences = 0
    for i in range(len(raw_data) - 2):
        if abs(raw_data[i] - raw_data[i+1]) <= 2 and abs(raw_data[i+1] - raw_data[i+2]) <= 2:
            sequences += 1
    print(f"  Sequential patterns: {sequences}")
    
    return most_common

def decode_as_line_image(raw_data, width=250, height=200):
    """Decode as a single line image (611x1) and display as a row"""
    print("🎯 Decoding as single line image (611x1)...")
    
    # Create output image with the line at the top
    output = bytearray(width * height)
    
    # Fill with white background
    for i in range(len(output)):
        output[i] = 255
    
    # Copy the line data to the top row
    line_length = min(len(raw_data), width)
    for x in range(line_length):
        output[x] = raw_data[x]
    
    filename = "single_line_image.png"
    save_grayscale_image(bytes(output), width, height, filename)
    print(f"  💾 {filename}")
    return filename

def decode_as_coordinate_map(raw_data, width=250, height=200):
    """Try to interpret as coordinate-value pairs"""
    print("🎯 Attempting coordinate-value pair decoding...")
    
    # Create blank canvas
    output = bytearray(width * height)
    for i in range(len(output)):
        output[i] = 255  # White background
    
    points_plotted = 0
    
    # Try different interpretations of the data
    # Option 1: [x, y, value] triplets
    if len(raw_data) % 3 == 0:
        print("  Trying [x, y, value] triplets...")
        for i in range(0, len(raw_data)-2, 3):
            x = raw_data[i] % width
            y = raw_data[i+1] % height
            value = raw_data[i+2]
            
            pos = y * width + x
            if pos < len(output):
                output[pos] = value
                points_plotted += 1
    
    # Option 2: [x, y] pairs (assume constant value)
    elif len(raw_data) % 2 == 0:
        print("  Trying [x, y] pairs...")
        for i in range(0, len(raw_data)-1, 2):
            x = raw_data[i] % width
            y = raw_data[i+1] % height
            
            pos = y * width + x
            if pos < len(output):
                output[pos] = 0  # Black dots
                points_plotted += 1
    
    if points_plotted > 0:
        filename = f"coordinate_map_{points_plotted}_points.png"
        save_grayscale_image(bytes(output), width, height, filename)
        print(f"  ✅ Plotted {points_plotted} points")
        return filename
    
    return None

def decode_as_compressed_signature(raw_data, width=250, height=200):
    """Maybe this is a signature or small graphic, not a photo"""
    print("🎯 Attempting to decode as compressed signature...")
    
    # Create output
    output = bytearray(width * height)
    for i in range(len(output)):
        output[i] = 255  # White background
    
    # Try to interpret as a sparse signature
    # Use the data to draw lines or points
    for i in range(len(raw_data)):
        # Use byte value to determine position and intensity
        x = (i * width) // len(raw_data)
        y = (raw_data[i] * height) // 255
        
        # Draw a vertical line at this position
        for dy in range(-2, 3):
            y_pos = min(max(y + dy, 0), height-1)
            pos = y_pos * width + x
            if pos < len(output):
                # Darker for higher values
                intensity = 255 - min(raw_data[i] * 2, 255)
                output[pos] = min(output[pos], intensity)
    
    filename = "signature_style.png"
    save_grayscale_image(bytes(output), width, height, filename)
    print(f"  💾 {filename}")
    return filename

def decode_as_data_visualization(raw_data, width=250, height=200):
    """Create a visualization of the raw data itself"""
    print("🎯 Creating data visualization...")
    
    output = bytearray(width * height)
    
    # Fill with gradient background
    for y in range(height):
        for x in range(width):
            output[y * width + x] = (x + y) % 256
    
    # Overlay the actual data values
    for i, byte_val in enumerate(raw_data):
        x = (i * width) // len(raw_data)
        y = (byte_val * height) // 255
        
        # Draw a point
        for dy in range(-1, 2):
            for dx in range(-1, 2):
                x_pos = (x + dx) % width
                y_pos = (y + dy) % height
                pos = y_pos * width + x_pos
                if pos < len(output):
                    output[pos] = 0  # Black point
    
    filename = "data_visualization.png"
    save_grayscale_image(bytes(output), width, height, filename)
    print(f"  💾 {filename}")
    return filename

def decode_as_text_or_binary(raw_data, width=250, height=200):
    """Check if this might be text or binary data, not an image"""
    print("🎯 Analyzing as text/binary data...")
    
    # Convert to string to check for text patterns
    try:
        text = raw_data.decode('ascii', errors='replace')
        printable_count = sum(1 for c in text if c.isprintable() or c in ' \t\n\r')
        
        print(f"  Printable characters: {printable_count}/{len(raw_data)} ({printable_count/len(raw_data)*100:.1f}%)")
        
        if printable_count > len(raw_data) * 0.7:
            print("  ⚡ High percentage of printable characters - might be text data")
            # Show first 100 characters
            preview = text[:100].replace('\n', '\\n').replace('\r', '\\r').replace('\t', '\\t')
            print(f"  Preview: {preview}")
    except:
        print("  Not primarily ASCII text")
    
    # Create a visualization of the binary data
    output = bytearray(width * height)
    for i in range(len(output)):
        output[i] = 255  # White background
    
    # Draw the bytes as a binary map
    bytes_per_row = min(width, len(raw_data))
    rows = min(height, (len(raw_data) + bytes_per_row - 1) // bytes_per_row)
    
    for row in range(rows):
        for col in range(bytes_per_row):
            idx = row * bytes_per_row + col
            if idx < len(raw_data):
                output[row * width + col] = raw_data[idx]
    
    filename = "binary_data_map.png"
    save_grayscale_image(bytes(output), width, height, filename)
    print(f"  💾 {filename}")
    return filename

def real_image_decoding(license_data):
    """Main function for real image decoding"""
    if not license_data or not license_data.image_bytes:
        return None
    
    raw_data = license_data.image_bytes
    width = license_data.image_width  
    height = license_data.image_height
    
    print("🎯 REAL IMAGE DECODING ATTEMPT")
    print("=" * 60)
    
    # First, understand what we're dealing with
    most_common = analyze_actual_image_data(raw_data, width, height)
    
    # Try different interpretations
    results = []
    
    print(f"\n🔄 ATTEMPTING VARIOUS DECODING METHODS")
    print("=" * 50)
    
    # Method 1: Single line image
    line_result = decode_as_line_image(raw_data, width, height)
    if line_result:
        results.append(("Single Line", line_result))
    
    # Method 2: Coordinate map
    coord_result = decode_as_coordinate_map(raw_data, width, height)
    if coord_result:
        results.append(("Coordinate Map", coord_result))
    
    # Method 3: Signature style
    sig_result = decode_as_compressed_signature(raw_data, width, height)
    if sig_result:
        results.append(("Signature", sig_result))
    
    # Method 4: Data visualization
    viz_result = decode_as_data_visualization(raw_data, width, height)
    if viz_result:
        results.append(("Data Visualization", viz_result))
    
    # Method 5: Text/binary analysis
    text_result = decode_as_text_or_binary(raw_data, width, height)
    if text_result:
        results.append(("Binary Data", text_result))
    
    # Summary
    print(f"\n📊 DECODING SUMMARY")
    print("=" * 50)
    
    if results:
        print(f"✅ Generated {len(results)} interpretations:")
        for name, filename in results:
            print(f"   - {name}: {filename}")
    else:
        print(f"❌ No interpretations generated")
    
    print(f"\n🔍 CONCLUSIONS:")
    print(f"• 611 bytes is only 1.2% of needed data for {width}x{height} image")
    print(f"• This is likely NOT a full photo")
    print(f"• Possible contents:")
    print(f"  - A single line of image data")
    print(f"  - Coordinate data for sparse image") 
    print(f"  - Compressed signature or small graphic")
    print(f"  - Binary metadata")
    print(f"  - The actual photo may be stored elsewhere")
    
    return results

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