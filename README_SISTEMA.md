# 🇧🇷 Sistema de Scraping Automatizado - Documentos Gubernamentales de Brasil

## 📋 Descripción General

Sistema completo de scraping automatizado que extrae, valida, procesa y almacena documentos gubernamentales de Brasil desde 2024 hasta la actualidad. Implementa una arquitectura robusta con simulador de Google Drive para desarrollo y sistema de validación de duplicados.

## 🏗️ Arquitectura del Sistema

### Componentes Principales

1. **🚀 Coordinador Principal** (`src/main.py`)
   - Orquesta todo el pipeline de scraping
   - Coordina scraping, validación, almacenamiento y traducción
   - Sistema de reportes y estadísticas

2. **💾 Sistema de Almacenamiento** (`src/storage/`)
   - **Drive Interface**: Abstracción común para operaciones
   - **Mock Drive Manager**: Simulador completo para desarrollo
   - **Drive Factory**: Selector automático entre modo real/simulado
   - **Configuración Flexible**: Soporte para Service Account + OAuth2

3. **🔍 Sistema de Validación** (`src/scraper/validators.py`)
   - Detección de duplicados por ID, hash de contenido y metadatos
   - Filtrado inteligente por fechas
   - Validación de integridad de archivos (PDF, JSON)
   - Cache de metadatos para rendimiento

4. **📅 Utilidades de Fecha** (`src/utils/date_utils.py`)
   - Parsing flexible de múltiples formatos
   - Rangos de fechas personalizables
   - Filtrado desde 2024 hasta hoy

5. **🌐 Clientes API** (`src/api/`)
   - Cliente asíncrono para Senado Federal
   - Integración con Cámara de Diputados existente
   - Manejo de errores y reintentos

6. **🔧 Sistema de Configuración** (`config/settings.py`)
   - Configuración centralizada con variables de entorno
   - Creación automática de directorios
   - Múltiples modos de operación

## 📁 Estructura del Proyecto

```
scraping_brasil/
├── 🏠 Raíz del Proyecto
│   ├── run_scraper.py              # Script principal de ejecución
│   ├── requirements.txt            # Dependencias completas
│   └── README_SISTEMA.md           # Esta documentación
│
├── 📂 config/
│   ├── settings.py                 # Configuración centralizada
│   └── mock_data/                  # Datos simulados (auto-creado)
│
├── 📂 src/
│   ├── main.py                     # Coordinador principal
│   ├── 🔍 scraper/
│   │   └── validators.py           # Sistema de validación
│   ├── 💾 storage/
│   │   ├── drive_interface.py      # Interface abstracta
│   │   ├── mock_drive_manager.py   # Simulador de Drive
│   │   └── drive_factory.py        # Factory pattern
│   ├── 🌐 api/
│   │   └── senate_client.py        # Cliente API del Senado
│   ├── ⚙️ processors/
│   │   └── data_processor.py       # Procesamiento de datos
│   └── 🛠️ utils/
│       ├── date_utils.py           # Utilidades de fecha
│       ├── translate_file_pt_to_es.py # Traducción PT→ES
│       └── translator.py           # Coordinador de traducción
│
├── 📂 tests/
│   └── test_integration.py         # Tests automatizados
│
├── 📂 data/                        # Datos (auto-creado)
│   ├── raw/                        # Datos originales
│   └── processed/                  # Datos procesados
│
├── 📂 mock_storage/                # Almacenamiento simulado (auto-creado)
│   ├── files/                      # Archivos simulados
│   └── metadata.json              # Metadatos del simulador
│
└── 📂 logs/                        # Logs del sistema (auto-creado)
    └── scraper.log                 # Log principal
```

## 🚀 Uso del Sistema

### Instalación

```bash
# Instalar dependencias
pip install -r requirements.txt

# El sistema creará automáticamente todas las carpetas necesarias
```

### Configuración

