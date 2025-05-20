from datetime import datetime
from typing import Optional, List
from pydantic import BaseModel, Field

class LegislativeProcess(BaseModel):
    """Model for legislative process data from the Senate API."""
    id: int
    sigla: str
    numero: int
    ano: int
    data_apresentacao: datetime
    descricao: str
    autor: Optional[str] = None
    ementa: Optional[str] = None
    situacao: Optional[str] = None
    link_inteiro_teor: Optional[str] = None
    
    class Config:
        from_attributes = True

class APIResponse(BaseModel):
    """Model for the API response structure."""
    ListaMateriasTramitando: List[LegislativeProcess]
    ListaMateriasNaoTramitando: Optional[List[LegislativeProcess]] = None
    Sigla: Optional[str] = None
    Numero: Optional[int] = None
    Ano: Optional[int] = None
    Data: Optional[datetime] = None
    Descricao: Optional[str] = None
    Autoria: Optional[str] = None
    Ementa: Optional[str] = None
    Situacao: Optional[str] = None
    LinkInteiroTeor: Optional[str] = None 