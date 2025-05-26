#!/usr/bin/env python3
# filepath: /Users/jona/Desktop/Projects/kitsune_projects/scraping_brasil/src/extract_pdf_text.py

import asyncio
import json
import os
import re
from pathlib import Path
from loguru import logger
from typing import Dict, Any, List, Optional
import PyPDF2
from tqdm import tqdm

# Define paths
PDF_DIR = Path("/Users/jona/Google Drive/My Drive/Kitsune/Fase1_Estructuracion_base/Brasil/PDF")
TEXT_JSON_DIR = Path("/Users/jona/Google Drive/My Drive/Kitsune/Fase1_Estructuracion_base/Brasil/text_json")

def extract_process_id_from_filename(filename: str) -> Optional[str]:
    """Extract the process ID from the filename."""
    # Try to extract process_XXX.pdf pattern
    match = re.search(r'process_(\d+)\.pdf', filename)
    if match:
        return match.group(1)
    
    # Try to extract other patterns that might contain IDs
    match = re.search(r'documento?[_-]?(\d+)\.pdf', filename, re.IGNORECASE)
    if match:
        return match.group(1)
    
    # Try to extract any number pattern
    match = re.search(r'(\d+)\.pdf', filename)
    if match:
        return match.group(1)
    
    # If no ID found, return None
    return None

def extract_text_from_pdf(pdf_path: Path) -> Dict[str, Any]:
    """Extract text from a PDF file and return it as a structured dictionary."""
    try:
        # Extract process ID from filename
        process_id = extract_process_id_from_filename(pdf_path.name)
        
        # Open the PDF file
        with open(pdf_path, 'rb') as file:
            # Create a PDF reader object
            pdf_reader = PyPDF2.PdfReader(file)
            
            # Get the number of pages
            num_pages = len(pdf_reader.pages)
            
            # Extract text from each page
            all_text = ""
            pages_text = []
            
            for page_num in range(num_pages):
                # Get the page
                page = pdf_reader.pages[page_num]
                
                # Extract text from the page
                text = page.extract_text()
                
                # Add to collections
                all_text += text + "\n"
                pages_text.append(text)
            
            # Create result dictionary with only id, filename, and full_text
            result = {
                "id": process_id,
                "filename": pdf_path.name,
                "full_text": all_text
            }
            
            return result
    except Exception as e:
        logger.error(f"Error extracting text from {pdf_path}: {str(e)}")
        # Return basic error info
        return {
            "id": process_id,
            "filename": pdf_path.name,
            "error": str(e)
        }

async def process_pdf_files():
    """Process all PDF files in the directory."""
    # Ensure output directory exists
    TEXT_JSON_DIR.mkdir(parents=True, exist_ok=True)
    
    # Get all PDF files in the directory
    pdf_files = list(PDF_DIR.glob('*.pdf'))
    total_files = len(pdf_files)
    logger.info(f"Found {total_files} PDF files to process")
    
    successful_extractions = 0
    failed_extractions = 0
    skipped_extractions = 0
    
    # Process each PDF file with progress bar
    for pdf_file in tqdm(pdf_files, desc="Extracting text from PDFs", unit="file"):
        try:
            # Extract process ID from filename
            process_id = extract_process_id_from_filename(pdf_file.name)
            
            # Set output JSON filename
            output_filename = f"text_{process_id}.json" if process_id else f"text_{pdf_file.stem}.json"
            output_path = TEXT_JSON_DIR / output_filename
            
            # Check if file already exists
            if output_path.exists():
                logger.info(f"Skipping existing file: {output_filename}")
                skipped_extractions += 1
                continue
                
            logger.info(f"Processing {pdf_file.name}")
            
            # Extract text from PDF
            result = extract_text_from_pdf(pdf_file)
            
            # Save result to JSON file
            with open(output_path, 'w', encoding='utf-8') as f:
                json.dump(result, f, ensure_ascii=False, indent=2)
            
            logger.info(f"Successfully saved text to {output_path}")
            successful_extractions += 1
            
        except Exception as e:
            logger.error(f"Error processing {pdf_file.name}: {str(e)}")
            failed_extractions += 1
    
    logger.info(f"Text extraction complete. Successfully extracted: {successful_extractions}, Failed: {failed_extractions}, Skipped: {skipped_extractions}")

if __name__ == "__main__":
    # Add missing import at top level
    from datetime import datetime
    
    # Configure logger
    logger.add(
        "logs/pdf_text_extraction_{time:YYYY-MM-DD_HH-mm-ss}.log",
        rotation="1 day",
        retention="7 days",
        level="INFO"
    )
    
    # Run the extraction process
    asyncio.run(process_pdf_files())
