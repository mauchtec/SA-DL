# https://github.com/ugommirikwe/sa-license-decoder/blob/master/SPEC.md
from PIL import Image
import numpy as np
import base64
import rsa
from pathlib import Path
from dbr import *

__version__ = '0.1.1'

v1 = [0x01, 0xe1, 0x02, 0x45]
v2 = [0x01, 0x9b, 0x09, 0x45]

pk_v1_128 = '''
-----BEGIN RSA PUBLIC KEY-----
MIGXAoGBAP7S4cJ+M2MxbncxenpSxUmBOVGGvkl0dgxyUY1j4FRKSNCIszLFsMNwx2XWXZg8H53gpCsxDMwHrncL0rYdak3M6sdXaJvcv2CEePrzEvYIfMSWw3Ys9cRlHK7No0mfrn7bfrQOPhjrMEFw6R7VsVaqzm9DLW7KbMNYUd6MZ49nAhEAu3l//ex/nkLJ1vebE3BZ2w==
-----END RSA PUBLIC KEY-----
'''

pk_v1_74 = '''
-----BEGIN RSA PUBLIC KEY-----
MGACSwD/POxrX0Djw2YUUbn8+u866wbcIynA5vTczJJ5cmcWzhW74F7tLFcRvPj1tsj3J221xDv6owQNwBqxS5xNFvccDOXqlT8MdUxrFwIRANsFuoItmswz+rfY9Cf5zmU=
-----END RSA PUBLIC KEY-----
'''

pk_v2_128 = '''
-----BEGIN RSA PUBLIC KEY-----
MIGWAoGBAMqfGO9sPz+kxaRh/qVKsZQGul7NdG1gonSS3KPXTjtcHTFfexA4MkGAmwKeu9XeTRFgMMxX99WmyaFvNzuxSlCFI/foCkx0TZCFZjpKFHLXryxWrkG1Bl9++gKTvTJ4rWk1RvnxYhm3n/Rxo2NoJM/822Oo7YBZ5rmk8NuJU4HLAhAYcJLaZFTOsYU+aRX4RmoF
-----END RSA PUBLIC KEY-----
'''

pk_v2_74 = '''
-----BEGIN RSA PUBLIC KEY-----
MF8CSwC0BKDfEdHKz/GhoEjU1XP5U6YsWD10klknVhpteh4rFAQlJq9wtVBUc5DqbsdI0w/bga20kODDahmGtASy9fae9dobZj5ZUJEw5wIQMJz+2XGf4qXiDJu0R2U4Kw==
-----END RSA PUBLIC KEY-----
'''


def decode_pdf417(image_file, license_key=''):
    """Decode PDF417 code from image"""
    key = "DLS2eyJoYW5kc2hha2VDb2RlIjoiMjAwMDAxLTE2NDk4Mjk3OTI2MzUiLCJvcmdhbml6YXRpb25JRCI6IjIwMDAwMSIsInNlc3Npb25QYXNzd29yZCI6IndTcGR6Vm05WDJrcEQ5YUoifQ=="
    if license_key != '':
        key = license_key
    BarcodeReader.init_license(key)
    reader = BarcodeReader()
    results = reader.decode_file(image_file)
    if results is not None and len(results) > 0:
        return results[0].barcode_bytes
    else:
        return None


def decrypt_data(data):
    """Decrypt data"""
    header = data[0:6]
    pk128 = pk_v1_128
    pk74 = pk_v1_74
    
    if header[0] == v1[0] and header[1] == v1[1] and header[2] == v1[2] and header[3] == v1[3]:
        pk128 = pk_v1_128
        pk74 = pk_v1_74
    elif header[0] == v2[0] and header[1] == v2[1] and header[2] == v2[2] and header[3] == v2[3]:
        pk128 = pk_v2_128
        pk74 = pk_v2_74
    
    all_data = bytearray()
    
    pubKey = rsa.PublicKey.load_pkcs1(pk128)
    start = 6
    for i in range(5):
        block = data[start: start + 128]
        input_val = int.from_bytes(block, byteorder='big', signed=False)
        output = pow(input_val, pubKey.e, mod=pubKey.n)
        decrypted_bytes = output.to_bytes(128, byteorder='big', signed=False)
        all_data += decrypted_bytes
        start += 128
    
    pubKey = rsa.PublicKey.load_pkcs1(pk74)
    block = data[start: start + 74]
    input_val = int.from_bytes(block, byteorder='big', signed=False)
    output = pow(input_val, pubKey.e, mod=pubKey.n)
    decrypted_bytes = output.to_bytes(74, byteorder='big', signed=False)
    all_data += decrypted_bytes
    
    return all_data


