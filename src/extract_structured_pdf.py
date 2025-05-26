#!/usr/bin/env python3
# filepath: /Users/jona/Desktop/Projects/kitsune_projects/scraping_brasil/src/extract_structured_pdf.py

import asyncio
import json
import os
import re
from pathlib import Path
from datetime import datetime
from loguru import logger
from typing import Dict, Any, List, Optional, Tuple
import PyPDF2
from tqdm import tqdm

# Define paths
PDF_DIR = Path("/Users/jona/Google Drive/My Drive/Kitsune/Fase1_Estructuracion_base/Brasil/PDF")
TEXT_JSON_DIR = Path("/Users/jona/Google Drive/My Drive/Kitsune/Fase1_Estructuracion_base/Brasil/text_json_structured")

# Patterns to identify common legislative document sections
SECTION_PATTERNS = {
    "ementa": r"(?i)ementa\s*:?",
    "autor": r"(?i)autor(es|ia)?\s*:?",
    "relator": r"(?i)relator(es|ia)?\s*:?",
    "data_apresentacao": r"(?i)data\s+d[ae]\s+apresenta[cç][aã]o\s*:?",
    "situacao": r"(?i)situa[çc][ãa]o\s*:?",
    "tramitacao": r"(?i)tramita[çc][ãa]o\s*:?",
    "decisao": r"(?i)decis[ãa]o\s*:?",
    "votacao": r"(?i)vota[çc][ãa]o\s*:?",
    "parecer": r"(?i)parecer\s*:?",
}

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

def extract_metadata(text: str) -> Dict[str, Any]:
    """Extract metadata from the text using pattern matching."""
    metadata = {}
    
    # Extract document type
    doc_type_match = re.search(r'(?i)(projeto\s+de\s+lei|proposta\s+de\s+emenda|lei|decreto|resolu[çc][ãa]o|portaria|parecer|aviso|of[íi]cio)\s+n[°\.]?\s*(\d+)[\/\-]?(\d{4})?', text)
    if doc_type_match:
        metadata['documento_tipo'] = doc_type_match.group(1).strip()
        metadata['documento_numero'] = doc_type_match.group(2)
        if doc_type_match.group(3):
            metadata['documento_ano'] = doc_type_match.group(3)
    
    # Look for dates in the text (DD/MM/YYYY format)
    date_matches = re.findall(r'(\d{1,2})[\/\-\.](\d{1,2})[\/\-\.](\d{4})', text)
    if date_matches:
        # Take the first date found as the document date
        day, month, year = date_matches[0]
        metadata['data_identificada'] = f"{year}-{month.zfill(2)}-{day.zfill(2)}"
    
    # Extract sections
    for section_name, pattern in SECTION_PATTERNS.items():
        match = re.search(f"{pattern}\\s*(.+?)\\n\\n", text, re.DOTALL)
        if match:
            metadata[section_name] = match.group(1).strip()
    
    return metadata

def extract_text_from_pdf(pdf_path: Path) -> Dict[str, Any]:
    """Extract text from a PDF file and return it as a structured dictionary with metadata."""
    try:
        # Extract process ID from filename
        process_id = extract_process_id_from_filename(pdf_path.name)
        
        # Open the PDF file
        with open(pdf_path, 'rb') as file:
            # Create a PDF reader object
            pdf_reader = PyPDF2.PdfReader(file)
            
            # Get document info
            info = pdf_reader.metadata
            document_info = {}
            if info:
                for key in info:
                    if info[key] and str(info[key]).strip():
                        # Clean up the key name
                        clean_key = key
                        if key.startswith('/'):
                            clean_key = key[1:]
                        document_info[clean_key] = str(info[key])
            
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
            
            # Extract metadata
            metadata = extract_metadata(all_text)
            
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
    
    logger.info(f"Structured text extraction complete. Successfully extracted: {successful_extractions}, Failed: {failed_extractions}, Skipped: {skipped_extractions}")

if __name__ == "__main__":
    # Configure logger
    logger.add(
        "logs/pdf_structured_extraction_{time:YYYY-MM-DD_HH-mm-ss}.log",
        rotation="1 day",
        retention="7 days",
        level="INFO"
    )
    
    # Run the extraction process
    asyncio.run(process_pdf_files())
