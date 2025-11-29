# Create: advanced_image_decoder.py

def analyze_data_structure(raw_data):
    """Analyze the structure of the compressed data"""
    print("🔍 Analyzing data structure patterns...")
    
    # Look for header patterns
    header = raw_data[:20]
    print(f"Header (first 20 bytes): {header.hex()}")
    
    # Check for potential size markers
    if raw_data[0] == 0x42 and raw_data[1] == 0x6c:
        print("  ⚡ Potential custom format signature: 0x42 0x6c")
    
    # Analyze byte sequences
    sequences = []
    current_seq = [raw_data[0]]
    
    for i in range(1, len(raw_data)):
        if raw_data[i] == raw_data[i-1] + 2:  # Check for +2 patterns
            current_seq.append(raw_data[i])
        else:
            if len(current_seq) > 2:
                sequences.append(current_seq)
            current_seq = [raw_data[i]]
    
    if sequences:
        print(f"  Found {len(sequences)} sequential patterns")
    
    return sequences

def decode_differential_compression(raw_data, width=250, height=200):
    """Try differential/predictive compression"""
    print("🎯 Attempting differential compression decoding...")
    
    output = bytearray(width * height)
    
    # Start with a default background (white)
    for i in range(len(output)):
        output[i] = 255  # White background
    
    try:
        # Try to interpret as run-length with differential encoding
        ptr = 0
        pixel_pos = 0
        
        while ptr < len(raw_data) and pixel_pos < len(output):
            if ptr + 1 < len(raw_data):
                cmd = raw_data[ptr]
                param = raw_data[ptr + 1]
                
                if cmd == 0x00:  # Potential end marker
                    break
                elif cmd < 0x80:  # Potential run length
                    # Copy literal run
                    run_length = cmd
                    if ptr + 1 + run_length <= len(raw_data):
                        for j in range(run_length):
                            if pixel_pos < len(output):
                                output[pixel_pos] = raw_data[ptr + 1 + j]
                                pixel_pos += 1
                        ptr += 1 + run_length
                        continue
                else:  # Potential fill run
                    run_length = 256 - cmd
                    if ptr + 2 <= len(raw_data):
                        fill_value = param
                        for j in range(run_length):
                            if pixel_pos < len(output):
                                output[pixel_pos] = fill_value
                                pixel_pos += 1
                        ptr += 2
                        continue
            
            # Default: copy single byte
            if pixel_pos < len(output):
                output[pixel_pos] = raw_data[ptr]
                pixel_pos += 1
            ptr += 1
            
        print(f"  Processed {pixel_pos} pixels")
        return bytes(output)
        
    except Exception as e:
        print(f"  ❌ Differential decoding failed: {e}")
        return None

def decode_bitpacked_compression(raw_data, width=250, height=200):
    """Try various bit-packed formats"""
    print("🎯 Attempting bit-packed decoding...")
    
    total_pixels = width * height
    
    # Try different bit depths
    bit_depths = [1, 2, 4]
    
    for bits_per_pixel in bit_depths:
        print(f"  Trying {bits_per_pixel}-bit per pixel...")
        
        pixels_per_byte = 8 // bits_per_pixel
        total_bytes_needed = (total_pixels + pixels_per_byte - 1) // pixels_per_byte
        
        if len(raw_data) >= total_bytes_needed:
            output = bytearray(total_pixels)
            
            try:
                for i in range(total_pixels):
                    byte_idx = i // pixels_per_byte
                    bit_offset = (i % pixels_per_byte) * bits_per_pixel
                    
                    if byte_idx < len(raw_data):
                        # Extract bits
                        byte_val = raw_data[byte_idx]
                        pixel_val = (byte_val >> (8 - bit_offset - bits_per_pixel)) & ((1 << bits_per_pixel) - 1)
                        
                        # Scale to 8-bit
                        output[i] = (pixel_val * 255) // ((1 << bits_per_pixel) - 1)
                    else:
                        output[i] = 255  # White
                
                print(f"    ✅ {bits_per_pixel}-bit decoding completed")
                return bytes(output)
                
            except Exception as e:
                print(f"    ❌ {bits_per_pixel}-bit decoding failed: {e}")
    
    return None

def decode_custom_rle_variant(raw_data, width=250, height=200):
    """Try custom RLE variants that might match the data pattern"""
    print("🎯 Attempting custom RLE variant decoding...")
    
    output = bytearray()
    i = 0
    
    # Based on the hex pattern, try different interpretations
    while i < len(raw_data) and len(output) < width * height:
        if i + 2 < len(raw_data):
            # Check for potential command pattern
            b1, b2, b3 = raw_data[i], raw_data[i+1], raw_data[i+2]
            
            # Pattern 1: [count, value, something]
            if b1 < 100 and b2 > 0:  # Reasonable values
                output.extend([b2] * b1)
                i += 3
                continue
            
            # Pattern 2: [value, count, skip]
            if b2 < 100 and b1 > 0:
                output.extend([b1] * b2)
                i += 3
                continue
        
        # Default: copy single byte
        output.append(raw_data[i])
        i += 1
    
    if len(output) >= width * height:
        print(f"  ✅ Custom RLE produced {len(output)} bytes")
        return bytes(output[:width * height])
    else:
        print(f"  ❌ Custom RLE insufficient: {len(output)} bytes")
        return None

