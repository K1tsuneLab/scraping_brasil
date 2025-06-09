import os
import json
import logging
from datetime import datetime
import requests
import pandas as pd
from tqdm import tqdm
import time
from pathlib import Path
import io

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('logs/historical_data_download.log'),
        logging.StreamHandler()
    ]
)

logger = logging.getLogger(__name__)

# Define base directory for data storage
BASE_DIR = Path("/Users/imakia/Google Drive/My Drive/Kitsune/Fase1_Estructuracion_base/Brasil")

class DownloadStats:
    def __init__(self):
        self.total_camara = 0
        self.total_senado = 0
        self.by_year_camara = {}
        self.by_year_senado = {}
        self.current_status = ""
        self.load_existing_stats()
    
    def load_existing_stats(self):
        """Load existing statistics if available."""
        stats_file = BASE_DIR / "historico" / "download_stats.json"
        if stats_file.exists():
            try:
                with open(stats_file, 'r', encoding='utf-8') as f:
                    stats = json.load(f)
                    self.by_year_camara = stats['by_year']['camara']
                    self.by_year_senado = stats['by_year']['senado']
                    self.total_camara = stats['total_projects']['camara']
                    self.total_senado = stats['total_projects']['senado']
                    logger.info("Loaded existing statistics")
            except Exception as e:
                logger.error(f"Error loading existing stats: {e}")
    
    def add_camara(self, year, count):
        self.total_camara += count
        self.by_year_camara[str(year)] = count
        self.update_status()
    
    def add_senado(self, year, count):
        self.total_senado += count
        self.by_year_senado[str(year)] = count
        self.update_status()
    
    def update_status(self):
        self.current_status = f"""
Current Download Status:
-----------------------
Câmara dos Deputados: {self.total_camara} projects
Senado Federal: {self.total_senado} projects
Total: {self.total_camara + self.total_senado} projects

By Year:
Câmara: {dict(sorted(self.by_year_camara.items()))}
Senado: {dict(sorted(self.by_year_senado.items()))}
"""
        print("\n" + self.current_status)
    
    def save_stats(self):
        stats = {
            "total_projects": {
                "camara": self.total_camara,
                "senado": self.total_senado,
                "total": self.total_camara + self.total_senado
            },
            "by_year": {
                "camara": self.by_year_camara,
                "senado": self.by_year_senado
            }
        }
        
        stats_file = BASE_DIR / "historico" / "download_stats.json"
        with open(stats_file, 'w', encoding='utf-8') as f:
            json.dump(stats, f, ensure_ascii=False, indent=2)
        
        logger.info(f"Total projects downloaded - Câmara: {self.total_camara}, Senado: {self.total_senado}")
        logger.info(f"Total combined projects: {self.total_camara + self.total_senado}")

