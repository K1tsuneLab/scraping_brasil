import requests
import json
from datetime import datetime
import time
from typing import List, Dict, Optional

def fetch_proposicoes_page(start_date: str, page: int = 1, items_per_page: int = 100, retries: int = 3, delay: int = 1) -> Optional[Dict]:
    """
    Fetch a page of propositions since the specified date.
    
    Args:
        start_date (str): Start date in YYYY-MM-DD format
        page (int): Page number to fetch
        items_per_page (int): Number of items per page
        retries (int): Number of retry attempts
        delay (int): Delay between retries in seconds
        
    Returns:
        Optional[Dict]: Dictionary containing 'dados' (data) and 'links' (pagination info) or None if failed
    """
    url = "https://dadosabertos.camara.leg.br/api/v2/proposicoes"
    params = {
        'dataApresentacaoInicio': start_date,
        'ordem': 'ASC',
        'ordenarPor': 'id',
        'itens': items_per_page,
        'pagina': page
    }
    
    for attempt in range(retries):
        try:
            print(f"Fetching page {page} (items per page: {items_per_page})")
            response = requests.get(url, params=params)
            response.raise_for_status()
            data = response.json()
            
            if 'dados' in data and isinstance(data['dados'], list):
                return data
            else:
                print(f"Unexpected response format: {data.keys()}")
                return None
                
        except requests.exceptions.RequestException as e:
            if attempt == retries - 1:  # Last attempt
                print(f"Error fetching page {page} after {retries} attempts: {e}")
                return None
            print(f"Attempt {attempt + 1} failed, retrying in {delay} seconds...")
            time.sleep(delay)

def fetch_all_proposicoes(start_date: str) -> List[Dict]:
    """
    Fetch all propositions since the specified date using pagination.
    
    Args:
        start_date (str): Start date in YYYY-MM-DD format
        
    Returns:
        List[Dict]: List of all propositions
    """
    all_propositions = []
    page = 1
    items_per_page = 100  # Maximum allowed by the API
    
    while True:
        result = fetch_proposicoes_page(start_date, page, items_per_page)
        
        if not result or not result['dados']:
            break
            
        all_propositions.extend(result['dados'])
        print(f"Total propositions fetched so far: {len(all_propositions)}")
        
        # Check if there are more pages
        links = result.get('links', [])
        has_next = any(link.get('rel') == 'next' for link in links)
        
        if not has_next:
            break
            
        page += 1
        time.sleep(1)  # Be nice to the API
    
    return all_propositions

def process_proposicoes(proposicoes: List[Dict]) -> List[Dict]:
    """
    Process and clean the propositions data.
    
    Args:
        proposicoes (List[Dict]): Raw propositions data
        
    Returns:
        List[Dict]: Cleaned and processed propositions
    """
    processed = []
    
    for prop in proposicoes:
        # Extract relevant fields and clean data
        processed_prop = {
            'id': prop.get('id', ''),
            'siglaTipo': prop.get('siglaTipo', ''),
            'numero': prop.get('numero', ''),
            'ano': prop.get('ano', ''),
            'ementa': prop.get('ementa', ''),
            'dataApresentacao': prop.get('dataApresentacao', ''),
            'uri': prop.get('uri', ''),
            'uriAutores': prop.get('uriAutores', ''),
            'statusProposicao': {
                'dataHora': prop.get('statusProposicao', {}).get('dataHora', ''),
                'sequencia': prop.get('statusProposicao', {}).get('sequencia', ''),
                'siglaOrgao': prop.get('statusProposicao', {}).get('siglaOrgao', ''),
                'regime': prop.get('statusProposicao', {}).get('regime', ''),
                'descricaoTramitacao': prop.get('statusProposicao', {}).get('descricaoTramitacao', ''),
                'descricaoSituacao': prop.get('statusProposicao', {}).get('descricaoSituacao', ''),
                'despacho': prop.get('statusProposicao', {}).get('despacho', '')
            }
        }
        processed.append(processed_prop)
    
    return processed

def save_to_json(proposicoes: List[Dict], filename: str = 'proposicoes_since_2023.json'):
    """Save the propositions to a JSON file with timestamp."""
    try:
        # Add timestamp to filename
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        filename_with_timestamp = f"{filename.rsplit('.', 1)[0]}_{timestamp}.json"
        
        with open(filename_with_timestamp, 'w', encoding='utf-8') as f:
            json.dump(proposicoes, f, ensure_ascii=False, indent=2)
        print(f"Successfully saved {len(proposicoes)} propositions to {filename_with_timestamp}")
        return filename_with_timestamp
    except Exception as e:
        print(f"Error saving to JSON: {e}")
        return None

def main():
    start_date = "2023-02-01"
    print(f"Starting extraction of propositions since {start_date}...")
    
    # Fetch all data
    proposicoes = fetch_all_proposicoes(start_date)
    
    if proposicoes:
        # Process and store results
        processed = process_proposicoes(proposicoes)
        
        # Save results with timestamp
        output_file = save_to_json(processed)
        
        if output_file:
            print("\nExtraction Summary:")
            print(f"- Total propositions fetched: {len(processed)}")
            print(f"- Output file: {output_file}")
            print("\nDate range:")
            dates = sorted([p['dataApresentacao'] for p in processed if p['dataApresentacao']])
            if dates:
                print(f"- First proposition date: {dates[0]}")
                print(f"- Last proposition date: {dates[-1]}")
            
            print("\nTypes of propositions:")
            types = {}
            for prop in processed:
                tipo = prop['siglaTipo']
                types[tipo] = types.get(tipo, 0) + 1
            for tipo, count in sorted(types.items()):
                print(f"- {tipo}: {count}")
    else:
        print("Extraction failed: No propositions were fetched")

if __name__ == "__main__":
    main() 