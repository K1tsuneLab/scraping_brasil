import aiohttp
import asyncio
from datetime import datetime
from typing import List, Optional
from loguru import logger
from models.legislative_process import APIResponse, LegislativeProcess

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
        
        def map_fields(item):
            def safe_int(val):
                try:
                    return int(val)
                except (ValueError, TypeError):
                    return None
            identificacao = item.get('identificacao', '')
            numero = item.get('numero')
            ano = item.get('ano')
            # Try to extract from identificacao if not present or not valid
            if not numero or not str(numero).isdigit():
                if ' ' in identificacao and '/' in identificacao:
                    try:
                        numero = safe_int(identificacao.split()[1].split('/')[0])
                    except Exception:
                        numero = None
                else:
                    numero = safe_int(numero)
            else:
                numero = safe_int(numero)
            if not ano or not str(ano).isdigit():
                if '/' in identificacao:
                    try:
                        ano = safe_int(identificacao.split('/')[-1])
                    except Exception:
                        ano = None
                else:
                    ano = safe_int(ano)
            else:
                ano = safe_int(ano)
            return {
                'id': item.get('id') or item.get('codigoMateria'),
                'sigla': item.get('sigla') or item.get('casaIdentificadora'),
                'numero': numero,
                'ano': ano,
                'data_apresentacao': item.get('data_apresentacao') or item.get('dataApresentacao'),
                'descricao': item.get('descricao') or item.get('objetivo'),
                'autor': item.get('autor') or item.get('autoria'),
                'ementa': item.get('ementa'),
                'situacao': item.get('situacao') or item.get('tramitando'),
                'link_inteiro_teor': item.get('link_inteiro_teor') or item.get('urlDocumento'),
            }
        
        try:
            async with self.session.get(url, headers=self.headers) as response:
                response.raise_for_status()
                data = await response.json()
                logger.debug(f"API Response for year {year}: {data}")
                # If the response is a list, parse each item as LegislativeProcess
                if isinstance(data, list):
                    processes = []
                    for item in data:
                        try:
                            mapped = map_fields(item)
                            # Parse date if present
                            if mapped['data_apresentacao']:
                                try:
                                    mapped['data_apresentacao'] = datetime.fromisoformat(mapped['data_apresentacao'])
                                except Exception:
                                    pass
                            process = LegislativeProcess(**mapped)
                            processes.append(process)
                        except Exception as e:
                            logger.error(f"Error parsing process item: {str(e)}")
                            continue
                    return processes
                # If the response is a dict, try the old logic
                elif isinstance(data, dict):
                    # Try to find the list of items in known keys
                    items = []
                    if 'ListaMateriasTramitando' in data:
                        items.extend(data['ListaMateriasTramitando'])
                    if 'ListaMateriasNaoTramitando' in data:
                        items.extend(data['ListaMateriasNaoTramitando'])
                    if items:
                        processes = []
                        for item in items:
                            try:
                                mapped = map_fields(item)
                                if mapped['data_apresentacao']:
                                    try:
                                        mapped['data_apresentacao'] = datetime.fromisoformat(mapped['data_apresentacao'])
                                    except Exception:
                                        pass
                                process = LegislativeProcess(**mapped)
                                processes.append(process)
                            except Exception as e:
                                logger.error(f"Error parsing process item: {str(e)}")
                                continue
                        return processes
                    try:
                        api_response = APIResponse(**data)
                        return api_response.get_processes()
                    except Exception as e:
                        logger.error(f"Error parsing API response: {str(e)}")
                        raise
                else:
                    logger.error(f"Unexpected API response type: {type(data)}")
                    return []
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
                logger.info(f"Raw processes fetched for year {year}: {len(processes)}")
                
                # Log sample of processes to understand the data structure
                if processes:
                    sample = processes[0]
                    logger.info(f"Sample process data for year {year}:")
                    logger.info(f"Fields: {sample.dict().keys()}")
                    logger.info(f"Data apresentacao: {sample.data_apresentacao}")
                    logger.info(f"Ano: {sample.ano}")
                    logger.info(f"Sigla: {sample.sigla}")
                    logger.info(f"Numero: {sample.numero}")
                
                # Filter processes by date range, but include those without data_apresentacao
                filtered_processes = [
                    p for p in processes 
                    if p.data_apresentacao and start_date <= p.data_apresentacao <= end_date
                ]
                
                all_processes.extend(filtered_processes)
                logger.info(f"Successfully filtered {len(filtered_processes)} processes for year {year}")
            except Exception as e:
                logger.error(f"Failed to fetch processes for year {year}: {str(e)}")
                continue
        
        return all_processes 