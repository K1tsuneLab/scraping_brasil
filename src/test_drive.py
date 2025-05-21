import json
from pathlib import Path
from datetime import datetime

# Define Google Drive path
GOOGLE_DRIVE_PATH = Path("/Users/jona/Google Drive/My Drive/Kitsune/Fase1_Estructuracion_base/Brasil/json/json")

def test_drive_path():
    # Test data
    test_data = {
        "test": "data",
        "timestamp": datetime.now().isoformat()
    }
    
    # Ensure directory exists
    if not GOOGLE_DRIVE_PATH.is_dir():
        raise FileNotFoundError(f"Directory does not exist: {GOOGLE_DRIVE_PATH}")
    
    # Save test file
    output_file = GOOGLE_DRIVE_PATH / f"test_file_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
    
    try:
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(test_data, f, indent=2, ensure_ascii=False)
        print(f"Successfully saved test file to: {output_file}")
        print(f"File exists: {output_file.exists()}")
    except Exception as e:
        print(f"Error saving file: {str(e)}")

if __name__ == "__main__":
    test_drive_path()
    # Additional test: save a document with more fields
    test_data = {
        "id": 123,
        "sigla": "SF",
        "numero": 456,
        "ano": 2025,
        "data_apresentacao": datetime.now().isoformat(),
        "descricao": "Test legislative process",
        "autor": "Senador Teste",
        "ementa": "Ementa de teste",
        "situacao": "Sim",
        "link_inteiro_teor": "https://example.com/documento.pdf"
    }
    output_file = GOOGLE_DRIVE_PATH / f"test_legislative_process_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
    try:
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(test_data, f, indent=2, ensure_ascii=False)
        print(f"Successfully saved test legislative process to: {output_file}")
        print(f"File exists: {output_file.exists()}")
    except Exception as e:
        print(f"Error saving test legislative process: {str(e)}") 