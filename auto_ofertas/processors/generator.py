from docx import Document
from typing import Dict, Any
from .ai_generator import AIGenerator
from ..models import LicitacionData

def generar_oferta(datos: Dict[str, Any], output_path: str) -> str:
    """Función de compatibilidad que usa el nuevo sistema de IA"""
    # Crear instancia del generador de IA
    ai_generator = AIGenerator()
    
    # Convertir datos a formato LicitacionData si es necesario
    if isinstance(datos, dict):
        licitacion = LicitacionData(
            titulo=datos.get('nombre_proyecto', 'Proyecto'),
            descripcion=datos.get('resumen', 'Descripción del proyecto'),
            requisitos=datos.get('requisitos', ['Requisitos básicos']),
            plazos=datos.get('plazos', {'duracion': 'No especificada'}),
            presupuesto=datos.get('presupuesto', 'No especificado'),
            contenido_completo=datos.get('contenido_bruto', '')
        )
    else:
        licitacion = datos
    
    # Generar oferta usando IA
    resultado = ai_generator.generar_oferta_tecnica(
        licitacion=licitacion,
        empresa_nombre=datos.get('empresa', 'Mi Empresa'),
        empresa_descripcion=datos.get('empresa_descripcion', '')
    )
    
    return resultado['oferta_generada']

def generar_oferta_avanzada(licitacion_path: str, empresa_nombre: str, 
                           empresa_descripcion: str = "", 
                           ofertas_dir: str = None, 
                           licitaciones_dir: str = None) -> Dict[str, Any]:
    """Genera una oferta técnica avanzada usando IA y datos históricos"""
    
    from .parser import DocumentParser
    from ..config import Config
    
    # Inicializar parser y generador
    parser = DocumentParser()
    ai_generator = AIGenerator()
    
    # Cargar datos históricos si se proporcionan directorios
    if ofertas_dir and licitaciones_dir:
        ai_generator.cargar_datos_historicos(ofertas_dir, licitaciones_dir)
    else:
        # Usar directorios por defecto
        ai_generator.cargar_datos_historicos(Config.OFERTAS_DIR, Config.LICITACIONES_DIR)
    
    # Parsear la licitación
    licitacion = parser.parse_licitacion(licitacion_path)
    
    # Generar oferta
    resultado = ai_generator.generar_oferta_tecnica(
        licitacion=licitacion,
        empresa_nombre=empresa_nombre,
        empresa_descripcion=empresa_descripcion
    )
    
    return resultado
