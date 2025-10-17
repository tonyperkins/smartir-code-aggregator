#!/usr/bin/env python3
"""
SmartIR Code Aggregator

Main script to aggregate IR codes from multiple sources and convert to SmartIR format.
"""

import argparse
import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from sources.fetch_irdb import IRDBFetcher
from sources.fetch_flipper import FlipperFetcher
from sources.fetch_smartir import SmartIRFetcher
from converters.irdb import IRDBConverter
from converters.flipper import FlipperConverter


def aggregate_irdb(output_dir: Path, category: str = "TV"):
    """
    Aggregate codes from IRDB.
    
    Args:
        output_dir: Output directory for converted files
        category: IRDB category to process
    """
    print("\n" + "=" * 60)
    print("AGGREGATING IRDB CODES")
    print("=" * 60)
    
    # Fetch IRDB
    fetcher = IRDBFetcher()
    repo_path = fetcher.fetch()
    
    # Get category path
    category_path = fetcher.get_category_path(category)
    if not category_path:
        print(f"✗ Category '{category}' not found")
        return
    
    # Convert
    converter = IRDBConverter()
    output_path = output_dir / "irdb" / category.lower()
    
    print(f"\nConverting {category} devices...")
    count = converter.batch_convert(category_path, output_path, category)
    
    converter.print_stats()
    print(f"\n✓ Converted {count} devices to {output_path}")


def aggregate_smartir(output_dir: Path):
    """
    Aggregate codes from SmartIR (original repository).
    
    Args:
        output_dir: Output directory for codes
    """
    print("\n" + "=" * 60)
    print("AGGREGATING SMARTIR CODES (ORIGINAL)")
    print("=" * 60)
    
    # Fetch SmartIR
    fetcher = SmartIRFetcher()
    repo_path = fetcher.fetch()
    
    # Copy codes directly (no conversion needed)
    print("\nCopying SmartIR codes (preserving original numbers 1-9999)...")
    output_path = output_dir / "smartir"
    
    stats = fetcher.copy_codes(output_path, preserve_numbers=True)
    
    print("\n" + "=" * 60)
    print("SmartIR Copy Statistics")
    print("=" * 60)
    print(f"Platforms: {stats['platforms']}")
    print(f"Codes copied: {stats['codes_copied']}")
    print(f"Errors: {stats['errors']}")
    print("=" * 60)
    
    print(f"\n✓ Copied {stats['codes_copied']} codes to {output_path}")


def aggregate_flipper(output_dir: Path, category: str = "TVs"):
    """
    Aggregate codes from Flipper IRDB.
    
    Args:
        output_dir: Output directory for converted files
        category: Flipper category to process
    """
    print("\n" + "=" * 60)
    print("AGGREGATING FLIPPER IRDB CODES")
    print("=" * 60)
    
    # Fetch Flipper IRDB
    fetcher = FlipperFetcher()
    repo_path = fetcher.fetch()
    
    # Get category path
    category_path = fetcher.get_category_path(category)
    if not category_path:
        print(f"✗ Category '{category}' not found")
        return
    
    # Convert
    converter = FlipperConverter()
    output_path = output_dir / "flipper" / category.lower()
    
    print(f"\nConverting {category} devices...")
    count = converter.batch_convert(category_path, output_path)
    
    converter.print_stats()
    print(f"\n✓ Converted {count} devices to {output_path}")


def main():
    """Main entry point"""
    parser = argparse.ArgumentParser(
        description="Aggregate IR codes from multiple sources to SmartIR format"
    )
    
    parser.add_argument(
        "--source",
        choices=["smartir", "irdb", "flipper", "all"],
        default="all",
        help="Source to aggregate from"
    )
    
    parser.add_argument(
        "--category",
        default="TV",
        help="Category to process (e.g., TV, Air_Conditioner, TVs, ACs)"
    )
    
    parser.add_argument(
        "--output",
        type=Path,
        default=Path("output/codes"),
        help="Output directory for converted files"
    )
    
    parser.add_argument(
        "--all",
        action="store_true",
        help="Process all categories from all sources"
    )
    
    args = parser.parse_args()
    
    # Create output directory
    args.output.mkdir(parents=True, exist_ok=True)
    
    print("=" * 60)
    print("SMARTIR CODE AGGREGATOR")
    print("=" * 60)
    print(f"Output directory: {args.output.absolute()}")
    
    if args.all:
        # Process all sources and categories
        print("\nProcessing ALL sources and categories...")
        
        # SmartIR (original codes)
        try:
            aggregate_smartir(args.output)
        except Exception as e:
            print(f"✗ Error processing SmartIR: {e}")
        
        # IRDB categories
        irdb_categories = ["TV", "DVD", "Air_Conditioner", "Fan"]
        for category in irdb_categories:
            try:
                aggregate_irdb(args.output, category)
            except Exception as e:
                print(f"✗ Error processing IRDB {category}: {e}")
        
        # Flipper categories
        flipper_categories = ["TVs", "ACs", "Fans"]
        for category in flipper_categories:
            try:
                aggregate_flipper(args.output, category)
            except Exception as e:
                print(f"✗ Error processing Flipper {category}: {e}")
    
    elif args.source == "smartir":
        aggregate_smartir(args.output)
    
    elif args.source == "irdb":
        aggregate_irdb(args.output, args.category)
    
    elif args.source == "flipper":
        aggregate_flipper(args.output, args.category)
    
    elif args.source == "all":
        aggregate_smartir(args.output)
        aggregate_irdb(args.output, args.category)
        
        # Map IRDB category to Flipper category
        flipper_category_map = {
            "TV": "TVs",
            "Air_Conditioner": "ACs",
            "Fan": "Fans"
        }
        flipper_category = flipper_category_map.get(args.category, args.category)
        aggregate_flipper(args.output, flipper_category)
    
    print("\n" + "=" * 60)
    print("AGGREGATION COMPLETE")
    print("=" * 60)
    print(f"\nAll codes saved to: {args.output.absolute()}")
    print("\nNext steps:")
    print("1. Review aggregated files in output directory")
    print("2. Move codes to repository root: mv output/codes/* codes/")
    print("3. Run generate_device_index.py to create index")
    print("4. Commit and push to repository")
    print("\nThis repository is now the single source of truth for all IR/RF codes!")


if __name__ == "__main__":
    main()
