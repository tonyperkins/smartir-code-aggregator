#!/usr/bin/env python3
"""
Check IRDB CSV File Structure

Examine actual CSV files to see if we can determine device categories.
"""

import csv
import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from sources.fetch_irdb import IRDBFetcher


def examine_csv(csv_path: Path):
    """Examine a CSV file structure"""
    print(f"\n{'='*70}")
    print(f"File: {csv_path.name}")
    print(f"Path: {csv_path.relative_to(csv_path.parent.parent.parent)}")
    print('='*70)
    
    try:
        with open(csv_path, 'r', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            
            # Print headers
            print("\nHeaders:")
            if reader.fieldnames:
                for i, header in enumerate(reader.fieldnames, 1):
                    print(f"  {i}. {header}")
            
            # Print first few rows
            print("\nFirst 3 rows:")
            for i, row in enumerate(reader, 1):
                if i > 3:
                    break
                print(f"\n  Row {i}:")
                for key, value in row.items():
                    if value:  # Only show non-empty values
                        print(f"    {key}: {value[:50] if len(value) > 50 else value}")
    
    except Exception as e:
        print(f"  Error reading CSV: {e}")


def main():
    print("Examining IRDB CSV file structure...")
    
    fetcher = IRDBFetcher()
    repo_path = fetcher.fetch()
    
    # Get some sample CSV files from different manufacturers
    manufacturers = ['Samsung', 'LG', 'Sony', 'Panasonic', 'Philips']
    
    for manufacturer in manufacturers:
        manufacturer_path = repo_path / manufacturer
        if manufacturer_path.exists():
            csv_files = list(manufacturer_path.glob('*.csv'))
            if csv_files:
                # Examine first CSV file from this manufacturer
                examine_csv(csv_files[0])
                break  # Just examine one for now
    
    print("\n" + "="*70)
    print("\nKey Question: Can we determine device type from CSV data?")
    print("Look for fields like 'device', 'type', 'category', or function names")
    print("="*70)


if __name__ == "__main__":
    main()
