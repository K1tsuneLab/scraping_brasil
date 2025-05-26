# Brazilian Legislative Data Extraction

This project extracts legislative data from the Brazilian Senate's open data API, focusing on legislative processes from February 1st, 2023, to the current date.

## Project Structure

```
scraping_brasil/
├── data/                   # Directory for storing extracted data
│   ├── raw/               # Raw JSON data
│   └── processed/         # Processed and cleaned data
├── src/                   # Source code
│   ├── api/              # API interaction modules
│   ├── models/           # Data models
│   ├── processors/       # Data processing modules
│   └── utils/            # Utility functions
├── logs/                  # Log files
├── tests/                 # Test files
├── .env                   # Environment variables
├── .gitignore            # Git ignore file
└── requirements.txt       # Project dependencies
```

## Setup

1. Create and activate virtual environment:
```bash
python -m venv venv
source venv/bin/activate  # On Unix/macOS
```

2. Install dependencies:
```bash
pip install -r requirements.txt
```

3. Create a `.env` file with your configuration (if needed)

## Usage

The main script supports several commands:

### Data Extraction
```bash
python src/main.py extract-api [--start YYYY-MM-DD] [--end YYYY-MM-DD]
```

### PDF Downloads
```bash
python src/main.py download-pdfs
```

### Text Extraction
```bash
python src/main.py extract-text [--structured]
```

### Text Translation (Portuguese to Spanish)
```bash
# Translate a JSON file
python src/main.py translate --file /path/to/file.json [--output /path/to/output.json]

# Translate text directly
python src/main.py translate --text "Texto em português para traduzir"
```

You can also run a quick translation test:
```bash
python src/test_translate.py
```

## Data Source

The project uses the Brazilian Senate's Open Data API:
- Base URL: https://legis.senado.leg.br/dadosabertos/processo
- Version: v1
- Parameters: ano (year)

## Features

- Asynchronous data extraction
- Data validation using Pydantic models
- Progress tracking with tqdm
- Comprehensive logging
- Data processing and cleaning
- Error handling and retry mechanisms
- Portuguese to Spanish translation of text and JSON files