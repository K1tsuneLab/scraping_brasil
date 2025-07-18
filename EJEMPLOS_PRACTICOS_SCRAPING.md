# 🛠️ Ejemplos Prácticos: Adaptando la Estructura para Diferentes Tipos de Scraping

## 📋 Casos de Uso Reales

### 🇦🇷 Ejemplo 1: Scraping de Argentina - Boletín Oficial

#### Adaptaciones específicas:

```python
# models/argentina_models.py
from src.models.base_models import ScrapedDocument
from datetime import datetime
from typing import Optional

class BoletinOficialDocument(ScrapedDocument):
    """Modelo específico para Boletín Oficial de Argentina"""
    seccion: str  # "Primera", "Segunda", "Tercera", "Cuarta"
    rubro: Optional[str] = None
    numero_boletin: str
    numero_norma: Optional[str] = None
    organismo: Optional[str] = None
    
    @classmethod
    def from_scraped_data(cls, data: dict):
        return cls(
            id=data['numero_norma'] or data['id'],
            title=data['titulo'],
            url=data['url_pdf'],
            publication_date=datetime.strptime(data['fecha'], '%Y-%m-%d'),
            document_type='pdf',
            source='boletin_oficial',
            seccion=data['seccion'],
            numero_boletin=data['numero_boletin'],
            numero_norma=data.get('numero_norma'),
            organismo=data.get('organismo')
        )
```

#### Procesador específico:

```python
# processors/argentina_processor.py
from src.processors.data_processor import DataProcessor
from src.models.argentina_models import BoletinOficialDocument

class ArgentinaProcessor(DataProcessor):
    def __init__(self):
        # Argentina tiene id_pais = 2 en la BD
        super().__init__(country_id=2, institution_id=3)  # Boletín Oficial
    
    def process_boletin_documents(self, documents: List[BoletinOficialDocument]):
        """Procesar documentos del Boletín Oficial"""
        for doc in documents:
            # Crear número de proyecto específico para Argentina
            project_number = f"AR-BO-{doc.numero_boletin}-{doc.seccion}"
            
            # Insertar con datos específicos
            self._insert_argentina_document(doc, project_number)
    
    def _insert_argentina_document(self, doc: BoletinOficialDocument, project_number: str):
        with database_transaction() as cursor:
            # Insertar en gacetas con campos específicos
            cursor.execute("""
                INSERT INTO gacetas (
                    id_pais, numero_gaceta, anio, fecha_publicacion, 
                    enlace_pdf, estado, id_institucion, metadata_json
                )
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
                RETURNING id_gaceta
            """, (
                self.country_id,
                doc.id,
                doc.publication_date.year,
                doc.publication_date.date(),
                doc.url,
                'aprobado',
                self.institution_id,
                json.dumps({
                    'seccion': doc.seccion,
                    'rubro': doc.rubro,
                    'numero_boletin': doc.numero_boletin,
                    'organismo': doc.organismo
                })
            ))
```

### 🇨🇴 Ejemplo 2: Scraping de Colombia - Diario Oficial

