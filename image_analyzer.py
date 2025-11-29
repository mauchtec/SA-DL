# Create a new file: image_analyzer.py

def hex_dump(data, bytes_per_line=16):
    """Create a formatted hex dump"""
    result = []
    for i in range(0, len(data), bytes_per_line):
        chunk = data[i:i + bytes_per_line]
        hex_str = ' '.join(f'{b:02x}' for b in chunk)
        ascii_str = ''.join(chr(b) if 32 <= b <= 126 else '.' for b in chunk)
        result.append(f'{i:04x}: {hex_str:<48} {ascii_str}')
    return '\n'.join(result)

def analyze_compressed_image(raw_data, width=250, height=200):
    """Deep analysis of the compressed image format"""
    print("🔍 DEEP IMAGE DATA ANALYSIS")
    print("=" * 60)
    
    print(f"Raw data size: {len(raw_data)} bytes")
    print(f"Expected size for {width}x{height} grayscale: {width * height} bytes")
    print(f"Compression ratio: {len(raw_data) / (width * height):.4%}")
    print()
    
    # Basic statistics
    unique_bytes = len(set(raw_data))
    print(f"Unique byte values: {unique_bytes}")
    print(f"Byte value range: {min(raw_data)} to {max(raw_data)}")
    
    # Count frequency of each byte value
    from collections import Counter
    byte_counts = Counter(raw_data)
    common_bytes = byte_counts.most_common(10)
    print(f"\nMost common bytes:")
    for byte_val, count in common_bytes:
        print(f"  {byte_val:3d} (0x{byte_val:02x}): {count:4d} times")
    
    # Look for patterns
    print(f"\nPattern analysis:")
    
    # Check for RLE patterns
    rle_patterns = 0
    for i in range(len(raw_data) - 2):
        if raw_data[i] == raw_data[i + 1] == raw_data[i + 2]:
            rle_patterns += 1
    
    print(f"  Repeated byte sequences: {rle_patterns}")
    
    # Check for zero patterns (common in sparse images)
    zero_count = raw_data.count(0)
    print(f"  Zero bytes: {zero_count} ({zero_count/len(raw_data):.1%})")
    
    # Check for potential header
    print(f"\nFirst 32 bytes:")
    print(hex_dump(raw_data[:32]))
    
    # Try to detect format
    detect_format(raw_data)
    
    return byte_counts

def detect_format(raw_data):
    """Try to detect the compression format"""
    print(f"\nFormat detection:")
    
    # Check for known markers
    if raw_data[0:2] == b'\xff\xd8':
        print("  ✅ JPEG format")
    elif raw_data[0:4] == b'\x89PNG':
        print("  ✅ PNG format")
    elif raw_data[0:2] == b'BM':
        print("  ✅ BMP format")
    elif all(b in [0, 1] for b in raw_data[:100]):
        print("  ⚡ 1-bit bitmap (black/white)")
    elif max(raw_data[:100]) <= 15:
        print("  ⚡ 4-bit grayscale")
    elif max(raw_data[:100]) <= 255:
        print("  ⚡ 8-bit grayscale")
    else:
        print("  ❓ Unknown format")
    
    # Check for RLE signatures
    if raw_data[0] == 0x01 and raw_data[1] == 0x00:
        print("  ⚡ Potential Windows BMP RLE")
    elif raw_data[0] == 0x57 and raw_data[1] == 0x04:
        print("  ⚡ Potential custom RLE format")

def decode_as_1bit_bitmap(raw_data, width=250, height=200):
    """Decode as 1-bit per pixel bitmap"""
    print(f"\n🎯 Attempting 1-bit bitmap decoding...")
    
    total_pixels = width * height
    total_bits_needed = total_pixels
    total_bits_available = len(raw_data) * 8
    
    print(f"  Available bits: {total_bits_available}")
    print(f"  Needed bits: {total_bits_needed}")
    
    if total_bits_available < total_pixels:
        print(f"  ❌ Not enough data for 1-bit bitmap")
        return None
    
    # Create output image (0=black, 255=white)
    output = bytearray()
    bit_pos = 0
    
    for y in range(height):
        row = bytearray()
        for x in range(width):
            byte_idx = bit_pos // 8
            bit_idx = bit_pos % 8
            
            if byte_idx < len(raw_data):
                # Get the bit (MSB first)
                bit = (raw_data[byte_idx] >> (7 - bit_idx)) & 1
                # Convert to grayscale: 0=black, 255=white
                pixel = 0 if bit else 255
                row.append(pixel)
            else:
                row.append(255)  # White padding
            
            bit_pos += 1
        output.extend(row)
    
    return bytes(output)

def decode_as_4bit_grayscale(raw_data, width=250, height=200):
    """Decode as 4-bit grayscale (2 pixels per byte)"""
    print(f"\n🎯 Attempting 4-bit grayscale decoding...")
    
    total_pixels = width * height
    total_bytes_needed = (total_pixels + 1) // 2  # 2 pixels per byte
    
    print(f"  Available bytes: {len(raw_data)}")
    print(f"  Needed bytes: {total_bytes_needed}")
    
    if len(raw_data) < total_bytes_needed:
        print(f"  ❌ Not enough data for 4-bit grayscale")
        return None
    
    output = bytearray()
    
    for i in range(total_pixels):
        byte_idx = i // 2
        if byte_idx >= len(raw_data):
            break
            
        if i % 2 == 0:
            # First pixel (high 4 bits)
            pixel_val = (raw_data[byte_idx] >> 4) & 0x0F
        else:
            # Second pixel (low 4 bits)
            pixel_val = raw_data[byte_idx] & 0x0F
        
        # Scale 4-bit (0-15) to 8-bit (0-255)
        pixel_8bit = (pixel_val * 255) // 15
        output.append(pixel_8bit)
    
    # Pad if necessary
    while len(output) < total_pixels:
        output.append(255)  # White
    
    return bytes(output)

