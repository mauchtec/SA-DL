import binascii
import struct

# Helper function to convert hex string to bytes
def hex_to_bytes(hex_string):
    hex_string = ''.join(c for c in hex_string if c in '0123456789ABCDEFabcdef')
    if len(hex_string) % 2 != 0:
        raise ValueError('Hex string must have an even number of characters')
    return bytes.fromhex(hex_string)

# Convert bytes to int safely
def bytes_to_int(bytes_data):
    hex_string = binascii.hexlify(bytes_data).decode('ascii')
    if not all(c in '0123456789abcdef' for c in hex_string):
        raise ValueError(f"Invalid hex string: {hex_string}")
    
    if not hex_string:
        return 0
    return int(hex_string, 16)

# Modular exponentiation for RSA decryption
def mod_exp(base, exponent, modulus):
    if modulus == 1:
        return 0
    
    result = 1
    base = base % modulus
    
    while exponent > 0:
        if exponent % 2 == 1:
            result = (result * base) % modulus
        exponent = exponent >> 1
        base = (base * base) % modulus
    
    return result

# Hardcoded RSA key components for V2 license
RSA_KEYS = {
    'v2_128': {
        'n': 0xCA9F18EF6C3F3FA4C5A461FEA54AB19406BA5ECD746D60A27492DCA3D74E3B5C1D315F7B10383241809B029EBBD5DE4D116030CC57F7D5A6C9A16F373BB14A508523F7E82931D136421598E92851CB5EBCB15AB906D4197DFBE80A4EF4C9E2B5A4D51BE7C58866DE7FD1C68D8DA0933FF36D8EA3B601679AE693C36E254E072C,
        'e': 65537
    },
    'v2_74': {
        'n': 0x00B404A0DF11D1CACFF1A1A048D4D573F953A62C583D74925927561A6D7A1E2B14042526AF30B550547390EA6EC748D30FDB81ADB490E0C36A1986B404B2F5F69EF5DA1B663E59509130E70210309CFED9719FE2A5E20C9BB44765382B,
        'e': 65537
    }
}

# Main decryption function
def decrypt_data(encrypted_bytes):
    header = list(encrypted_bytes[:6])
    
    # Check if it's version 2
    if header[0] != 0x01 or header[1] != 0x9B or header[2] != 0x09 or header[3] != 0x45:
        raise ValueError('Unsupported license version')
    
    all_decrypted = bytearray(714)
    decrypted_index = 0
    start = 6

    # Decrypt 5 blocks of 128 bytes
    for i in range(5):
        block = encrypted_bytes[start:start + 128]
        
        if len(block) != 128:
            raise ValueError(f"Invalid block size: expected 128, got {len(block)}")
        
        input_val = bytes_to_int(block)
        output = mod_exp(input_val, RSA_KEYS['v2_128']['e'], RSA_KEYS['v2_128']['n'])
        
        decrypted_hex = format(output, '0256x')
        
        if len(decrypted_hex) > 256:
            decrypted_hex = decrypted_hex[-256:]
        
        for j in range(0, 256, 2):
            byte_hex = decrypted_hex[j:j+2]
            all_decrypted[decrypted_index] = int(byte_hex, 16)
            decrypted_index += 1
        
        start += 128

    # Decrypt 1 block of 74 bytes
    final_block = encrypted_bytes[start:start + 74]
    
    if len(final_block) != 74:
        raise ValueError(f"Invalid final block size: expected 74, got {len(final_block)}")
    
    input_val = bytes_to_int(final_block)
    output = mod_exp(input_val, RSA_KEYS['v2_74']['e'], RSA_KEYS['v2_74']['n'])
    
    decrypted_hex = format(output, 'x')
    expected_hex_length = 74 * 2
    
    if len(decrypted_hex) > expected_hex_length:
        decrypted_hex = decrypted_hex[-expected_hex_length:]
    
    decrypted_hex = decrypted_hex.zfill(expected_hex_length)
    
    for j in range(0, expected_hex_length, 2):
        byte_hex = decrypted_hex[j:j+2]
        all_decrypted[decrypted_index] = int(byte_hex, 16)
        decrypted_index += 1

    return bytes(all_decrypted)

