#!/usr/bin/env python3
"""
SmartIR Fetcher

Downloads and organizes SmartIR repository codes.

Source: https://github.com/smartHomeHub/SmartIR
"""

import subprocess
import shutil
from pathlib import Path
from typing import Optional


class SmartIRFetcher:
    """Fetch and manage SmartIR repository"""
    
    REPO_URL = "https://github.com/smartHomeHub/SmartIR.git"
    
    def __init__(self, cache_dir: Path = None):
        """
        Initialize SmartIR fetcher.
        
        Args:
            cache_dir: Directory to store SmartIR repository
        """
        self.cache_dir = cache_dir or Path.home() / ".cache" / "smartir-aggregator" / "smartir"
        self.cache_dir.mkdir(parents=True, exist_ok=True)
        self.repo_path = self.cache_dir / "SmartIR"
    
    def fetch(self, force: bool = False) -> Path:
        """
        Fetch SmartIR repository.
        
        Args:
            force: Force re-clone even if repo exists
            
        Returns:
            Path to SmartIR repository
        """
        if self.repo_path.exists() and not force:
            print(f"SmartIR repository already exists at {self.repo_path}")
            print("Pulling latest changes...")
            self._git_pull()
        else:
            print(f"Cloning SmartIR repository to {self.repo_path}...")
            self._git_clone()
        
        return self.repo_path
    
    def _git_clone(self):
        """Clone SmartIR repository"""
        try:
            subprocess.run(
                ["git", "clone", "--depth", "1", self.REPO_URL, str(self.repo_path)],
                check=True,
                capture_output=True
            )
            print("✓ SmartIR repository cloned successfully")
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
            print("✓ SmartIR repository updated")
        except subprocess.CalledProcessError as e:
            print(f"✗ Error updating repository: {e.stderr.decode()}")
    
    def get_codes_path(self) -> Path:
        """
        Get path to codes directory in SmartIR.
        
        Returns:
            Path to codes directory
        """
        return self.repo_path / "codes"
    
    def get_platform_path(self, platform: str) -> Optional[Path]:
        """
        Get path to specific platform in SmartIR.
        
        Args:
            platform: Platform name (climate, media_player, fan, light)
            
        Returns:
            Path to platform directory or None if not found
        """
        platform_path = self.get_codes_path() / platform
        
        if platform_path.exists():
            return platform_path
        
        print(f"Platform '{platform}' not found in SmartIR")
        return None
    
    def list_platforms(self) -> list:
        """
        List all available platforms in SmartIR.
        
        Returns:
            List of platform names
        """
        codes_path = self.get_codes_path()
        if not codes_path.exists():
            return []
        
        return [d.name for d in codes_path.iterdir() if d.is_dir()]
    
    def copy_codes(self, output_dir: Path, preserve_numbers: bool = True) -> dict:
        """
        Copy SmartIR codes to output directory.
        
        Args:
            output_dir: Output directory for codes
            preserve_numbers: Keep original code numbers (1-9999 range)
            
        Returns:
            Dictionary with copy statistics
        """
        stats = {
            'platforms': 0,
            'codes_copied': 0,
            'errors': 0
        }
        
        codes_path = self.get_codes_path()
        if not codes_path.exists():
            print("✗ SmartIR codes directory not found")
            return stats
        
        platforms = [d for d in codes_path.iterdir() if d.is_dir()]
        
        for platform in platforms:
            platform_name = platform.name
            stats['platforms'] += 1
            
            # Create output directory for platform
            platform_output = output_dir / platform_name
            platform_output.mkdir(parents=True, exist_ok=True)
            
            # Copy all JSON files
            json_files = list(platform.glob('*.json'))
            
            for json_file in json_files:
                try:
                    # Preserve original filename/number
                    output_file = platform_output / json_file.name
                    shutil.copy2(json_file, output_file)
                    stats['codes_copied'] += 1
                except Exception as e:
                    print(f"✗ Error copying {json_file.name}: {e}")
                    stats['errors'] += 1
        
        return stats
    
    def get_stats(self) -> dict:
        """
        Get statistics about SmartIR repository.
        
        Returns:
            Dictionary with statistics
        """
        stats = {
            'platforms': 0,
            'codes': 0
        }
        
        codes_path = self.get_codes_path()
        if not codes_path.exists():
            return stats
        
        platforms = [d for d in codes_path.iterdir() if d.is_dir()]
        stats['platforms'] = len(platforms)
        
        for platform in platforms:
            stats['codes'] += len(list(platform.glob('*.json')))
        
        return stats


if __name__ == "__main__":
    # Test fetcher
    fetcher = SmartIRFetcher()
    
    print("Fetching SmartIR repository...")
    repo_path = fetcher.fetch()
    
    print("\nSmartIR Statistics:")
    stats = fetcher.get_stats()
    print(f"Platforms: {stats['platforms']}")
    print(f"Codes: {stats['codes']}")
    
    print("\nAvailable platforms:")
    for platform in fetcher.list_platforms():
        print(f"  - {platform}")
