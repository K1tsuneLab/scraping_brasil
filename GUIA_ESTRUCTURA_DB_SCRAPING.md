# 🗃️ Guía: Estructura de Base de Datos para Proyectos de Scraping

## 📋 Introducción

Esta guía te enseña cómo aplicar la arquitectura de base de datos del proyecto Brasil Scraping a cualquier otro proyecto de scraping. El sistema está diseñado para ser robusto, escalable y fácil de adaptar.

## 🏗️ Arquitectura General

### Concepto Principal
La estructura está basada en **3 entidades fundamentales**:

1. **📄 DOCUMENTOS/GACETAS**: Los archivos que extraes (PDFs, HTMLs, JSONs)
2. **📋 PROYECTOS**: Los elementos legislativos/normativos que contienen esos documentos  
3. **🔗 VERSIONES**: Las diferentes versiones de un mismo proyecto a lo largo del tiempo

### Flujo de Datos
```
API/Scraping → Validación → Modelos Pydantic → Base de Datos → Almacenamiento
```

## 🗂️ Esquema de Base de Datos

### 1. Tabla Principal: `gacetas`
```sql
CREATE TABLE gacetas (
    id_gaceta SERIAL PRIMARY KEY,
    id_pais INTEGER NOT NULL,
    numero_gaceta VARCHAR(100) NOT NULL,
    anio INTEGER NOT NULL,
    fecha_publicacion DATE NOT NULL,
    enlace_pdf TEXT,
    estado VARCHAR(50) DEFAULT 'pendiente',
    id_institucion INTEGER,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```
**Propósito**: Almacena los documentos/archivos extraídos del scraping.

### 2. Tabla: `proyectos`
```sql
CREATE TABLE proyectos (
    id_proyecto SERIAL PRIMARY KEY,
    numero_proyecto VARCHAR(100) UNIQUE NOT NULL,
    anio_legislativo VARCHAR(20),
    titulo_proyecto TEXT NOT NULL,
    autores_proyecto TEXT,
    estado_proyecto VARCHAR(50) DEFAULT 'activo',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```
**Propósito**: Representa los proyectos/elementos legislativos principales.

### 3. Tabla: `versionesproyecto`
```sql
CREATE TABLE versionesproyecto (
    id_version SERIAL PRIMARY KEY,
    id_proyecto INTEGER REFERENCES proyectos(id_proyecto),
    id_gaceta INTEGER REFERENCES gacetas(id_gaceta),
    version_num INTEGER DEFAULT 1,
    descripcion_cambios TEXT,
    texto_crudo TEXT,
    fecha_version DATE,
    resumen_proyecto TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```
**Propósito**: Conecta proyectos con documentos y maneja versiones.

### 4. Tablas de Soporte

#### `paises`
```sql
CREATE TABLE paises (
    id_pais SERIAL PRIMARY KEY,
    nombre_pais VARCHAR(100) NOT NULL,
    codigo_pais VARCHAR(10),
    activo BOOLEAN DEFAULT TRUE
);
```

#### `instituciones`
```sql
CREATE TABLE instituciones (
    id_institucion SERIAL PRIMARY KEY,
    nombre_institucion VARCHAR(200) NOT NULL,
    tipo_institucion VARCHAR(100),
    id_pais INTEGER REFERENCES paises(id_pais)
);
```

#### `temas`
```sql
CREATE TABLE temas (
    id_tema SERIAL PRIMARY KEY,
    nombre_tema VARCHAR(200) NOT NULL,
    descripcion TEXT,
    categoria VARCHAR(100)
);
```

#### `proyecto_tema` (Relación Many-to-Many)
```sql
CREATE TABLE proyecto_tema (
    id_proyecto INTEGER REFERENCES proyectos(id_proyecto),
    id_tema INTEGER REFERENCES temas(id_tema),
    asignacion_timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    tema_recomendado BOOLEAN DEFAULT FALSE,
    PRIMARY KEY (id_proyecto, id_tema)
);
```

## 🔧 Implementación Paso a Paso

### Paso 1: Configuración del Entorno

#### 1.1 Instalar Dependencias
```bash
pip install psycopg2-binary python-dotenv pydantic loguru aiohttp
```

