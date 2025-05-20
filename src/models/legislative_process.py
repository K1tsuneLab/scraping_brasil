from datetime import datetime
from typing import Optional, List, Dict, Any
from pydantic import BaseModel, Field
from loguru import logger

class LegislativeProcess(BaseModel):
    """Model for legislative process data from the Senate API."""
    id: Optional[int] = None
    sigla: Optional[str] = None
    numero: Optional[int] = None
    ano: Optional[int] = None
    data_apresentacao: Optional[datetime] = None
    descricao: Optional[str] = None
    autor: Optional[str] = None
    ementa: Optional[str] = None
    situacao: Optional[str] = None
    link_inteiro_teor: Optional[str] = None
    
    class Config:
        from_attributes = True

class APIResponse(BaseModel):
    """Model for the API response structure."""
    ListaMateriasTramitando: Optional[List[Dict[str, Any]]] = None
    ListaMateriasNaoTramitando: Optional[List[Dict[str, Any]]] = None
    
    def get_processes(self) -> List[LegislativeProcess]:
        """Convert the raw response into a list of LegislativeProcess objects."""
        processes = []
        
        if self.ListaMateriasTramitando:
            for item in self.ListaMateriasTramitando:
                try:
                    process = LegislativeProcess(**item)
                    processes.append(process)
                except Exception as e:
                    logger.error(f"Error parsing process: {str(e)}")
                    continue
                    
        if self.ListaMateriasNaoTramitando:
            for item in self.ListaMateriasNaoTramitando:
                try:
                    process = LegislativeProcess(**item)
                    processes.append(process)
                except Exception as e:
                    logger.error(f"Error parsing process: {str(e)}")
                    continue
                    
        return processes 