import asyncio
import json
import aiohttp
from pathlib import Path
from loguru import logger
from urllib.parse import urlparse
import os

# Define paths
JSON_DIR = Path("/Users/jona/Google Drive/My Drive/Kitsune/Fase1_Estructuracion_base/Brasil/json/json")
PDF_DIR = Path("/Users/jona/Google Drive/My Drive/Kitsune/Fase1_Estructuracion_base/Brasil/PDF")

async def download_pdf(session: aiohttp.ClientSession, url: str, output_path: Path) -> bool:
    """Download a single PDF file."""
    try:
        async with session.get(url) as response:
            if response.status == 200:
                # Get filename from URL or use a default name
                filename = os.path.basename(urlparse(url).path)
                if not filename.endswith('.pdf'):
                    filename = f"{filename}.pdf"
                
                output_file = output_path / filename
                
                # Save the file
                with open(output_file, 'wb') as f:
                    f.write(await response.read())
                
                logger.info(f"Successfully downloaded: {filename}")
                return True
            else:
                logger.error(f"Failed to download {url}: HTTP {response.status}")
                return False
    except Exception as e:
        logger.error(f"Error downloading {url}: {str(e)}")
        return False

async def process_json_file(session: aiohttp.ClientSession, json_file: Path) -> tuple[int, int]:
    """Process a single JSON file and download its PDFs."""
    try:
        with open(json_file, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        successful_downloads = 0
        failed_downloads = 0
        
        for process in data:
            url = process.get('urlDocumento')
            if url:
                if await download_pdf(session, url, PDF_DIR):
                    successful_downloads += 1
                else:
                    failed_downloads += 1
        
        return successful_downloads, failed_downloads
    except Exception as e:
        logger.error(f"Error processing {json_file}: {str(e)}")
        return 0, 0

async def download_all_pdfs():
    """Main function to download all PDFs from JSON files."""
    # Ensure PDF directory exists
    PDF_DIR.mkdir(parents=True, exist_ok=True)
    
    total_successful = 0
    total_failed = 0
    
    async with aiohttp.ClientSession() as session:
        # Get all JSON files in the directory
        json_files = list(JSON_DIR.glob('*.json'))
        logger.info(f"Found {len(json_files)} JSON files to process")
        
        for json_file in json_files:
            logger.info(f"Processing {json_file.name}")
            successful, failed = await process_json_file(session, json_file)
            total_successful += successful
            total_failed += failed
    
    logger.info(f"Download complete. Successfully downloaded: {total_successful}, Failed: {total_failed}")

if __name__ == "__main__":
    # Configure logger
    logger.add(
        "logs/pdf_download_{time:YYYY-MM-DD_HH-mm-ss}.log",
        rotation="1 day",
        retention="7 days",
        level="INFO"
    )
    
    # Run the download process
    asyncio.run(download_all_pdfs()) 