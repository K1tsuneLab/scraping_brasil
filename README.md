# Brazilian Chamber of Deputies Propositions Scraper

This script fetches and processes propositions data from the Brazilian Chamber of Deputies REST API. It retrieves propositions for a specified year and saves them to a JSON file.

## Requirements

- Python 3.6+
- `requests` library
- `python-dateutil` library

## Installation

1. Create a virtual environment (optional but recommended):
```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

2. Install dependencies:
```bash
pip install -r requirements.txt
```

## Usage

The script is configured to fetch propositions for the year 2024 by default. You can modify the year range in the `main()` function of `scrape_proposicoes.py`:

- `start_year`: First year to fetch data for
- `end_year`: Last year to fetch data for

To run the script:

```bash
python scrape_proposicoes.py
```

The script will:
1. Connect to the Chamber of Deputies REST API
2. Fetch propositions for the specified year(s)
3. Process and clean the data
4. Save all propositions to `proposicoes.json`

## Output

The script generates a JSON file (`proposicoes.json`) containing an array of propositions. Each proposition includes:
- `id`: Proposition ID
- `siglaTipo`: Type of proposition (e.g., PL for Projeto de Lei)
- `numero`: Proposition number
- `ano`: Year
- `ementa`: Description/summary
- `dataApresentacao`: Presentation date
- `uri`: API endpoint for more details
- `uriAutores`: API endpoint for authors information
- `statusProposicao`: Current status information including:
  - Processing timestamp
  - Sequence number
  - Department code
  - Processing regime
  - Processing description
  - Situation description
  - Dispatch information

## Error Handling

The script includes error handling for:
- Network request failures (with retries)
- API response validation
- JSON parsing errors
- File saving errors

Errors are logged to the console with appropriate messages.