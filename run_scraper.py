#!/usr/bin/env python3
"""
Simple runner script for the Brazil Scraping System.
This script provides an easy way to run the complete scraping pipeline.
"""
import asyncio
import argparse
import sys
from pathlib import Path
from loguru import logger

# Add project root to path
project_root = Path(__file__).parent
sys.path.append(str(project_root))

from src.main import BrazilScrapingCoordinator, main as run_main
from src.storage.drive_factory import DriveFactory
from config.settings import settings

def setup_logging(level: str = "INFO"):
    """Setup logging configuration."""
    logger.remove()  # Remove default handler
    
    # Add console handler
    logger.add(
        sys.stdout,
        level=level,
        format="<green>{time:YYYY-MM-DD HH:mm:ss}</green> | <level>{level: <8}</level> | <cyan>{name}</cyan>:<cyan>{function}</cyan>:<cyan>{line}</cyan> - <level>{message}</level>"
    )
    
    # Add file handler
    log_file = settings.LOG_PATH / "scraper.log"
    logger.add(
        log_file,
        level=level,
        format="{time:YYYY-MM-DD HH:mm:ss} | {level: <8} | {name}:{function}:{line} - {message}",
        rotation="10 MB",
        retention="7 days"
    )

async def run_scraper(mode: str = None, start_date: str = None, end_date: str = None):
    """
    Run the scraping system with specified parameters.
    
    Args:
        mode: Drive mode (mock, real, auto)
        start_date: Start date for scraping (YYYY-MM-DD)
        end_date: End date for scraping (YYYY-MM-DD)
    """
    logger.info("🇧🇷 Brazil Government Documents Scraper")
    logger.info("=" * 60)
    
    # Override settings if provided
    if mode is not None:
        settings.APP_MODE = mode
        logger.info(f"🔧 Mode override: {mode}")
    
    if start_date is not None:
        settings.DEFAULT_START_DATE = start_date
        logger.info(f"📅 Start date override: {start_date}")
    
    # Show configuration
    logger.info("⚙️  Configuration:")
    logger.info(f"   • Mode: {settings.APP_MODE}")
    logger.info(f"   • Start Date: {settings.DEFAULT_START_DATE}")
    logger.info(f"   • End Date: {settings.get_end_date()}")
    logger.info(f"   • Data Path: {settings.DATA_RAW_PATH}")
    logger.info(f"   • Mock Storage: {settings.MOCK_STORAGE_PATH}")
    
    # Run the main pipeline
    try:
        result = await run_main()
        return result
    except KeyboardInterrupt:
        logger.warning("⚠️  Scraping interrupted by user")
        return 1
    except Exception as e:
        logger.error(f"💥 Unexpected error: {e}")
        return 1

async def test_system():
    """Test system configuration and connectivity."""
    logger.info("🧪 Testing system configuration...")
    
    try:
        # Test Drive system
        logger.info("📁 Testing Drive system...")
        drive = DriveFactory.create_drive_manager()
        stats = drive.get_stats()
        logger.success(f"✅ Drive system OK: {type(drive).__name__}")
        
        # Test folder creation
        logger.info("📂 Testing folder operations...")
        folders = await drive.setup_folder_structure()
        logger.success(f"✅ Created {len(folders)} folders")
        
        # Test file operations
        logger.info("📄 Testing file operations...")
        test_content = f"Test file created at {asyncio.get_event_loop().time()}"
        file_info = await drive.upload_file(
            file_content=test_content,
            filename="system_test.txt"
        )
        logger.success(f"✅ File upload OK: {file_info.name} ({file_info.size} bytes)")
        
        # Show final stats
        final_stats = drive.get_stats()
        logger.info("📊 Final statistics:")
        for key, value in final_stats.items():
            logger.info(f"   • {key}: {value}")
        
        logger.success("🎉 All system tests passed!")
        return 0
        
    except Exception as e:
        logger.error(f"❌ System test failed: {e}")
        return 1

async def show_status():
    """Show current system status and configuration."""
    logger.info("📋 System Status")
    logger.info("=" * 40)
    
    # Configuration info
    logger.info("⚙️  Configuration:")
    logger.info(f"   • App Mode: {settings.APP_MODE}")
    logger.info(f"   • Log Level: {settings.LOG_LEVEL}")
    logger.info(f"   • Start Date: {settings.DEFAULT_START_DATE}")
    logger.info(f"   • End Date: {settings.get_end_date()}")
    
    # Path info
    logger.info("📁 Paths:")
    logger.info(f"   • Project Root: {settings.PROJECT_ROOT}")
    logger.info(f"   • Raw Data: {settings.DATA_RAW_PATH}")
    logger.info(f"   • Processed Data: {settings.DATA_PROCESSED_PATH}")
    logger.info(f"   • Mock Storage: {settings.MOCK_STORAGE_PATH}")
    logger.info(f"   • Logs: {settings.LOG_PATH}")
    
    # Drive info
    drive_info = DriveFactory.get_mode_info()
    logger.info("🚗 Drive Configuration:")
    for key, value in drive_info.items():
        logger.info(f"   • {key}: {value}")
    
    return 0

def main():
    """Main entry point for the runner script."""
    parser = argparse.ArgumentParser(
        description="Brazil Government Documents Scraper",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python run_scraper.py                           # Run with default settings
  python run_scraper.py --mode mock               # Force mock mode
  python run_scraper.py --start-date 2024-06-01   # Custom start date
  python run_scraper.py --test                    # Test system configuration
  python run_scraper.py --status                  # Show current status
  python run_scraper.py --verbose                 # Enable verbose logging
        """
    )
    
    parser.add_argument(
        "--mode", 
        choices=['mock', 'real', 'auto'],
        help="Drive mode (default: from settings)"
    )
    
    parser.add_argument(
        "--start-date",
        help="Start date for scraping (YYYY-MM-DD format)"
    )
    
    parser.add_argument(
        "--end-date", 
        help="End date for scraping (YYYY-MM-DD format, default: today)"
    )
    
    parser.add_argument(
        "--test", 
        action="store_true",
        help="Test system configuration without scraping"
    )
    
    parser.add_argument(
        "--status",
        action="store_true", 
        help="Show current system status and exit"
    )
    
    parser.add_argument(
        "--verbose", "-v",
        action="store_true",
        help="Enable verbose logging"
    )
    
    args = parser.parse_args()
    
    # Setup logging
    log_level = "DEBUG" if args.verbose else "INFO"
    setup_logging(log_level)
    
    # Choose operation
    if args.status:
        exit_code = asyncio.run(show_status())
    elif args.test:
        exit_code = asyncio.run(test_system())
    else:
        exit_code = asyncio.run(run_scraper(
            mode=args.mode,
            start_date=args.start_date,
            end_date=args.end_date
        ))
    
    sys.exit(exit_code)

if __name__ == "__main__":
    main() 