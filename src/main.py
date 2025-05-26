import asyncio
import argparse
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

async def extract_api_data(start_date=None, end_date=None):
    """Extract legislative process data from the Senate API."""
    # Set default dates if not provided
    if start_date is None:
        start_date = datetime(2022, 1, 1)  # Default to January 1, 2022
    if end_date is None:
        end_date = datetime.now()  # Current date
    
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

async def download_pdfs():
    """Download PDF files for legislative processes."""
    from src.download_pdfs import download_all_pdfs
    await download_all_pdfs()

async def extract_pdf_text(structured=False):
    """Extract text from PDF files."""
    if structured:
        from src.extract_structured_pdf import process_pdf_files
    else:
        from src.extract_pdf_text import process_pdf_files
    await process_pdf_files()

async def main():
    """Main function to parse arguments and execute the requested task."""
    parser = argparse.ArgumentParser(description="Brazilian Legislative Data Processing Tool")
    
    # Create subparsers for different commands
    subparsers = parser.add_subparsers(dest="command", help="Command to execute")
    
    # API data extraction command
    api_parser = subparsers.add_parser("extract-api", help="Extract data from Senate API")
    api_parser.add_argument("--start", help="Start date (YYYY-MM-DD)", default=None)
    api_parser.add_argument("--end", help="End date (YYYY-MM-DD)", default=None)
    
    # PDF download command
    pdf_parser = subparsers.add_parser("download-pdfs", help="Download PDF files")
    
    # PDF text extraction command
    text_parser = subparsers.add_parser("extract-text", help="Extract text from PDFs")
    text_parser.add_argument("--structured", action="store_true", help="Use structured extraction with metadata")
    
    # Parse arguments
    args = parser.parse_args()
    
    # Execute the requested command
    if args.command == "extract-api":
        # Parse dates if provided
        start_date = None
        end_date = None
        if args.start:
            start_date = datetime.strptime(args.start, "%Y-%m-%d")
        if args.end:
            end_date = datetime.strptime(args.end, "%Y-%m-%d")
        await extract_api_data(start_date, end_date)
    elif args.command == "download-pdfs":
        await download_pdfs()
    elif args.command == "extract-text":
        await extract_pdf_text(structured=args.structured)
    else:
        # Default to API extraction if no command provided
        logger.info("No command specified. Running default data extraction.")
        await extract_api_data()

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("Process interrupted by user")
    except Exception as e:
        logger.error(f"Unexpected error: {str(e)}")
        sys.exit(1)