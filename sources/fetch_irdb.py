#!/usr/bin/env python3
"""
IRDB Fetcher

Downloads and organizes IRDB repository for conversion.

Source: https://github.com/probonopd/irdb
"""

import os
import subprocess
from pathlib import Path
from typing import Optional


class IRDBFetcher:
    """Fetch and manage IRDB repository"""
    
    REPO_URL = "https://github.com/probonopd/irdb.git"
    
    def __init__(self, cache_dir: Path = None):
        """
        Initialize IRDB fetcher.
        
        Args:
            cache_dir: Directory to store IRDB repository
        """
        self.cache_dir = cache_dir or Path.home() / ".cache" / "smartir-aggregator" / "irdb"
        self.cache_dir.mkdir(parents=True, exist_ok=True)
        self.repo_path = self.cache_dir / "irdb"
    
    def fetch(self, force: bool = False) -> Path:
        """
        Fetch IRDB repository.
        
        Args:
            force: Force re-clone even if repo exists
            
        Returns:
            Path to IRDB repository
        """
        if self.repo_path.exists() and not force:
            print(f"IRDB repository already exists at {self.repo_path}")
            print("Pulling latest changes...")
            self._git_pull()
        else:
            print(f"Cloning IRDB repository to {self.repo_path}...")
            self._git_clone()
        
        return self.repo_path
    
    def _git_clone(self):
        """Clone IRDB repository"""
        try:
            subprocess.run(
                ["git", "clone", "--depth", "1", self.REPO_URL, str(self.repo_path)],
                check=True,
                capture_output=True
            )
            print("✓ IRDB repository cloned successfully")
        except subprocess.CalledProcessError as e:
            print(f"✗ Error cloning repository: {e.stderr.decode()}")
            raise
    
    def _git_pull(self):
        """Pull latest changes"""
        try:
            subprocess.run(
                ["git", "-C", str(self.repo_path), "pull"],
                check=True,
                capture_output=True
            )
            print("✓ IRDB repository updated")
        except subprocess.CalledProcessError as e:
            print(f"✗ Error updating repository: {e.stderr.decode()}")
    
    def get_category_path(self, category: str) -> Optional[Path]:
        """
        Get path to specific category in IRDB.
        
        Args:
            category: Category name (e.g., 'TV', 'Air_Conditioner')
            
        Returns:
            Path to category directory or None if not found
        """
        # IRDB structure: codes/category/manufacturer/model.csv
        category_path = self.repo_path / "codes" / category
        
        if category_path.exists():
            return category_path
        
        print(f"Category '{category}' not found in IRDB")
        return None
    
    def list_categories(self) -> list:
        """
        List all available categories in IRDB.
        
        Returns:
            List of category names
        """
        codes_path = self.repo_path / "codes"
        if not codes_path.exists():
            return []
        
        return [d.name for d in codes_path.iterdir() if d.is_dir()]
    
    def get_stats(self) -> dict:
        """
        Get statistics about IRDB repository.
        
        Returns:
            Dictionary with statistics
        """
        stats = {
            'categories': 0,
            'manufacturers': 0,
            'devices': 0
        }
        
        codes_path = self.repo_path / "codes"
        if not codes_path.exists():
            return stats
        
        categories = list(codes_path.iterdir())
        stats['categories'] = len([d for d in categories if d.is_dir()])
        
        manufacturers = set()
        devices = 0
        
        for category in categories:
            if not category.is_dir():
                continue
            
            for manufacturer in category.iterdir():
                if manufacturer.is_dir():
                    manufacturers.add(manufacturer.name)
                    devices += len(list(manufacturer.glob('*.csv')))
        
        stats['manufacturers'] = len(manufacturers)
        stats['devices'] = devices
        
        return stats


if __name__ == "__main__":
    # Test fetcher
    fetcher = IRDBFetcher()
    
    print("Fetching IRDB repository...")
    repo_path = fetcher.fetch()
    
    print("\nIRDB Statistics:")
    stats = fetcher.get_stats()
    print(f"Categories: {stats['categories']}")
    print(f"Manufacturers: {stats['manufacturers']}")
    print(f"Devices: {stats['devices']}")
    
    print("\nAvailable categories:")
    for category in fetcher.list_categories():
        print(f"  - {category}")