#### 1.2 Archivo `.env`
```bash
# Base de datos
DB_HOST=localhost
DB_PORT=5432
DB_NAME=tu_proyecto_scraping
DB_USER=postgres
DB_PASSWORD=tu_password

# Configuración del scraping
APP_MODE=mock  # mock, real, auto
LOG_LEVEL=INFO
API_TIMEOUT=30
DEFAULT_START_DATE=2024-01-01
```

### Paso 2: Sistema de Configuración

#### 2.1 `config/settings.py`
```python
import os
from pathlib import Path
from datetime import date
from dotenv import load_dotenv

load_dotenv()

class Settings:
    # Rutas del proyecto
    PROJECT_ROOT = Path(__file__).parent.parent
    
    # Base de datos
    DB_HOST: str = os.getenv('DB_HOST', 'localhost')
    DB_PORT: str = os.getenv('DB_PORT', '5432')
    DB_NAME: str = os.getenv('DB_NAME', 'scraping_db')
    DB_USER: str = os.getenv('DB_USER', 'postgres')
    DB_PASSWORD: str = os.getenv('DB_PASSWORD', '')
    
    # Configuración de aplicación
    APP_MODE: str = os.getenv('APP_MODE', 'mock')
    LOG_LEVEL: str = os.getenv('LOG_LEVEL', 'INFO')
    
    # Rutas de almacenamiento
    DATA_RAW_PATH: Path = PROJECT_ROOT / "data/raw"
    DATA_PROCESSED_PATH: Path = PROJECT_ROOT / "data/processed"
    LOG_PATH: Path = PROJECT_ROOT / "logs"
    
    @classmethod
    def get_database_url(cls) -> str:
        return f"postgresql://{cls.DB_USER}:{cls.DB_PASSWORD}@{cls.DB_HOST}:{cls.DB_PORT}/{cls.DB_NAME}"
    
    @classmethod
    def ensure_directories_exist(cls) -> None:
        for directory in [cls.DATA_RAW_PATH, cls.DATA_PROCESSED_PATH, cls.LOG_PATH]:
            directory.mkdir(parents=True, exist_ok=True)

settings = Settings()
settings.ensure_directories_exist()
```

### Paso 3: Modelos de Datos

#### 3.1 `src/models/base_models.py`
```python
from datetime import datetime
from typing import Optional, List
from pydantic import BaseModel, Field

class ScrapedDocument(BaseModel):
    """Modelo base para documentos extraídos"""
    id: Optional[str] = None
    title: str
    url: str
    publication_date: Optional[datetime] = None
    document_type: str
    source: str  # 'senado', 'camara', etc.
    content: Optional[str] = None
    file_size: Optional[int] = None
    
    class Config:
        from_attributes = True

class Project(BaseModel):
    """Modelo para proyectos legislativos"""
    project_number: str
    title: str
    authors: Optional[str] = None
    year: int
    status: str = "active"
    
class Version(BaseModel):
    """Modelo para versiones de proyectos"""
    project_id: int
    document_id: int
    version_number: int = 1
    changes_description: Optional[str] = None
    raw_text: Optional[str] = None
    version_date: Optional[datetime] = None
```

### Paso 4: Conexión a Base de Datos

#### 4.1 `src/database/connection.py`
```python
import psycopg2
from psycopg2 import Error
from contextlib import contextmanager
from config.settings import settings
import logging

logger = logging.getLogger(__name__)

def get_database_connection():
    """Crear conexión a la base de datos"""
    try:
        connection = psycopg2.connect(
            host=settings.DB_HOST,
            port=settings.DB_PORT,
            database=settings.DB_NAME,
            user=settings.DB_USER,
            password=settings.DB_PASSWORD
        )
        return connection
    except Error as e:
        logger.error(f"Error conectando a PostgreSQL: {e}")
        return None

@contextmanager
def database_transaction():
    """Context manager para transacciones seguras"""
    connection = get_database_connection()
    if not connection:
        raise Exception("No se pudo conectar a la base de datos")
    
    try:
        cursor = connection.cursor()
        yield cursor
        connection.commit()
    except Exception as e:
        connection.rollback()
        logger.error(f"Error en transacción: {e}")
        raise
    finally:
        cursor.close()
        connection.close()
```

