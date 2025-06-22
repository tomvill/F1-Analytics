"""
Utilities for handling FastF1 cache configuration and management.
This module standardizes cache behavior across the application.
"""

import logging
import os
from pathlib import Path

import fastf1

logger = logging.getLogger(__name__)

CACHE_DIR = ".fast-f1-cache"


def setup_fastf1_cache(cache_dir=CACHE_DIR):
    """
    Set up the FastF1 cache directory, creating it if it doesn't exist.

    This function centralizes the cache configuration for FastF1 data.
    The cache directory is excluded from git via .gitignore.

    Args:
        cache_dir (str, optional): Path to the cache directory. Defaults to ".fast-f1-cache".

    Returns:
        bool: True if cache was successfully configured, False otherwise.
    """
    try:
        cache_path = Path(cache_dir)
        cache_path.mkdir(exist_ok=True)

        fastf1.Cache.enable_cache(str(cache_path.absolute()))
        logger.info(f"FastF1 cache enabled at {cache_path.absolute()}")
        return True
    except Exception as e:
        logger.warning(f"Failed to configure FastF1 cache: {e}")
        logger.warning("Data will be fetched from the API each time (slower)")
        return False


def get_cache_info():
    """
    Get information about the FastF1 cache.

    Returns:
        tuple: (cache_size in bytes, number of files)
    """
    cache_path = os.path.abspath(CACHE_DIR)
    cache_size = 0
    num_files = 0

    try:
        for path, dirs, files in os.walk(cache_path):
            num_files += len(files)
            for f in files:
                cache_size += os.path.getsize(os.path.join(path, f))
        return cache_size, num_files
    except Exception:
        return 0, 0


def clear_fastf1_cache():
    """Clear the FastF1 cache. Returns success status and message."""
    cache_path = os.path.abspath(CACHE_DIR)
    try:
        fastf1.Cache.clear_cache(cache_path)
        return True, "Cache cleared successfully"
    except FileNotFoundError:
        return False, "Cache directory does not exist"
    except Exception as e:
        return False, f"Error clearing cache: {e}"
