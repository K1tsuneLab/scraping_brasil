import asyncio
import json
import aiohttp
from pathlib import Path
from loguru import logger
from urllib.parse import urlparse
import os
from typing import Optional, Tuple

# Define paths
JSON_DIR = Path("/Users/jona/Google Drive/My Drive/Kitsune/Fase1_Estructuracion_base/Brasil/json/json")
PDF_DIR = Path("/Users/jona/Google Drive/My Drive/Kitsune/Fase1_Estructuracion_base/Brasil/PDF")

async def download_pdf(session: aiohttp.ClientSession, url: str, output_path: Path, process_id: Optional[str] = None) -> Tuple[bool, bool]:
    """Download a single PDF file.
    Returns a tuple of (success, was_skipped)"""
    try:
        # Get filename from URL or use process ID
        filename = os.path.basename(urlparse(url).path)
        if not filename or not filename.endswith('.pdf'):
            filename = f"process_{process_id}.pdf" if process_id else "document.pdf"
        
        output_file = output_path / filename
        
        # Check if file already exists
        if output_file.exists():
            logger.info(f"Skipping existing file: {filename}")
            return True, True
            
        async with session.get(url) as response:
            if response.status == 200:
                # Save the file
                with open(output_file, 'wb') as f:
                    f.write(await response.read())
                
                logger.info(f"Successfully downloaded: {filename}")
                return True, False
            else:
                logger.error(f"Failed to download {url}: HTTP {response.status}")
                return False, False
    except Exception as e:
        logger.error(f"Error downloading {url}: {str(e)}")
        return False, False

async def process_json_file(session: aiohttp.ClientSession, json_file: Path) -> tuple[int, int, int]:
    """Process a single JSON file and download its PDFs.
    Returns (successful_downloads, failed_downloads, skipped_downloads)"""
    try:
        with open(json_file, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        successful_downloads = 0
        failed_downloads = 0
        skipped_downloads = 0
        
        # Handle both list and dictionary JSON structures
        if isinstance(data, list):
            processes = data
        elif isinstance(data, dict):
            # Try to find the list of processes in common keys
            processes = []
            for key in ['ListaMateriasTramitando', 'ListaMateriasNaoTramitando', 'processes', 'data']:
                if key in data and isinstance(data[key], list):
                    processes.extend(data[key])
                    break
            if not processes and 'processes' in data:
                processes = data['processes']
        else:
            logger.error(f"Unexpected JSON structure in {json_file}")
            return 0, 0, 0
        
        logger.info(f"Found {len(processes)} processes in {json_file.name}")
        
        for process in processes:
            if not isinstance(process, dict):
                logger.warning(f"Skipping invalid process entry: {process}")
                continue
                
            url = process.get('urlDocumento') or process.get('link_inteiro_teor')
            if url:
                process_id = str(process.get('id') or process.get('numero') or 'unknown')
                success, was_skipped = await download_pdf(session, url, PDF_DIR, process_id)
                if was_skipped:
                    skipped_downloads += 1
                elif success:
                    successful_downloads += 1
                else:
                    failed_downloads += 1
            else:
                logger.debug(f"No URL found for process: {process.get('id') or process.get('numero')}")
        
        return successful_downloads, failed_downloads, skipped_downloads
    except json.JSONDecodeError as e:
        logger.error(f"Invalid JSON in {json_file}: {str(e)}")
        return 0, 0, 0
    except Exception as e:
        logger.error(f"Error processing {json_file}: {str(e)}")
        return 0, 0, 0

async def download_all_pdfs():
    """Main function to download all PDFs from JSON files."""
    # Ensure PDF directory exists
    PDF_DIR.mkdir(parents=True, exist_ok=True)
    
    total_successful = 0
    total_failed = 0
    total_skipped = 0
    
    async with aiohttp.ClientSession() as session:
        # Get all JSON files in the directory
        json_files = list(JSON_DIR.glob('*.json'))
        logger.info(f"Found {len(json_files)} JSON files to process")
        
        for json_file in json_files:
            logger.info(f"Processing {json_file.name}")
            successful, failed, skipped = await process_json_file(session, json_file)
            total_successful += successful
            total_failed += failed
            total_skipped += skipped
            logger.info(f"Completed {json_file.name}: {successful} successful, {failed} failed, {skipped} skipped")
    
    logger.info(f"Download complete. Successfully downloaded: {total_successful}, Failed: {total_failed}, Skipped: {total_skipped}")

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