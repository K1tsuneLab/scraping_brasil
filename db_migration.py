import psycopg2
from psycopg2 import Error
from datetime import datetime
import json
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

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

def get_processed_ids(cursor):
    """Get list of already processed IDs from both tables"""
    try:
        # Get IDs from gacetas
        cursor.execute("SELECT numero_gaceta FROM gacetas WHERE id_pais = 16")
        gaceta_ids = set(row[0] for row in cursor.fetchall())
        
        return gaceta_ids
    except Error as e:
        print(f"Error fetching processed IDs: {e}")
        return set()

def process_record(connection, record_data, processed_ids):
    """Process a single record"""
    try:
        cursor = connection.cursor()
        
        # Check if record already exists
        if record_data['id'] in processed_ids:
            print(f"Record already exists for ID: {record_data['id']}, skipping...")
            return False
            
        # Format the date, handling possible timestamp
        fecha_publicacion = datetime.strptime(record_data['data_apresentacao'].split('T')[0], '%Y-%m-%d').strftime('%Y-%m-%d')
        numero_proyecto = f"{record_data['sigla']}-{record_data['id']}"
        
        # Start a new transaction
        cursor.execute("BEGIN")
        
        try:
            # Insert data into gacetas
            gaceta_sql = """
            INSERT INTO gacetas (id_pais, numero_gaceta, anio, fecha_publicacion, enlace_pdf, estado, id_institucion)
            VALUES (%s, %s, %s, %s, %s, %s, %s)
            RETURNING id_gaceta;
            """
            
            gaceta_data = (
                16,  # id_pais
                record_data['id'],  # numero_gaceta
                record_data['ano'],  # anio
                fecha_publicacion,  # fecha_publicacion
                record_data['link_inteiro_teor'],  # enlace_pdf
                'aprobado',  # estado
                1  # id_institucion
            )
            
            cursor.execute(gaceta_sql, gaceta_data)
            
            # Insert data into proyectos
            proyecto_sql = """
            INSERT INTO proyectos (numero_proyecto, anio_legislativo, titulo_proyecto, autores_proyecto)
            VALUES (%s, %s, %s, %s)
            RETURNING id_proyecto;
            """
            
            proyecto_data = (
                numero_proyecto,  # numero_proyecto
                '2023-2027',  # anio_legislativo
                record_data['ementa'],  # titulo_proyecto
                record_data['autor']  # autores_proyecto
            )
            
            cursor.execute(proyecto_sql, proyecto_data)
            
            # Commit the transaction
            connection.commit()
            print(f"Successfully processed record ID: {record_data['id']}")
            return True
            
        except Error as e:
            # Rollback in case of error
            connection.rollback()
            print(f"Error processing record {record_data['id']}: {e}")
            return False
            
    except Error as e:
        print(f"Error in process_record: {e}")
        return False
    finally:
        cursor.close()

def main():
    try:
        # Load all data from JSON
        with open('data/processed/senate_processes_20230201_to_20250521_es.json', 'r', encoding='utf-8') as f:
            senate_data = json.load(f)
            
        if not senate_data:
            raise ValueError("No data found in JSON file")
        
        # Connect to database
        connection = connect_to_database()
        if not connection:
            raise Exception("Failed to connect to database")
            
        # Get already processed IDs
        cursor = connection.cursor()
        processed_ids = get_processed_ids(cursor)
        cursor.close()
        
        # Process all records
        total_records = len(senate_data)
        processed_count = 0
        skipped_count = 0
        
        print(f"\nStarting to process {total_records} records...")
        print(f"Found {len(processed_ids)} already processed records")
        
        try:
            for i, record in enumerate(senate_data, 1):
                print(f"\nProcessing record {i} of {total_records}")
                if process_record(connection, record, processed_ids):
                    processed_count += 1
                    processed_ids.add(record['id'])  # Add to processed set
                else:
                    skipped_count += 1
                
                # Print progress every 10 records
                if i % 10 == 0:
                    print(f"\nProgress: {i}/{total_records} records processed")
                    print(f"Processed: {processed_count}, Skipped: {skipped_count}")
                    
        finally:
            connection.close()
            print("\nDatabase connection closed")
            
        # Print final summary
        print(f"\nProcessing complete!")
        print(f"Total records: {total_records}")
        print(f"Successfully processed: {processed_count}")
        print(f"Skipped (already existed): {skipped_count}")
        
    except FileNotFoundError:
        print("Error: JSON file not found. Please ensure the file exists in data/processed/ directory.")
    except json.JSONDecodeError:
        print("Error: Invalid JSON format in the file.")
    except Exception as e:
        print(f"Unexpected error: {e}")

if __name__ == "__main__":
    main() 