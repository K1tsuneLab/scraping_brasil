import asyncio
import json
from datetime import datetime
from pathlib import Path
from loguru import logger
from api.senate_client import SenateAPIClient

# Define Google Drive path
GOOGLE_DRIVE_PATH = Path("/Users/jona/Google Drive/My Drive/Kitsune/Fase1_Estructuracion_base/Brasil/json/json")

async def extract_and_save_processes():
    start_date = datetime(2023, 2, 1)
    end_date = datetime.now()
    
    logger.info(f"Starting extraction from {start_date} to {end_date}")
    
    async with SenateAPIClient() as client:
        try:
            # Fetch processes for the date range
            processes = await client.get_processes_date_range(start_date, end_date)
            logger.info(f"Found {len(processes)} processes in the date range")
            
            if not processes:
                logger.warning("No processes found in the specified date range")
                return
            
            # Convert processes to list of dictionaries
            processes_data = [process.dict() for process in processes]
            
            # Create filename with date range
            filename = f"senate_processes_{start_date.strftime('%Y%m%d')}_to_{end_date.strftime('%Y%m%d')}.json"
            output_file = GOOGLE_DRIVE_PATH / filename
            
            # Ensure directory exists
            GOOGLE_DRIVE_PATH.mkdir(parents=True, exist_ok=True)
            
            # Save to file
            class DateTimeEncoder(json.JSONEncoder):
                def default(self, obj):
                    if isinstance(obj, datetime):
                        return obj.isoformat()
                    return super().default(obj)
            with open(output_file, 'w', encoding='utf-8') as f:
                json.dump(processes_data, f, indent=2, ensure_ascii=False, cls=DateTimeEncoder)
            
            logger.info(f"Successfully saved {len(processes)} processes to {output_file}")
            
        except Exception as e:
            logger.error(f"Error during extraction: {str(e)}")
            raise

if __name__ == "__main__":
    # Configure logger
    logger.add(
        "logs/extraction_{time:YYYY-MM-DD_HH-mm-ss}.log",
        rotation="1 day",
        retention="7 days",
        level="INFO"
    )
    
    # Run the extraction
    asyncio.run(extract_and_save_processes()) 