def readNibbleDateString(nibbleQueue):
    m = nibbleQueue.pop(0)
    if m == 10:
        return ''
    
    c = nibbleQueue.pop(0)
    d = nibbleQueue.pop(0)
    y = nibbleQueue.pop(0)
    m1 = nibbleQueue.pop(0)
    m2 = nibbleQueue.pop(0)
    d1 = nibbleQueue.pop(0)
    d2 = nibbleQueue.pop(0)
    
    return f'{m}{c}{d}{y}/{m1}{m2}/{d1}{d2}'


def readNibbleDateList(nibbleQueue, length):
    dateList = []
    for i in range(length):
        dateString = readNibbleDateString(nibbleQueue)
        if dateString != '':
            dateList.append(dateString)
    return dateList


def readStrings(data, index, length):
    strings = []
    i = 0
    while i < length:
        value = ''
        while True:
            currentByte = data[index]
            index += 1
            if currentByte == 0xe0:
                break
            elif currentByte == 0xe1:
                if value != '':
                    i += 1
                break
            value += chr(currentByte)
        i += 1
        if value != '':
            strings.append(value)
    return strings, index


def readString(data, index):
    value = ''
    delimiter = 0xe0
    while True:
        currentByte = data[index]
        index += 1
        if currentByte == 0xe0 or currentByte == 0xe1:
            delimiter = currentByte
            break
        value += chr(currentByte)
    return value, index, delimiter


def parse_data(data):
    """Parse data including extracting the actual image"""
    index = 0
    for i in range(0, len(data)):
        if data[i] == 0x82:
            index = i
            break
   
    # Section 1: Strings
    vehicleCodes, index = readStrings(data, index + 2, 4)
    surname, index, delimiter = readString(data, index)
    initials, index, delimiter = readString(data, index)
    
    PrDPCode = ''
    if delimiter == 0xe0:
        PrDPCode, index, delimiter = readString(data, index)
    
    idCountryOfIssue, index, delimiter = readString(data, index)
    licenseCountryOfIssue, index, delimiter = readString(data, index)
    vehicleRestrictions, index = readStrings(data, index, 4)
    licenseNumber, index, delimiter = readString(data, index)
    
    idNumber = ''
    for i in range(13):
        idNumber += chr(data[index])
        index += 1
    
    # Section 2: Binary Data
    idNumberType = f'{data[index]:02d}'
    index += 1
    
    nibbleQueue = []
    while True:
        currentByte = data[index]
        index += 1
        if currentByte == 0x57:
            break
        nibbles = [currentByte >> 4, currentByte & 0x0f]
        nibbleQueue += nibbles
        
    licenseCodeIssueDates = readNibbleDateList(nibbleQueue, 4)
    driverRestrictionCodes = f'{nibbleQueue.pop(0)}{nibbleQueue.pop(0)}'
    PrDPermitExpiryDate = readNibbleDateString(nibbleQueue)
    licenseIssueNumber = f'{nibbleQueue.pop(0)}{nibbleQueue.pop(0)}'
    birthdate = readNibbleDateString(nibbleQueue)
    licenseIssueDate = readNibbleDateString(nibbleQueue)
    licenseExpiryDate = readNibbleDateString(nibbleQueue)
    
    gender = f'{nibbleQueue.pop(0)}{nibbleQueue.pop(0)}'
    if gender == '01':
        gender = 'male'
    else:
        gender = 'female'
    
    # Section 3: Image Data
    index += 3
    width = data[index]
    index += 2
    height = data[index]
    index += 1
    
    # Extract image data
    image_bytes = None
    image_format = "unknown"
    
    # Look for JPEG
    jpeg_start = -1
    for i in range(index, len(data) - 2):
        if data[i] == 0xFF and data[i+1] == 0xD8 and data[i+2] == 0xFF:
            jpeg_start = i
            break
    
    if jpeg_start != -1:
        jpeg_end = -1
        for i in range(jpeg_start + 2, len(data) - 1):
            if data[i] == 0xFF and data[i+1] == 0xD9:
                jpeg_end = i + 2
                break
        if jpeg_end != -1:
            image_bytes = data[jpeg_start:jpeg_end]
            image_format = "jpeg"
            print(f"📸 Extracted JPEG image: {len(image_bytes)} bytes")
    
    # Handle raw image data
    if image_bytes is None:
        remaining_data = data[index:]
        print(f"🔍 Raw image data analysis:")
        print(f"   - Expected size for {width}x{height} RGB: {width * height * 3} bytes")
        print(f"   - Expected size for {width}x{height} grayscale: {width * height} bytes") 
        print(f"   - Actual available: {len(remaining_data)} bytes")
        
        image_bytes = remaining_data
        image_format = "raw"
        print(f"📸 Extracted raw image data: {len(image_bytes)} bytes")
    
    return DrivingLicense(
        vehicleCodes, surname, initials, PrDPCode, idCountryOfIssue, 
        licenseCountryOfIssue, vehicleRestrictions, licenseNumber, 
        idNumber, idNumberType, licenseCodeIssueDates, driverRestrictionCodes, 
        PrDPermitExpiryDate, licenseIssueNumber, birthdate, licenseIssueDate, 
        licenseExpiryDate, gender, width, height, image_bytes, image_format
    )


