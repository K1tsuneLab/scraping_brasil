# Brazilian Legislative Data Pipeline

A comprehensive data pipeline for extracting, processing, and storing Brazilian Senate legislative data into a PostgreSQL database. This project handles the complete workflow from data extraction to database migration, with support for multilingual content (Portuguese to Spanish translation).

## 🌟 Features

- Automated data extraction from Brazilian Senate's Open Data API
- Robust PostgreSQL database integration
- Data validation and cleaning
- Portuguese to Spanish translation capabilities
- Asynchronous processing for improved performance
- Comprehensive error handling and logging
- Progress tracking and reporting
- Configurable through environment variables

## 📋 Prerequisites

- Python 3.8 or higher
- PostgreSQL database
- Internet connection for API access
- API key for translation service (if using translation features)

## 🚀 Quick Start

1. **Clone the repository**
   ```bash
   git clone [your-repo-url]
   cd scraping_brasil
   ```

2. **Set up virtual environment**
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Unix/macOS
   # or
   .\venv\Scripts\activate  # On Windows
   ```

3. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

4. **Configure environment variables**
   Create a `.env` file in the project root:
   ```env
   DB_HOST=localhost
   DB_PORT=5432
   DB_NAME=postgres
   DB_USER=postgres
   DB_PASSWORD=your_password
   ```

5. **Run the data pipeline**
   ```bash
   python db_migration.py
   ```

## 🗄️ Project Structure

```
scraping_brasil/
├── data/                   # Data storage
│   ├── raw/               # Raw API data
│   └── processed/         # Processed JSON files
├── src/                   # Source code
│   ├── api/              # API interaction modules
│   ├── models/           # Data models
│   ├── processors/       # Data processing logic
│   └── utils/            # Utility functions
├── logs/                  # Log files
├── tests/                # Test suites
├── .env                  # Environment configuration
├── db_migration.py       # Database migration script
├── requirements.txt      # Project dependencies
└── README.md            # Project documentation
```

## 💾 Database Schema

The project uses two main tables:

### Gacetas Table
- `id_gaceta` (Primary Key)
- `id_pais` (Country identifier)
- `numero_gaceta` (Gazette number)
- `anio` (Year)
- `fecha_publicacion` (Publication date)
- `enlace_pdf` (PDF link)
- `estado` (Status)
- `id_institucion` (Institution identifier)

### Proyectos Table
- `id_proyecto` (Primary Key)
- `numero_proyecto` (Project number)
- `anio_legislativo` (Legislative year)
- `titulo_proyecto` (Project title)
- `autores_proyecto` (Project authors)

## 🔧 Configuration

The project uses environment variables for configuration. Create a `.env` file with the following variables:

```env
DB_HOST=your_host
DB_PORT=your_port
DB_NAME=your_database
DB_USER=your_username
DB_PASSWORD=your_password
```

## 📊 Data Processing

The pipeline performs the following steps:
1. Extracts data from the Brazilian Senate API
2. Processes and validates the data
3. Translates relevant content from Portuguese to Spanish
4. Migrates the data to PostgreSQL database
5. Handles duplicates and updates existing records

## 🛠️ Usage Examples

### Running the Database Migration
```bash
python db_migration.py
```

### Data Extraction
```bash
python src/main.py extract-api --start 2023-02-01 --end 2025-05-21
```

### Translation
```bash
python src/main.py translate --file data/processed/senate_processes.json
```

## 📝 Logging

The project includes comprehensive logging:
- Success/failure of database operations
- Processing statistics
- Error tracking
- Progress monitoring

Logs are stored in the `logs/` directory.

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch
3. Commit your changes
4. Push to the branch
5. Create a Pull Request

## 📄 License

[Your License Here]

## 📞 Support

For support, please [create an issue](your-repo-issues-url) or contact the maintainers.

## 🙏 Acknowledgments

- Brazilian Senate Open Data API
- Contributors and maintainers
- Open source community