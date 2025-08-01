import os
from dotenv import load_dotenv
import logging
from datetime import datetime

# Cargar variables de entorno
load_dotenv()

class Config:
    # Configuración de OpenAI
    OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
    MODEL_NAME = os.getenv("MODEL_NAME", "gpt-4")
    MAX_TOKENS = int(os.getenv("MAX_TOKENS", "1000"))
    TEMPERATURE = float(os.getenv("TEMPERATURE", "0.7"))
    
    # Configuración del servidor
    HOST = os.getenv("HOST", "0.0.0.0")
    PORT = int(os.getenv("PORT", "8000"))
    RELOAD = os.getenv("RELOAD", "true").lower() == "true"
    
    # Directorios
    BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    UPLOAD_DIR = os.path.join(BASE_DIR, "uploads")
    LICITACIONES_DIR = os.path.join(UPLOAD_DIR, "licitaciones")
    OFERTAS_DIR = os.path.join(UPLOAD_DIR, "ofertas")
    GENERADAS_DIR = os.path.join(UPLOAD_DIR, "generadas")
    
    # Configuración de logging
    LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO")
    LOG_FORMAT = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    LOG_FILE = os.path.join(BASE_DIR, "logs", "api.log")
    
    @classmethod
    def setup_logging(cls):
        """Configura el sistema de logging"""
        # Crear directorio de logs si no existe
        os.makedirs(os.path.dirname(cls.LOG_FILE), exist_ok=True)
        
        # Configurar logging
        logging.basicConfig(
            level=getattr(logging, cls.LOG_LEVEL),
            format=cls.LOG_FORMAT,
            handlers=[
                logging.FileHandler(cls.LOG_FILE, encoding='utf-8'),
                logging.StreamHandler()  # También mostrar en consola
            ]
        )
        
        # Crear logger específico para la API
        logger = logging.getLogger("API_GUX")
        logger.setLevel(getattr(logging, cls.LOG_LEVEL))
        
        return logger
    
    @classmethod
    def create_directories(cls):
        """Crea los directorios necesarios si no existen"""
        directories = [cls.UPLOAD_DIR, cls.LICITACIONES_DIR, cls.OFERTAS_DIR, cls.GENERADAS_DIR]
        for directory in directories:
            if not os.path.exists(directory):
                os.makedirs(directory)
                print(f"📁 Directorio creado: {directory}") 