class DrivingLicense:    
    def __init__(self, vehicleCodes, surname, initials, PrDPCode, idCountryOfIssue, 
                 licenseCountryOfIssue, vehicleRestrictions, licenseNumber, 
                 idNumber, idNumberType, licenseCodeIssueDates, driverRestrictionCodes, 
                 PrDPermitExpiryDate, licenseIssueNumber, birthdate, licenseIssueDate, 
                 licenseExpiryDate, gender, width, height, image_bytes=None, image_format="unknown"):
        self.vehicleCodes = vehicleCodes
        self.surname = surname
        self.initials = initials
        self.PrDPCode = PrDPCode
        self.idCountryOfIssue = idCountryOfIssue
        self.licenseCountryOfIssue = licenseCountryOfIssue
        self.vehicleRestrictions = vehicleRestrictions
        self.licenseNumber = licenseNumber
        self.idNumber = idNumber
        self.idNumberType = idNumberType
        self.licenseCodeIssueDates = licenseCodeIssueDates
        self.driverRestrictionCodes = driverRestrictionCodes
        self.PrDPermitExpiryDate = PrDPermitExpiryDate
        self.licenseIssueNumber = licenseIssueNumber
        self.birthdate = birthdate
        self.licenseIssueDate = licenseIssueDate
        self.licenseExpiryDate = licenseExpiryDate
        self.gender = gender
        self.image_width = width
        self.image_height = height
        self.image_bytes = image_bytes
        self.image_format = image_format
        
    def __str__(self) -> str:
        base_info = f'''Vehicle codes: {self.vehicleCodes}
Surname: {self.surname}
Initials: {self.initials}
PrDP Code: {self.PrDPCode}
ID Country of Issue: {self.idCountryOfIssue}
License Country of Issue: {self.licenseCountryOfIssue}
Vehicle Restriction: {self.vehicleRestrictions}
License Number: {self.licenseNumber}
ID Number: {self.idNumber}
ID number type: {self.idNumberType}
License code issue date: {self.licenseCodeIssueDates}
Driver restriction codes: {self.driverRestrictionCodes}
PrDP permit expiry date: {self.PrDPermitExpiryDate}
License issue number: {self.licenseIssueNumber}
Birthdate: {self.birthdate}
License Valid From: {self.licenseIssueDate}
License Valid To: {self.licenseExpiryDate}
Gender: {self.gender}
Image width: {self.image_width}
Image height: {self.image_height}'''
        
        if self.image_bytes:
            base_info += f"\nImage data: {len(self.image_bytes)} bytes"
            if self.image_format == "jpeg":
                base_info += " (JPEG format)"
            else:
                base_info += " (Raw format)"
        
        return base_info
    
    def save_image(self, filename='license_photo'):
        """Save the extracted image to a file"""
        if not self.image_bytes:
            print("❌ No image data to save")
            return False
            
        try:
            if self.image_format == "jpeg" or self.image_bytes.startswith(b'\xff\xd8'):
                full_filename = filename + '.jpg'
                with open(full_filename, 'wb') as f:
                    f.write(self.image_bytes)
                print(f"💾 JPEG image saved as: {full_filename}")
                
            elif self.image_format == "raw":
                full_filename = self._convert_raw_image(filename)
                if full_filename:
                    print(f"💾 Converted image saved as: {full_filename}")
                else:
                    full_filename = filename + '.raw'
                    with open(full_filename, 'wb') as f:
                        f.write(self.image_bytes)
                    print(f"💾 Raw image data saved as: {full_filename} (for analysis)")
            else:
                full_filename = filename + '.bin'
                with open(full_filename, 'wb') as f:
                    f.write(self.image_bytes)
                print(f"💾 Unknown format image saved as: {full_filename}")
                
            return True
            
        except Exception as e:
            print(f"❌ Error saving image: {e}")
            return False
    
    def _convert_raw_image(self, filename):
        """Try to convert raw image data to proper formats"""
        try:
            raw_data = self.image_bytes
            width = self.image_width
            height = self.image_height
            
            print(f"🔄 Attempting to convert raw image data...")
            print(f"   - Dimensions: {width}x{height}")
            print(f"   - Data size: {len(raw_data)} bytes")
            
            expected_rgb = width * height * 3
            expected_grayscale = width * height
            
            if len(raw_data) == expected_grayscale:
                print("   - Detected: Grayscale format")
                img = Image.frombytes('L', (width, height), raw_data)
                full_filename = filename + '_grayscale.png'
                img.save(full_filename)
                return full_filename
                
            elif len(raw_data) == expected_rgb:
                print("   - Detected: RGB format")
                img = Image.frombytes('RGB', (width, height), raw_data)
                full_filename = filename + '_rgb.png'
                img.save(full_filename)
                return full_filename
                
            else:
                print("   - Trying auto-detection...")
                if len(raw_data) < expected_grayscale:
                    print("   - Data appears compressed, saving as raw")
                    return None
                    
                try:
                    if len(raw_data) > expected_rgb:
                        raw_data = raw_data[:expected_rgb]
                        img = Image.frombytes('RGB', (width, height), raw_data)
                        full_filename = filename + '_rgb_trimmed.png'
                    elif len(raw_data) > expected_grayscale:
                        raw_data = raw_data[:expected_grayscale]
                        img = Image.frombytes('L', (width, height), raw_data)
                        full_filename = filename + '_grayscale_trimmed.png'
                    else:
                        return None
                    img.save(full_filename)
                    return full_filename
                except Exception as e:
                    print(f"   - Auto-detection failed: {e}")
                    return None
                    
        except Exception as e:
            print(f"   - Conversion error: {e}")
            return None

    def show_image_info(self):
        """Display image information"""
        print(f"🖼️  Image Dimensions: {self.image_width}x{self.image_height}")
        if self.image_bytes:
            print(f"📊 Image data size: {len(self.image_bytes)} bytes")
            print(f"🎯 Format: {self.image_format}")
            
            expected_rgb = self.image_width * self.image_height * 3
            expected_grayscale = self.image_width * self.image_height
            
            print(f"📐 Expected sizes:")
            print(f"   - RGB: {expected_rgb} bytes")
            print(f"   - Grayscale: {expected_grayscale} bytes")
            
            if len(self.image_bytes) == expected_grayscale:
                print("   ✅ Matches grayscale format")
            elif len(self.image_bytes) == expected_rgb:
                print("   ✅ Matches RGB format")
            else:
                print("   ⚠️  Size doesn't match standard formats")
        else:
            print("❌ No image data extracted")


