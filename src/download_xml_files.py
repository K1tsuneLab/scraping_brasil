#!/usr/bin/env python3

import json
import os
import aiohttp
import asyncio
from pathlib import Path
from loguru import logger
from typing import List, Dict, Any
import xml.etree.ElementTree as ET

# Define paths
GOOGLE_DRIVE_PATH = Path("/Users/imakia/Google Drive/My Drive/Kitsune/Fase1_Estructuracion_base/Brasil/xml_Camara")
JSON_FILE = "proposicoes_since_2023_20250603_200223.json"  # The JSON file containing the propositions

# Create the XML directory if it doesn't exist
GOOGLE_DRIVE_PATH.mkdir(parents=True, exist_ok=True)

async def download_xml(session: aiohttp.ClientSession, prop_id: int, output_dir: Path) -> bool:
    """
    Download XML content for a specific proposition.
    
    Args:
        session: aiohttp client session
        prop_id: Proposition ID
        output_dir: Directory to save XML files
    
    Returns:
        bool: True if successful, False otherwise
    """
    url = f"https://www.camara.leg.br/SitCamaraWS/Proposicoes.asmx/ObterProposicaoPorID?IdProp={prop_id}"
    
    try:
        async with session.get(url) as response:
            if response.status == 200:
                content = await response.text()
                
                # Validate that it's valid XML
                try:
                    ET.fromstring(content)
                except ET.ParseError:
                    logger.error(f"Invalid XML received for proposition {prop_id}")
                    return False
                
                # Save the XML file
                output_file = output_dir / f"proposition_{prop_id}.xml"
                with open(output_file, "w", encoding="utf-8") as f:
                    f.write(content)
                
                logger.info(f"Successfully downloaded XML for proposition {prop_id}")
                return True
            else:
                logger.error(f"Failed to download XML for proposition {prop_id}: HTTP {response.status}")
                return False
    except Exception as e:
        logger.error(f"Error downloading XML for proposition {prop_id}: {str(e)}")
        return False

async def process_propositions(json_file: str, target_types: List[str]) -> None:
    """
    Process propositions from JSON file and download their XML files.
    
    Args:
        json_file: Path to the JSON file containing propositions
        target_types: List of proposition types to process (e.g., ['PL', 'PLV'])
    """
    try:
        # Load propositions from JSON file
        with open(json_file, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        # Filter propositions by type
        filtered_props = [
            prop for prop in data
            if prop.get('siglaTipo') in target_types
        ]
        
        logger.info(f"Found {len(filtered_props)} propositions of types {', '.join(target_types)}")
        
        # Download XML files
        async with aiohttp.ClientSession() as session:
            tasks = []
            for prop in filtered_props:
                prop_id = prop.get('id')
                if prop_id:
                    task = download_xml(session, prop_id, GOOGLE_DRIVE_PATH)
                    tasks.append(task)
            
            # Run downloads concurrently with a limit of 5 concurrent downloads
            for i in range(0, len(tasks), 5):
                batch = tasks[i:i+5]
                await asyncio.gather(*batch)
    except Exception as e:
        logger.error(f"Error processing propositions: {str(e)}")

def main():
    # Target proposition types
    target_types = ['PLV', 'PLN', 'PLP', 'PL']
    
    logger.info(f"Starting XML download for proposition types: {', '.join(target_types)}")
    logger.info(f"Output directory: {GOOGLE_DRIVE_PATH}")
    
    # Run the async process
    asyncio.run(process_propositions(JSON_FILE, target_types))
    
    logger.info("XML download process completed")

if __name__ == "__main__":
    main() 