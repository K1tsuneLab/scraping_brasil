import os
from typing import List, Dict, Any
import pandas as pd
import psycopg2
from sentence_transformers import SentenceTransformer
import numpy as np
from dotenv import load_dotenv
from loguru import logger
import torch

# Load environment variables
load_dotenv()

# Configure logger
logger.add("logs/embeddings.log", rotation="100 MB")

class EmbeddingGenerator:
    def __init__(self):
        self.model = SentenceTransformer('sentence-transformers/multilingual-MiniLM-L12-v2')
        self.db_params = {
            'dbname': os.getenv('DB_NAME'),
            'user': os.getenv('DB_USER'),
            'password': os.getenv('DB_PASSWORD'),
            'host': os.getenv('DB_HOST'),
            'port': os.getenv('DB_PORT')
        }

    def get_connection(self):
        return psycopg2.connect(**self.db_params)

    def fetch_data(self) -> pd.DataFrame:
        query = """
        SELECT 
            p.id_proyecto,
            p.titulo_proyecto,
            p.autores_proyecto,
            pt.tema_recomendado,
            vp.resumen_proyecto,
            i.id_institucion,
            i.nombre_institucion,
            pa.id_pais,
            pa.nombre_pais,
            t.id_tema,
            t.nombre_tema,
            t.descripcion as descripcion_tema
        FROM proyectos p
        LEFT JOIN proyecto_tema pt ON p.id_proyecto = pt.id_proyecto
        LEFT JOIN temas t ON pt.id_tema = t.id_tema
        LEFT JOIN versionesproyecto vp ON p.id_proyecto = vp.id_proyecto
        LEFT JOIN gacetas g ON vp.id_gaceta = g.id_gaceta
        LEFT JOIN instituciones i ON g.id_institucion = i.id_institucion
        LEFT JOIN paises pa ON g.id_pais = pa.id_pais
        WHERE vp.version_num = (
            SELECT MAX(version_num)
            FROM versionesproyecto
            WHERE id_proyecto = p.id_proyecto
        )
        """
        
        with self.get_connection() as conn:
            df = pd.read_sql_query(query, conn)
        return df

    def create_context_text(self, row: pd.Series) -> str:
        """Create a rich context text from all relevant fields."""
        context_parts = [
            f"Título: {row['titulo_proyecto']}",
            f"Autores: {row['autores_proyecto']}",
            f"Tema recomendado: {row['tema_recomendado']}" if pd.notna(row['tema_recomendado']) else "",
            f"Resumen: {row['resumen_proyecto']}" if pd.notna(row['resumen_proyecto']) else "",
            f"Institución: {row['nombre_institucion']} (ID: {row['id_institucion']})",
            f"País: {row['nombre_pais']} (ID: {row['id_pais']})",
            f"Tema: {row['nombre_tema']} (ID: {row['id_tema']})",
            f"Descripción del tema: {row['descripcion_tema']}"
        ]
        return " | ".join([part for part in context_parts if part])

    def generate_embeddings(self) -> Dict[str, Any]:
        """Generate embeddings for all projects."""
        logger.info("Fetching data from database...")
        df = self.fetch_data()
        
        logger.info(f"Generating embeddings for {len(df)} projects...")
        
        # Create context texts
        contexts = df.apply(self.create_context_text, axis=1).tolist()
        
        # Generate embeddings
        embeddings = self.model.encode(contexts, show_progress_bar=True)
        
        # Create result dictionary
        result = {
            'project_ids': df['id_proyecto'].tolist(),
            'embeddings': embeddings,
            'metadata': {
                'institution_ids': df['id_institucion'].tolist(),
                'country_ids': df['id_pais'].tolist(),
                'theme_ids': df['id_tema'].tolist(),
                'contexts': contexts
            }
        }
        
        return result

    def save_embeddings(self, result: Dict[str, Any], output_path: str):
        """Save embeddings and metadata to disk."""
        logger.info(f"Saving embeddings to {output_path}")
        np.savez_compressed(
            output_path,
            embeddings=result['embeddings'],
            project_ids=result['project_ids'],
            institution_ids=result['metadata']['institution_ids'],
            country_ids=result['metadata']['country_ids'],
            theme_ids=result['metadata']['theme_ids'],
            contexts=result['metadata']['contexts']
        )

def main():
    generator = EmbeddingGenerator()
    result = generator.generate_embeddings()
    
    # Create output directory if it doesn't exist
    os.makedirs('data/embeddings', exist_ok=True)
    
    # Save embeddings
    output_path = 'data/embeddings/project_embeddings.npz'
    generator.save_embeddings(result, output_path)
    logger.info("Embedding generation completed successfully!")

if __name__ == "__main__":
    main() 