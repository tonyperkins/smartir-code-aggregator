#!/usr/bin/env python3
"""
IRDB to SmartIR Converter

Converts IRDB CSV files to SmartIR JSON format.
IRDB uses Pronto Hex format which we convert to Broadlink Base64.

Source: https://github.com/probonopd/irdb
"""

import json
import csv
from pathlib import Path
from typing import Dict, List, Optional
from .pronto import pronto_to_broadlink, validate_pronto


class IRDBConverter:
    """Convert IRDB CSV files to SmartIR JSON format"""
    
    # Map IRDB categories to SmartIR platforms
    CATEGORY_MAP = {
        'TV': 'media_player',
        'DVD': 'media_player',
        'Blu-ray': 'media_player',
        'Receiver': 'media_player',
        'Amplifier': 'media_player',
        'CD': 'media_player',
        'Air Conditioner': 'climate',
        'Fan': 'fan',
        'Light': 'light'
    }
    
    # Map IRDB button names to SmartIR command names
    COMMAND_MAP = {
        # TV/Media Player
        'Power': 'power',
        'Power On': 'turn_on',
        'Power Off': 'turn_off',
        'Volume Up': 'volume_up',
        'Volume Down': 'volume_down',
        'Mute': 'mute',
        'Channel Up': 'channel_up',
        'Channel Down': 'channel_down',
        'Input': 'source',
        'Menu': 'menu',
        'Up': 'up',
        'Down': 'down',
        'Left': 'left',
        'Right': 'right',
        'OK': 'select',
        'Enter': 'select',
        'Back': 'back',
        'Exit': 'exit',
        'Home': 'home',
        'Play': 'play',
        'Pause': 'pause',
        'Stop': 'stop',
        'Record': 'record',
        'Rewind': 'rewind',
        'Fast Forward': 'fast_forward',
        
        # Climate
        'Cool': 'cool',
        'Heat': 'heat',
        'Auto': 'auto',
        'Dry': 'dry',
        'Fan': 'fan_only',
        'Temp Up': 'temp_up',
        'Temp Down': 'temp_down',
        'Fan Speed': 'fan_speed',
        'Swing': 'swing',
        'Timer': 'timer',
        
        # Numbers
        '0': 'num_0',
        '1': 'num_1',
        '2': 'num_2',
        '3': 'num_3',
        '4': 'num_4',
        '5': 'num_5',
        '6': 'num_6',
        '7': 'num_7',
        '8': 'num_8',
        '9': 'num_9',
    }
    
    def __init__(self):
        self.stats = {
            'processed': 0,
            'converted': 0,
            'failed': 0,
            'skipped': 0
        }
    
    def parse_csv(self, csv_path: Path) -> List[Dict]:
        """
        Parse IRDB CSV file.
        
        IRDB CSV format:
        functionname,protocol,device,subdevice,function,hex,misc
        
        Args:
            csv_path: Path to CSV file
            
        Returns:
            List of command dictionaries
        """
        commands = []
        
        try:
            with open(csv_path, 'r', encoding='utf-8') as f:
                reader = csv.DictReader(f)
                for row in reader:
                    if 'hex' in row and row['hex']:
                        commands.append({
                            'name': row.get('functionname', ''),
                            'protocol': row.get('protocol', ''),
                            'pronto': row.get('hex', ''),
                            'device': row.get('device', ''),
                            'subdevice': row.get('subdevice', '')
                        })
        except Exception as e:
            print(f"Error parsing CSV {csv_path}: {e}")
            
        return commands
    
    def convert_device(self, manufacturer: str, model: str, csv_path: Path, 
                      category: str = 'TV') -> Optional[Dict]:
        """
        Convert IRDB device to SmartIR format.
        
        Args:
            manufacturer: Device manufacturer
            model: Device model
            csv_path: Path to IRDB CSV file
            category: Device category (TV, DVD, Air Conditioner, etc.)
            
        Returns:
            SmartIR JSON dictionary or None if conversion fails
        """
        self.stats['processed'] += 1
        
        # Parse CSV
        commands = self.parse_csv(csv_path)
        if not commands:
            self.stats['skipped'] += 1
            return None
        
        # Convert commands
        smartir_commands = {}
        conversion_failures = 0
        
        for cmd in commands:
            # Map command name
            cmd_name = self._map_command_name(cmd['name'])
            if not cmd_name:
                continue
            
            # Validate and convert Pronto code
            if not validate_pronto(cmd['pronto']):
                conversion_failures += 1
                continue
                
            broadlink_code = pronto_to_broadlink(cmd['pronto'])
            if broadlink_code:
                smartir_commands[cmd_name] = broadlink_code
            else:
                conversion_failures += 1
        
        # Check if we have enough commands
        if len(smartir_commands) < 3:  # Minimum viable device
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
        
        # Add platform-specific fields
        platform = self.CATEGORY_MAP.get(category, 'media_player')
        if platform == 'climate':
            smartir_json["minTemperature"] = 16
            smartir_json["maxTemperature"] = 30
            smartir_json["precision"] = 1
        
        self.stats['converted'] += 1
        success_rate = len(smartir_commands) / (len(smartir_commands) + conversion_failures) * 100
        print(f"  ✓ {manufacturer} {model}: {len(smartir_commands)} commands ({success_rate:.0f}% success)")
        
        return smartir_json
    
    def _map_command_name(self, irdb_name: str) -> Optional[str]:
        """Map IRDB command name to SmartIR command name"""
        # Direct mapping
        if irdb_name in self.COMMAND_MAP:
            return self.COMMAND_MAP[irdb_name]
        
        # Fuzzy matching
        irdb_lower = irdb_name.lower().replace(' ', '_')
        for irdb_key, smartir_name in self.COMMAND_MAP.items():
            if irdb_key.lower().replace(' ', '_') == irdb_lower:
                return smartir_name
        
        # Use original name (sanitized)
        return irdb_lower.replace('-', '_')
    
    def batch_convert(self, irdb_dir: Path, output_dir: Path, 
                     category: str = 'TV') -> int:
        """
        Convert all CSV files in IRDB directory.
        
        Args:
            irdb_dir: Path to IRDB category directory
            output_dir: Path to output directory
            category: Device category
            
        Returns:
            Number of devices converted
        """
        output_dir.mkdir(parents=True, exist_ok=True)
        
        csv_files = list(irdb_dir.glob('**/*.csv'))
        print(f"Found {len(csv_files)} CSV files in {irdb_dir}")
        
        for csv_file in csv_files:
            # Extract manufacturer and model from path
            # Typical structure: irdb/codes/TV/Samsung/UE40F6500.csv
            parts = csv_file.relative_to(irdb_dir).parts
            if len(parts) >= 2:
                manufacturer = parts[0]
                model = csv_file.stem
            else:
                manufacturer = "Unknown"
                model = csv_file.stem
            
            # Convert device
            smartir_json = self.convert_device(manufacturer, model, csv_file, category)
            
            if smartir_json:
                # Save to output directory
                output_file = output_dir / f"{manufacturer}_{model}.json"
                with open(output_file, 'w', encoding='utf-8') as f:
                    json.dump(smartir_json, f, indent=2, ensure_ascii=False)
        
        return self.stats['converted']
    
    def print_stats(self):
        """Print conversion statistics"""
        print("\n" + "=" * 60)
        print("IRDB Conversion Statistics")
        print("=" * 60)
        print(f"Processed: {self.stats['processed']}")
        print(f"Converted: {self.stats['converted']}")
        print(f"Failed:    {self.stats['failed']}")
        print(f"Skipped:   {self.stats['skipped']}")
        if self.stats['processed'] > 0:
            success_rate = self.stats['converted'] / self.stats['processed'] * 100
            print(f"Success:   {success_rate:.1f}%")
        print("=" * 60)


if __name__ == "__main__":
    # Test conversion
    converter = IRDBConverter()
    print("IRDB to SmartIR Converter initialized")
    print("Use batch_convert() to process IRDB directory")