def decode_as_rle_compressed(raw_data, width=250, height=200):
    """Try various RLE decompression methods"""
    print(f"\n🎯 Attempting RLE decompression...")
    
    methods = [
        ("Standard RLE", decode_standard_rle),
        ("PackBits RLE", decode_packbits_rle),
        ("TIFF RLE", decode_tiff_rle),
    ]
    
    for name, decoder in methods:
        try:
            print(f"  Trying {name}...")
            result = decoder(raw_data, width, height)
            if result and len(result) >= width * height:
                print(f"  ✅ {name} successful: {len(result)} bytes")
                return result
        except Exception as e:
            print(f"  ❌ {name} failed: {e}")
    
    return None

def decode_standard_rle(raw_data, width, height):
    """Standard Run-Length Encoding"""
    output = bytearray()
    i = 0
    
    while i < len(raw_data) and len(output) < width * height:
        if i + 1 < len(raw_data):
            count = raw_data[i]
            value = raw_data[i + 1]
            
            if count > 0:
                output.extend([value] * count)
                i += 2
                continue
        
        output.append(raw_data[i])
        i += 1
    
    return output

def decode_packbits_rle(raw_data, width, height):
    """Apple PackBits RLE decompression"""
    output = bytearray()
    i = 0
    
    while i < len(raw_data) and len(output) < width * height:
        header = raw_data[i]
        i += 1
        
        if header <= 127:  # Literal run
            count = header + 1
            if i + count <= len(raw_data):
                output.extend(raw_data[i:i + count])
                i += count
        else:  # Repeated run
            count = 256 - header
            if i < len(raw_data):
                value = raw_data[i]
                output.extend([value] * count)
                i += 1
    
    return output

def decode_tiff_rle(raw_data, width, height):
    """TIFF-style RLE decompression"""
    output = bytearray()
    i = 0
    
    while i < len(raw_data) and len(output) < width * height:
        count_byte = raw_data[i]
        i += 1
        
        if count_byte < 128:  # Literal run
            count = count_byte + 1
            if i + count <= len(raw_data):
                output.extend(raw_data[i:i + count])
                i += count
        else:  # Repeated run
            count = 256 - count_byte
            if i < len(raw_data):
                value = raw_data[i]
                output.extend([value] * count)
                i += 1
    
    return output

def save_image_result(data, width, height, filename, format_name):
    """Save the decoded image"""
    try:
        from PIL import Image
        
        # Ensure correct size
        required_size = width * height
        if len(data) < required_size:
            data = data + b'\xFF' * (required_size - len(data))  # Pad with white
        elif len(data) > required_size:
            data = data[:required_size]
        
        img = Image.frombytes('L', (width, height), bytes(data))
        full_filename = f"{filename}_{format_name}.png"
        img.save(full_filename)
        print(f"  💾 Saved as: {full_filename}")
        return full_filename
    except Exception as e:
        print(f"  ❌ Failed to save {format_name}: {e}")
        return None

# Main analysis function
def comprehensive_image_analysis(raw_data, width=250, height=200, base_filename="license_photo"):
    """Comprehensive analysis and decoding of image data"""
    
    # First, analyze the raw data
    byte_counts = analyze_compressed_image(raw_data, width, height)
    
    # Try different decoding methods
    successful_decodings = []
    
    print(f"\n" + "=" * 60)
    print(f"ATTEMPTING DECODING METHODS")
    print("=" * 60)
    
    # Method 1: 1-bit bitmap
    result = decode_as_1bit_bitmap(raw_data, width, height)
    if result:
        filename = save_image_result(result, width, height, base_filename, "1bit")
        if filename:
            successful_decodings.append(("1-bit Bitmap", filename))
    
    # Method 2: 4-bit grayscale
    result = decode_as_4bit_grayscale(raw_data, width, height)
    if result:
        filename = save_image_result(result, width, height, base_filename, "4bit")
        if filename:
            successful_decodings.append(("4-bit Grayscale", filename))
    
    # Method 3: RLE decompression
    result = decode_as_rle_compressed(raw_data, width, height)
    if result:
        filename = save_image_result(result, width, height, base_filename, "rle")
        if filename:
            successful_decodings.append(("RLE Compressed", filename))
    
    # Save raw data for external analysis
    raw_filename = f"{base_filename}_raw_{len(raw_data)}bytes.bin"
    with open(raw_filename, 'wb') as f:
        f.write(raw_data)
    print(f"\n💾 Raw data saved as: {raw_filename}")
    
    # Summary
    print(f"\n" + "=" * 60)
    print(f"DECODING SUMMARY")
    print("=" * 60)
    
    if successful_decodings:
        print(f"✅ Successful decodings:")
        for name, filename in successful_decodings:
            print(f"   - {name}: {filename}")
    else:
        print(f"❌ No successful decodings")
        print(f"   The image uses an unknown compression format")
        print(f"   Raw data saved for further analysis: {raw_filename}")
    
    return successful_decodings

# Usage example:
if __name__ == "__main__":
    # You'll need to extract the 611 bytes from your license data
    # For now, let's assume you have the raw_data variable
    # raw_data = your_611_bytes_here
    
    print("Please run this with your actual image data.")
    print("To use: comprehensive_image_analysis(your_raw_data, 250, 200)")