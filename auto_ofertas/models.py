from pydantic import BaseModel
from typing import List, Optional, Dict, Any
from datetime import datetime

class LicitacionData(BaseModel):
    titulo: str
    descripcion: str
    requisitos: List[str]
    plazos: Dict[str, Any]
    presupuesto: Optional[str] = None
    contenido_completo: str

class OfertaTecnicaData(BaseModel):
    titulo: str
    empresa: str
    resumen_ejecutivo: str
    metodologia: str
    cronograma: str
    equipo: List[str]
    experiencia: str
    contenido_completo: str

class GeneracionRequest(BaseModel):
    licitacion_id: str
    empresa_nombre: str
    empresa_descripcion: Optional[str] = None

class GeneracionResponse(BaseModel):
    mensaje: str
    oferta_generada: str
    datos_extraidos: Dict[str, Any]
    similitud_encontrada: Optional[float] = None 