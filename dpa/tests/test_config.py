"""
Test configuration module
"""
from dpa.config.settings import config_manager
from dpa.utils.logger import logger

def test_config():
    """Test configuration loading and saving"""
    logger.info("=== Testing Configuration Module ===")
    
    # Load config
    config = config_manager.load()
    logger.info(f"Loaded config: enrolled={config.enrolled}, backend_url={config.backend_url}")
    
    # Update config
    config_manager.update(
        backend_url="http://localhost:8000",
        log_level="DEBUG"
    )
    logger.info("Configuration updated")
    
    # Get config
    config = config_manager.get()
    logger.info(f"Current backend URL: {config.backend_url}")
    logger.info(f"Current log level: {config.log_level}")
    
    logger.info("=== Configuration Test Complete ===")

if __name__ == "__main__":
    test_config()