def parse_base64(base64_string, encrypted=False):
    """Parse base64 string"""
    data = base64.b64decode(base64_string)
    if len(data) != 720 and encrypted:
        return None
    if encrypted:
        data = decrypt_data(data)
    return parse_data(data)


def parse_bytes(bytes_data, encrypted=False):
    """Parse bytes"""
    data = bytes_data
    if len(data) != 720 and encrypted:
        return None
    if encrypted:
        data = decrypt_data(bytes_data)
    return parse_data(data)


def parse_file(filename, encrypted=True, license=''):
    """Parse file"""
    data = decode_pdf417(filename, license)
    if data is None or len(data) != 720:
        return None
    return parse_bytes(data, encrypted)


def decrypt_hex_license(hex_string, save_image=True):
    """Decrypt and parse license data directly from hex"""
    try:
        raw_bytes = bytes.fromhex(hex_string)
        print(f"📦 Raw encrypted data: {len(raw_bytes)} bytes")
        
        decrypted_data = decrypt_data(raw_bytes)
        print(f"🔓 Decrypted data: {len(decrypted_data)} bytes")
        
        license_data = parse_data(decrypted_data)
        
        if license_data:
            print("✅ Successfully decrypted and parsed license data!")
            print("\n" + "="*50)
            print(license_data)
            
            print("\n" + "="*50)
            license_data.show_image_info()
            
            if save_image and license_data.image_bytes:
                license_data.save_image('extracted_license_photo')
            
            return license_data
        else:
            print("❌ Failed to parse decrypted data")
            return None
            
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()


