import aiohttp
import asyncio
from datetime import datetime
from typing import List, Optional
from loguru import logger
from ..models.legislative_process import APIResponse, LegislativeProcess

class SenateAPIClient:
    """Client for interacting with the Brazilian Senate API."""
    
    BASE_URL = "https://legis.senado.leg.br/dadosabertos/processo"
    
    def __init__(self, session: Optional[aiohttp.ClientSession] = None):
        self.session = session or aiohttp.ClientSession()
        self.headers = {
            "accept": "application/json"
        }
    
    async def __aenter__(self):
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        await self.session.close()
    
    async def get_processes_by_year(self, year: int) -> List[LegislativeProcess]:
        """Fetch legislative processes for a specific year."""
        url = f"{self.BASE_URL}?v=1&ano={year}"
        
        try:
            async with self.session.get(url, headers=self.headers) as response:
                response.raise_for_status()
                data = await response.json()
                
                # Parse response using Pydantic model
                api_response = APIResponse(**data)
                return api_response.get_processes()
                
        except aiohttp.ClientError as e:
            logger.error(f"Error fetching data for year {year}: {str(e)}")
            raise
        except Exception as e:
            logger.error(f"Unexpected error for year {year}: {str(e)}")
            raise
    
    async def get_processes_date_range(self, start_date: datetime, end_date: datetime) -> List[LegislativeProcess]:
        """Fetch legislative processes within a date range."""
        start_year = start_date.year
        end_year = end_date.year
        
        all_processes = []
        for year in range(start_year, end_year + 1):
            try:
                processes = await self.get_processes_by_year(year)
                # Filter processes by date range
                filtered_processes = [
                    p for p in processes 
                    if p.data_apresentacao and start_date <= p.data_apresentacao <= end_date
                ]
                all_processes.extend(filtered_processes)
                logger.info(f"Successfully fetched {len(filtered_processes)} processes for year {year}")
            except Exception as e:
                logger.error(f"Failed to fetch processes for year {year}: {str(e)}")
                continue
        
        return all_processes 