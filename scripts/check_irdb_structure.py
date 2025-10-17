#!/usr/bin/env python3
"""
Check IRDB Repository Structure

Diagnostic script to see what's actually in the IRDB repository.
"""

import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from sources.fetch_irdb import IRDBFetcher


def main():
    print("Checking IRDB repository structure...")
    print("=" * 60)
    
    fetcher = IRDBFetcher()
    repo_path = fetcher.fetch()
    
    print(f"\nRepository path: {repo_path}")
    print(f"Repository exists: {repo_path.exists()}")
    
    if repo_path.exists():
        print("\nTop-level directories:")
        for item in sorted(repo_path.iterdir()):
            if item.is_dir():
                file_count = len(list(item.rglob('*')))
                print(f"  📁 {item.name}/ ({file_count} items)")
        
        # Check for codes directory
        codes_path = repo_path / "codes"
        if codes_path.exists():
            print(f"\nCodes directory exists: {codes_path}")
            print("\nCategories in codes/:")
            for item in sorted(codes_path.iterdir()):
                if item.is_dir():
                    csv_count = len(list(item.glob('**/*.csv')))
                    print(f"  📁 {item.name}/ ({csv_count} CSV files)")
        else:
            print(f"\n⚠️  No 'codes' directory found at {codes_path}")
            print("\nSearching for CSV files in repository...")
            csv_files = list(repo_path.rglob('*.csv'))
            print(f"Found {len(csv_files)} CSV files total")
            if csv_files:
                print("\nSample CSV locations:")
                for csv_file in csv_files[:5]:
                    rel_path = csv_file.relative_to(repo_path)
                    print(f"  📄 {rel_path}")
    
    print("\n" + "=" * 60)
    print("\nAvailable categories (from fetcher):")
    categories = fetcher.list_categories()
    for cat in categories:
        print(f"  - {cat}")


if __name__ == "__main__":
    main()
