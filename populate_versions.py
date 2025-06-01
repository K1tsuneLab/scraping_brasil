import psycopg2
from psycopg2 import Error
from pathlib import Path
import json
import os
from dotenv import load_dotenv
from datetime import datetime
import re
from collections import defaultdict
import logging
from tqdm import tqdm

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('populate_versions.log'),
        logging.StreamHandler()
    ]
)

# Load environment variables
load_dotenv()

# Configure paths
TEXT_JSON_DIR = Path("/Users/imakia/Google Drive/My Drive/Kitsune/Fase1_Estructuracion_base/brasil/text_json_es")
PROGRESS_FILE = Path("processed_files.json")
ERROR_FILE = Path("error_files.json")

def load_error_files():
    """Load the list of files that had errors"""
    if ERROR_FILE.exists():
        try:
            with open(ERROR_FILE, 'r') as f:
                return set(json.load(f))
        except Exception as e:
            logging.error(f"Error loading error files list: {e}")
    return set()

def save_error_files(error_files):
    """Save the list of files that had errors"""
    try:
        with open(ERROR_FILE, 'w') as f:
            json.dump(list(error_files), f)
    except Exception as e:
        logging.error(f"Error saving error files list: {e}")

def load_progress():
    """Load the list of successfully processed files"""
    if PROGRESS_FILE.exists():
        try:
            with open(PROGRESS_FILE, 'r') as f:
                return set(json.load(f))
        except Exception as e:
            logging.error(f"Error loading progress file: {e}")
    return set()

def save_progress(processed_files):
    """Save the list of successfully processed files"""
    try:
        with open(PROGRESS_FILE, 'w') as f:
            json.dump(list(processed_files), f)
    except Exception as e:
        logging.error(f"Error saving progress file: {e}")

def read_json_file(file_path):
    """Read JSON file with robust error handling"""
    try:
        # First try normal reading
        with open(file_path, 'r', encoding='utf-8') as f:
            return json.load(f)
    except UnicodeDecodeError:
        # If that fails, try reading as bytes and remove NUL bytes
        try:
            with open(file_path, 'rb') as f:
                content = f.read()
                # Remove NUL bytes and decode
                cleaned = content.replace(b'\x00', b'')
                return json.loads(cleaned.decode('utf-8'))
        except Exception as e:
            logging.error(f"Error reading file {file_path} as bytes: {e}")
            return None
    except json.JSONDecodeError as e:
        logging.error(f"JSON decode error in file {file_path}: {e}")
        return None
    except Exception as e:
        logging.error(f"Unexpected error reading file {file_path}: {e}")
        return None

def split_into_sentences(text):
    """Split text into sentences"""
    # Split on sentence endings
    sentences = re.split(r'[.!?]+', text)
    # Remove empty sentences and strip whitespace
    return [s.strip() for s in sentences if s.strip()]

def calculate_word_frequencies(sentences):
    """Calculate word frequencies across all sentences"""
    word_freq = defaultdict(int)
    for sentence in sentences:
        words = sentence.lower().split()
        for word in words:
            word_freq[word] += 1
    return word_freq

def score_sentences(sentences, word_freq):
    """Score sentences based on word frequencies"""
    scores = []
    for sentence in sentences:
        words = sentence.lower().split()
        if not words:
            scores.append(0)
            continue
        
        # Calculate score as average word frequency
        score = sum(word_freq[word] for word in words) / len(words)
        # Boost score for longer sentences (but not too much)
        length_factor = min(len(words) / 10.0, 1.0)
        scores.append(score * length_factor)
    
    return scores

def generate_summary(text, num_sentences=2):
    """Generate summary by selecting most important sentences"""
    try:
        # Clean the text first
        cleaned_text = clean_text(text)
        
        # Split into sentences
        sentences = split_into_sentences(cleaned_text)
        if len(sentences) <= num_sentences:
            return text
        
        # Calculate word frequencies
        word_freq = calculate_word_frequencies(sentences)
        
        # Score sentences
        scores = score_sentences(sentences, word_freq)
        
        # Get indices of top scoring sentences while preserving order
        indices = sorted(range(len(scores)), key=lambda i: scores[i], reverse=True)[:num_sentences]
        indices = sorted(indices)  # Sort to maintain original order
        
        # Join selected sentences
        summary = '. '.join(sentences[i] for i in indices)
        return summary + '.'
        
    except Exception as e:
        print(f"Error in generate_summary: {e}")
        return None

def connect_to_database():
    try:
        connection = psycopg2.connect(
            host=os.getenv('DB_HOST', 'localhost'),
            port=os.getenv('DB_PORT', '5432'),
            database=os.getenv('DB_NAME', 'postgres'),
            user=os.getenv('DB_USER', 'postgres'),
            password=os.getenv('DB_PASSWORD')
        )
        return connection
    except Error as e:
        print(f"Error connecting to PostgreSQL: {e}")
        return None

def get_processed_version_ids(cursor):
    """Get list of already processed version IDs"""
    try:
        cursor.execute("SELECT id_proyecto FROM versionesproyecto")
        return set(row[0] for row in cursor.fetchall())
    except Error as e:
        print(f"Error fetching processed version IDs: {e}")
        return set()

def clean_text(text):
    """Clean and normalize text"""
    # Remove extra whitespace and normalize spaces
    text = ' '.join(text.split())
    # Remove special characters but keep periods and basic punctuation
    text = re.sub(r'[^\w\s.,;:?!-]', '', text)
    # Normalize multiple periods/dots
    text = re.sub(r'\.{2,}', '.', text)
    # Ensure proper spacing after punctuation
    text = re.sub(r'([.,;:?!])([^\s])', r'\1 \2', text)
    return text

