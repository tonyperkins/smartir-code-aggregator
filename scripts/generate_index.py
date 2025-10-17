#!/usr/bin/env python3
"""
Generate device index from aggregated IR codes
This script scans the codes directory and creates an index file
for fast lookups.

Run this after aggregating codes from all sources.
"""

import json
from pathlib import Path
from typing import Dict, List, Any
from datetime import datetime

PLATFORMS = ["climate", "media_player", "fan", "light"]


def generate_index(codes_dir: Path) -> Dict[str, Any]:
    """
    Generate complete device index from local files.
    
    Args:
        codes_dir: Path to codes directory
        
    Returns:
        Index dictionary
    """
    index = {
        "version": "1.0.0",
        "last_updated": datetime.utcnow().isoformat() + "Z",
        "source": "https://github.com/tonyperkins/smartir-code-aggregator",
        "sources": {
            "smartir": "https://github.com/smartHomeHub/SmartIR",
            "irdb": "https://github.com/probonopd/irdb",
            "flipper": "https://github.com/Lucaslhm/Flipper-IRDB"
        },
        "platforms": {}
    }
    
    for platform in PLATFORMS:
        print(f"Processing {platform}...")
        platform_data = {
            "manufacturers": {},
            "total_devices": 0
        }
        
        # Check all source directories for this platform
        source_dirs = [
            codes_dir / "smartir" / platform,
            codes_dir / "irdb" / platform,
            codes_dir / "flipper" / platform.replace("_", "").lower()  # flipper uses different naming
        ]
        
        for source_dir in source_dirs:
            if not source_dir.exists():
                continue
            
            # Get all JSON files
            json_files = list(source_dir.glob("*.json"))
            
            for json_file in json_files:
                code = json_file.stem
                
                try:
                    # Read device metadata
                    with open(json_file, 'r', encoding='utf-8') as f:
                        device_data = json.load(f)
                    
                    manufacturer = device_data.get("manufacturer", "Unknown")
                    supported_models = device_data.get("supportedModels", [])
                    
                    # Initialize manufacturer if needed
                    if manufacturer not in platform_data["manufacturers"]:
                        platform_data["manufacturers"][manufacturer] = {
                            "models": []
                        }
                    
                    # Determine source from path
                    if "smartir" in str(source_dir):
                        source = "smartir"
                    elif "irdb" in str(source_dir):
                        source = "irdb"
                    else:
                        source = "flipper"
                    
                    # Add device entry
                    device_entry = {
                        "code": code,
                        "models": supported_models,
                        "source": source
                    }
                    
                    platform_data["manufacturers"][manufacturer]["models"].append(device_entry)
                    platform_data["total_devices"] += 1
                    
                    print(f"  ✓ {code}: {manufacturer} - {supported_models[0] if supported_models else 'Unknown'} ({source})")
                    
                except Exception as e:
                    print(f"  ✗ Error processing {json_file.name}: {e}")
                    continue
        
        # Sort manufacturers and models
        for manufacturer in platform_data["manufacturers"].values():
            manufacturer["models"].sort(key=lambda x: int(x["code"]) if x["code"].isdigit() else 0)
        
        index["platforms"][platform] = platform_data
        print(f"✓ {platform}: {platform_data['total_devices']} devices")
    
    return index


def main():
    """Main entry point"""
    print("Generating SmartIR device index from aggregated codes...")
    print("=" * 60)
    
    # Determine codes directory
    repo_root = Path(__file__).parent.parent
    codes_dir = repo_root / "output" / "codes"
    
    if not codes_dir.exists():
        print(f"✗ Codes directory not found: {codes_dir}")
        print("Run aggregate_all.py first to generate codes")
        return
    
    # Generate index
    index = generate_index(codes_dir)
    
    # Save to repository root
    output_file = repo_root / "smartir_device_index.json"
    with open(output_file, "w", encoding="utf-8") as f:
        json.dump(index, f, indent=2, ensure_ascii=False)
    
    print("=" * 60)
    print(f"✓ Index saved to: {output_file}")
    print(f"  Total platforms: {len(index['platforms'])}")
    
    total_devices = 0
    for platform, data in index["platforms"].items():
        count = data['total_devices']
        total_devices += count
        print(f"  - {platform}: {count} devices, {len(data['manufacturers'])} manufacturers")
    
    print(f"\n  TOTAL: {total_devices} devices across all platforms")
    print("\nNext step: Commit smartir_device_index.json to repository")


if __name__ == "__main__":
    main()
