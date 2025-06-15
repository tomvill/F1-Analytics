"""
Utilities for handling FastF1 cache configuration and management.
This module standardizes cache behavior across the application.
"""
import logging
from pathlib import Path
import fastf1

logger = logging.getLogger(__name__)

def setup_fastf1_cache(cache_dir=".fast-f1-cache"):
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
