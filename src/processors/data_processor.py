import json
import pandas as pd
from datetime import datetime
from pathlib import Path
from typing import List
from loguru import logger
from ..models.legislative_process import LegislativeProcess

class DataProcessor:
    """Process and store legislative process data."""
    
    def __init__(self, data_dir: str = "data"):
        self.data_dir = Path(data_dir)
        self.raw_dir = self.data_dir / "raw"
        self.processed_dir = self.data_dir / "processed"
        
        # Create directories if they don't exist
        self.raw_dir.mkdir(parents=True, exist_ok=True)
        self.processed_dir.mkdir(parents=True, exist_ok=True)
    
    def save_raw_data(self, processes: List[LegislativeProcess], year: int) -> None:
        """Save raw JSON data for a specific year."""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = self.raw_dir / f"legislative_processes_{year}_{timestamp}.json"
        
        # Convert to JSON-serializable format
        data = [process.model_dump() for process in processes]
        
        with open(filename, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2, default=str)
        
        logger.info(f"Saved raw data to {filename}")
    
    def process_to_dataframe(self, processes: List[LegislativeProcess]) -> pd.DataFrame:
        """Convert legislative processes to a pandas DataFrame."""
        data = [process.model_dump() for process in processes]
        df = pd.DataFrame(data)
        
        # Convert datetime columns
        datetime_columns = ['data_apresentacao']
        for col in datetime_columns:
            if col in df.columns:
                df[col] = pd.to_datetime(df[col])
        
        return df
    
    def save_processed_data(self, df: pd.DataFrame, year: int) -> None:
        """Save processed data as CSV and Excel files."""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        base_filename = f"legislative_processes_{year}_{timestamp}"
        
        # Save as CSV
        csv_path = self.processed_dir / f"{base_filename}.csv"
        df.to_csv(csv_path, index=False, encoding='utf-8')
        logger.info(f"Saved processed data to CSV: {csv_path}")
        
        # Save as Excel
        excel_path = self.processed_dir / f"{base_filename}.xlsx"
        df.to_excel(excel_path, index=False)
        logger.info(f"Saved processed data to Excel: {excel_path}")
    
    def process_and_save(self, processes: List[LegislativeProcess], year: int) -> None:
        """Process and save data in both raw and processed formats."""
        # Save raw data
        self.save_raw_data(processes, year)
        
        # Process and save as DataFrame
        df = self.process_to_dataframe(processes)
        self.save_processed_data(df, year)
        
        logger.info(f"Successfully processed and saved data for year {year}")
        logger.info(f"Total processes: {len(processes)}") 