#!/usr/bin/env python3
"""
Script para ejecutar la API de Generación Automática de Ofertas Técnicas
"""

import uvicorn
import os
from auto_ofertas.config import Config

def main():
    """Función principal para ejecutar la aplicación"""
    
    # Verificar si existe la API key de OpenAI
    if not Config.OPENAI_API_KEY:
        print("⚠️  ADVERTENCIA: No se ha configurado OPENAI_API_KEY")
        print("   La generación de ofertas funcionará con contenido básico")
        print("   Para usar IA completa, configura tu API key en el archivo .env")
        print()
    
    # Crear directorios necesarios
    Config.create_directories()
    
    # Configuración del servidor
    host = os.getenv("HOST", "0.0.0.0")
    port = int(os.getenv("PORT", 8000))
    reload = os.getenv("RELOAD", "true").lower() == "true"
    
    print("🚀 Iniciando API de Generación Automática de Ofertas Técnicas")
    print(f"📍 Servidor: http://{host}:{port}")
    print(f"📚 Documentación: http://{host}:{port}/docs")
    print(f"🔄 Recarga automática: {'Activada' if reload else 'Desactivada'}")
    print()
    
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