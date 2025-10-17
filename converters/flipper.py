#!/usr/bin/env python3
"""
Flipper IRDB to SmartIR Converter

Converts Flipper Zero .ir files to SmartIR JSON format.
Flipper uses raw IR format which we convert to Broadlink Base64.

Source: https://github.com/Lucaslhm/Flipper-IRDB
"""

import json
import base64
import struct
from pathlib import Path
from typing import Dict, List, Optional


class FlipperConverter:
    """Convert Flipper .ir files to SmartIR JSON format"""
    
    # Map Flipper button names to SmartIR command names
    COMMAND_MAP = {
        # TV/Media Player
        'Power': 'power',
        'Vol_up': 'volume_up',
        'Vol_dn': 'volume_down',
        'Mute': 'mute',
        'Ch_next': 'channel_up',
        'Ch_prev': 'channel_down',
        'Source': 'source',
        'Menu': 'menu',
        'Up': 'up',
        'Down': 'down',
        'Left': 'left',
        'Right': 'right',
        'Ok': 'select',
        'Back': 'back',
        'Exit': 'exit',
        'Home': 'home',
        'Play': 'play',
        'Pause': 'pause',
        'Stop': 'stop',
        
        # Climate
        'Cool': 'cool',
        'Heat': 'heat',
        'Auto': 'auto',
        'Dry': 'dry',
        'Fan': 'fan_only',
        'Temp_up': 'temp_up',
        'Temp_dn': 'temp_down',
        'Speed': 'fan_speed',
        'Swing': 'swing',
    }
    
    def __init__(self):
        self.stats = {
            'processed': 0,
            'converted': 0,
            'failed': 0
        }
    
    def parse_ir_file(self, ir_path: Path) -> Dict:
        """
        Parse Flipper .ir file.
        
        Flipper IR format:
        Filetype: IR signals file
        Version: 1
        #
        name: Power
        type: raw
        frequency: 38000
        duty_cycle: 0.330000
        data: 9024 4512 564 564 564 1692 564 564 564...
        
        Args:
            ir_path: Path to .ir file
            
        Returns:
            Dictionary with device info and commands
        """
        device_info = {
            'commands': {},
            'frequency': 38000,
            'protocol': 'raw'
        }
        
        current_button = None
        
        try:
            with open(ir_path, 'r', encoding='utf-8') as f:
                for line in f:
                    line = line.strip()
                    
                    if line.startswith('name:'):
                        current_button = line.split(':', 1)[1].strip()
                    elif line.startswith('type:'):
                        device_info['protocol'] = line.split(':', 1)[1].strip()
                    elif line.startswith('frequency:'):
                        device_info['frequency'] = int(line.split(':', 1)[1].strip())
                    elif line.startswith('data:') and current_button:
                        # Parse raw timing data
                        data_str = line.split(':', 1)[1].strip()
                        timings = [int(x) for x in data_str.split()]
                        device_info['commands'][current_button] = timings
                        
        except Exception as e:
            print(f"Error parsing {ir_path}: {e}")
            
        return device_info
    
    def raw_to_broadlink(self, timings: List[int], frequency: int = 38000) -> Optional[str]:
        """
        Convert Flipper raw timings to Broadlink Base64.
        
        Flipper uses microseconds, Broadlink uses 32.84us units.
        
        Args:
            timings: List of timing values in microseconds
            frequency: IR frequency in Hz
            
        Returns:
            Broadlink Base64 string or None if conversion fails
        """
        try:
            # Build Broadlink packet
            packet = bytearray([0x26, 0x00])  # IR command type
            packet.extend([0x01, 0x00])  # Repeat count
            
            # Convert timings to Broadlink units (32.84us per unit)
            for timing_us in timings:
                broadlink_units = int(timing_us / 32.84)
                
                # Clamp to 16-bit range
                if broadlink_units > 0xFFFF:
                    broadlink_units = 0xFFFF
                elif broadlink_units < 0:
                    broadlink_units = 0
                
                # Little-endian 16-bit
                packet.extend(struct.pack('<H', broadlink_units))
            
            # Add terminator
            packet.extend([0x0d, 0x05])
            
            # Encode to Base64
            return base64.b64encode(packet).decode('utf-8')
            
        except Exception as e:
            print(f"Error converting raw timings: {e}")
            return None
    
    def convert_device(self, ir_path: Path, manufacturer: str = None, 
                      model: str = None) -> Optional[Dict]:
        """
        Convert Flipper .ir file to SmartIR format.
        
        Args:
            ir_path: Path to .ir file
            manufacturer: Device manufacturer (extracted from path if None)
            model: Device model (extracted from filename if None)
            
        Returns:
            SmartIR JSON dictionary or None if conversion fails
        """
        self.stats['processed'] += 1
        
        # Extract manufacturer and model from path if not provided
        if not manufacturer or not model:
            # Typical structure: Flipper-IRDB/TVs/Samsung/Samsung_UE40F6500.ir
            parts = ir_path.parts
            if len(parts) >= 2:
                manufacturer = manufacturer or parts[-2]
                model = model or ir_path.stem.replace(f"{parts[-2]}_", "")
            else:
                manufacturer = manufacturer or "Unknown"
                model = model or ir_path.stem
        
        # Parse .ir file
        device_info = self.parse_ir_file(ir_path)
        
        if not device_info['commands']:
            self.stats['failed'] += 1
            return None
        
        # Convert commands
        smartir_commands = {}
        conversion_failures = 0
        
        for button_name, timings in device_info['commands'].items():
            # Map command name
            cmd_name = self._map_command_name(button_name)
            
            # Convert to Broadlink
            broadlink_code = self.raw_to_broadlink(timings, device_info['frequency'])
            
            if broadlink_code:
                smartir_commands[cmd_name] = broadlink_code
            else:
                conversion_failures += 1
        
        # Check if we have enough commands
        if len(smartir_commands) < 3:
            self.stats['failed'] += 1
            print(f"  ✗ {manufacturer} {model}: Too few commands ({len(smartir_commands)})")
            return None
        
        # Build SmartIR JSON
        smartir_json = {
            "manufacturer": manufacturer,
            "supportedModels": [model],
            "supportedController": "Broadlink",
            "commandsEncoding": "Base64",
            "commands": smartir_commands
        }
        
        self.stats['converted'] += 1
        success_rate = len(smartir_commands) / (len(smartir_commands) + conversion_failures) * 100
        print(f"  ✓ {manufacturer} {model}: {len(smartir_commands)} commands ({success_rate:.0f}% success)")
        
        return smartir_json
    
    def _map_command_name(self, flipper_name: str) -> str:
        """Map Flipper command name to SmartIR command name"""
        # Direct mapping
        if flipper_name in self.COMMAND_MAP:
            return self.COMMAND_MAP[flipper_name]
        
        # Sanitize name
        return flipper_name.lower().replace(' ', '_').replace('-', '_')
    
    def batch_convert(self, flipper_dir: Path, output_dir: Path) -> int:
        """
        Convert all .ir files in Flipper directory.
        
        Args:
            flipper_dir: Path to Flipper IRDB directory
            output_dir: Path to output directory
            
        Returns:
            Number of devices converted
        """
        output_dir.mkdir(parents=True, exist_ok=True)
        
        ir_files = list(flipper_dir.glob('**/*.ir'))
        print(f"Found {len(ir_files)} .ir files in {flipper_dir}")
        
        for ir_file in ir_files:
            # Convert device
            smartir_json = self.convert_device(ir_file)
            
            if smartir_json:
                # Save to output directory
                manufacturer = smartir_json['manufacturer']
                model = smartir_json['supportedModels'][0]
                output_file = output_dir / f"{manufacturer}_{model}.json"
                
                with open(output_file, 'w', encoding='utf-8') as f:
                    json.dump(smartir_json, f, indent=2, ensure_ascii=False)
        
        return self.stats['converted']
    
    def print_stats(self):
        """Print conversion statistics"""
        print("\n" + "=" * 60)
        print("Flipper Conversion Statistics")
        print("=" * 60)
        print(f"Processed: {self.stats['processed']}")
        print(f"Converted: {self.stats['converted']}")
        print(f"Failed:    {self.stats['failed']}")
        if self.stats['processed'] > 0:
            success_rate = self.stats['converted'] / self.stats['processed'] * 100
            print(f"Success:   {success_rate:.1f}%")
        print("=" * 60)


if __name__ == "__main__":
    # Test conversion
    converter = FlipperConverter()
    print("Flipper to SmartIR Converter initialized")
    print("Use batch_convert() to process Flipper IRDB directory")
