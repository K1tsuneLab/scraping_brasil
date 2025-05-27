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

try:
    from src.utils.translate_file_pt_to_es import translate_file_pt_to_es
    
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
            
            # Translate the file
            await translate_file_pt_to_es(input_path, output_path)
            
            logger.success(f"Translation completed successfully!")
            logger.info(f"Translated data saved to: {output_path}")
            
        except Exception as e:
            logger.error(f"Error during translation: {str(e)}")
            raise
    
    if __name__ == "__main__":
        asyncio.run(translate_senate_data())
except ImportError as e:
    logger.error(f"Import error: {str(e)}")
    logger.info("Please make sure the translation module is properly installed.")
    sys.exit(1)
