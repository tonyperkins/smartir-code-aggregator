#!/usr/bin/env python3
"""
SmartIR JSON Validator

Validates SmartIR JSON files for correctness and completeness.
"""

import json
import base64
from pathlib import Path
from typing import Dict, List, Tuple, Optional


class SmartIRValidator:
    """Validate SmartIR JSON files"""
    
    # Required fields for all platforms
    REQUIRED_FIELDS = [
        "manufacturer",
        "supportedModels",
        "supportedController",
        "commandsEncoding",
        "commands"
    ]
    
    # Platform-specific required commands
    PLATFORM_COMMANDS = {
        "media_player": ["power"],  # Minimum
        "climate": ["off"],  # Minimum
        "fan": ["off"],  # Minimum
        "light": ["off"]  # Minimum
    }
    
    # Climate-specific fields
    CLIMATE_FIELDS = [
        "minTemperature",
        "maxTemperature",
        "precision"
    ]
    
    def __init__(self):
        self.errors = []
        self.warnings = []
    
    def validate_file(self, json_path: Path, platform: str = None) -> Tuple[bool, List[str], List[str]]:
        """
        Validate SmartIR JSON file.
        
        Args:
            json_path: Path to JSON file
            platform: Platform type (media_player, climate, fan, light)
            
        Returns:
            Tuple of (is_valid, errors, warnings)
        """
        self.errors = []
        self.warnings = []
        
        # Load JSON
        try:
            with open(json_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
        except json.JSONDecodeError as e:
            self.errors.append(f"Invalid JSON: {e}")
            return False, self.errors, self.warnings
        except Exception as e:
            self.errors.append(f"Error reading file: {e}")
            return False, self.errors, self.warnings
        
        # Validate structure
        self._validate_structure(data)
        
        # Validate commands
        self._validate_commands(data, platform)
        
        # Validate platform-specific fields
        if platform == "climate":
            self._validate_climate(data)
        
        # Validate codes
        self._validate_codes(data)
        
        is_valid = len(self.errors) == 0
        return is_valid, self.errors, self.warnings
    
    def _validate_structure(self, data: Dict):
        """Validate basic structure"""
        # Check required fields
        for field in self.REQUIRED_FIELDS:
            if field not in data:
                self.errors.append(f"Missing required field: {field}")
        
        # Validate manufacturer
        if "manufacturer" in data:
            if not isinstance(data["manufacturer"], str) or not data["manufacturer"]:
                self.errors.append("manufacturer must be a non-empty string")
        
        # Validate supportedModels
        if "supportedModels" in data:
            if not isinstance(data["supportedModels"], list):
                self.errors.append("supportedModels must be a list")
            elif len(data["supportedModels"]) == 0:
                self.warnings.append("supportedModels is empty")
        
        # Validate supportedController
        if "supportedController" in data:
            if data["supportedController"] not in ["Broadlink", "Xiaomi", "MQTT", "LOOKin", "ESPHome"]:
                self.warnings.append(f"Unusual controller: {data['supportedController']}")
        
        # Validate commandsEncoding
        if "commandsEncoding" in data:
            if data["commandsEncoding"] not in ["Base64", "Hex", "Pronto"]:
                self.errors.append(f"Invalid commandsEncoding: {data['commandsEncoding']}")
    
    def _validate_commands(self, data: Dict, platform: Optional[str]):
        """Validate commands section"""
        if "commands" not in data:
            return
        
        commands = data["commands"]
        
        if not isinstance(commands, dict):
            self.errors.append("commands must be a dictionary")
            return
        
        if len(commands) == 0:
            self.errors.append("commands dictionary is empty")
            return
        
        # Check platform-specific required commands
        if platform and platform in self.PLATFORM_COMMANDS:
            required_commands = self.PLATFORM_COMMANDS[platform]
            for cmd in required_commands:
                if cmd not in commands:
                    self.warnings.append(f"Missing recommended command: {cmd}")
        
        # Validate command values
        for cmd_name, cmd_value in commands.items():
            if not isinstance(cmd_value, str):
                self.errors.append(f"Command '{cmd_name}' value must be a string")
            elif not cmd_value:
                self.errors.append(f"Command '{cmd_name}' has empty value")
    
    def _validate_climate(self, data: Dict):
        """Validate climate-specific fields"""
        for field in self.CLIMATE_FIELDS:
            if field not in data:
                self.warnings.append(f"Missing climate field: {field}")
        
        # Validate temperature range
        if "minTemperature" in data and "maxTemperature" in data:
            min_temp = data["minTemperature"]
            max_temp = data["maxTemperature"]
            
            if not isinstance(min_temp, (int, float)):
                self.errors.append("minTemperature must be a number")
            if not isinstance(max_temp, (int, float)):
                self.errors.append("maxTemperature must be a number")
            
            if isinstance(min_temp, (int, float)) and isinstance(max_temp, (int, float)):
                if min_temp >= max_temp:
                    self.errors.append("minTemperature must be less than maxTemperature")
        
        # Validate precision
        if "precision" in data:
            if data["precision"] not in [0.1, 0.5, 1, 1.0]:
                self.warnings.append(f"Unusual precision value: {data['precision']}")
    
    def _validate_codes(self, data: Dict):
        """Validate IR codes"""
        if "commands" not in data or "commandsEncoding" not in data:
            return
        
        encoding = data["commandsEncoding"]
        commands = data["commands"]
        
        for cmd_name, cmd_value in commands.items():
            if encoding == "Base64":
                if not self._is_valid_base64(cmd_value):
                    self.errors.append(f"Command '{cmd_name}' has invalid Base64 encoding")
            elif encoding == "Hex":
                if not self._is_valid_hex(cmd_value):
                    self.errors.append(f"Command '{cmd_name}' has invalid Hex encoding")
    
    def _is_valid_base64(self, s: str) -> bool:
        """Check if string is valid Base64"""
        try:
            base64.b64decode(s, validate=True)
            return True
        except:
            return False
    
    def _is_valid_hex(self, s: str) -> bool:
        """Check if string is valid Hex"""
        try:
            bytes.fromhex(s.replace(" ", ""))
            return True
        except:
            return False
    
    def batch_validate(self, directory: Path, platform: str = None) -> Dict:
        """
        Validate all JSON files in directory.
        
        Args:
            directory: Directory containing JSON files
            platform: Platform type
            
        Returns:
            Dictionary with validation results
        """
        results = {
            'total': 0,
            'valid': 0,
            'invalid': 0,
            'files': []
        }
        
        json_files = list(directory.glob('**/*.json'))
        results['total'] = len(json_files)
        
        for json_file in json_files:
            is_valid, errors, warnings = self.validate_file(json_file, platform)
            
            results['files'].append({
                'file': str(json_file),
                'valid': is_valid,
                'errors': errors,
                'warnings': warnings
            })
            
            if is_valid:
                results['valid'] += 1
            else:
                results['invalid'] += 1
        
        return results
    
    def print_results(self, results: Dict):
        """Print validation results"""
        print("\n" + "=" * 60)
        print("VALIDATION RESULTS")
        print("=" * 60)
        print(f"Total files: {results['total']}")
        print(f"Valid: {results['valid']}")
        print(f"Invalid: {results['invalid']}")
        
        if results['invalid'] > 0:
            print("\nInvalid files:")
            for file_result in results['files']:
                if not file_result['valid']:
                    print(f"\n  {file_result['file']}")
                    for error in file_result['errors']:
                        print(f"    ✗ {error}")
        
        print("=" * 60)


if __name__ == "__main__":
    # Test validator
    validator = SmartIRValidator()
    print("SmartIR Validator initialized")
    print("Use validate_file() or batch_validate() to validate JSON files")