```python
# models/colombia_models.py
class DiarioOficialDocument(ScrapedDocument):
    """Modelo para Diario Oficial de Colombia"""
    numero_diario: str
    numero_ley: Optional[str] = None
    tipo_norma: str  # "Ley", "Decreto", "Resolución", etc.
    ministerio: Optional[str] = None
    vigencia_desde: Optional[datetime] = None
    vigencia_hasta: Optional[datetime] = None
    
    @classmethod
    def from_gov_co_data(cls, data: dict):
        return cls(
            id=data['numero_ley'] or data['id'],
            title=data['titulo_norma'],
            url=data['url_documento'],
            publication_date=datetime.strptime(data['fecha_publicacion'], '%Y-%m-%d'),
            document_type='pdf',
            source='diario_oficial',
            numero_diario=data['numero_diario'],
            numero_ley=data.get('numero_ley'),
            tipo_norma=data['tipo_norma'],
            ministerio=data.get('ministerio'),
            vigencia_desde=data.get('vigencia_desde'),
            vigencia_hasta=data.get('vigencia_hasta')
        )

# scrapers/colombia_scraper.py
import aiohttp
import asyncio
from bs4 import BeautifulSoup

class ColombiaScraper:
    def __init__(self):
        self.base_url = "https://www.funcionpublica.gov.co"
        self.processor = ColombiaProcessor()
    
    async def scrape_diario_oficial(self, start_date: str, end_date: str):
        """Scraper específico para el Diario Oficial de Colombia"""
        async with aiohttp.ClientSession() as session:
            documents = []
            
            # Lógica específica de scraping para Colombia
            url = f"{self.base_url}/eva/gestornormativo/norma_pdf.php"
            params = {
                'fecha_inicio': start_date,
                'fecha_fin': end_date,
                'tipo': 'diario_oficial'
            }
            
            async with session.get(url, params=params) as response:
                html = await response.text()
                soup = BeautifulSoup(html, 'html.parser')
                
                # Extraer documentos específicos
                for item in soup.find_all('div', class_='norma-item'):
                    doc_data = {
                        'numero_ley': item.get('data-numero-ley'),
                        'titulo_norma': item.find('h3').text.strip(),
                        'url_documento': item.find('a')['href'],
                        'fecha_publicacion': item.get('data-fecha'),
                        'numero_diario': item.get('data-diario'),
                        'tipo_norma': item.get('data-tipo'),
                        'ministerio': item.find('.ministerio').text.strip() if item.find('.ministerio') else None
                    }
                    
                    documents.append(DiarioOficialDocument.from_gov_co_data(doc_data))
            
            # Procesar documentos
            result = self.processor.process_diario_documents(documents)
            return result
```

### 🇺🇸 Ejemplo 3: Scraping de Estados Unidos - Federal Register

```python
# models/usa_models.py
class FederalRegisterDocument(ScrapedDocument):
    """Modelo para Federal Register de EE.UU."""
    federal_register_number: str
    cfr_title: Optional[str] = None
    agency: str
    document_type: str  # "Rule", "Proposed Rule", "Notice"
    effective_date: Optional[datetime] = None
    comment_period_end: Optional[datetime] = None
    regulation_id: Optional[str] = None
    
    @classmethod
    def from_federal_api(cls, data: dict):
        return cls(
            id=data['document_number'],
            title=data['title'],
            url=data['pdf_url'],
            publication_date=datetime.strptime(data['publication_date'], '%Y-%m-%d'),
            document_type='pdf',
            source='federal_register',
            federal_register_number=data['document_number'],
            cfr_title=data.get('cfr_title'),
            agency=data['agency'],
            document_type=data['type'],
            effective_date=data.get('effective_date'),
            comment_period_end=data.get('comment_period_end'),
            regulation_id=data.get('regulation_id')
        )

# scrapers/usa_scraper.py
class USAScraper:
    def __init__(self):
        self.api_url = "https://www.federalregister.gov/api/v1/documents"
        self.processor = USAProcessor()
    
    async def scrape_federal_register(self, start_date: str, agencies: List[str] = None):
        """Scraper para Federal Register usando API oficial"""
        async with aiohttp.ClientSession() as session:
            params = {
                'fields[]': ['document_number', 'title', 'pdf_url', 'publication_date', 
                           'agency', 'type', 'effective_date'],
                'order': 'newest',
                'per_page': 1000,
                'conditions[publication_date][gte]': start_date
            }
            
            if agencies:
                params['conditions[agencies][]'] = agencies
            
            async with session.get(self.api_url, params=params) as response:
                data = await response.json()
                
                documents = []
                for item in data['results']:
                    documents.append(FederalRegisterDocument.from_federal_api(item))
                
                # Procesar documentos
                result = self.processor.process_federal_documents(documents)
                return result
```

### 🏛️ Ejemplo 4: Scraping Genérico - Sitios Web de Noticias Legales