### Paso 5: Sistema de Migración

#### 5.1 `migrations/create_tables.sql`
```sql
-- Crear todas las tablas necesarias
CREATE TABLE IF NOT EXISTS paises (
    id_pais SERIAL PRIMARY KEY,
    nombre_pais VARCHAR(100) NOT NULL,
    codigo_pais VARCHAR(10),
    activo BOOLEAN DEFAULT TRUE
);

CREATE TABLE IF NOT EXISTS instituciones (
    id_institucion SERIAL PRIMARY KEY,
    nombre_institucion VARCHAR(200) NOT NULL,
    tipo_institucion VARCHAR(100),
    id_pais INTEGER REFERENCES paises(id_pais)
);

CREATE TABLE IF NOT EXISTS gacetas (
    id_gaceta SERIAL PRIMARY KEY,
    id_pais INTEGER REFERENCES paises(id_pais),
    numero_gaceta VARCHAR(100) NOT NULL,
    anio INTEGER NOT NULL,
    fecha_publicacion DATE NOT NULL,
    enlace_pdf TEXT,
    estado VARCHAR(50) DEFAULT 'pendiente',
    id_institucion INTEGER REFERENCES instituciones(id_institucion),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS proyectos (
    id_proyecto SERIAL PRIMARY KEY,
    numero_proyecto VARCHAR(100) UNIQUE NOT NULL,
    anio_legislativo VARCHAR(20),
    titulo_proyecto TEXT NOT NULL,
    autores_proyecto TEXT,
    estado_proyecto VARCHAR(50) DEFAULT 'activo',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS versionesproyecto (
    id_version SERIAL PRIMARY KEY,
    id_proyecto INTEGER REFERENCES proyectos(id_proyecto),
    id_gaceta INTEGER REFERENCES gacetas(id_gaceta),
    version_num INTEGER DEFAULT 1,
    descripcion_cambios TEXT,
    texto_crudo TEXT,
    fecha_version DATE,
    resumen_proyecto TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS temas (
    id_tema SERIAL PRIMARY KEY,
    nombre_tema VARCHAR(200) NOT NULL,
    descripcion TEXT,
    categoria VARCHAR(100)
);

CREATE TABLE IF NOT EXISTS proyecto_tema (
    id_proyecto INTEGER REFERENCES proyectos(id_proyecto),
    id_tema INTEGER REFERENCES temas(id_tema),
    asignacion_timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    tema_recomendado BOOLEAN DEFAULT FALSE,
    PRIMARY KEY (id_proyecto, id_tema)
);

-- Índices para mejorar rendimiento
CREATE INDEX IF NOT EXISTS idx_gacetas_fecha ON gacetas(fecha_publicacion);
CREATE INDEX IF NOT EXISTS idx_gacetas_numero ON gacetas(numero_gaceta);
CREATE INDEX IF NOT EXISTS idx_proyectos_numero ON proyectos(numero_proyecto);
CREATE INDEX IF NOT EXISTS idx_versiones_proyecto ON versionesproyecto(id_proyecto);
```

#### 5.2 `migrations/migrate.py`
```python
import psycopg2
from pathlib import Path
from config.settings import settings
import logging

def run_migration():
    """Ejecutar migración de base de datos"""
    try:
        connection = psycopg2.connect(settings.get_database_url())
        cursor = connection.cursor()
        
        # Leer archivo SQL
        migration_file = Path(__file__).parent / "create_tables.sql"
        with open(migration_file, 'r', encoding='utf-8') as f:
            sql_script = f.read()
        
        # Ejecutar migración
        cursor.execute(sql_script)
        connection.commit()
        
        print("✅ Migración completada exitosamente")
        
    except Exception as e:
        print(f"❌ Error en migración: {e}")
        if connection:
            connection.rollback()
    finally:
        if cursor:
            cursor.close()
        if connection:
            connection.close()

if __name__ == "__main__":
    run_migration()
```

### Paso 6: Procesador de Datos