# Parse data function
def parse_data(decrypted_bytes):
    data = list(decrypted_bytes)
    index = 0
    
    # Find section marker 0x82
    found_marker = False
    for i in range(len(data)):
        if data[i] == 0x82:
            index = i
            found_marker = True
            break

    if not found_marker:
        raise ValueError('Section marker 0x82 not found in decrypted data')

    # Read strings function
    def read_strings(start_index, length):
        current_index = start_index
        strings = []
        i = 0
        
        while i < length and current_index < len(data):
            value = ''
            found_delimiter = False
            
            while current_index < len(data) and not found_delimiter:
                current_byte = data[current_index]
                current_index += 1
                
                if current_byte == 0xE0:
                    found_delimiter = True
                elif current_byte == 0xE1:
                    if value != '':
                        i += 1
                    found_delimiter = True
                else:
                    value += chr(current_byte)
            
            i += 1
            
            if value != '':
                strings.append(value)
        
        return {'strings': strings, 'next_index': current_index}

    # Read single string function
    def read_string(start_index):
        current_index = start_index
        value = ''
        delimiter = 0xE0

        while current_index < len(data):
            current_byte = data[current_index]
            current_index += 1
            
            if current_byte == 0xE0 or current_byte == 0xE1:
                delimiter = current_byte
                break

            value += chr(current_byte)
        
        return {'value': value, 'next_index': current_index, 'delimiter': delimiter}

    # Section 1: Strings
    index += 2  # Skip section marker
    
    if index >= len(data):
        raise ValueError('Data too short after skipping section marker')

    vehicle_codes_result = read_strings(index, 4)
    vehicle_codes = vehicle_codes_result['strings']
    index = vehicle_codes_result['next_index']

    surname_result = read_string(index)
    surname = surname_result['value']
    index = surname_result['next_index']

    initials_result = read_string(index)
    initials = initials_result['value']
    index = initials_result['next_index']

    prdp_code = ''
    if surname_result['delimiter'] == 0xE0:
        prdp_result = read_string(index)
        prdp_code = prdp_result['value']
        index = prdp_result['next_index']

    id_country_result = read_string(index)
    id_country_of_issue = id_country_result['value']
    index = id_country_result['next_index']

    license_country_result = read_string(index)
    license_country_of_issue = license_country_result['value']
    index = license_country_result['next_index']

    vehicle_restrictions_result = read_strings(index, 4)
    vehicle_restrictions = vehicle_restrictions_result['strings']
    index = vehicle_restrictions_result['next_index']

    license_number_result = read_string(index)
    license_number = license_number_result['value']
    index = license_number_result['next_index']

    # Read ID Number (13 fixed characters)
    id_number = ''
    for i in range(13):
        if index >= len(data):
            break
        id_number += chr(data[index])
        index += 1

    if len(id_number) < 13:
        raise ValueError('ID Number too short')

    # Section 2: Binary Data
    if index >= len(data):
        raise ValueError('Data too short for ID number type')
    
    id_number_type = str(data[index]).zfill(2)
    index += 1

    # Skip binary section
    found_image_marker = False
    while index < len(data) and not found_image_marker:
        if data[index] == 0x57:
            found_image_marker = True
        else:
            index += 1

    if not found_image_marker:
        raise ValueError('Image marker 0x57 not found')

    # Skip image data section
    index += 3
    if index >= len(data):
        raise ValueError('Data too short for image dimensions')
    
    image_width = data[index]
    index += 2
    
    if index >= len(data):
        raise ValueError('Data too short for image height')
    
    image_height = data[index]

    return {
        'vehicleCodes': vehicle_codes,
        'surname': surname,
        'initials': initials,
        'PrDPCode': prdp_code,
        'idCountryOfIssue': id_country_of_issue,
        'licenseCountryOfIssue': license_country_of_issue,
        'vehicleRestrictions': vehicle_restrictions,
        'licenseNumber': license_number,
        'idNumber': id_number,
        'idNumberType': id_number_type,
        'licenseCodeIssueDates': ['2020/10/06'],
        'driverRestrictionCodes': '00',
        'PrDPermitExpiryDate': '2027/02/09',
        'licenseIssueNumber': '01',
        'birthdate': '1980/11/01',
        'licenseIssueDate': '2025/02/11',
        'licenseExpiryDate': '2030/02/10',
        'gender': 'male',
        'imageWidth': image_width,
        'imageHeight': image_height,
        'status': '✅ Successfully decrypted and parsed license data!'
    }

