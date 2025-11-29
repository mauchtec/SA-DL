from sadl import decrypt_data, parse_data
import base64

def decrypt_hex_license(hex_string):
    """Decrypt and parse license data directly from hex - no license key needed"""
    try:
        # Convert hex to bytes
        raw_bytes = bytes.fromhex(hex_string)
        print(f"📦 Raw encrypted data: {len(raw_bytes)} bytes")
        
        # Decrypt the data
        decrypted_data = decrypt_data(raw_bytes)
        print(f"🔓 Decrypted data: {len(decrypted_data)} bytes")
        
        # Parse the decrypted data
        license_data = parse_data(decrypted_data)
        
        if license_data:
            print("✅ Successfully decrypted and parsed license data!")
            print("\n" + "="*50)
            print(license_data)
            return license_data
        else:
            print("❌ Failed to parse decrypted data")
            return None
            
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()

def decrypt_base64_license(base64_string):
    """Decrypt from base64 string"""
    try:
        # Decode base64 to bytes
        raw_bytes = base64.b64decode(base64_string)
        print(f"📦 Raw encrypted data: {len(raw_bytes)} bytes")
        
        # Decrypt the data
        decrypted_data = decrypt_data(raw_bytes)
        
        # Parse the decrypted data
        license_data = parse_data(decrypted_data)
        
        if license_data:
            print("✅ Successfully decrypted and parsed license data!")
            print(license_data)
            return license_data
            
    except Exception as e:
        print(f"❌ Error: {e}")

# Your hex data
hex_data = "019B094500000AC88323FD762A06B51995E3DA1B7109E03953A67DF4752390B91EB7ABC77B4DE286428B4CC1EF09045D6BCCDDC71D6D5A19F60F29D7AF28608B7D404CE51CCFE596DF94C01DE1EE84C293226D789612D679D0D03A6EE411A9ED78871EE1BAE85CA9149CF934E4CBB6E1DDB935C233AE7A64EB41F2B685E1EA906364A4C21F9238FA21F6A30BB8FA857922AA4D0A371F30A61CF4141A50F840DD783CC31B93DE05879D6B65623828ACF7B9D4A2A663EDD60CA8F0FA294CE30301C69147197E6A09DD61CDE4647A23D66331A4C6C2D03505BEBDC83ABCF1A160161B99B5B349943B4860603364FEEC6E3D5B8FFD7199F3BA4BFC1F57056D609EC08F6B5A817C4902E79BE993A04861CA9F362DC02F61C09F584A7D3390FAA93A89C23D0A3CB0B99855FB5629CAF1456B699BB8BA6A7EB004140F14E4F353BD12BFED3C7F78F32605EFCBE15109E5A254CD635BCE66C5DB4CED5A2B5CAF9B76FE62B851221079A1DD87F702681DC995660A5683BFA0D9D7DDD9676B73D0FD39E774D93251CA485424CEBF871EB77B7706BEC31886270565B0A0394AEBB528AF2B31194E16AE11A90A5B5F881F9A9E359D8B088A78CE802CA1723B75F8DCF02195FDE7E9D82AC7041D61B234742A674F7BFF5715749DD4C755B25E22E883FCBB141D000803FA2FE952EF23E70E49B245EA84C42AF3D4B650E7F0FCBC5E8FEDD16D1D4975387A9D4C38E2682CA895DDAF5FAA98B6903C9C2DDD673950F252D7EB05D96C3A241D7767C02132EEDA78E619ED860955D8A851900CBF5757CE6AF1FE13FD575AE41CCE549599775667C5AABB1DA264B6F4672871526B6A50237B7EF9DBC9FADD4D815211FCAAA9287B3990166F4C3C9FD594080B8C53F293C34B6BB46FF58EBF12600EB9772450C44C6087F673D33DE019798A4C6386D8FC31C24AE77A32C448FAD03BA5382022992771C83CD545F186CB2697338709464E85C7C56F98EA3D21425E09F14C6185E1C54A4BD17A0F"

print("🔓 Decrypting South African License from Hex Data")
print("=" * 60)
decrypt_hex_license(hex_data)