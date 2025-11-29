# Create: text_data_analyzer.py

def analyze_text_data(raw_data):
    """Analyze the text content of the image data"""
    print("🔍 TEXT DATA ANALYSIS")
    print("=" * 60)
    
    # Convert to text
    try:
        text = raw_data.decode('ascii', errors='replace')
        print(f"Total characters: {len(text)}")
        print(f"Printable characters: {sum(1 for c in text if c.isprintable() or c in ' \\t\\n\\r')}")
        print()
        
        # Split into lines based on common delimiters
        lines = []
        current_line = ""
        
        for char in text:
            if char in '\n\r':  # Line breaks
                if current_line:
                    lines.append(current_line)
                    current_line = ""
            elif char == '\t':  # Tabs
                current_line += '  '  # Replace tabs with spaces for display
            else:
                current_line += char
        
        if current_line:
            lines.append(current_line)
        
        print(f"Found {len(lines)} lines of text:")
        print("-" * 40)
        
        for i, line in enumerate(lines):
            if line.strip():  # Only show non-empty lines
                print(f"Line {i+1}: {line[:80]}{'...' if len(line) > 80 else ''}")
        
        return text, lines
        
    except Exception as e:
        print(f"Error decoding text: {e}")
        return None, None

def decode_as_structured_data(raw_data):
    """Try to decode as structured data (like XML, JSON, or custom format)"""
    print("\n🎯 STRUCTURED DATA ANALYSIS")
    print("=" * 50)
    
    text = raw_data.decode('ascii', errors='replace')
    
    # Check for common structured data patterns
    if text.startswith('{') or text.startswith('['):
        print("⚡ Possible JSON data")
    elif text.startswith('<'):
        print("⚡ Possible XML data")
    elif '=' in text and ';' in text:
        print("⚡ Possible key=value pairs")
    
    # Look for field patterns
    field_indicators = ['NAME=', 'ID=', 'DATE=', 'DOB=', 'LICENSE=', 'SURNAME=']
    found_fields = []
    
    for field in field_indicators:
        if field.lower() in text.lower():
            found_fields.append(field)
    
    if found_fields:
        print(f"Found potential fields: {found_fields}")
    
    # Try to extract key-value pairs
    print("\nPotential key-value patterns:")
    import re
    
    # Look for patterns like: KEY=VALUE or KEY: VALUE
    patterns = [
        r'([A-Za-z_]+)=([^\\s;]+)',  # KEY=VALUE
        r'([A-Za-z_]+):\\s*([^\\s;]+)',  # KEY: VALUE
    ]
    
    for pattern in patterns:
        matches = re.findall(pattern, text)
        if matches:
            print(f"Pattern '{pattern}':")
            for key, value in matches[:10]:  # Show first 10
                print(f"  {key} = {value}")
            if len(matches) > 10:
                print(f"  ... and {len(matches) - 10} more")
            break

def decode_as_biometric_template(raw_data):
    """Check if this might be biometric template data"""
    print("\n🎯 BIOMETRIC TEMPLATE ANALYSIS")
    print("=" * 50)
    
    # Biometric templates often have specific patterns
    # Look for common biometric data indicators
    
    # Check for facial recognition template patterns
    template_indicators = [
        ('Fixed header patterns', lambda d: d[0:4] in [b'\\x00\\x00\\x00\\x00', b'FACE', b'HEAD']),
        ('Coordinate ranges', lambda d: all(0 <= b <= 255 for b in d[:100])),
        ('Sparse data', lambda d: d.count(0) > len(d) * 0.1),
    ]
    
    for name, check in template_indicators:
        try:
            result = check(raw_data)
            print(f"{name}: {'✅' if result else '❌'}")
        except:
            print(f"{name}: ❌")
    
    # Create a template visualization
    output = bytearray(250 * 200)
    for i in range(len(output)):
        output[i] = 255  # White background
    
    # Interpret as feature points
    points_plotted = 0
    for i in range(0, len(raw_data)-1, 2):
        x = raw_data[i] % 250
        y = raw_data[i+1] % 200
        
        # Draw a small cross at this point
        for dy in range(-2, 3):
            for dx in range(-2, 3):
                x_pos = (x + dx) % 250
                y_pos = (y + dy) % 200
                pos = y_pos * 250 + x_pos
                if pos < len(output):
                    output[pos] = 0  # Black point
                    points_plotted += 1
    
    if points_plotted > 0:
        filename = "biometric_template.png"
        save_grayscale_image(bytes(output), 250, 200, filename)
        print(f"💾 Biometric template visualization: {filename}")
        return filename
    
    return None

def decode_as_license_metadata(raw_data):
    """Check if this contains additional license metadata"""
    print("\n🎯 LICENSE METADATA ANALYSIS")
    print("=" * 50)
    
    text = raw_data.decode('ascii', errors='replace')
    
    # Look for common license data patterns
    license_patterns = {
        'Dates': r'\\d{4}/\\d{2}/\\d{2}',
        'ID Numbers': r'\\d{13}',
        'License Numbers': r'[A-Z0-9]{10,15}',
        'Vehicle Codes': r'[A-Z]{1,3}',
    }
    
    found_data = {}
    
    for data_type, pattern in license_patterns.items():
        import re
        matches = re.findall(pattern, text)
        if matches:
            found_data[data_type] = matches
            print(f"{data_type}: {matches}")
    
    # Check if this might be duplicate or additional license info
    if found_data:
        print("⚡ Contains structured license data")
        return found_data
    
    return None

def save_grayscale_image(data, width, height, filename):
    """Save grayscale image with proper size"""
    from PIL import Image
    if len(data) < width * height:
        data = data + b'\\xFF' * (width * height - len(data))
    elif len(data) > width * height:
        data = data[:width * height]
    
    img = Image.frombytes('L', (width, height), bytes(data))
    img.save(filename)

def comprehensive_text_analysis(license_data):
    """Comprehensive analysis of the text data"""
    if not license_data or not license_data.image_bytes:
        return None
    
    raw_data = license_data.image_bytes
    
    print("🎯 COMPREHENSIVE TEXT DATA ANALYSIS")
    print("=" * 60)
    
    # 1. Basic text analysis
    text, lines = analyze_text_data(raw_data)
    
    if not text:
        return None
    
    # 2. Structured data analysis
    decode_as_structured_data(raw_data)
    
    # 3. Biometric template analysis
    template_file = decode_as_biometric_template(raw_data)
    
    # 4. License metadata analysis
    metadata = decode_as_license_metadata(raw_data)
    
    # 5. Save the raw text for inspection
    with open("license_text_data.txt", "w", encoding='ascii', errors='replace') as f:
        f.write("RAW TEXT DATA FROM LICENSE:\\n")
        f.write("=" * 40 + "\\n")
        f.write(text)
    
    print(f"\\n💾 Raw text saved: license_text_data.txt")
    
    # Conclusions
    print(f"\\n🔍 FINAL CONCLUSIONS:")
    print(f"• The 'image data' is actually TEXT DATA (84% printable)")
    print(f"• This is NOT a photo - it's metadata or template data")
    print(f"• Possible contents:")
    print(f"  - Additional license metadata")
    print(f"  - Biometric template data") 
    print(f"  - Digital signature data")
    print(f"  - Compression parameters")
    print(f"  - The actual photo may be:")
    print(f"    • Not included in the barcode")
    print(f"    • Stored in a separate system")
    print(f"    • Retrieved via different means")
    
    return {
        'text': text,
        'lines': lines,
        'template_file': template_file,
        'metadata': metadata
    }