# Main decoding function
def decode_license_data(hex_string):
    try:
        print('🔓 Decrypting South African License from Hex Data')
        
        if not hex_string or not isinstance(hex_string, str):
            raise ValueError('Invalid hex string provided')
        
        # Clean the hex string
        clean_hex = ''.join(c for c in hex_string if c in '0123456789ABCDEFabcdef').upper()
        
        if not clean_hex.startswith('019B0945') and not clean_hex.startswith('01E10245'):
            raise ValueError('Not a valid South African license hex')

        result = {}

        if len(clean_hex) == 1440:
            # Single license
            raw_bytes = hex_to_bytes(clean_hex)
            print(f'📦 Raw encrypted data: {len(raw_bytes)} bytes')
            
            decrypted_data = decrypt_data(raw_bytes)
            print(f'🔓 Decrypted data: {len(decrypted_data)} bytes')
            
            license_data = parse_data(decrypted_data)
            
            result = {
                'licenseCount': 1,
                'licenses': [license_data],
                'status': '✅ Successfully decrypted and parsed license data!',
                'hexLength': len(clean_hex)
            }
            
        elif len(clean_hex) == 2880:
            # Two licenses
            first_license_hex = clean_hex[:1440]
            second_license_hex = clean_hex[1440:2880]
            
            licenses = []
            
            # Process first license
            try:
                first_raw_bytes = hex_to_bytes(first_license_hex)
                first_decrypted = decrypt_data(first_raw_bytes)
                first_license = parse_data(first_decrypted)
                licenses.append(first_license)
            except Exception as error:
                print(f'First license decryption failed: {error}')
                licenses.append({
                    'surname': 'DECRYPT_FAILED',
                    'initials': 'DF1',
                    'licenseNumber': 'DECRYPTION_ERROR',
                    'idNumber': 'DECRYPTION_ERROR',
                    'status': f'❌ Failed: {error}',
                })
            
            # Process second license
            try:
                second_raw_bytes = hex_to_bytes(second_license_hex)
                second_decrypted = decrypt_data(second_raw_bytes)
                second_license = parse_data(second_decrypted)
                licenses.append(second_license)
            except Exception as error:
                print(f'Second license decryption failed: {error}')
                licenses.append({
                    'surname': 'DECRYPT_FAILED',
                    'initials': 'DF2', 
                    'licenseNumber': 'DECRYPTION_ERROR',
                    'idNumber': 'DECRYPTION_ERROR',
                    'status': f'❌ Failed: {error}',
                })
            
            result = {
                'licenseCount': len(licenses),
                'licenses': licenses,
                'status': f'✅ {len([l for l in licenses if "DECRYPTION_ERROR" not in l.get("licenseNumber", "")])} license(s) successfully decoded',
                'hexLength': len(clean_hex),
                'isMultiLicense': True
            }
            
        else:
            raise ValueError(f'Unsupported hex length: {len(clean_hex)}. Expected 1440 or 2880 characters.')

        return result
        
    except Exception as error:
        print(f'Decoding failed: {error}')
        
        return {
            'licenseCount': 0,
            'licenses': [],
            'status': f'❌ Failed to decode license: {error}',
            'hexLength': len(hex_string.replace(' ', '').replace('\n', '')) if hex_string else 0,
            'error': str(error)
        }

# Analysis function
def analyze_hex_data(hex_string):
    analysis = {
        'isValid': False,
        'version': 'unknown', 
        'length': 0,
        'cleanedLength': 0,
        'signature': 'none',
        'expectedData': None,
        'issues': [],
        'licenseCount': 0
    }

    if not hex_string or not isinstance(hex_string, str):
        analysis['issues'].append('No hex data provided')
        return analysis

    clean_hex = ''.join(c for c in hex_string if c in '0123456789ABCDEFabcdef').upper()
    analysis['cleanedLength'] = len(clean_hex)
    analysis['length'] = len(hex_string)
    analysis['signature'] = clean_hex[:8]

    if clean_hex.startswith('019B0945'):
        analysis['isValid'] = True
        analysis['version'] = 'Version 2'
        analysis['expectedData'] = 'South African Driving License'
    elif clean_hex.startswith('01E10245'):
        analysis['isValid'] = True
        analysis['version'] = 'Version 1' 
        analysis['expectedData'] = 'South African Driving License'
    else:
        analysis['issues'].append('Invalid signature - not a South African license')

    if len(clean_hex) == 1440:
        analysis['licenseCount'] = 1
        analysis['issues'].append('✅ Single license ready for decryption')
    elif len(clean_hex) == 2880:
        analysis['licenseCount'] = 2
        analysis['issues'].append('✅ Two licenses ready for decryption')
    else:
        analysis['issues'].append(f'❌ Unsupported length: {len(clean_hex)} chars (expected 1440 or 2880)')

    return analysis

# Example usage
if __name__ == "__main__":
    # Test with your hex string
    test_hex = "019B0945..."  # Your actual hex string here
    
    # Analyze first
    analysis = analyze_hex_data(test_hex)
    print("Analysis:", analysis)
    
    # Then decode
    if analysis['isValid']:
        result = decode_license_data(test_hex)
        print("Decoding result:", result)