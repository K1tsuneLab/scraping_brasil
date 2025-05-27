"""
Utilities for translating files from Portuguese to Spanish.
"""

import asyncio
import json
from pathlib import Path
from loguru import logger
from typing import Any, Dict, List, Union
from deep_translator import GoogleTranslator

async def translate_text_pt_to_es(text: str) -> str:
    """
    Translate text from Portuguese to Spanish using Google Translate.
    
    Args:
        text: The Portuguese text to translate
    
    Returns:
        Translated Spanish text
    """
    if not text or not isinstance(text, str):
        return text
    
    try:
        translator = GoogleTranslator(source='pt', target='es')
        translated = translator.translate(text)
        return translated
    except Exception as e:
        logger.error(f"Translation error: {str(e)}")
        # Return original text if translation fails
        return text

async def translate_json_value(value: Any) -> Any:
    """
    Recursively translate JSON value from Portuguese to Spanish.
    
    Args:
        value: The value to translate (can be any JSON-compatible type)
    
    Returns:
        Translated value
    """
    if isinstance(value, str):
        return await translate_text_pt_to_es(value)
    elif isinstance(value, dict):
        return {k: await translate_json_value(v) for k, v in value.items()}
    elif isinstance(value, list):
        return [await translate_json_value(item) for item in value]
    else:
        return value

async def translate_file_pt_to_es(input_path: str, output_path: str) -> str:
    """
    Translate a JSON file from Portuguese to Spanish.
    
    Args:
        input_path: Path to the input JSON file
        output_path: Path to save the translated JSON file
    
    Returns:
        Path to the translated file
    """
    logger.info(f"Translating file: {input_path} -> {output_path}")
    
    try:
        # Create output directory if it doesn't exist
        output_dir = Path(output_path).parent
        output_dir.mkdir(parents=True, exist_ok=True)
        
        # Read input JSON file
        with open(input_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        total_entries = len(data)
        logger.info(f"Loaded JSON data with {total_entries} entries")
        
        # Create a temporary file for progress tracking and incremental saves
        temp_output_path = output_path + ".temp"
        
        # Translate the data with progress tracking
        translated_data = []
        for i, item in enumerate(data):
            translated_item = await translate_json_value(item)
            translated_data.append(translated_item)
            
            # Log progress every 10 items or at specific percentages
            if i % 10 == 0 or i + 1 == total_entries or (i + 1) % 100 == 0:
                progress = (i + 1) / total_entries * 100
                logger.info(f"Progress: {i + 1}/{total_entries} ({progress:.1f}%)")
                
                # Save progress incrementally every 100 items
                if (i + 1) % 100 == 0 or i + 1 == total_entries:
                    with open(temp_output_path, 'w', encoding='utf-8') as f:
                        json.dump(translated_data, f, ensure_ascii=False, indent=2)
                    logger.info(f"Saved progress: {i + 1} items translated")
        
        # Save final translated data
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(translated_data, f, ensure_ascii=False, indent=2)
        
        # Remove temporary file
        if Path(temp_output_path).exists():
            Path(temp_output_path).unlink()
        
        logger.success(f"Translation completed successfully!")
        logger.info(f"Translated data saved to: {output_path}")
        return output_path
    
    except Exception as e:
        logger.error(f"Error translating file: {str(e)}")
        raise
