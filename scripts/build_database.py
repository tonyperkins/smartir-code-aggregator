#!/usr/bin/env python3
"""
Build Complete IR/RF Device Database

Master script that executes the entire workflow:
1. Aggregate codes from all sources (SmartIR, IRDB, Flipper)
2. Generate unified device index
3. Organize codes into repository structure
4. Generate statistics

This creates the single source of truth for all IR/RF codes.
"""

import argparse
import shutil
import sys
from pathlib import Path
from datetime import datetime

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from sources.fetch_smartir import SmartIRFetcher
from sources.fetch_irdb import IRDBFetcher
from sources.fetch_flipper import FlipperFetcher
from converters.irdb import IRDBConverter
from converters.flipper import FlipperConverter


def print_header(title: str):
    """Print formatted header"""
    print("\n" + "=" * 70)
    print(f"  {title}")
    print("=" * 70)


def print_step(step: int, total: int, description: str):
    """Print step progress"""
    print(f"\n[{step}/{total}] {description}")
    print("-" * 70)


def aggregate_smartir(output_dir: Path) -> dict:
    """Aggregate SmartIR codes"""
    print_step(1, 5, "Aggregating SmartIR codes (original)")
    
    fetcher = SmartIRFetcher()
    fetcher.fetch()
    
    output_path = output_dir / "smartir"
    stats = fetcher.copy_codes(output_path, preserve_numbers=True)
    
    print(f"✓ Copied {stats['codes_copied']} codes from SmartIR")
    return stats


def aggregate_irdb_DISABLED(output_dir: Path, device_types: list = None) -> dict:
    """Aggregate IRDB codes by scanning manufacturer subdirectories"""
    print_step(2, 5, "Aggregating IRDB codes (converted from Pronto)")
    
    fetcher = IRDBFetcher()
    repo_path = fetcher.fetch()
    
    print(f"  IRDB repo path: {repo_path}")
    print(f"  Repo exists: {repo_path.exists()}")
    
    # Device type mappings (IRDB folder name -> SmartIR platform)
    device_type_map = {
        'TV': 'media_player',
        'DVD': 'media_player',
        'DVD Player': 'media_player',
        'Blu-ray': 'media_player',
        'CD Player': 'media_player',
        'Receiver': 'media_player',
        'Amplifier': 'media_player',
        'Air Conditioner': 'climate',
        'Fan': 'fan',
    }
    
    if device_types is None:
        device_types = list(device_type_map.keys())
    
    total_converted = 0
    total_failed = 0
    total_processed = 0
    
    print(f"\n  Scanning manufacturers for device types: {', '.join(device_types[:5])}...")
    
    # IRDB has a 'codes' subdirectory
    codes_dir = repo_path / "codes"
    print(f"  Codes dir: {codes_dir}")
    print(f"  Codes dir exists: {codes_dir.exists()}")
    
    if not codes_dir.exists():
        print(f"  ✗ No 'codes' directory found in IRDB")
        return {'converted': 0, 'failed': 0, 'processed': 0}
    
    # Scan all manufacturer directories
    manufacturers = [d for d in codes_dir.iterdir() if d.is_dir() and not d.name.startswith('.')]
    
    print(f"  Found {len(manufacturers)} manufacturers")
    if len(manufacturers) > 0:
        print(f"  First few: {', '.join([m.name for m in manufacturers[:5]])}")
    
    for manufacturer in manufacturers:
        # Check each device type subdirectory
        for device_type in device_types:
            device_dir = manufacturer / device_type
            if not device_dir.exists():
                continue
            
            # Get platform for output
            platform = device_type_map.get(device_type, 'media_player')
            output_path = output_dir / "irdb" / platform
            output_path.mkdir(parents=True, exist_ok=True)
            
            try:
                # Convert all CSV files in this device type directory
                csv_files = list(device_dir.glob('*.csv'))
                if not csv_files:
                    continue
                
                # Debug: Show what we found
                if total_processed == 0:  # First batch
                    print(f"    Found {len(csv_files)} CSV files in {manufacturer.name}/{device_type}")
                
                total_processed += len(csv_files)
                
                for csv_file in csv_files:
                    model = csv_file.stem
                    
                    try:
                        converter = IRDBConverter()
                        smartir_json = converter.convert_device(
                            manufacturer.name,
                            model,
                            csv_file,
                            device_type
                        )
                        
                        if smartir_json:
                            # Save to output
                            output_file = output_path / f"{manufacturer.name}_{model}.json"
                            
                            import json
                            with open(output_file, 'w', encoding='utf-8') as f:
                                json.dump(smartir_json, f, indent=2, ensure_ascii=False)
                            
                            total_converted += 1
                            if total_converted <= 5:  # Show first few successes
                                print(f"    ✓ {manufacturer.name}/{device_type}/{model}")
                        else:
                            total_failed += 1
                            if total_failed <= 3:  # Show first few failures
                                print(f"    ✗ {manufacturer.name}/{device_type}/{model}: No commands converted")
                    except Exception as e:
                        total_failed += 1
                        if total_failed <= 3:
                            print(f"    ✗ {manufacturer.name}/{device_type}/{model}: {e}")
                
            except Exception as e:
                print(f"    ✗ Error processing {manufacturer.name}/{device_type}: {e}")
                total_failed += 1
                continue
    
    print(f"\n  Processed {total_processed} CSV files")
    print(f"  → Converted: {total_converted}")
    print(f"  → Failed: {total_failed}")
    
    print(f"\n✓ IRDB aggregation complete")
    return {'converted': total_converted, 'failed': total_failed, 'processed': total_processed}