def get_total_pages(base_url, year):
    """Get total number of pages for Câmara data."""
    try:
        params = {"ano": year, "itens": 100, "pagina": 1}
        response = requests.get(base_url, params=params)
        response.raise_for_status()
        data = response.json()
        return (data['links'][0]['total'] // 100) + 1
    except:
        return None

def download_camara_data(start_year, end_year, end_date, stats):
    """Download data from Câmara dos Deputados."""
    base_url = "https://dadosabertos.camara.leg.br/api/v2/proposicoes"
    output_dir = BASE_DIR / "historico" / "camara"
    output_dir.mkdir(parents=True, exist_ok=True)
    
    years = list(range(start_year, end_year + 1))
    for year in tqdm(years, desc="Processing years (Câmara)", unit="year"):
        # Skip if already downloaded
        if str(year) in stats.by_year_camara:
            logger.info(f"Skipping year {year} (already downloaded)")
            continue
            
        logger.info(f"Downloading Câmara data for year {year}")
        print(f"\nProcessing Câmara data for year {year}")
        
        total_pages = get_total_pages(base_url, year)
        params = {
            "ano": year,
            "itens": 100,
            "pagina": 1
        }
        
        all_proposicoes = []
        
        if total_pages:
            pbar = tqdm(total=total_pages, desc=f"Downloading pages for {year}", unit="page")
        
        while True:
            try:
                response = requests.get(base_url, params=params)
                response.raise_for_status()
                data = response.json()
                
                if not data['dados']:
                    break
                
                # Filter propositions by date if it's the end year
                if year == end_year:
                    filtered_data = [
                        prop for prop in data['dados']
                        if 'dataApresentacao' in prop and
                        datetime.fromisoformat(prop['dataApresentacao'].split('T')[0]) <= end_date
                    ]
                    all_proposicoes.extend(filtered_data)
                else:
                    all_proposicoes.extend(data['dados'])
                
                params['pagina'] += 1
                if total_pages:
                    pbar.update(1)
                print(f"Downloaded {len(all_proposicoes)} propositions so far...")
                
                time.sleep(1)  # Respect rate limits
                
            except requests.exceptions.RequestException as e:
                logger.error(f"Error downloading Câmara data for year {year}: {e}")
                break
        
        if total_pages:
            pbar.close()
        
        if all_proposicoes:
            output_file = output_dir / f"proposicoes_camara_{year}.json"
            with open(output_file, 'w', encoding='utf-8') as f:
                json.dump(all_proposicoes, f, ensure_ascii=False, indent=2)
            
            stats.add_camara(year, len(all_proposicoes))
            logger.info(f"Saved {len(all_proposicoes)} propositions for year {year}")
            # Save stats after each year
            stats.save_stats()

def download_senado_data(start_year, end_year, end_date, stats):
    """Download data from Senado Federal."""
    base_url = "https://legis.senado.leg.br/dadosabertos/materia/pesquisa/lista"
    output_dir = BASE_DIR / "historico" / "senado"
    output_dir.mkdir(parents=True, exist_ok=True)
    
    years = list(range(start_year, end_year + 1))
    for year in tqdm(years, desc="Processing years (Senado)", unit="year"):
        logger.info(f"Downloading Senado data for year {year}")
        print(f"\nProcessing Senado data for year {year}")
        
        # Parameters for the Senado API
        params = {
            "ano": year,
            "sigla": "PL"  # Projetos de Lei
        }
        
        try:
            print(f"Downloading data...")
            response = requests.get(base_url, params=params)
            response.raise_for_status()
            
            print(f"Parsing XML data...")
            # Convert response content to string buffer
            content_str = io.StringIO(response.content.decode('utf-8'))
            
            # Use pandas to parse XML and convert to DataFrame
            df = pd.read_xml(content_str, xpath=".//PesquisaBasicaMateria/Materias/Materia")
            
            if not df.empty:
                # Convert date columns
                date_columns = ['DataApresentacao', 'DataLeitura', 'DataVencimento']
                for col in date_columns:
                    if col in df.columns:
                        df[col] = pd.to_datetime(df[col], errors='coerce')
                
                # Filter by date if it's the end year
                if year == end_year:
                    print(f"Filtering data for end year...")
                    df = df[df['DataApresentacao'] <= end_date]
                
                # Convert to records format
                materias = df.to_dict('records')
                
                print(f"Saving {len(materias)} records...")
                output_file = output_dir / f"materias_senado_{year}.json"
                with open(output_file, 'w', encoding='utf-8') as f:
                    json.dump(materias, f, ensure_ascii=False, indent=2)
                
                stats.add_senado(year, len(materias))
                logger.info(f"Saved {len(materias)} materials for year {year}")
                
                # Print some sample data for verification
                if len(materias) > 0:
                    print("\nSample data from first record:")
                    sample = materias[0]
                    print(f"- Número: {sample.get('Numero', 'N/A')}")
                    print(f"- Ementa: {sample.get('Ementa', 'N/A')[:100]}...")
                    print(f"- Data Apresentação: {sample.get('DataApresentacao', 'N/A')}")
                
                # Save stats after each year
                stats.save_stats()
            else:
                logger.warning(f"No materials found for year {year}")
            
            time.sleep(1)  # Respect rate limits
            
        except Exception as e:
            logger.error(f"Error downloading Senado data for year {year}: {e}")
            print(f"Error: {e}")
            # Print the raw response for debugging
            print("\nRaw response content:")
            print(response.content[:500].decode('utf-8'))

def verify_downloaded_data():
    """Verify which years are missing from the downloaded data."""
    camara_dir = BASE_DIR / "historico" / "camara"
    senado_dir = BASE_DIR / "historico" / "senado"
    
    # Check Câmara files
    camara_files = list(camara_dir.glob("proposicoes_camara_*.json"))
    camara_years = {int(f.stem.split('_')[-1]) for f in camara_files}
    
    # Check Senado files
    senado_files = list(senado_dir.glob("materias_senado_*.json"))
    senado_years = {int(f.stem.split('_')[-1]) for f in senado_files}
    
    print("\nData Verification Results:")
    print("========================")
    print("\nCâmara dos Deputados:")
    print(f"Years present: {sorted(camara_years)}")
    print(f"Missing years (2015-2023): {sorted(set(range(2015, 2024)) - camara_years)}")
    
    print("\nSenado Federal:")
    print(f"Years present: {sorted(senado_years)}")
    print(f"Missing years (2015-2023): {sorted(set(range(2015, 2024)) - senado_years)}")
    
    return camara_years, senado_years

def main():
    """Main function to orchestrate the download process."""
    try:
        print("\nStarting download of historical legislative data...")
        print("================================================")
        
        # Create necessary directories
        for house in ["camara", "senado"]:
            (BASE_DIR / "historico" / house).mkdir(parents=True, exist_ok=True)
        
        # Verify existing data
        print("\nVerifying existing data...")
        camara_years, senado_years = verify_downloaded_data()
        
        # Set date range
        start_year = 2015
        end_date = datetime(2023, 2, 1)
        end_year = end_date.year
        
        print(f"\nDownload Configuration:")
        print(f"- Start Year: {start_year}")
        print(f"- End Date: {end_date.strftime('%Y-%m-%d')}")
        print(f"- Output Directory: {BASE_DIR}/historico")
        print("\nStarting downloads...\n")
        
        # Initialize statistics
        stats = DownloadStats()
        
        # Download missing Câmara data (2022)
        if 2022 not in camara_years:
            print("\nDownloading Câmara dos Deputados data for 2022...")
            print("=============================================")
            download_camara_data(2022, 2022, end_date, stats)
        else:
            print("\nCâmara data for 2022 is already present.")
        
        # Download Senado data (all years)
        print("\nDownloading Senado Federal data...")
        print("==============================")
        download_senado_data(start_year, end_year, end_date, stats)
        
        # Save statistics
        stats.save_stats()
        
        # Final verification
        print("\nPerforming final verification...")
        final_camara_years, final_senado_years = verify_downloaded_data()
        
        print("\nDownload completed successfully!")
        print("Final Statistics:")
        print(stats.current_status)
        
        logger.info("Data download completed successfully")
        
    except Exception as e:
        logger.error(f"An error occurred: {e}")
        print(f"\nError: {e}")

if __name__ == "__main__":
    main() 