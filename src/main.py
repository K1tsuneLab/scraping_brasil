"""
Script to translate the senate processes data from Portuguese to Spanish.
"""
import asyncio
import sys
from pathlib import Path
from loguru import logger

# Add the project root to Python path
project_root = Path(__file__).parent
sys.path.append(str(project_root))

from translate_text import translate_text

async def translate_senate_data():
    """
    Translate the senate processes data from Portuguese to Spanish.
    """
    try:
        # Input and output file paths
        input_path = "data/raw/senate_processes_20230201_to_20250521.json"
        output_path = "data/processed/senate_processes_20230201_to_20250521_es.json"
        
        logger.info(f"Starting translation of senate processes data...")
        logger.info(f"Input file: {input_path}")
        logger.info(f"Output file: {output_path}")
        
        # Use the translate_text function from main.py
        translated_file = await translate_text(file_path=input_path, output_path=output_path)
        
        logger.success(f"Translation completed successfully!")
        logger.info(f"Translated data saved to: {translated_file}")
        
    except Exception as e:
        logger.error(f"Error during translation: {str(e)}")
        raise

if __name__ == "__main__":
    asyncio.run(translate_senate_data())