```bash
# Copiar archivo de configuración de ejemplo (si existe)
cp .env.example .env

# Editar configuración según necesidades
nano .env
```

### Ejecución Básica

```bash
# Ejecutar con configuración por defecto (modo mock)
python run_scraper.py

# Forzar modo simulador
python run_scraper.py --mode mock

# Ejecutar con fecha personalizada
python run_scraper.py --start-date 2024-06-01

# Modo verbose para debugging
python run_scraper.py --verbose
```

### Comandos Disponibles

```bash
# 📊 Ver estado del sistema
python run_scraper.py --status

# 🧪 Probar configuración sin ejecutar scraping
python run_scraper.py --test

# 🔧 Ayuda completa
python run_scraper.py --help
```

## ⚙️ Modos de Operación

### 🧪 Modo Mock (Desarrollo)
- **Propósito**: Desarrollo sin credenciales de Google Drive
- **Características**:
  - Simulación completa de operaciones Drive
  - Almacenamiento local en `mock_storage/`
  - Estadísticas y debugging completos
  - No requiere configuración externa

### 🌐 Modo Real (Producción)
- **Propósito**: Integración real con Google Drive
- **Requisitos**:
  - Credenciales de Google Drive API
  - ID de carpeta de destino
  - Archivos `credentials.json` y `token.json`

### 🔄 Modo Auto (Recomendado)
- **Propósito**: Intenta modo real, fallback a mock
- **Comportamiento**:
  - Si hay credenciales → Modo real
  - Si no hay credenciales → Modo mock automáticamente
  - Ideal para equipos mixtos de desarrollo/producción

## 🔍 Sistema de Validación

### Detección de Duplicados

El sistema usa múltiples estrategias para detectar duplicados:

1. **🎯 Coincidencia Exacta de ID**: Identificación precisa por ID único
2. **🔐 Hash de Contenido**: Comparación MD5 para detectar contenido idéntico
3. **📝 Metadatos**: Comparación por título, fecha y fuente

### Filtrado por Fechas

- **📅 Rango Configurable**: Desde 2024-01-01 hasta hoy (por defecto)
- **🎯 Filtros Personalizados**: Fechas específicas via parámetros
- **⚡ Optimización**: Procesamiento solo de documentos relevantes

## 📊 Fuentes de Datos

### 🏛️ Senado Federal
- **API**: Sistema asíncrono con cliente dedicado
- **Datos**: Procesos legislativos, matérias em tramitação
- **Formato**: JSON estructurado con metadatos completos

### 🏢 Cámara de Diputados
- **API**: REST API pública
- **Datos**: Proposições, projetos de lei
- **Integración**: Reutiliza script existente (`scrape_proposicoes_since_2023.py`)

## 🧪 Testing y Validación

### Tests Automatizados

```bash
# Ejecutar todos los tests
python -m pytest tests/ -v

# Test específico de integración
python tests/test_integration.py

# Tests con coverage
python -m pytest tests/ --cov=src
```

### Validación del Sistema

```bash
# Verificar configuración completa
python run_scraper.py --test

# Ver estadísticas detalladas
python run_scraper.py --status --verbose
```

## 📈 Monitoreo y Reportes

### Estadísticas Automáticas

El sistema genera automáticamente:

- **📊 Estadísticas de Scraping**: Documentos procesados, nuevos, duplicados
- **💾 Métricas de Almacenamiento**: Uso de espacio, operaciones realizadas
- **⏱️ Rendimiento**: Tiempos de ejecución, errores encontrados
- **📋 Reportes de Sesión**: JSON detallado guardado en `data/processed/`

### Logs Estructurados

- **📝 Console**: Output colorizado con niveles de log
- **📄 Archivo**: Rotación automática en `logs/scraper.log`
- **🔍 Debugging**: Nivel DEBUG disponible con `--verbose`

## 🔧 Configuración Avanzada

### Variables de Entorno