def aggregate_flipper(output_dir: Path, categories: list = None) -> dict:
    """Aggregate Flipper codes"""
    print_step(3, 5, "Aggregating Flipper IRDB codes (converted from raw)")
    
    if categories is None:
        categories = ["TVs", "ACs", "Fans"]
    
    fetcher = FlipperFetcher()
    fetcher.fetch()
    
    total_converted = 0
    total_failed = 0
    
    for category in categories:
        category_path = fetcher.get_category_path(category)
        if not category_path:
            print(f"  ⚠️  Category '{category}' not found in Flipper IRDB, skipping...")
            continue
        
        converter = FlipperConverter()
        output_path = output_dir / "flipper" / category.lower()
        
        print(f"\n  Converting {category}...")
        try:
            count = converter.batch_convert(category_path, output_path)
            total_converted += converter.stats['converted']
            total_failed += converter.stats['failed']
            print(f"    → {converter.stats['converted']} converted, {converter.stats['failed']} failed")
        except Exception as e:
            print(f"    ✗ Error: {e}")
            continue
    
    print(f"\n✓ Converted {total_converted} codes from Flipper ({total_failed} failed)")
    return {'converted': total_converted, 'failed': total_failed}


def organize_codes(output_dir: Path, repo_root: Path) -> dict:
    """Organize codes into repository structure"""
    print_step(4, 5, "Organizing codes into repository structure")
    
    codes_dir = repo_root / "codes"
    codes_dir.mkdir(exist_ok=True)
    
    stats = {
        'platforms': 0,
        'total_codes': 0
    }
    
    platforms = ["climate", "media_player", "fan", "light"]
    
    for platform in platforms:
        platform_dir = codes_dir / platform
        platform_dir.mkdir(exist_ok=True)
        
        codes_copied = 0
        
        # Copy from all sources
        source_dirs = [
            output_dir / "smartir" / platform,
            output_dir / "irdb" / platform,
            output_dir / "flipper" / platform.replace("_", "").lower()
        ]
        
        for source_dir in source_dirs:
            if not source_dir.exists():
                continue
            
            for json_file in source_dir.glob("*.json"):
                dest_file = platform_dir / json_file.name
                shutil.copy2(json_file, dest_file)
                codes_copied += 1
        
        if codes_copied > 0:
            stats['platforms'] += 1
            stats['total_codes'] += codes_copied
            print(f"  ✓ {platform}: {codes_copied} codes")
    
    print(f"\n✓ Organized {stats['total_codes']} codes into {stats['platforms']} platforms")
    return stats


