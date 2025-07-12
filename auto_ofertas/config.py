import os
from dotenv import load_dotenv

load_dotenv()

class Config:
    # Directorios
    UPLOAD_DIR = "uploads"
    LICITACIONES_DIR = os.path.join(UPLOAD_DIR, "licitaciones")
    OFERTAS_DIR = os.path.join(UPLOAD_DIR, "ofertas")
    GENERADAS_DIR = os.path.join(UPLOAD_DIR, "generadas")
    
    # Configuración de IA
    OPENAI_API_KEY = os.getenv("OPENAI_API_KEY", "")
    # Configuración del modelo de IA
    MODEL_NAME = os.getenv("MODEL_NAME", "gpt-3.5-turbo")  # Cambiado de gpt-4 a gpt-3.5-turbo
    MAX_TOKENS = int(os.getenv("MAX_TOKENS", "4000"))
    TEMPERATURE = float(os.getenv("TEMPERATURE", "0.7"))
    
    # Configuración de procesamiento
    # MAX_TOKENS = 4000
    # TEMPERATURE = 0.7
    
    # Crear directorios si no existen
    @classmethod
    def create_directories(cls):
        for directory in [cls.UPLOAD_DIR, cls.LICITACIONES_DIR, cls.OFERTAS_DIR, cls.GENERADAS_DIR]:
            os.makedirs(directory, exist_ok=True) 