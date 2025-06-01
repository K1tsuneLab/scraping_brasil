import psycopg2
from sklearn.feature_extraction.text import CountVectorizer
from sklearn.metrics.pairwise import cosine_similarity
import numpy as np
from datetime import datetime
import os
from dotenv import load_dotenv
from loguru import logger
import unicodedata
import re

# Load environment variables
load_dotenv()

# Database connection parameters
DB_PARAMS = {
    'dbname': os.getenv('DB_NAME', ''),
    'user': os.getenv('DB_USER', ''),
    'password': os.getenv('DB_PASSWORD', ''),
    'host': os.getenv('DB_HOST', ''),
    'port': os.getenv('DB_PORT', '5432')
}

# Remove None values from DB_PARAMS
DB_PARAMS = {k: v for k, v in DB_PARAMS.items() if v is not None and v != ''}

# Domain-specific terms mapping
DOMAIN_TERMS = {
    'democracia': ['democracia', 'democratica', 'democratico', 'resistencia', 'monumento'],
    'cultura': ['monumento', 'honor', 'memoria', 'cultural', 'historico'],
    'derechos': ['derechos', 'resistencia', 'honor', 'memoria'],
    'institucional': ['senado', 'federal', 'institucion', 'gobierno'],
}

def preprocess_text(text: str) -> str:
    """Preprocess text for better matching."""
    # Convert to lowercase
    text = text.lower()
    
    # Remove accents
    text = ''.join(c for c in unicodedata.normalize('NFKD', text)
                  if not unicodedata.combining(c))
    
    # Remove special characters but keep spaces between words
    text = re.sub(r'[^a-z0-9\s]', ' ', text)
    
    # Remove extra whitespace
    text = ' '.join(text.split())
    
    # Expand text with domain terms
    expanded_terms = []
    for category, terms in DOMAIN_TERMS.items():
        if any(term in text for term in terms):
            expanded_terms.extend(terms)
    
    # Add expanded terms to the text
    if expanded_terms:
        text = text + ' ' + ' '.join(expanded_terms)
    
    return text

def get_temas_and_proyectos(conn) -> tuple:
    """Fetch all temas and all Brazilian proyectos from the database."""
    with conn.cursor() as cur:
        # Get all temas
        cur.execute("SELECT id_tema, nombre_tema, descripcion FROM temas")
        temas = cur.fetchall()
        logger.info(f"Found {len(temas)} temas in total")

        # Get Brazilian projects with detailed logging
        cur.execute("""
            SELECT DISTINCT p.id_proyecto, p.titulo_proyecto, p.autores_proyecto 
            FROM proyectos p
            JOIN versionesproyecto vp ON p.id_proyecto = vp.id_proyecto
            JOIN gacetas g ON vp.id_gaceta = g.id_gaceta
            JOIN paises pa ON g.id_pais = pa.id_pais
            WHERE LOWER(pa.nombre_pais) LIKE '%brasil%'
            AND p.titulo_proyecto IS NOT NULL
            ORDER BY p.id_proyecto
        """)
        proyectos = cur.fetchall()
        
        if proyectos:
            logger.info("Found the following Brazilian projects:")
            for p in proyectos:
                logger.info(f"Project ID: {p[0]} - Title: {p[1][:100]}")
        else:
            logger.warning("No Brazilian projects found! Checking data:")
            
            # Check paises table
            cur.execute("SELECT id_pais, nombre_pais FROM paises WHERE LOWER(nombre_pais) LIKE '%brasil%'")
            brasil_records = cur.fetchall()
            logger.info(f"Brasil records in paises table: {brasil_records}")
            
            # Check some gacetas linked to Brasil
            if brasil_records:
                brasil_id = brasil_records[0][0]
                cur.execute("SELECT id_gaceta FROM gacetas WHERE id_pais = %s LIMIT 5", (brasil_id,))
                gacetas = cur.fetchall()
                logger.info(f"Sample gacetas for Brasil: {gacetas}")
        
        logger.info(f"Total Brazilian projects to process: {len(proyectos)}")
    
    return temas, proyectos

