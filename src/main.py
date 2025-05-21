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
    level="DEBUG"
)

async def main():
    # Define date range - from January 1, 2022 to current date
    end_date = datetime.now()  # Current date
    start_date = datetime(2022, 1, 1)  # January 1, 2022
    
    logger.info(f"Starting data extraction from {start_date.strftime('%Y-%m-%d')} to {end_date.strftime('%Y-%m-%d')}")
    logger.info(f"Total days to process: {(end_date - start_date).days}")
    
    # Initialize components
    processor = DataProcessor()
    
    async with SenateAPIClient() as client:
        try:
            # Fetch processes for the date range
            logger.info("Fetching processes from Senate API...")
            processes = await client.get_processes_date_range(start_date, end_date)
            
            if not processes:
                logger.warning("No processes found in the specified date range")
                return
            
            total_processes = len(processes)
            logger.info(f"Found {total_processes} processes to process")
            
            # Process and save data for each year
            years = sorted(set(p.ano for p in processes if p.ano is not None))
            logger.info(f"Processing data for years: {years}")
            
            for year in years:
                year_processes = [p for p in processes if p.ano == year]
                logger.info(f"Processing {len(year_processes)} processes for year {year}")
                processor.process_and_save(year_processes, year)
                logger.info(f"Completed processing for year {year}")
            
            logger.info("Data extraction completed successfully")
            logger.info(f"Total processes processed: {total_processes}")
            
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