#### 6.1 `src/processors/data_processor.py`
```python
from datetime import datetime
from typing import List, Dict, Any
from src.models.base_models import ScrapedDocument, Project
from src.database.connection import database_transaction
import logging

logger = logging.getLogger(__name__)

class DataProcessor:
    """Procesador principal de datos para insertar en base de datos"""
    
    def __init__(self, country_id: int = 1, institution_id: int = 1):
        self.country_id = country_id
        self.institution_id = institution_id
    
    def process_scraped_documents(self, documents: List[ScrapedDocument]) -> Dict[str, int]:
        """Procesar lista de documentos extraídos"""
        processed_count = 0
        skipped_count = 0
        
        for doc in documents:
            try:
                if self._document_exists(doc.id):
                    logger.info(f"Documento {doc.id} ya existe, saltando...")
                    skipped_count += 1
                    continue
                
                # Insertar documento (gaceta)
                gaceta_id = self._insert_document(doc)
                
                # Crear o obtener proyecto
                project_id = self._create_or_get_project(doc)
                
                # Crear versión que conecta documento con proyecto
                self._create_version(project_id, gaceta_id, doc)
                
                processed_count += 1
                logger.info(f"Documento {doc.id} procesado exitosamente")
                
            except Exception as e:
                logger.error(f"Error procesando documento {doc.id}: {e}")
                skipped_count += 1
        
        return {
            'processed': processed_count,
            'skipped': skipped_count,
            'total': len(documents)
        }
    
    def _document_exists(self, document_id: str) -> bool:
        """Verificar si el documento ya existe"""
        with database_transaction() as cursor:
            cursor.execute(
                "SELECT COUNT(*) FROM gacetas WHERE numero_gaceta = %s AND id_pais = %s",
                (document_id, self.country_id)
            )
            return cursor.fetchone()[0] > 0
    
    def _insert_document(self, doc: ScrapedDocument) -> int:
        """Insertar documento en tabla gacetas"""
        with database_transaction() as cursor:
            cursor.execute("""
                INSERT INTO gacetas (
                    id_pais, numero_gaceta, anio, fecha_publicacion, 
                    enlace_pdf, estado, id_institucion
                )
                VALUES (%s, %s, %s, %s, %s, %s, %s)
                RETURNING id_gaceta
            """, (
                self.country_id,
                doc.id,
                doc.publication_date.year if doc.publication_date else datetime.now().year,
                doc.publication_date.date() if doc.publication_date else datetime.now().date(),
                doc.url,
                'aprobado',
                self.institution_id
            ))
            
            return cursor.fetchone()[0]
    
    def _create_or_get_project(self, doc: ScrapedDocument) -> int:
        """Crear o obtener proyecto existente"""
        project_number = f"{doc.source.upper()}-{doc.id}"
        
        with database_transaction() as cursor:
            # Buscar proyecto existente
            cursor.execute(
                "SELECT id_proyecto FROM proyectos WHERE numero_proyecto = %s",
                (project_number,)
            )
            
            result = cursor.fetchone()
            if result:
                return result[0]
            
            # Crear nuevo proyecto
            cursor.execute("""
                INSERT INTO proyectos (
                    numero_proyecto, anio_legislativo, titulo_proyecto, autores_proyecto
                )
                VALUES (%s, %s, %s, %s)
                RETURNING id_proyecto
            """, (
                project_number,
                f"{datetime.now().year}-{datetime.now().year + 4}",
                doc.title,
                "Sistema de Scraping"  # Placeholder
            ))
            
            return cursor.fetchone()[0]
    
    def _create_version(self, project_id: int, gaceta_id: int, doc: ScrapedDocument):
        """Crear versión que conecta proyecto con documento"""
        with database_transaction() as cursor:
            cursor.execute("""
                INSERT INTO versionesproyecto (
                    id_proyecto, id_gaceta, version_num, texto_crudo, fecha_version
                )
                VALUES (%s, %s, %s, %s, %s)
            """, (
                project_id,
                gaceta_id,
                1,  # Versión por defecto
                doc.content,
                doc.publication_date.date() if doc.publication_date else datetime.now().date()
            ))
```

## 🚀 Uso Práctico