```bash
# Configuración de Base de Datos
DB_HOST=localhost
DB_PORT=5432
DB_NAME=brasil_scraping
DB_USER=postgres
DB_PASSWORD=tu_password

# Configuración de Google Drive
GOOGLE_DRIVE_FOLDER_ID=tu_folder_id
GOOGLE_CREDENTIALS_PATH=credentials.json
GOOGLE_TOKEN_PATH=token.json

# Configuración de Aplicación
APP_MODE=auto                    # mock, real, auto
LOG_LEVEL=INFO                   # DEBUG, INFO, WARNING, ERROR
MAX_CONCURRENT_DOWNLOADS=5       # Límite de descargas simultáneas
RETRY_ATTEMPTS=3                 # Intentos de reintento
RETRY_DELAY=1                    # Delay entre reintentos (segundos)

# Rutas de Almacenamiento
DATA_RAW_PATH=data/raw
DATA_PROCESSED_PATH=data/processed
MOCK_STORAGE_PATH=mock_storage
LOG_PATH=logs

# Configuración de API
API_RATE_LIMIT_DELAY=1          # Delay entre llamadas API
API_TIMEOUT=30                   # Timeout de requests

# Rango de Fechas
DEFAULT_START_DATE=2024-01-01   # Fecha de inicio por defecto
# DEFAULT_END_DATE=             # Si no se especifica, usa fecha actual
```

### Personalización de Comportamiento

El sistema permite personalización a través de:

- **🎛️ Parámetros de Línea de Comandos**: Para ejecuciones específicas
- **📝 Variables de Entorno**: Para configuración persistente
- **⚙️ Archivos de Configuración**: Para setups complejos

## 🚨 Troubleshooting

### Problemas Comunes

#### Error de Credenciales de Google Drive
```bash
# Verificar configuración
python run_scraper.py --status

# Forzar modo mock para testing
python run_scraper.py --mode mock
```

#### Problemas de Dependencias
```bash
# Reinstalar dependencias
pip install -r requirements.txt --force-reinstall

# Verificar instalación
python -c "import src.main; print('✅ Imports OK')"
```

#### Errores de Permisos de Archivo
```bash
# Verificar permisos de directorios
ls -la data/ mock_storage/ logs/

# Recrear directorios si es necesario
python -c "from config.settings import settings; settings.ensure_directories_exist()"
```

### Debugging Avanzado

```bash
# Logs detallados
python run_scraper.py --verbose

# Test de componentes individuales
python -c "
from src.storage.drive_factory import DriveFactory
drive = DriveFactory.create_drive_manager('mock')
print('✅ Drive System OK')
"
```

## 🔄 Futuras Mejoras (Roadmap)

### Fase 2: Integración Completa con Google Drive
- [ ] Implementar `RealDriveManager` con Google Drive API completa
- [ ] Sistema de autenticación OAuth2 automatizado
- [ ] Manejo de cuotas y rate limiting de Google Drive

### Fase 3: Automatización Cloud
- [ ] Integración con Google Cloud Functions
- [ ] Cloud Scheduler para ejecución automática diaria
- [ ] Sistema de alertas y monitoring en cloud
- [ ] Dashboard web para visualización de datos

### Mejoras Adicionales
- [ ] Soporte para más fuentes de datos gubernamentales
- [ ] Sistema de traducción automática mejorado
- [ ] API REST para acceso a datos procesados
- [ ] Exportación a múltiples formatos (Excel, PDF, etc.)

## 📞 Soporte

Para problemas, sugerencias o contribuciones:

1. **🐛 Reportar Bugs**: Crear issue con logs detallados
2. **💡 Sugerencias**: Proponer mejoras en GitHub
3. **🤝 Contribuir**: Fork → Branch → Pull Request

---

**✨ Sistema desarrollado con arquitectura moderna, testing automatizado y documentación completa para máxima confiabilidad y mantenibilidad.** 