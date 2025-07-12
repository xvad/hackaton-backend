#!/usr/bin/env python3
"""
Script para cargar automáticamente archivos históricos de licitaciones y ofertas técnicas
"""

import os
import shutil
import requests
from pathlib import Path

def cargar_archivos_historicos():
    """Carga automáticamente archivos históricos desde carpetas específicas"""
    
    # Configuración
    API_BASE_URL = "http://localhost:8000"
    CARPETA_LICITACIONES_ORIGEN = "licitaciones_historicas"  # Carpeta con tus licitaciones
    CARPETA_OFERTAS_ORIGEN = "ofertas_historicas"           # Carpeta con tus ofertas técnicas
    
    print("🚀 Cargando archivos históricos a la API")
    print("=" * 50)
    
    # Crear directorios de origen si no existen
    os.makedirs(CARPETA_LICITACIONES_ORIGEN, exist_ok=True)
    os.makedirs(CARPETA_OFERTAS_ORIGEN, exist_ok=True)
    
    # Verificar que la API esté funcionando
    try:
        response = requests.get(f"{API_BASE_URL}/")
        if response.status_code != 200:
            print("❌ Error: La API no está funcionando")
            return
        print("✅ API funcionando correctamente")
    except Exception as e:
        print(f"❌ Error conectando a la API: {e}")
        return
    
    # Cargar licitaciones históricas
    print(f"\n📄 Cargando licitaciones desde: {CARPETA_LICITACIONES_ORIGEN}")
    licitaciones_cargadas = 0
    
    if os.path.exists(CARPETA_LICITACIONES_ORIGEN):
        for filename in os.listdir(CARPETA_LICITACIONES_ORIGEN):
            if filename.endswith('.docx'):
                file_path = os.path.join(CARPETA_LICITACIONES_ORIGEN, filename)
                try:
                    with open(file_path, 'rb') as f:
                        files = {'file': f}
                        response = requests.post(f"{API_BASE_URL}/cargar-licitacion/", files=files)
                    
                    if response.status_code == 200:
                        print(f"✅ Licitación cargada: {filename}")
                        licitaciones_cargadas += 1
                    else:
                        print(f"❌ Error cargando {filename}: {response.status_code}")
                except Exception as e:
                    print(f"❌ Error procesando {filename}: {e}")
    else:
        print(f"⚠️  Carpeta {CARPETA_LICITACIONES_ORIGEN} no existe")
    
    # Cargar ofertas técnicas históricas
    print(f"\n📋 Cargando ofertas técnicas desde: {CARPETA_OFERTAS_ORIGEN}")
    ofertas_cargadas = 0
    
    if os.path.exists(CARPETA_OFERTAS_ORIGEN):
        for filename in os.listdir(CARPETA_OFERTAS_ORIGEN):
            if filename.endswith('.docx'):
                file_path = os.path.join(CARPETA_OFERTAS_ORIGEN, filename)
                try:
                    with open(file_path, 'rb') as f:
                        files = {'file': f}
                        response = requests.post(f"{API_BASE_URL}/cargar-oferta/", files=files)
                    
                    if response.status_code == 200:
                        print(f"✅ Oferta técnica cargada: {filename}")
                        ofertas_cargadas += 1
                    else:
                        print(f"❌ Error cargando {filename}: {response.status_code}")
                except Exception as e:
                    print(f"❌ Error procesando {filename}: {e}")
    else:
        print(f"⚠️  Carpeta {CARPETA_OFERTAS_ORIGEN} no existe")
    
    # Mostrar resumen
    print("\n" + "=" * 50)
    print("📊 RESUMEN DE CARGA:")
    print(f"   Licitaciones cargadas: {licitaciones_cargadas}")
    print(f"   Ofertas técnicas cargadas: {ofertas_cargadas}")
    print(f"   Total de archivos: {licitaciones_cargadas + ofertas_cargadas}")
    
    # Verificar estado final
    try:
        response = requests.get(f"{API_BASE_URL}/estado/")
        if response.status_code == 200:
            estado = response.json()
            print(f"\n📈 Estado actual del sistema:")
            print(f"   Licitaciones en sistema: {estado['datos_cargados']['licitaciones']}")
            print(f"   Ofertas históricas en sistema: {estado['datos_cargados']['ofertas_historicas']}")
    except Exception as e:
        print(f"❌ Error obteniendo estado: {e}")
    
    print("\n🎉 Proceso completado!")
    print("💡 Consejo: Coloca tus archivos .docx en las carpetas:")
    print(f"   - {CARPETA_LICITACIONES_ORIGEN}/ (para licitaciones históricas)")
    print(f"   - {CARPETA_OFERTAS_ORIGEN}/ (para ofertas técnicas históricas)")
    print("   Y ejecuta este script nuevamente para cargarlos.")

if __name__ == "__main__":
    cargar_archivos_historicos() 