def process_relationships(temas: list, proyecto: tuple) -> list:
    """Process relationships between one proyecto and temas using simple word matching."""
    logger.info("Preparing text for analysis...")
    
    # Prepare and preprocess text data
    tema_texts = [preprocess_text(f"{tema[1]} {tema[2]}") for tema in temas]
    proyecto_text = preprocess_text(f"{proyecto[1]} {proyecto[2]}")
    
    # Initialize and fit CountVectorizer
    vectorizer = CountVectorizer(
        binary=True,  # Use binary counts (presence/absence)
        analyzer='word',
        token_pattern=r'[a-z]+',  # Only consider words
        min_df=1
    )
    
    # Fit and transform all texts
    all_texts = tema_texts + [proyecto_text]
    count_matrix = vectorizer.fit_transform(all_texts)
    
    # Get feature names for debugging
    feature_names = vectorizer.get_feature_names_out()
    logger.debug(f"Project terms: {[term for term, val in zip(feature_names, count_matrix[-1].toarray()[0]) if val > 0]}")
    
    # Split into tema and proyecto vectors
    tema_vectors = count_matrix[:len(tema_texts)]
    proyecto_vector = count_matrix[len(tema_texts):]
    
    # Calculate similarities
    similarities = cosine_similarity(proyecto_vector, tema_vectors)[0]
    
    # Get top 2 matching temas
    top_2_indices = np.argsort(similarities)[-2:][::-1]
    
    # Create relationships list
    relationships = []
    current_time = datetime.now()
    
    # Print results for verification
    logger.info(f"\nMatching Results for Proyecto: {proyecto[1]}")
    logger.info("Project text after preprocessing:")
    logger.info(f"- {proyecto_text}")
    logger.info("\nTop 2 matching temas:")
    
    # Add primary matches (with their own tema names)
    for idx in top_2_indices:
        tema_name = temas[idx][1].lower()  # Get the actual tema name
        logger.info(f"- {temas[idx][1]}: {similarities[idx]:.3f}")
        logger.info(f"  Preprocessed tema text: {tema_texts[idx]}")
        relationships.append((proyecto[0], temas[idx][0], current_time, tema_name))  # Store tema name instead of None
    
    # For recommended tema, exclude already matched temas
    mask = np.ones(len(temas), dtype=bool)
    mask[top_2_indices] = False
    remaining_similarities = similarities[mask]
    remaining_temas = [tema for i, tema in enumerate(temas) if mask[i]]
    
    if remaining_temas:
        recommended_idx = np.argmax(remaining_similarities)
        recommended_tema = remaining_temas[recommended_idx]
        
        # Add recommended tema with its name
        logger.info("Recommended tema:")
        logger.info(f"- {recommended_tema[1]}: {remaining_similarities[recommended_idx]:.3f}")
        logger.info(f"  Preprocessed tema text: {tema_texts[temas.index(recommended_tema)]}")
        
        # Add the relationship with the tema name
        relationships.append((
            proyecto[0], 
            recommended_tema[0], 
            current_time, 
            recommended_tema[1].lower()  # Use the actual tema name
        ))
    
    return relationships

def populate_proyecto_tema():
    """Main function to populate the proyecto_tema table with relationships for all projects."""
    conn = psycopg2.connect(**DB_PARAMS)
    try:
        # First check if we can connect and if the table exists
        with conn.cursor() as cur:
            cur.execute("SELECT COUNT(*) FROM proyecto_tema")
            initial_count = cur.fetchone()[0]
            logger.info(f"Initial records in proyecto_tema: {initial_count}")
        
        temas, proyectos = get_temas_and_proyectos(conn)
        if not proyectos:
            logger.error("No proyectos found in database")
            return
        
        total_relationships = 0
        processed_ids = []
        
        # Process each proyecto
        for proyecto in proyectos:
            try:
                proyecto_id = proyecto[0]
                
                # Check existing relationships
                with conn.cursor() as cur:
                    cur.execute("SELECT COUNT(*) FROM proyecto_tema WHERE id_proyecto = %s", (proyecto_id,))
                    existing = cur.fetchone()[0]
                    logger.info(f"Project {proyecto_id} - Existing relationships: {existing}")
                
                # Process relationships for the current proyecto
                relationships = process_relationships(temas, proyecto)
                
                # Clear existing entries for this proyecto and insert new ones
                with conn.cursor() as cur:
                    cur.execute("DELETE FROM proyecto_tema WHERE id_proyecto = %s", (proyecto_id,))
                    deleted = cur.rowcount
                    
                    # Insert new relationships
                    cur.executemany("""
                        INSERT INTO proyecto_tema (id_proyecto, id_tema, asignacion_timestamp, tema_recomendado)
                        VALUES (%s, %s, %s, %s)
                    """, relationships)
                    
                    # Verify the insert
                    cur.execute("SELECT COUNT(*) FROM proyecto_tema WHERE id_proyecto = %s", (proyecto_id,))
                    new_count = cur.fetchone()[0]
                
                total_relationships += len(relationships)
                processed_ids.append(proyecto_id)
                logger.info(f"Project {proyecto_id}: Deleted {deleted}, Inserted {len(relationships)}, Final count {new_count}")
                
                # Commit after each proyecto
                conn.commit()
                
            except Exception as e:
                logger.error(f"Error processing proyecto {proyecto[0]}: {str(e)}")
                continue
        
        # Final verification
        with conn.cursor() as cur:
            cur.execute("SELECT COUNT(*) FROM proyecto_tema")
            final_count = cur.fetchone()[0]
            logger.info(f"Final records in proyecto_tema: {final_count}")
            logger.info(f"Net change in records: {final_count - initial_count}")
            logger.info(f"Processed project IDs: {processed_ids}")
            
            # Sample some results
            cur.execute("""
                SELECT id_proyecto, id_tema, tema_recomendado 
                FROM proyecto_tema 
                WHERE id_proyecto = ANY(%s)
                LIMIT 5
            """, (processed_ids,))
            sample_results = cur.fetchall()
            logger.info(f"Sample results: {sample_results}")
        
        logger.success(f"Successfully processed {len(processed_ids)} projects with {total_relationships} total relationships")
        
    except Exception as e:
        logger.error(f"Error populating proyecto_tema table: {str(e)}")
        conn.rollback()
    finally:
        conn.close()

if __name__ == "__main__":
    populate_proyecto_tema() 