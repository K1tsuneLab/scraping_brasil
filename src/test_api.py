import asyncio
import json
import sys
from pathlib import Path
from datetime import datetime

# Add the project root to Python path
project_root = Path(__file__).parent.parent
sys.path.append(str(project_root))

from loguru import logger
from src.api.senate_client import SenateAPIClient

async def test_api():
    async with SenateAPIClient() as client:
        try:
            # Test single year request
            url = f"{client.BASE_URL}?ano=2023&v=1"
            async with client.session.get(url, headers=client.headers) as response:
                response.raise_for_status()
                data = await response.json()
                
                # Take only first 5 items from the response
                if isinstance(data, list):
                    sample_data = data[:5]
                else:
                    # If it's a dict, try to get items from ListaMateriasTramitando
                    sample_data = data.get('ListaMateriasTramitando', [])[:5]
                
                # Save to JSON file
                output_file = project_root / 'data' / 'raw' / f'sample_data_{datetime.now().strftime("%Y%m%d_%H%M%S")}.json'
                with open(output_file, 'w', encoding='utf-8') as f:
                    json.dump(sample_data, f, indent=2, ensure_ascii=False)
                
                print(f"Saved 5 sample items to: {output_file}")
                print("\nSample data preview:")
                print(json.dumps(sample_data, indent=2, ensure_ascii=False))
                
        except Exception as e:
            logger.error(f"Error: {str(e)}")
            raise

if __name__ == "__main__":
    asyncio.run(test_api()) 