def process_version(connection, json_data):
    try:
        cursor = connection.cursor()
        
        json_id = str(json_data['id'])
        logging.info(f"Processing version for ID: {json_id}")
        
        # Get proyecto_id using the numero_proyecto
        numero_proyecto = f"SF-{json_id}"
        logging.debug(f"Looking for proyecto with numero_proyecto: {numero_proyecto}")
        
        cursor.execute("""
            SELECT id_proyecto 
            FROM proyectos 
            WHERE numero_proyecto = %s
        """, (numero_proyecto,))
        
        proyecto_result = cursor.fetchone()
        if not proyecto_result:
            logging.warning(f"No matching proyecto found for numero_proyecto: {numero_proyecto}")
            return False
            
        id_proyecto = proyecto_result[0]
        
        # Get gaceta_id using numero_gaceta
        cursor.execute("""
            SELECT id_gaceta, fecha_publicacion 
            FROM gacetas 
            WHERE numero_gaceta = %s
        """, (json_id,))
        
        gaceta_result = cursor.fetchone()
        if not gaceta_result:
            logging.warning(f"No matching gaceta found for numero_gaceta: {json_id}")
            return False
            
        id_gaceta, fecha_publicacion = gaceta_result
        
        # Generate summary from full_text
        full_text = json_data['full_text']
        logging.debug(f"Original text length: {len(full_text)} characters")
        
        summary = generate_summary(full_text)
        if not summary:
            logging.warning("Failed to generate summary, using truncated text")
            summary = full_text[:2000] + "..."
        
        # Insert into versionesproyecto
        version_sql = """
        INSERT INTO versionesproyecto (
            id_proyecto, id_gaceta, version_num, 
            descripcion_cambios, texto_crudo, fecha_version, 
            resumen_proyecto
        )
        VALUES (%s, %s, %s, %s, %s, %s, %s)
        """
        
        version_data = (
            id_proyecto,
            id_gaceta,
            1,  # version_num
            None,  # descripcion_cambios
            full_text,
            fecha_publicacion,
            summary
        )
        
        cursor.execute(version_sql, version_data)
        connection.commit()
        logging.info(f"Successfully processed version for proyecto ID: {id_proyecto}")
        return True
        
    except Error as e:
        connection.rollback()
        logging.error(f"Error processing version: {e}")
        return False
    finally:
        cursor.close()

def process_files_batch(connection, batch_files, processed_in_batch, error_files):
    """Process a batch of files"""
    for file in batch_files:
        if str(file) in error_files:
            logging.info(f"Skipping previously errored file: {file}")
            continue
            
        try:
            json_data = read_json_file(file)
            if json_data is None:
                error_files.add(str(file))
                continue
                
            success = process_version(connection, json_data)
            if success:
                processed_in_batch.add(str(file))
            else:
                logging.warning(f"Failed to process file: {file}")
                error_files.add(str(file))
                
        except Exception as e:
            logging.error(f"Unexpected error processing file {file}: {e}")
            error_files.add(str(file))
            continue
    return True

def process_batch(connection, json_files, processed_files, error_files, batch_size=10):
    """Process a batch of files with progress tracking"""
    batch = []
    processed_in_batch = set()
    
    for file in json_files:
        if str(file) in processed_files:
            continue
            
        batch.append(file)
        if len(batch) >= batch_size:
            success = process_files_batch(connection, batch, processed_in_batch, error_files)
            batch = []
            # Save progress after each batch
            processed_files.update(processed_in_batch)
            save_progress(processed_files)
            save_error_files(error_files)
            processed_in_batch.clear()
    
    # Process remaining files
    if batch:
        success = process_files_batch(connection, batch, processed_in_batch, error_files)
        processed_files.update(processed_in_batch)
        save_progress(processed_files)
        save_error_files(error_files)
    
    return True

def main():
    try:
        # Load progress and error files from previous runs
        processed_files = load_progress()
        error_files = load_error_files()
        logging.info(f"Found {len(processed_files)} previously processed files")
        logging.info(f"Found {len(error_files)} files with previous errors")
        
        # Connect to database
        connection = connect_to_database()
        if not connection:
            raise Exception("Failed to connect to database")
        logging.info("Database connection successful")
        
        # Get all JSON files
        json_files = list(TEXT_JSON_DIR.glob('*.json'))
        if not json_files:
            logging.warning("No JSON files found in directory")
            return
            
        total_files = len(json_files)
        remaining_files = total_files - len(processed_files) - len(error_files)
        logging.info(f"Found {total_files} total files, {remaining_files} remaining to process")
        
        # Process files in batches with progress bar
        with tqdm(total=remaining_files, desc="Processing files") as pbar:
            current_processed = len(processed_files)
            current_errors = len(error_files)
            
            success = process_batch(connection, json_files, processed_files, error_files)
            
            # Update progress bar with both successful and error files
            new_processed = len(processed_files) - current_processed
            new_errors = len(error_files) - current_errors
            pbar.update(new_processed + new_errors)
            
            if success:
                logging.info(f"Processing completed! Processed: {len(processed_files)}, Errors: {len(error_files)}")
            else:
                logging.warning("Processing stopped due to an error")
                
    except Exception as e:
        logging.error(f"Unexpected error: {e}")
    finally:
        if connection:
            connection.close()
            logging.info("Database connection closed")

if __name__ == "__main__":
    main() 