### Ejemplo Completo de Implementación

```python
# main.py
import asyncio
from src.models.base_models import ScrapedDocument
from src.processors.data_processor import DataProcessor
from datetime import datetime

async def main():
    # 1. Simular datos extraídos del scraping
    documents = [
        ScrapedDocument(
            id="123",
            title="Ley de Transparencia",
            url="https://ejemplo.com/doc123.pdf",
            publication_date=datetime(2024, 1, 15),
            document_type="pdf",
            source="senado",
            content="Contenido del documento..."
        ),
        ScrapedDocument(
            id="124",
            title="Reforma Educativa",
            url="https://ejemplo.com/doc124.pdf",
            publication_date=datetime(2024, 2, 20),
            document_type="pdf",
            source="camara",
            content="Contenido de la reforma..."
        )
    ]
    
    # 2. Procesar documentos
    processor = DataProcessor(country_id=1, institution_id=1)
    result = processor.process_scraped_documents(documents)
    
    print(f"✅ Procesamiento completado:")
    print(f"  - Procesados: {result['processed']}")
    print(f"  - Saltados: {result['skipped']}")
    print(f"  - Total: {result['total']}")

if __name__ == "__main__":
    asyncio.run(main())
```

## 📋 Adaptación para Diferentes Países/Fuentes

### Para otro país (ej: Colombia):

1. **Agregar nuevo país**:
```sql
INSERT INTO paises (nombre_pais, codigo_pais) VALUES ('Colombia', 'CO');
```

2. **Agregar instituciones**:
```sql
INSERT INTO instituciones (nombre_institucion, tipo_institucion, id_pais) 
VALUES ('Senado de Colombia', 'Legislativo', 2);
```

3. **Adaptar modelos**:
```python
class ColombianDocument(ScrapedDocument):
    """Modelo específico para documentos colombianos"""
    ley_number: Optional[str] = None
    department: Optional[str] = None
```

### Para diferentes tipos de documentos:

```python
class NewsDocument(ScrapedDocument):
    """Para scraping de noticias"""
    category: str
    author: str
    
class LegalDocument(ScrapedDocument):
    """Para documentos legales"""
    law_type: str
    approval_date: Optional[datetime] = None
```

## 📊 Ventajas de esta Estructura

1. **✅ Escalabilidad**: Soporta múltiples países e instituciones
2. **✅ Flexibilidad**: Fácil adaptación a diferentes tipos de documentos
3. **✅ Trazabilidad**: Historial completo de versiones
4. **✅ Relaciones**: Sistema de categorización por temas
5. **✅ Integridad**: Validaciones y constraints de base de datos
6. **✅ Performance**: Índices optimizados para consultas frecuentes

## 🔧 Herramientas de Monitoreo

### Script de verificación:
```python
def verify_data_integrity():
    """Verificar integridad de los datos"""
    with database_transaction() as cursor:
        # Verificar documentos sin proyecto
        cursor.execute("""
            SELECT COUNT(*) FROM gacetas g 
            LEFT JOIN versionesproyecto vp ON g.id_gaceta = vp.id_gaceta 
            WHERE vp.id_gaceta IS NULL
        """)
        orphaned_docs = cursor.fetchone()[0]
        
        # Verificar proyectos sin documentos
        cursor.execute("""
            SELECT COUNT(*) FROM proyectos p 
            LEFT JOIN versionesproyecto vp ON p.id_proyecto = vp.id_proyecto 
            WHERE vp.id_proyecto IS NULL
        """)
        orphaned_projects = cursor.fetchone()[0]
        
        print(f"Documentos huérfanos: {orphaned_docs}")
        print(f"Proyectos huérfanos: {orphaned_projects}")
```

## 🎯 Próximos Pasos

1. **Implementar la estructura base** siguiendo esta guía
2. **Adaptar los modelos** a tu fuente específica de datos
3. **Crear validaciones** específicas para tu dominio
4. **Implementar sistema de backups** automáticos
5. **Agregar monitoreo** y alertas
6. **Crear API REST** para consultar los datos

¡Con esta estructura tendrás una base sólida y escalable para cualquier proyecto de scraping! 