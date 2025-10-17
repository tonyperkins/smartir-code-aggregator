#!/usr/bin/env python3
"""
Pronto Hex to Broadlink Base64 Converter

Converts Pronto Hex IR codes to Broadlink Base64 format.
Based on proven working code from:
- https://github.com/emilsoman/pronto_broadlink
- https://gist.github.com/appden/42d5272bf128125b019c45bc2ed3311f

References:
- Pronto format: http://www.remotecentral.com/features/irdisp2.htm
- Broadlink protocol: https://github.com/mjg59/python-broadlink
"""

import base64
import binascii
import struct
from typing import Optional, List


def pronto2lirc(pronto: bytearray) -> List[int]:
    """
    Convert Pronto Hex to LIRC pulse format.
    
    Args:
        pronto: Pronto code as bytearray
        
    Returns:
        List of pulse widths in microseconds
    """
    codes = [int(binascii.hexlify(pronto[i:i+2]), 16) for i in range(0, len(pronto), 2)]
    
    if codes[0]:
        raise ValueError('Pronto code should start with 0000')
    if len(codes) != 4 + 2 * (codes[2] + codes[3]):
        raise ValueError('Number of pulse widths does not match the preamble')
    
    frequency = 1 / (codes[1] * 0.241246)
    return [int(round(code / frequency)) for code in codes[4:]]


def lirc2broadlink(pulses: List[int]) -> bytearray:
    """
    Convert LIRC pulses to Broadlink packet format.
    
    Args:
        pulses: List of pulse widths in microseconds
        
    Returns:
        Broadlink packet as bytearray
    """
    array = bytearray()
    
    for pulse in pulses:
        pulse = int(pulse * 269 / 8192)  # Convert to 32.84ms units
        
        if pulse < 256:
            array += bytearray(struct.pack('>B', pulse))  # big endian (1-byte)
        else:
            array += bytearray([0x00])  # indicate next number is 2-bytes
            array += bytearray(struct.pack('>H', pulse))  # big endian (2-bytes)
    
    packet = bytearray([0x26, 0x00])  # 0x26 = IR, 0x00 = no repeats
    packet += bytearray(struct.pack('<H', len(array)))  # little endian byte count
    packet += array
    packet += bytearray([0x0d, 0x05])  # IR terminator
    
    # Add 0s to make ultimate packet size a multiple of 16 for 128-bit AES encryption.
    remainder = (len(packet) + 4) % 16  # rm.send_data() adds 4-byte header (02 00 00 00)
    if remainder:
        packet += bytearray(16 - remainder)
    
    return packet


def pronto_to_broadlink(pronto_code: str) -> Optional[str]:
    """
    Convert Pronto Hex code to Broadlink Base64 format.
    
    Args:
        pronto_code: Pronto Hex string (e.g., "0000 006C 0022 0002 015B...")
        
    Returns:
        Broadlink Base64 string or None if conversion fails
        
    Example:
        >>> pronto = "0000 006C 0022 0002 015B 00AD 0016 0016..."
        >>> broadlink = pronto_to_broadlink(pronto)
        >>> print(broadlink)
        "JgBQAAABJQAVABUAFQA..."
    """
    try:
        # Remove whitespace and convert to bytearray
        code = pronto_code.strip().replace(" ", "")
        pronto = bytearray.fromhex(code)
        
        # Convert Pronto → LIRC → Broadlink
        pulses = pronto2lirc(pronto)
        packet = lirc2broadlink(pulses)
        
        # Encode to Base64
        return base64.b64encode(packet).decode('utf-8')
        
    except Exception as e:
        # Silently fail for invalid codes
        return None


def validate_pronto(pronto_code: str) -> bool:
    """
    Validate Pronto Hex code format.
    
    Args:
        pronto_code: Pronto Hex string
        
    Returns:
        True if valid, False otherwise
    """
    try:
        values = [int(x, 16) for x in pronto_code.split()]
        
        if len(values) < 4:
            return False
            
        # Check code type (should be 0000 or 0100)
        if values[0] not in [0x0000, 0x0100]:
            return False
            
        # Check frequency is non-zero
        if values[1] == 0:
            return False
            
        # Check burst lengths match data
        first_length = values[2] * 2
        repeat_length = values[3] * 2
        expected_length = 4 + first_length + repeat_length
        
        return len(values) >= 4 + first_length
        
    except:
        return False


def batch_convert_pronto(pronto_codes: List[str]) -> List[Optional[str]]:
    """
    Convert multiple Pronto codes to Broadlink format.
    
    Args:
        pronto_codes: List of Pronto Hex strings
        
    Returns:
        List of Broadlink Base64 strings (None for failed conversions)
    """
    return [pronto_to_broadlink(code) for code in pronto_codes]


if __name__ == "__main__":
    # Test conversion
    test_pronto = "0000 006C 0022 0002 015B 00AD 0016 0016 0016 0016 0016 0041 0016 0041 0016 0041 0016 0041 0016 0041 0016 0041 0016 0041 0016 0016 0016 0041 0016 0016 0016 0016 0016 0016 0016 0016 0016 0016 0016 0016 0016 0041 0016 0016 0016 0016 0016 0016 0016 0016 0016 0016 0016 0016 0016 0016 0016 0016 0016 0041 0016 0041 0016 0041 0016 0041 0016 0041 0016 0041 0016 0041 0016 0689"
    
    print("Testing Pronto to Broadlink conversion...")
    print(f"Input: {test_pronto[:50]}...")
    
    broadlink = pronto_to_broadlink(test_pronto)
    if broadlink:
        print(f"Output: {broadlink[:50]}...")
        print("✓ Conversion successful")
    else:
        print("✗ Conversion failed")