def generate_index(repo_root: Path) -> dict:
    """Generate device index"""
    print_step(5, 5, "Generating unified device index")
    
    import json
    
    codes_dir = repo_root / "codes"
    platforms = ["climate", "media_player", "fan", "light"]
    
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
    
    total_devices = 0
    
    for platform in platforms:
        platform_dir = codes_dir / platform
        if not platform_dir.exists():
            continue
        
        platform_data = {
            "manufacturers": {},
            "total_devices": 0
        }
        
        for json_file in platform_dir.glob("*.json"):
            try:
                with open(json_file, 'r', encoding='utf-8') as f:
                    device_data = json.load(f)
                
                manufacturer = device_data.get("manufacturer", "Unknown")
                supported_models = device_data.get("supportedModels", [])
                code = json_file.stem
                
                if manufacturer not in platform_data["manufacturers"]:
                    platform_data["manufacturers"][manufacturer] = {"models": []}
                
                platform_data["manufacturers"][manufacturer]["models"].append({
                    "code": code,
                    "models": supported_models
                })
                
                platform_data["total_devices"] += 1
                
            except Exception as e:
                print(f"  ✗ Error processing {json_file.name}: {e}")
                continue
        
        # Sort
        for manufacturer in platform_data["manufacturers"].values():
            manufacturer["models"].sort(key=lambda x: int(x["code"]) if x["code"].isdigit() else 0)
        
        index["platforms"][platform] = platform_data
        total_devices += platform_data["total_devices"]
        print(f"  ✓ {platform}: {platform_data['total_devices']} devices, {len(platform_data['manufacturers'])} manufacturers")
    
    # Save index
    index_file = repo_root / "smartir_device_index.json"
    with open(index_file, "w", encoding="utf-8") as f:
        json.dump(index, f, indent=2, ensure_ascii=False)
    
    print(f"\n✓ Generated index with {total_devices} total devices")
    print(f"  Saved to: {index_file}")
    
    return {'total_devices': total_devices, 'platforms': len(index["platforms"])}


def print_summary(stats: dict):
    """Print final summary"""
    print_header("BUILD COMPLETE - DATABASE SUMMARY")
    
    print(f"\n📊 Statistics:")
    print(f"  • SmartIR codes:     {stats['smartir']['codes_copied']}")
    print(f"  • IRDB converted:    {stats['irdb']['converted']}")
    print(f"  • Flipper converted: {stats['flipper']['converted']}")
    print(f"  • Total devices:     {stats['index']['total_devices']}")
    print(f"  • Platforms:         {stats['index']['platforms']}")
    
    print(f"\n📁 Output:")
    print(f"  • Codes directory:   codes/")
    print(f"  • Device index:      smartir_device_index.json")
    
    print(f"\n✅ Success! The database is ready.")
    print(f"\nNext steps:")
    print(f"  1. Review codes in codes/ directory")
    print(f"  2. Commit to repository:")
    print(f"     git add codes/ smartir_device_index.json")
    print(f"     git commit -m 'Update device database'")
    print(f"     git push")
    print(f"  3. Update Broadlink Manager to use this repository")
    
    print("\n" + "=" * 70)


def main():
    """Main entry point"""
    parser = argparse.ArgumentParser(
        description="Build complete IR/RF device database from all sources"
    )
    
    parser.add_argument(
        "--skip-smartir",
        action="store_true",
        help="Skip SmartIR aggregation"
    )
    
    parser.add_argument(
        "--skip-irdb",
        action="store_true",
        help="Skip IRDB aggregation"
    )
    
    parser.add_argument(
        "--skip-flipper",
        action="store_true",
        help="Skip Flipper aggregation"
    )
    
    parser.add_argument(
        "--clean",
        action="store_true",
        help="Clean output directory before building"
    )
    
    args = parser.parse_args()
    
    # Setup paths
    repo_root = Path(__file__).parent.parent
    output_dir = repo_root / "output" / "codes"
    
    # Clean if requested
    if args.clean and output_dir.exists():
        print("🧹 Cleaning output directory...")
        shutil.rmtree(output_dir)
    
    output_dir.mkdir(parents=True, exist_ok=True)
    
    # Print header
    print_header("SMARTIR CODE AGGREGATOR - DATABASE BUILD")
    print(f"\nRepository: {repo_root}")
    print(f"Output:     {output_dir}")
    print(f"Started:    {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    # Track statistics
    stats = {}
    
    # Execute workflow
    try:
        if not args.skip_smartir:
            stats['smartir'] = aggregate_smartir(output_dir)
        else:
            print_step(1, 5, "Skipping SmartIR aggregation")
            stats['smartir'] = {'codes_copied': 0}
        
        # IRDB disabled - uses protocol definitions, not Pronto codes
        # Would require protocol encoder (IrpTransmogrifier)
        print_step(2, 5, "Skipping IRDB (not supported - uses protocol definitions)")
        stats['irdb'] = {'converted': 0, 'failed': 0}
        
        if not args.skip_flipper:
            stats['flipper'] = aggregate_flipper(output_dir)
        else:
            print_step(3, 5, "Skipping Flipper aggregation")
            stats['flipper'] = {'converted': 0, 'failed': 0}
        
        stats['organize'] = organize_codes(output_dir, repo_root)
        stats['index'] = generate_index(repo_root)
        
        # Print summary
        print_summary(stats)
        
    except KeyboardInterrupt:
        print("\n\n⚠️  Build interrupted by user")
        sys.exit(1)
    except Exception as e:
        print(f"\n\n❌ Build failed: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()