def debug_license_structure(hex_string):
    """Debug function to examine the license structure"""
    try:
        raw_bytes = bytes.fromhex(hex_string)
        decrypted_data = decrypt_data(raw_bytes)
        
        print("🔍 Debugging license structure:")
        print(f"Total decrypted bytes: {len(decrypted_data)}")
        
        jpeg_start = decrypted_data.find(b'\xff\xd8')
        if jpeg_start != -1:
            print(f"📍 JPEG start found at position: {jpeg_start}")
            jpeg_end = decrypted_data.find(b'\xff\xd9', jpeg_start)
            if jpeg_end != -1:
                print(f"📍 JPEG end found at position: {jpeg_end}")
                image_size = jpeg_end + 2 - jpeg_start
                print(f"📸 JPEG image size: {image_size} bytes")
                image_data = decrypted_data[jpeg_start:jpeg_end+2]
                with open('debug_license_image.jpg', 'wb') as f:
                    f.write(image_data)
                print("💾 Debug image saved as: debug_license_image.jpg")
        
        png_start = decrypted_data.find(b'\x89PNG')
        if png_start != -1:
            print(f"📍 PNG header found at position: {png_start}")
            
        print("\nFirst 100 bytes of decrypted data (hex):")
        print(decrypted_data[:100].hex())
        
    except Exception as e:
        print(f"❌ Debug error: {e}")
    # Add this function to analyze and decode the compressed image data

def analyze_and_decode_image(raw_data, width, height, filename='license_photo'):
    """Analyze and decode the compressed image data"""
    print(f"🔍 Analyzing compressed image data...")
    print(f"   Data size: {len(raw_data)} bytes")
    print(f"   Expected: {width}x{height} = {width * height} pixels")
    
    # Print first 50 bytes in hex for analysis
    print(f"   First 50 bytes (hex): {raw_data[:50].hex()}")
    print(f"   First 50 bytes (decimal): {list(raw_data[:50])}")
    
    # Check for common compression markers
    if raw_data[0] == 0x57 and raw_data[1] == 0x04:
        print("   ⚡ Detected potential RLE or custom compression format")
        return decode_compressed_image(raw_data, width, height, filename)
    else:
        # Try different decoding approaches
        return try_multiple_decodings(raw_data, width, height, filename)

