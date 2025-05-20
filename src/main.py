import asyncio
from datetime import datetime, timedelta
from loguru import logger
import sys
from pathlib import Path

# Add the project root to Python path
project_root = Path(__file__).parent.parent
sys.path.append(str(project_root))

from src.api.senate_client import SenateAPIClient
from src.processors.data_processor import DataProcessor

# Configure logger
logger.add(
    "logs/extraction_{time}.log",
    rotation="500 MB",
    retention="10 days",
    level="INFO"
)

async def main():
    # Define date range - using 2023 dates for testing
    end_date = datetime(2023, 2, 6)  # February 6, 2023
    start_date = datetime(2023, 2, 1)  # February 1, 2023
    
    logger.info(f"Starting data extraction from {start_date} to {end_date}")
    
    # Initialize components
    processor = DataProcessor()
    
    async with SenateAPIClient() as client:
        try:
            # Fetch processes for the date range
            processes = await client.get_processes_date_range(start_date, end_date)
            
            if not processes:
                logger.warning("No processes found in the specified date range")
                return
            
            # Process and save data for each year
            years = sorted(set(p.ano for p in processes if p.ano is not None))
            for year in years:
                year_processes = [p for p in processes if p.ano == year]
                processor.process_and_save(year_processes, year)
            
            logger.info("Data extraction completed successfully")
            
        except Exception as e:
            logger.error(f"Error during data extraction: {str(e)}")
            raise

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("Process interrupted by user")
    except Exception as e:
        logger.error(f"Unexpected error: {str(e)}")
        sys.exit(1)