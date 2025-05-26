"""
Text translation utility for converting Portuguese text to Spanish.
"""
import asyncio
from typing import Dict, Any, Optional, Union
from loguru import logger

class TranslationError(Exception):
    """Exception raised for errors in the translation process."""
    pass

async def translate_text_pt_to_es(text: str) -> str:
    """
    Translate text from Portuguese to Spanish.
    
    Args:
        text (str): The Portuguese text to translate
        
    Returns:
        str: The translated Spanish text
        
    Raises:
        TranslationError: If translation fails
    """
    try:
        # We'll use deep-translator which is more reliable than googletrans
        from deep_translator import GoogleTranslator
        
        # Handle empty text
        if not text or not text.strip():
            return text
            
        # GoogleTranslator has character limit per request
        # We'll split long texts and translate in chunks if needed
        MAX_CHARS = 5000  # Google Translate limit
        
        if len(text) <= MAX_CHARS:
            translator = GoogleTranslator(source='pt', target='es')
            return translator.translate(text)
        else:
            # Split into chunks that respect word boundaries
            chunks = []
            start = 0
            while start < len(text):
                end = min(start + MAX_CHARS, len(text))
                
                # If we're in the middle of a word and not at the end of text,
                # move back to the last space
                if end < len(text) and not text[end].isspace():
                    # Find the last space within the chunk
                    last_space = text.rfind(' ', start, end)
                    if last_space != -1:  # If space found
                        end = last_space + 1
                
                chunks.append(text[start:end])
                start = end
            
            # Translate each chunk
            translator = GoogleTranslator(source='pt', target='es')
            translated_chunks = [translator.translate(chunk) for chunk in chunks]
            
            # Join the translated chunks
            return ''.join(translated_chunks)
    
    except ImportError:
        logger.error("deep-translator package not installed. Run 'pip install deep-translator'")
        raise TranslationError("Translation library not available")
    except Exception as e:
        logger.error(f"Translation error: {str(e)}")
        raise TranslationError(f"Failed to translate text: {str(e)}")

async def translate_json_pt_to_es(data: Union[Dict[str, Any], list]) -> Union[Dict[str, Any], list]:
    """
    Translate text fields in a JSON structure from Portuguese to Spanish.
    
    Args:
        data (dict or list): The data structure containing text to translate
        
    Returns:
        dict or list: The structure with translated text fields
    """
    # Handle dictionaries
    if isinstance(data, dict):
        translated_data = {}
        for key, value in data.items():
            # Skip None values
            if value is None:
                translated_data[key] = None
                continue
                
            # Translate string values
            if isinstance(value, str) and len(value.strip()) > 0:
                try:
                    translated_data[key] = await translate_text_pt_to_es(value)
                except TranslationError:
                    # Keep original on error
                    translated_data[key] = value
                    logger.warning(f"Failed to translate field {key}, keeping original")
            # Recursively translate nested dictionaries and lists
            elif isinstance(value, (dict, list)):
                translated_data[key] = await translate_json_pt_to_es(value)
            else:
                # Keep non-string values unchanged
                translated_data[key] = value
        return translated_data
    
    # Handle lists
    elif isinstance(data, list):
        translated_list = []
        for item in data:
            if isinstance(item, (dict, list)):
                translated_list.append(await translate_json_pt_to_es(item))
            elif isinstance(item, str) and len(item.strip()) > 0:
                try:
                    translated_list.append(await translate_text_pt_to_es(item))
                except TranslationError:
                    translated_list.append(item)
                    logger.warning("Failed to translate list item, keeping original")
            else:
                translated_list.append(item)
        return translated_list
    
    # Return unchanged for other types
    else:
        return data

async def translate_file_pt_to_es(input_file_path: str, output_file_path: Optional[str] = None) -> str:
    """
    Translate a JSON file from Portuguese to Spanish.
    
    Args:
        input_file_path (str): Path to the input JSON file
        output_file_path (str, optional): Path to save the translated JSON file.
            If not provided, will generate a path based on input file.
            
    Returns:
        str: The path to the translated file
    """
    import json
    from pathlib import Path
    
    try:
        # Read the input file
        with open(input_file_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        # Generate output path if not provided
        if output_file_path is None:
            input_path = Path(input_file_path)
            output_path = input_path.parent / f"{input_path.stem}_es{input_path.suffix}"
            output_file_path = str(output_path)
        
        # Translate the data
        translated_data = await translate_json_pt_to_es(data)
        
        # Write the translated data
        with open(output_file_path, 'w', encoding='utf-8') as f:
            json.dump(translated_data, f, ensure_ascii=False, indent=2)
        
        logger.info(f"Successfully translated file to {output_file_path}")
        return output_file_path
    
    except json.JSONDecodeError:
        logger.error(f"Invalid JSON file: {input_file_path}")
        raise
    except Exception as e:
        logger.error(f"Error translating file {input_file_path}: {str(e)}")
        raise