```python
# models/news_models.py
class LegalNewsDocument(ScrapedDocument):
    """Modelo genérico para noticias legales"""
    category: str
    author: Optional[str] = None
    tags: List[str] = []
    summary: Optional[str] = None
    word_count: Optional[int] = None
    
    @classmethod
    def from_news_data(cls, data: dict):
        return cls(
            id=data['article_id'],
            title=data['headline'],
            url=data['url'],
            publication_date=datetime.strptime(data['published_at'], '%Y-%m-%d %H:%M:%S'),
            document_type='html',
            source=data['source_name'],
            category=data['category'],
            author=data.get('author'),
            tags=data.get('tags', []),
            summary=data.get('summary'),
            content=data.get('full_text'),
            word_count=len(data.get('full_text', '').split()) if data.get('full_text') else None
        )

# scrapers/generic_news_scraper.py
class LegalNewsScraper:
    def __init__(self, base_urls: Dict[str, str]):
        self.base_urls = base_urls  # {'source_name': 'base_url'}
        self.processor = NewsProcessor()
    
    async def scrape_multiple_sources(self, keywords: List[str] = None):
        """Scraper genérico para múltiples fuentes de noticias legales"""
        all_documents = []
        
        for source_name, base_url in self.base_urls.items():
            documents = await self._scrape_single_source(source_name, base_url, keywords)
            all_documents.extend(documents)
        
        # Procesar todos los documentos
        result = self.processor.process_news_documents(all_documents)
        return result
    
    async def _scrape_single_source(self, source_name: str, base_url: str, keywords: List[str]):
        """Scraping específico por fuente"""
        # Implementación específica según la estructura del sitio
        pass
```

## 🔧 Configuración por País

### Archivo de configuración específico:

```python
# config/countries_config.py
COUNTRIES_CONFIG = {
    'argentina': {
        'id_pais': 2,
        'instituciones': {
            'boletin_oficial': 3,
            'senado': 4,
            'diputados': 5
        },
        'sources': {
            'boletin_oficial': 'https://www.boletinoficial.gob.ar',
            'senado': 'https://www.senado.gob.ar',
            'diputados': 'https://www.diputados.gob.ar'
        },
        'date_format': '%d/%m/%Y',
        'timezone': 'America/Argentina/Buenos_Aires'
    },
    'colombia': {
        'id_pais': 3,
        'instituciones': {
            'diario_oficial': 6,
            'senado': 7,
            'camara': 8
        },
        'sources': {
            'diario_oficial': 'https://www.funcionpublica.gov.co',
            'senado': 'https://www.senado.gov.co',
            'camara': 'https://www.camara.gov.co'
        },
        'date_format': '%Y-%m-%d',
        'timezone': 'America/Bogota'
    }
}

def get_country_config(country_code: str) -> dict:
    """Obtener configuración específica por país"""
    return COUNTRIES_CONFIG.get(country_code, {})
```

## 🚀 Script de Inicialización Completo

```python
# init_new_country.py
import asyncio
from config.countries_config import get_country_config
from src.database.connection import database_transaction

async def initialize_new_country(country_code: str, country_name: str):
    """Inicializar un nuevo país en el sistema"""
    
    print(f"🚀 Inicializando {country_name} ({country_code})...")
    
    # 1. Insertar país
    with database_transaction() as cursor:
        cursor.execute("""
            INSERT INTO paises (nombre_pais, codigo_pais, activo)
            VALUES (%s, %s, %s)
            RETURNING id_pais
        """, (country_name, country_code.upper(), True))
        
        id_pais = cursor.fetchone()[0]
        print(f"✅ País creado con ID: {id_pais}")
    
    # 2. Crear instituciones por defecto
    instituciones_default = [
        ('Poder Ejecutivo', 'ejecutivo'),
        ('Poder Legislativo', 'legislativo'),
        ('Poder Judicial', 'judicial'),
        ('Organismos Autónomos', 'autonomo')
    ]
    
    with database_transaction() as cursor:
        for nombre, tipo in instituciones_default:
            cursor.execute("""
                INSERT INTO instituciones (nombre_institucion, tipo_institucion, id_pais)
                VALUES (%s, %s, %s)
            """, (nombre, tipo, id_pais))
        
        print(f"✅ {len(instituciones_default)} instituciones creadas")
    
    # 3. Crear temas por defecto
    temas_default = [
        ('Legislación General', 'Leyes y normativas generales'),
        ('Economía y Finanzas', 'Regulaciones económicas y financieras'),
        ('Educación', 'Normativas educativas'),
        ('Salud', 'Regulaciones de salud pública'),
        ('Medio Ambiente', 'Legislación ambiental'),
        ('Justicia', 'Normativas del sistema judicial'),
        ('Trabajo y Empleo', 'Legislación laboral'),
        ('Comercio', 'Regulaciones comerciales')
    ]
    
    with database_transaction() as cursor:
        for nombre, descripcion in temas_default:
            cursor.execute("""
                INSERT INTO temas (nombre_tema, descripcion, categoria)
                VALUES (%s, %s, %s)
            """, (nombre, descripcion, 'general'))
        
        print(f"✅ {len(temas_default)} temas creados")
    
    print(f"🎉 Inicialización de {country_name} completada!")
    
    return {
        'id_pais': id_pais,
        'instituciones_creadas': len(instituciones_default),
        'temas_creados': len(temas_default)
    }

# Uso:
# asyncio.run(initialize_new_country('ar', 'Argentina'))
# asyncio.run(initialize_new_country('co', 'Colombia'))
```