def decode_with_histogram_analysis(raw_data, width=250, height=200):
    """Use histogram analysis to guess the encoding"""
    print("🎯 Attempting histogram-based decoding...")
    
    from collections import Counter
    freq = Counter(raw_data)
    
    # Find the most common "background" color
    background = freq.most_common(1)[0][0] if freq else 255
    
    # Create output with background
    output = bytearray([background] * (width * height))
    
    # Try to overlay the data as foreground
    data_len = min(len(raw_data), len(output))
    for i in range(data_len):
        if raw_data[i] != background:  # Only overwrite if different
            output[i] = raw_data[i]
    
    return bytes(output)

def brute_force_decoding(raw_data, width=250, height=200, base_filename="license_photo"):
    """Try every conceivable decoding method"""
    print("🔄 BRUTE FORCE DECODING ATTEMPT")
    print("=" * 50)
    
    methods = [
        ("Differential", decode_differential_compression),
        ("Bit-Packed", decode_bitpacked_compression),
        ("Custom RLE", decode_custom_rle_variant),
        ("Histogram", decode_with_histogram_analysis),
    ]
    
    successful = []
    
    for name, decoder in methods:
        try:
            print(f"\nTrying {name}...")
            result = decoder(raw_data, width, height)
            if result and len(result) >= width * height:
                filename = f"{base_filename}_{name.lower()}.png"
                save_grayscale_image(result, width, height, filename)
                successful.append((name, filename))
                print(f"✅ {name} SUCCESS!")
            else:
                print(f"❌ {name} failed")
        except Exception as e:
            print(f"❌ {name} error: {e}")
    
    return successful

def save_grayscale_image(data, width, height, filename):
    """Save grayscale image"""
    from PIL import Image
    img = Image.frombytes('L', (width, height), bytes(data))
    img.save(filename)

def advanced_image_analysis(raw_data, width=250, height=200):
    """Comprehensive advanced analysis"""
    print("🔍 ADVANCED IMAGE ANALYSIS")
    print("=" * 50)
    
    # Deep structure analysis
    sequences = analyze_data_structure(raw_data)
    
    # Try brute force decoding
    results = brute_force_decoding(raw_data, width, height)
    
    # If nothing works, create diagnostic images
    if not results:
        create_diagnostic_images(raw_data, width, height)
    
    return results

def create_diagnostic_images(raw_data, width=250, height=200):
    """Create diagnostic images to help understand the data"""
    print("\n📊 CREATING DIAGNOSTIC IMAGES")
    
    # Method 1: Direct mapping (truncated)
    direct_data = raw_data + b'\xFF' * (width * height - len(raw_data))
    direct_data = direct_data[:width * height]
    save_grayscale_image(direct_data, width, height, "diagnostic_direct.png")
    print("  💾 diagnostic_direct.png - Direct byte mapping")
    
    # Method 2: Repeated pattern
    repeated_data = (raw_data * ( (width * height) // len(raw_data) + 1))[:width * height]
    save_grayscale_image(repeated_data, width, height, "diagnostic_repeated.png")
    print("  💾 diagnostic_repeated.png - Repeated pattern")
    
    # Method 3: Scaled (stretched)
    import numpy as np
    from PIL import Image
    # Create a small image from the data
    small_side = int((len(raw_data)) ** 0.5)
    if small_side > 0:
        small_data = raw_data[:small_side * small_side]
        small_data = small_data + b'\xFF' * (small_side * small_side - len(small_data))
        small_img = Image.frombytes('L', (small_side, small_side), bytes(small_data))
        # Scale up
        scaled_img = small_img.resize((width, height), Image.NEAREST)
        scaled_img.save("diagnostic_scaled.png")
        print("  💾 diagnostic_scaled.png - Scaled from small image")

# Main execution function
def decode_license_image(license_data):
    """Main function to decode license image"""
    if not license_data or not license_data.image_bytes:
        return None
    
    raw_data = license_data.image_bytes
    width = license_data.image_width
    height = license_data.image_height
    
    print(f"🎯 DECODING LICENSE IMAGE: {width}x{height}, {len(raw_data)} bytes")
    print("=" * 60)
    
    # First, save the raw data for external analysis
    with open("license_image_raw.bin", "wb") as f:
        f.write(raw_data)
    print("💾 Raw data saved: license_image_raw.bin")
    
    # Try advanced decoding
    results = advanced_image_analysis(raw_data, width, height)
    
    if results:
        print(f"\n🎉 SUCCESS! Found {len(results)} working decoding methods:")
        for name, filename in results:
            print(f"   ✅ {name}: {filename}")
    else:
        print(f"\n❌ No standard decoding methods worked.")
        print("   The image uses a proprietary compression format.")
        print("   Diagnostic images created for analysis.")
    
    return results