def decode_compressed_image(raw_data, width, height, filename):
    """Attempt to decode the compressed image format"""
    try:
        print("   🎯 Attempting RLE (Run-Length Encoding) decompression...")
        
        decompressed = bytearray()
        i = 0
        
        while i < len(raw_data):
            if i + 1 < len(raw_data):
                # Try RLE format: [value, count]
                value = raw_data[i]
                count = raw_data[i + 1]
                
                # Validate count
                if count > 0 and count < 250:  # Reasonable range
                    decompressed.extend([value] * count)
                    i += 2
                    continue
            
            # If not RLE, just copy the byte
            decompressed.append(raw_data[i])
            i += 1
        
        if len(decompressed) >= width * height:
            print(f"   ✅ RLE decompression successful: {len(decompressed)} bytes")
            return save_grayscale_image(decompressed, width, height, filename + '_rle')
        else:
            print(f"   ❌ RLE decompression insufficient: {len(decompressed)} bytes")
            return None
            
    except Exception as e:
        print(f"   ❌ RLE decompression failed: {e}")
        return None

def try_multiple_decodings(raw_data, width, height, filename):
    """Try multiple image decoding approaches"""
    results = []
    
    # Approach 1: Direct grayscale (if data matches)
    if len(raw_data) == width * height:
        results.append(save_grayscale_image(raw_data, width, height, filename + '_direct'))
    
    # Approach 2: Try as packed bits (1-bit per pixel)
    elif len(raw_data) * 8 >= width * height:
        result = decode_1bit_image(raw_data, width, height, filename)
        if result:
            results.append(result)
    
    # Approach 3: Try different RLE variations
    result = decode_rle_variations(raw_data, width, height, filename)
    if result:
        results.append(result)
    
    # Approach 4: Save raw data for external analysis
    raw_filename = filename + '_raw.bin'
    with open(raw_filename, 'wb') as f:
        f.write(raw_data)
    print(f"   💾 Raw data saved as: {raw_filename}")
    
    return results

def decode_1bit_image(raw_data, width, height, filename):
    """Decode 1-bit per pixel image"""
    try:
        print("   🎯 Attempting 1-bit per pixel decoding...")
        
        total_pixels = width * height
        total_bits = len(raw_data) * 8
        
        if total_bits >= total_pixels:
            # Convert to 8-bit grayscale
            output = bytearray()
            bit_pos = 0
            
            for _ in range(total_pixels):
                byte_idx = bit_pos // 8
                bit_idx = bit_pos % 8
                
                if byte_idx < len(raw_data):
                    bit = (raw_data[byte_idx] >> (7 - bit_idx)) & 1
                    output.append(255 if bit else 0)  # Black or white
                else:
                    output.append(0)  # Padding
                
                bit_pos += 1
            
            return save_grayscale_image(output, width, height, filename + '_1bit')
        
    except Exception as e:
        print(f"   ❌ 1-bit decoding failed: {e}")
    
    return None

def decode_rle_variations(raw_data, width, height, filename):
    """Try different RLE variations"""
    variations = [
        ("Standard RLE", decode_standard_rle),
        ("Count-Value RLE", decode_count_value_rle),
        ("Value-Count RLE", decode_value_count_rle),
    ]
    
    for name, decoder in variations:
        try:
            print(f"   🎯 Trying {name}...")
            result = decoder(raw_data, width, height)
            if result and len(result) >= width * height:
                print(f"   ✅ {name} successful: {len(result)} bytes")
                return save_grayscale_image(result, width, height, filename + f'_{name.lower().replace(" ", "_")}')
        except Exception as e:
            print(f"   ❌ {name} failed: {e}")
    
    return None

def decode_standard_rle(raw_data, width, height):
    """Standard RLE: [value, count] pairs"""
    output = bytearray()
    i = 0
    
    while i < len(raw_data):
        if i + 1 < len(raw_data):
            value = raw_data[i]
            count = raw_data[i + 1]
            
            if count > 0:
                output.extend([value] * count)
                i += 2
                continue
        
        output.append(raw_data[i])
        i += 1
    
    return output

def decode_count_value_rle(raw_data, width, height):
    """RLE: [count, value] pairs"""
    output = bytearray()
    i = 0
    
    while i < len(raw_data):
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