## 📊 Monitoreo y Estadísticas

```python
# utils/monitoring.py
def generate_country_report(country_code: str) -> dict:
    """Generar reporte de estadísticas por país"""
    
    config = get_country_config(country_code)
    id_pais = config.get('id_pais')
    
    with database_transaction() as cursor:
        # Documentos por año
        cursor.execute("""
            SELECT anio, COUNT(*) as total
            FROM gacetas 
            WHERE id_pais = %s 
            GROUP BY anio 
            ORDER BY anio DESC
        """, (id_pais,))
        docs_por_ano = dict(cursor.fetchall())
        
        # Proyectos por estado
        cursor.execute("""
            SELECT p.estado_proyecto, COUNT(*) as total
            FROM proyectos p
            JOIN versionesproyecto vp ON p.id_proyecto = vp.id_proyecto
            JOIN gacetas g ON vp.id_gaceta = g.id_gaceta
            WHERE g.id_pais = %s
            GROUP BY p.estado_proyecto
        """, (id_pais,))
        proyectos_por_estado = dict(cursor.fetchall())
        
        # Documentos por institución
        cursor.execute("""
            SELECT i.nombre_institucion, COUNT(*) as total
            FROM gacetas g
            JOIN instituciones i ON g.id_institucion = i.id_institucion
            WHERE g.id_pais = %s
            GROUP BY i.nombre_institucion
            ORDER BY total DESC
        """, (id_pais,))
        docs_por_institucion = dict(cursor.fetchall())
    
    return {
        'pais': country_code,
        'documentos_por_año': docs_por_ano,
        'proyectos_por_estado': proyectos_por_estado,
        'documentos_por_institucion': docs_por_institucion,
        'total_documentos': sum(docs_por_ano.values()),
        'total_proyectos': sum(proyectos_por_estado.values())
    }
```

## 🎯 Checklist de Implementación

### ✅ Para cada nuevo país:

1. **Configuración inicial**:
   - [ ] Agregar entrada en `COUNTRIES_CONFIG`
   - [ ] Ejecutar `initialize_new_country()`
   - [ ] Configurar variables de entorno específicas

2. **Modelos de datos**:
   - [ ] Crear modelo específico heredando de `ScrapedDocument`
   - [ ] Implementar método `from_*_data()`
   - [ ] Agregar validaciones específicas

3. **Scraper**:
   - [ ] Implementar clase scraper específica
   - [ ] Manejar autenticación si es necesaria
   - [ ] Implementar rate limiting
   - [ ] Agregar manejo de errores robusto

4. **Procesador**:
   - [ ] Crear procesador heredando de `DataProcessor`
   - [ ] Implementar lógica específica de proyectos
   - [ ] Agregar validaciones de duplicados

5. **Testing**:
   - [ ] Crear tests unitarios
   - [ ] Probar con datos de muestra
   - [ ] Verificar integridad de datos

6. **Monitoreo**:
   - [ ] Agregar logging específico
   - [ ] Configurar alertas
   - [ ] Crear dashboard de métricas

¡Con estos ejemplos tienes todo lo necesario para adaptar la estructura a cualquier fuente de datos de scraping! 