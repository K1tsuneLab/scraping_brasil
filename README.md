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

The main script to run the data extraction is:
```bash
python src/main.py
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