def decode_value_count_rle(raw_data, width, height):
    """RLE with special markers"""
    output = bytearray()
    i = 0
    
    while i < len(raw_data):
        current = raw_data[i]
        
        if current == 0x00 and i + 1 < len(raw_data):  # Potential RLE marker
            count = raw_data[i + 1]
            if count > 0 and i + 2 < len(raw_data):
                value = raw_data[i + 2]
                output.extend([value] * count)
                i += 3
                continue
        
        output.append(current)
        i += 1
    
    return output

def save_grayscale_image(data, width, height, filename):
    """Save data as grayscale image"""
    try:
        # Ensure we have enough data
        required_size = width * height
        if len(data) < required_size:
            # Pad with zeros
            data = data + b'\x00' * (required_size - len(data))
        elif len(data) > required_size:
            # Truncate
            data = data[:required_size]
        
        img = Image.frombytes('L', (width, height), bytes(data))
        full_filename = filename + '.png'
        img.save(full_filename)
        print(f"   💾 Grayscale image saved as: {full_filename}")
        return full_filename
        
    except Exception as e:
        print(f"   ❌ Failed to save grayscale image: {e}")
        return None

# Update the _convert_raw_image method in DrivingLicense class:

def _convert_raw_image(self, filename):
    """Try to convert raw image data to proper formats"""
    try:
        raw_data = self.image_bytes
        width = self.image_width
        height = self.image_height
        
        print(f"🔄 Attempting to convert raw image data...")
        print(f"   - Dimensions: {width}x{height}")
        print(f"   - Data size: {len(raw_data)} bytes")
        
        # Use the new analysis function
        results = analyze_and_decode_image(raw_data, width, height, filename)
        
        if results:
            if isinstance(results, list):
                return results[0]  # Return first successful result
            return results
        else:
            # Fallback: save raw data
            raw_filename = filename + '.raw'
            with open(raw_filename, 'wb') as f:
                f.write(raw_data)
            print(f"   💾 Raw data saved as: {raw_filename}")
            return None
            
    except Exception as e:
        print(f"   - Conversion error: {e}")
        return None

# Also add this method to the DrivingLicense class for detailed analysis:

def analyze_image_data(self):
    """Detailed analysis of the image data"""
    if not self.image_bytes:
        print("❌ No image data to analyze")
        return
    
    print(f"🔍 Detailed Image Analysis:")
    print(f"   Dimensions: {self.image_width}x{self.image_height}")
    print(f"   Data size: {len(self.image_bytes)} bytes")
    print(f"   Compression ratio: {len(self.image_bytes) / (self.image_width * self.image_height):.2%}")
    
    # Analyze byte distribution
    unique_bytes = len(set(self.image_bytes))
    print(f"   Unique byte values: {unique_bytes}")
    
    # Check for patterns
    if all(b in [0, 255] for b in self.image_bytes[:100]):
        print("   Pattern: Likely binary (black/white) image")
    elif max(self.image_bytes) <= 1:
        print("   Pattern: Likely 1-bit image")
    else:
        print("   Pattern: Grayscale or custom format")
    
    # Save detailed analysis
    analysis_file = 'image_analysis.txt'
    with open(analysis_file, 'w') as f:
        f.write(f"Image Analysis Report\n")
        f.write(f"====================\n")
        f.write(f"Dimensions: {self.image_width}x{self.image_height}\n")
        f.write(f"Data size: {len(self.image_bytes)} bytes\n")
        f.write(f"Expected size: {self.image_width * self.image_height} bytes\n")
        f.write(f"Compression: {len(self.image_bytes) / (self.image_width * self.image_height):.2%}\n")
        f.write(f"\nFirst 100 bytes (hex):\n")
        f.write(self.image_bytes[:100].hex() + '\n')
        f.write(f"\nFirst 100 bytes (decimal):\n")
        f.write(str(list(self.image_bytes[:100])) + '\n')
    
    print(f"   📄 Detailed analysis saved as: {analysis_file}")
    # Add this to your main code after the license is parsed:

def extract_and_analyze_image(license_data):
    """Extract and analyze the image data from a license"""
    if not license_data or not license_data.image_bytes:
        print("❌ No image data available")
        return
    
    print(f"\n" + "=" * 60)
    print(f"EXTRACTING AND ANALYZING LICENSE IMAGE")
    print("=" * 60)
    
    raw_data = license_data.image_bytes
    width = license_data.image_width
    height = license_data.image_height
    
    # Use the comprehensive analyzer
    from image_analyzer import comprehensive_image_analysis
    results = comprehensive_image_analysis(raw_data, width, height, "license_photo")
    




# Your hex data
hex_data = "019B094500000AC88323FD762A06B51995E3DA1B7109E03953A67DF4752390B91EB7ABC77B4DE286428B4CC1EF09045D6BCCDDC71D6D5A19F60F29D7AF28608B7D404CE51CCFE596DF94C01DE1EE84C293226D789612D679D0D03A6EE411A9ED78871EE1BAE85CA9149CF934E4CBB6E1DDB935C233AE7A64EB41F2B685E1EA906364A4C21F9238FA21F6A30BB8FA857922AA4D0A371F30A61CF4141A50F840DD783CC31B93DE05879D6B65623828ACF7B9D4A2A663EDD60CA8F0FA294CE30301C69147197E6A09DD61CDE4647A23D66331A4C6C2D03505BEBDC83ABCF1A160161B99B5B349943B4860603364FEEC6E3D5B8FFD7199F3BA4BFC1F57056D609EC08F6B5A817C4902E79BE993A04861CA9F362DC02F61C09F584A7D3390FAA93A89C23D0A3CB0B99855FB5629CAF1456B699BB8BA6A7EB004140F14E4F353BD12BFED3C7F78F32605EFCBE15109E5A254CD635BCE66C5DB4CED5A2B5CAF9B76FE62B851221079A1DD87F702681DC995660A5683BFA0D9D7DDD9676B73D0FD39E774D93251CA485424CEBF871EB77B7706BEC31886270565B0A0394AEBB528AF2B31194E16AE11A90A5B5F881F9A9E359D8B088A78CE802CA1723B75F8DCF02195FDE7E9D82AC7041D61B234742A674F7BFF5715749DD4C755B25E22E883FCBB141D000803FA2FE952EF23E70E49B245EA84C42AF3D4B650E7F0FCBC5E8FEDD16D1D4975387A9D4C38E2682CA895DDAF5FAA98B6903C9C2DDD673950F252D7EB05D96C3A241D7767C02132EEDA78E619ED860955D8A851900CBF5757CE6AF1FE13FD575AE41CCE549599775667C5AABB1DA264B6F4672871526B6A50237B7EF9DBC9FADD4D815211FCAAA9287B3990166F4C3C9FD594080B8C53F293C34B6BB46FF58EBF12600EB9772450C44C6087F673D33DE019798A4C6386D8FC31C24AE77A32C448FAD03BA5382022992771C83CD545F186CB2697338709464E85C7C56F98EA3D21425E09F14C6185E1C54A4BD17A0F"


# In your main execution section, add this:

if __name__ == "__main__":
    print("🔓 Decrypting South African License from Hex Data")
    print("=" * 60)
    
    print("🔍 First, let's examine the data structure...")
    debug_license_structure(hex_data)
    
    print("\n" + "=" * 60)
    print("🎯 Now extracting complete license data with image...")
    print("=" * 60)
    
     # ... your existing decryption code ...
    
    license_data = decrypt_hex_license(hex_data, save_image=False)
    
    if license_data and license_data.image_bytes:
        print(f"\n🔍 Performing TEXT DATA analysis...")
        from text_data_analyzer import comprehensive_text_analysis
        results = comprehensive_text_analysis(license_data)
        
        if results:
            print(f"\n🎉 ANALYSIS COMPLETE!")
            print("The 'image data' is actually TEXT data, not a photo.")
            print("Check 'license_text_data.txt' to see the actual content.")
        else:
            print(f"\n❌ Could not analyze the text data.")
    else:
        print(f"\n⚠️  No data found")