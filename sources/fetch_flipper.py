#!/usr/bin/env python3
"""
Flipper IRDB Fetcher

Downloads and organizes Flipper Zero IRDB repository for conversion.

Source: https://github.com/Lucaslhm/Flipper-IRDB
"""

import subprocess
from pathlib import Path
from typing import Optional


class FlipperFetcher:
    """Fetch and manage Flipper IRDB repository"""
    
    REPO_URL = "https://github.com/Lucaslhm/Flipper-IRDB.git"
    
    def __init__(self, cache_dir: Path = None):
        """
        Initialize Flipper fetcher.
        
        Args:
            cache_dir: Directory to store Flipper IRDB repository
        """
        self.cache_dir = cache_dir or Path.home() / ".cache" / "smartir-aggregator" / "flipper"
        self.cache_dir.mkdir(parents=True, exist_ok=True)
        self.repo_path = self.cache_dir / "Flipper-IRDB"
    
    def fetch(self, force: bool = False) -> Path:
        """
        Fetch Flipper IRDB repository.
        
        Args:
            force: Force re-clone even if repo exists
            
        Returns:
            Path to Flipper IRDB repository
        """
        if self.repo_path.exists() and not force:
            print(f"Flipper IRDB repository already exists at {self.repo_path}")
            print("Pulling latest changes...")
            self._git_pull()
        else:
            print(f"Cloning Flipper IRDB repository to {self.repo_path}...")
            self._git_clone()
        
        return self.repo_path
    
    def _git_clone(self):
        """Clone Flipper IRDB repository"""
        try:
            subprocess.run(
                ["git", "clone", "--depth", "1", self.REPO_URL, str(self.repo_path)],
                check=True,
                capture_output=True
            )
            print("✓ Flipper IRDB repository cloned successfully")
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
            print("✓ Flipper IRDB repository updated")
        except subprocess.CalledProcessError as e:
            print(f"✗ Error updating repository: {e.stderr.decode()}")
    
    def get_category_path(self, category: str) -> Optional[Path]:
        """
        Get path to specific category in Flipper IRDB.
        
        Args:
            category: Category name (e.g., 'TVs', 'ACs')
            
        Returns:
            Path to category directory or None if not found
        """
        category_path = self.repo_path / category
        
        if category_path.exists():
            return category_path
        
        print(f"Category '{category}' not found in Flipper IRDB")
        return None
    
    def list_categories(self) -> list:
        """
        List all available categories in Flipper IRDB.
        
        Returns:
            List of category names
        """
        if not self.repo_path.exists():
            return []
        
        # Flipper IRDB has categories as top-level directories
        return [d.name for d in self.repo_path.iterdir() 
                if d.is_dir() and not d.name.startswith('.')]
    
    def get_stats(self) -> dict:
        """
        Get statistics about Flipper IRDB repository.
        
        Returns:
            Dictionary with statistics
        """
        stats = {
            'categories': 0,
            'manufacturers': 0,
            'devices': 0
        }
        
        if not self.repo_path.exists():
            return stats
        
        categories = [d for d in self.repo_path.iterdir() 
                     if d.is_dir() and not d.name.startswith('.')]
        stats['categories'] = len(categories)
        
        manufacturers = set()
        devices = 0
        
        for category in categories:
            for manufacturer in category.iterdir():
                if manufacturer.is_dir():
                    manufacturers.add(manufacturer.name)
                    devices += len(list(manufacturer.glob('*.ir')))
        
        stats['manufacturers'] = len(manufacturers)
        stats['devices'] = devices
        
        return stats


if __name__ == "__main__":
    # Test fetcher
    fetcher = FlipperFetcher()
    
    print("Fetching Flipper IRDB repository...")
    repo_path = fetcher.fetch()
    
    print("\nFlipper IRDB Statistics:")
    stats = fetcher.get_stats()
    print(f"Categories: {stats['categories']}")
    print(f"Manufacturers: {stats['manufacturers']}")
    print(f"Devices: {stats['devices']}")
    
    print("\nAvailable categories:")
    for category in fetcher.list_categories():
        print(f"  - {category}")
