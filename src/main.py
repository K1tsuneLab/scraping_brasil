"""
Main coordination script for the Brazil Scraping project.
Coordinates all components: scraping, validation, translation, and storage.
"""
import asyncio
import sys
from pathlib import Path
from datetime import datetime
from loguru import logger
from typing import List, Dict, Any

# Add the project root to Python path
project_root = Path(__file__).parent.parent
sys.path.append(str(project_root))

from config.settings import settings
from src.storage.drive_factory import DriveFactory
from src.scraper.validators import DocumentValidator, DocumentMetadata
from src.utils.date_utils import get_date_range_since_2024
from src.api.senate_client import SenateAPIClient
from src.processors.data_processor import DataProcessor
from src.utils.translate_file_pt_to_es import translate_file_pt_to_es

class BrazilScrapingCoordinator:
    """Main coordinator for the Brazil scraping system."""
    
    def __init__(self):
        self.drive_manager = DriveFactory.create_drive_manager()
        self.validator = DocumentValidator(self.drive_manager)
        self.data_processor = DataProcessor()
        self.start_date, self.end_date = get_date_range_since_2024()
        
        logger.info("Brazil Scraping Coordinator initialized")
        logger.info(f"Drive mode: {settings.APP_MODE}")
        logger.info(f"Date range: {self.start_date} to {self.end_date}")
    
    async def scrape_senate_documents(self) -> List[DocumentMetadata]:
        """Scrape documents from the Senate API."""
        logger.info("Starting Senate document scraping...")
        
        documents = []
        async with SenateAPIClient() as client:
            # Parse date range for Senate API
            start_year = int(self.start_date.split('-')[0])
            end_year = int(self.end_date.split('-')[0])
            
            for year in range(start_year, end_year + 1):
                try:
                    processes = await client.get_processes_by_year(year)
                    logger.info(f"Retrieved {len(processes)} processes for year {year}")
                    
                    # Convert to DocumentMetadata
                    for process in processes:
                        doc = DocumentMetadata(
                            id=str(process.id) if process.id else f"senate_{year}_{process.numero}",
                            title=process.ementa or process.descricao or "Sem título",
                            date=process.data_apresentacao.strftime('%Y-%m-%d') if process.data_apresentacao else f"{year}-01-01",
                            source='senado',
                            document_type=process.sigla or 'UNKNOWN',
                            url=process.link_inteiro_teor or ""
                        )
                        documents.append(doc)
                        
                except Exception as e:
                    logger.error(f"Error scraping Senate data for year {year}: {e}")
                    continue
        
        logger.info(f"Total Senate documents scraped: {len(documents)}")
        return documents
    
    async def scrape_camara_documents(self) -> List[DocumentMetadata]:
        """Scrape documents from the Chamber of Deputies."""
        logger.info("Starting Chamber of Deputies document scraping...")
        
        # Import and use the existing scraping script
        from scrape_proposicoes_since_2023 import fetch_all_proposicoes, process_proposicoes
        
        try:
            # Fetch raw data
            proposicoes = fetch_all_proposicoes(self.start_date)
            processed = process_proposicoes(proposicoes)
            
            # Convert to DocumentMetadata
            documents = []
            for prop in processed:
                doc = DocumentMetadata(
                    id=str(prop['id']),
                    title=prop['ementa'],
                    date=prop['dataApresentacao'][:10] if prop['dataApresentacao'] else self.start_date,
                    source='camara',
                    document_type=prop['siglaTipo'],
                    url=prop['uri']
                )
                documents.append(doc)
            
            logger.info(f"Total Chamber documents scraped: {len(documents)}")
            return documents
            
        except Exception as e:
            logger.error(f"Error scraping Chamber data: {e}")
            return []
    
    async def validate_and_filter_documents(self, documents: List[DocumentMetadata]) -> List[DocumentMetadata]:
        """Validate and filter documents for new ones only."""
        logger.info(f"Validating {len(documents)} documents...")
        
        # Filter for new documents within date range
        new_documents = self.validator.filter_new_documents(
            documents, self.start_date, self.end_date
        )
        
        logger.info(f"Found {len(new_documents)} new documents to process")
        return new_documents
    
    async def store_documents(self, documents: List[DocumentMetadata]) -> Dict[str, Any]:
        """Store documents in Drive and update tracking."""
        logger.info(f"Storing {len(documents)} documents...")
        
        stored_count = 0
        failed_count = 0
        
        # Setup folder structure
        folders = await self.drive_manager.setup_folder_structure()
        
        for doc in documents:
            try:
                # Prepare document data
                document_data = {
                    'metadata': doc.to_dict(),
                    'stored_at': datetime.now().isoformat()
                }
                
                # Determine target folder
                folder_id = folders.get('documentos_senado' if doc.source == 'senado' else 'documentos_camara')
                
                # Create filename
                filename = f"{doc.source}_{doc.id}_{doc.date}.json"
                
                # Upload document metadata
                await self.drive_manager.upload_file(
                    file_content=str(document_data),
                    filename=filename,
                    folder_id=folder_id,
                    mime_type='application/json'
                )
                
                # Add to validator tracking
                self.validator.add_document(doc)
                stored_count += 1
                
                logger.debug(f"Stored document: {doc.id}")
                
            except Exception as e:
                logger.error(f"Failed to store document {doc.id}: {e}")
                failed_count += 1
        
        result = {
            'stored_count': stored_count,
            'failed_count': failed_count,
            'total_processed': len(documents)
        }
        
        logger.info(f"Storage complete: {stored_count} stored, {failed_count} failed")
        return result
    
    async def translate_documents(self, file_path: str) -> str:
        """Translate documents from Portuguese to Spanish."""
        logger.info(f"Starting translation of {file_path}...")
        
        try:
            output_path = file_path.replace('.json', '_es.json')
            await translate_file_pt_to_es(file_path, output_path)
            
            logger.info(f"Translation completed: {output_path}")
            return output_path
            
        except Exception as e:
            logger.error(f"Translation failed: {e}")
            raise
    
    async def generate_report(self) -> Dict[str, Any]:
        """Generate a comprehensive report of the scraping session."""
        logger.info("Generating session report...")
        
        # Get validator statistics
        validator_stats = self.validator.get_statistics()
        
        # Get drive statistics
        drive_stats = self.drive_manager.get_stats()
        
        # Combine all statistics
        report = {
            'session_info': {
                'start_time': datetime.now().isoformat(),
                'date_range': f"{self.start_date} to {self.end_date}",
                'mode': settings.APP_MODE
            },
            'document_statistics': validator_stats,
            'storage_statistics': drive_stats,
            'configuration': {
                'data_paths': {
                    'raw': str(settings.DATA_RAW_PATH),
                    'processed': str(settings.DATA_PROCESSED_PATH),
                    'mock_storage': str(settings.MOCK_STORAGE_PATH)
                }
            }
        }
        
        # Save report
        report_path = settings.DATA_PROCESSED_PATH / f"scraping_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        
        import json
        with open(report_path, 'w', encoding='utf-8') as f:
            json.dump(report, f, indent=2, ensure_ascii=False)
        
        logger.info(f"Report saved to: {report_path}")
        return report
    
    async def run_full_scraping_pipeline(self) -> Dict[str, Any]:
        """Execute the complete scraping pipeline."""
        logger.info("🚀 Starting full Brazil scraping pipeline...")
        
        try:
            # 1. Scrape documents from both sources
            logger.info("📥 Phase 1: Document Scraping")
            senate_docs = await self.scrape_senate_documents()
            camara_docs = await self.scrape_camara_documents()
            
            all_documents = senate_docs + camara_docs
            logger.info(f"Total documents scraped: {len(all_documents)}")
            
            # 2. Validate and filter documents
            logger.info("🔍 Phase 2: Validation and Filtering")
            new_documents = await self.validate_and_filter_documents(all_documents)
            
            # 3. Store documents
            logger.info("💾 Phase 3: Document Storage")
            storage_result = await self.store_documents(new_documents)
            
            # 4. Generate report
            logger.info("📊 Phase 4: Report Generation")
            report = await self.generate_report()
            
            # 5. Summary
            logger.success("✅ Scraping pipeline completed successfully!")
            logger.info(f"📋 Summary:")
            logger.info(f"  - Total scraped: {len(all_documents)}")
            logger.info(f"  - New documents: {len(new_documents)}")
            logger.info(f"  - Successfully stored: {storage_result['stored_count']}")
            logger.info(f"  - Failed: {storage_result['failed_count']}")
            
            return {
                'success': True,
                'total_scraped': len(all_documents),
                'new_documents': len(new_documents),
                'storage_result': storage_result,
                'report': report
            }
            
        except Exception as e:
            logger.error(f"❌ Pipeline failed: {e}")
            return {
                'success': False,
                'error': str(e)
            }

async def main():
    """Main entry point for the Brazil scraping system."""
    logger.info("🇧🇷 Brazil Government Documents Scraping System")
    logger.info("=" * 50)
    
    # Initialize coordinator
    coordinator = BrazilScrapingCoordinator()
    
    # Run the pipeline
    result = await coordinator.run_full_scraping_pipeline()
    
    if result['success']:
        logger.success("🎉 All operations completed successfully!")
        return 0
    else:
        logger.error(f"💥 Pipeline failed: {result.get('error', 'Unknown error')}")
        return 1

if __name__ == "__main__":
    exit_code = asyncio.run(main())