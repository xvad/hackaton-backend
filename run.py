#!/usr/bin/env python3
"""
Script para ejecutar la API de Generación Automática de Ofertas Técnicas
"""

import uvicorn
import os
import logging
from auto_ofertas.config import Config

def main():
    """Función principal para ejecutar la aplicación"""
    
    # Configurar logging
    logger = Config.setup_logging()
    
    logger.info("=" * 60)
    logger.info("🚀 INICIANDO API DE GENERACIÓN AUTOMÁTICA DE OFERTAS TÉCNICAS")
    logger.info("=" * 60)
    
    # Verificar si existe la API key de OpenAI
    if not Config.OPENAI_API_KEY:
        logger.warning("⚠️  ADVERTENCIA: No se ha configurado OPENAI_API_KEY")
        logger.warning("   La generación de ofertas funcionará con contenido básico")
        logger.warning("   Para usar IA completa, configura tu API key en el archivo .env")
    else:
        logger.info("✅ OpenAI API Key configurada correctamente")
    
    # Crear directorios necesarios
    logger.info("📁 Creando directorios necesarios...")
    Config.create_directories()
    
    # Configuración del servidor
    host = os.getenv("HOST", "0.0.0.0")
    port = int(os.getenv("PORT", 8000))
    reload = os.getenv("RELOAD", "true").lower() == "true"
    
    logger.info("⚙️  Configuración del servidor:")
    logger.info(f"   📍 Host: {host}")
    logger.info(f"   🚪 Puerto: {port}")
    logger.info(f"   🔄 Recarga automática: {'Activada' if reload else 'Desactivada'}")
    logger.info(f"   📚 Documentación: http://{host}:{port}/docs")
    logger.info(f"   🧠 Modelo IA: {Config.MODEL_NAME}")
    logger.info(f"   📝 Nivel de log: {Config.LOG_LEVEL}")
    logger.info(f"   📄 Archivo de log: {Config.LOG_FILE}")
    
    logger.info("=" * 60)
    logger.info("🎯 Servidor iniciando...")
    logger.info("=" * 60)
    
    # Ejecutar servidor
    uvicorn.run(
        "auto_ofertas.main:app",
        host=host,
        port=port,
        reload=reload,
        log_level="info"
    )

if __name__ == "__main__":
    main() 