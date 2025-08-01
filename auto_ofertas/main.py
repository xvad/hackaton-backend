from fastapi import FastAPI, UploadFile, File, HTTPException, BackgroundTasks
from fastapi.responses import FileResponse
from fastapi.middleware.cors import CORSMiddleware
import os
import uuid
import shutil
import time
import logging
from typing import List, Dict, Any

from auto_ofertas.config import Config
from auto_ofertas.models import GeneracionRequest, GeneracionResponse, LicitacionData, OfertaTecnicaData
from auto_ofertas.processors.parser import parse_licitacion_dinamica
from auto_ofertas.processors.ai_generator import AIGenerator
from auto_ofertas.processors.generator import generar_oferta_avanzada

# Configurar logging
logger = Config.setup_logging()

# Crear directorios necesarios
Config.create_directories()

app = FastAPI(
    title="API de Generación Automática de Ofertas Técnicas",
    description="API para generar ofertas técnicas automáticamente basadas en licitaciones usando IA",
    version="1.0.0"
)

logger.info("🚀 Iniciando API de Generación Automática de Ofertas Técnicas")
logger.info(f"📁 Directorios configurados: {Config.UPLOAD_DIR}")
logger.info(f"🤖 Modelo IA configurado: {Config.MODEL_NAME}")
logger.info(f"🔑 OpenAI API Key configurada: {'Sí' if Config.OPENAI_API_KEY else 'No'}")

# Configurar CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Inicializar componentes
ai_generator = AIGenerator()
logger.info("🤖 Generador de IA inicializado")

@app.on_event("startup")
async def startup_event():
    """Cargar datos históricos al iniciar la aplicación"""
    logger.info("📚 Iniciando carga de datos históricos...")
    try:
        ai_generator.cargar_datos_historicos(Config.OFERTAS_DIR, Config.LICITACIONES_DIR)
        logger.info("✅ Datos históricos cargados correctamente")
    except Exception as e:
        logger.error(f"❌ Error cargando datos históricos: {e}")
        logger.exception("Detalles del error:")

@app.get("/")
async def root():
    """Endpoint raíz con información del sistema"""
    logger.info("📊 Consulta de información del sistema")
    return {
        "mensaje": "API de Generación Automática de Ofertas Técnicas",
        "version": "1.0.0",
        "estado": "activo",
        "endpoints": {
            "cargar_licitacion": "POST /cargar-licitacion/",
            "cargar_oferta": "POST /cargar-oferta/",
            "generar_oferta": "POST /generar-oferta/",
            "generar_oferta_multiple": "POST /generar-oferta-multiple/",
            "generar_oferta_estructurada": "POST /generar-oferta-estructurada/",
            "listar_licitaciones": "GET /licitaciones/",
            "listar_ofertas": "GET /ofertas/",
            "descargar_archivo": "GET /descargar/{tipo}/{filename}"
        }
    }

@app.post("/cargar-licitacion/")
async def cargar_licitacion(file: UploadFile = File(...)):
    """Carga una licitación en formato Word o PDF"""
    start_time = time.time()
    logger.info(f"📄 Iniciando carga de licitación: {file.filename}")
    
    if not (file.filename.endswith('.docx') or file.filename.endswith('.pdf')):
        logger.warning(f"❌ Formato de archivo no válido: {file.filename}")
        raise HTTPException(status_code=400, detail="Solo se aceptan archivos .docx y .pdf")
    
    # Generar nombre único manteniendo la extensión original
    file_id = str(uuid.uuid4())
    extension = os.path.splitext(file.filename)[1].lower()
    filename = f"licitacion_{file_id}{extension}"
    file_path = os.path.join(Config.LICITACIONES_DIR, filename)
    
    logger.info(f"💾 Guardando archivo: {filename}")
    
    # Guardar archivo
    try:
        with open(file_path, "wb") as f:
            shutil.copyfileobj(file.file, f)
        logger.info(f"✅ Archivo guardado exitosamente: {file_path}")
    except Exception as e:
        logger.error(f"❌ Error guardando archivo: {e}")
        raise HTTPException(status_code=500, detail=f"Error guardando archivo: {str(e)}")
    
    # Parsear licitación
    logger.info(f"🔍 Iniciando parsing de licitación: {filename}")
    try:
        licitacion_data = parse_licitacion_dinamica(file_path)
        tiempo_procesamiento = round(time.time() - start_time, 2)
        logger.info(f"✅ Licitación procesada exitosamente en {tiempo_procesamiento}s")
        logger.info(f"📊 Secciones extraídas: {len(licitacion_data)}")
        
        return {
            "mensaje": "Licitación cargada exitosamente",
            "archivo": filename,
            "datos_extraidos": licitacion_data,
            "tiempo_procesamiento": tiempo_procesamiento
        }
    except Exception as e:
        logger.error(f"❌ Error procesando licitación: {e}")
        logger.exception("Detalles del error:")
        # Eliminar archivo si hay error
        if os.path.exists(file_path):
            os.remove(file_path)
            logger.info(f"🗑️ Archivo eliminado debido al error: {filename}")
        raise HTTPException(status_code=500, detail=f"Error procesando licitación: {str(e)}")

@app.post("/cargar-oferta/")
async def cargar_oferta(file: UploadFile = File(...)):
    """Carga una oferta técnica histórica en formato Word o PDF"""
    start_time = time.time()
    logger.info(f"📄 Iniciando carga de oferta técnica: {file.filename}")
    
    if not (file.filename.endswith('.docx') or file.filename.endswith('.pdf')):
        logger.warning(f"❌ Formato de archivo no válido: {file.filename}")
        raise HTTPException(status_code=400, detail="Solo se aceptan archivos .docx y .pdf")
    
    # Generar nombre único manteniendo la extensión original
    file_id = str(uuid.uuid4())
    extension = os.path.splitext(file.filename)[1].lower()
    filename = f"oferta_{file_id}{extension}"
    file_path = os.path.join(Config.OFERTAS_DIR, filename)

    logger.info(f"💾 Guardando archivo: {filename}")
    
    # Guardar archivo
    try:
        with open(file_path, "wb") as f:
            shutil.copyfileobj(file.file, f)
        logger.info(f"✅ Archivo guardado exitosamente: {file_path}")
    except Exception as e:
        logger.error(f"❌ Error guardando archivo: {e}")
        raise HTTPException(status_code=500, detail=f"Error guardando archivo: {str(e)}")
    
    # Parsear oferta
    logger.info(f"🔍 Iniciando parsing de oferta técnica: {filename}")
    try:
        oferta_data = parse_licitacion_dinamica(file_path)
        
        logger.info("🔄 Recargando datos históricos...")
        # Recargar datos históricos para incluir la nueva oferta
        ai_generator.cargar_datos_historicos(Config.OFERTAS_DIR, Config.LICITACIONES_DIR)
        
        tiempo_procesamiento = round(time.time() - start_time, 2)
        logger.info(f"✅ Oferta técnica procesada exitosamente en {tiempo_procesamiento}s")
        logger.info(f"📊 Secciones extraídas: {len(oferta_data)}")
        
        return {
            "mensaje": "Oferta técnica cargada exitosamente",
            "archivo": filename,
            "datos_extraidos": oferta_data,
            "tiempo_procesamiento": tiempo_procesamiento
        }
    except Exception as e:
        logger.error(f"❌ Error procesando oferta: {e}")
        logger.exception("Detalles del error:")
        # Eliminar archivo si hay error
        if os.path.exists(file_path):
            os.remove(file_path)
            logger.info(f"🗑️ Archivo eliminado debido al error: {filename}")
        raise HTTPException(status_code=500, detail=f"Error procesando oferta: {str(e)}")

@app.post("/generar-oferta/")
async def generar_oferta_api(request: GeneracionRequest):
    """Genera una oferta técnica automáticamente basada en una licitación existente y responde con JSON dinámico"""
    import time
    start_time = time.time()
    
    licitacion_path = os.path.join(Config.LICITACIONES_DIR, request.licitacion_id)
    if not os.path.exists(licitacion_path):
        raise HTTPException(status_code=404, detail="Licitación no encontrada")
    
    try:
        # Generar oferta usando contexto histórico
        resultado_json = ai_generator.generar_oferta_json_dinamico(
            licitacion_path=licitacion_path,
            empresa_nombre=request.empresa_nombre,
            empresa_descripcion=request.empresa_descripcion or ""
        )
        
        tiempo_generacion = round(time.time() - start_time, 2)
        
        # Crear respuesta con metadatos
        response = {
            "id": str(uuid.uuid4()),
            "archivo": request.licitacion_id,
            "empresa": request.empresa_nombre,
            "tiempo_generacion": tiempo_generacion,
            "datos_historicos_usados": {
                "ofertas_historicas": len(ai_generator.ofertas_historicas),
                "licitaciones_historicas": len(ai_generator.licitaciones_historicas)
            },
            "oferta_json": resultado_json,
            "mensaje": f"Oferta generada exitosamente usando {len(ai_generator.ofertas_historicas)} ofertas históricas como base de conocimiento"
        }
        
        return response
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error generando oferta: {str(e)}")

@app.post("/generar-oferta-archivo/")
async def generar_oferta_desde_archivo(
    licitacion_file: UploadFile = File(...),
    empresa_nombre: str = "GUX Technologies",
    empresa_descripcion: str = ""
):
    """Genera una oferta técnica desde un archivo de licitación subido usando contexto histórico"""
    import time
    start_time = time.time()
    
    if not (licitacion_file.filename.endswith('.docx') or licitacion_file.filename.endswith('.pdf')):
        raise HTTPException(status_code=400, detail="Solo se aceptan archivos .docx y .pdf")
    
    # Guardar archivo temporalmente manteniendo la extensión original
    temp_file_id = str(uuid.uuid4())
    extension = os.path.splitext(licitacion_file.filename)[1].lower()
    temp_filename = f"temp_licitacion_{temp_file_id}{extension}"
    temp_file_path = os.path.join(Config.UPLOAD_DIR, temp_filename)
    
    try:
        with open(temp_file_path, "wb") as f:
            shutil.copyfileobj(licitacion_file.file, f)
        
        # Generar oferta usando contexto histórico
        resultado_json = ai_generator.generar_oferta_json_dinamico(
            licitacion_path=temp_file_path,
            empresa_nombre=empresa_nombre,
            empresa_descripcion=empresa_descripcion
        )
        
        tiempo_generacion = round(time.time() - start_time, 2)
        
        # Crear respuesta con metadatos
        response = {
            "id": str(uuid.uuid4()),
            "archivo": licitacion_file.filename,
            "empresa": empresa_nombre,
            "tiempo_generacion": tiempo_generacion,
            "datos_historicos_usados": {
                "ofertas_historicas": len(ai_generator.ofertas_historicas),
                "licitaciones_historicas": len(ai_generator.licitaciones_historicas)
            },
            "oferta_json": resultado_json,
            "mensaje": f"Oferta generada exitosamente usando {len(ai_generator.ofertas_historicas)} ofertas históricas como base de conocimiento"
        }
        
        return response
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error generando oferta: {str(e)}")
    finally:
        # Limpiar archivo temporal
        if os.path.exists(temp_file_path):
            os.remove(temp_file_path)

@app.post("/generar-oferta-multiple/")
async def generar_oferta_multiple(
    licitacion_files: List[UploadFile] = File(...),
    empresa_nombre: str = "GUX Technologies",
    empresa_descripcion: str = ""
):
    """Genera la mejor oferta técnica analizando múltiples archivos de licitación usando contexto histórico y IA para calcular todos los parámetros"""
    start_time = time.time()
    request_id = str(uuid.uuid4())[:8]
    
    logger.info(f"🚀 [{request_id}] Iniciando generación de oferta múltiple")
    logger.info(f"📊 [{request_id}] Archivos recibidos: {len(licitacion_files)}")
    logger.info(f"🏢 [{request_id}] Empresa: {empresa_nombre}")
    
    if not licitacion_files:
        logger.warning(f"❌ [{request_id}] No se proporcionaron archivos")
        raise HTTPException(status_code=400, detail="Debe proporcionar al menos un archivo de licitación")
    
    # Validar que todos los archivos sean .docx o .pdf
    for file in licitacion_files:
        if not (file.filename.endswith('.docx') or file.filename.endswith('.pdf')):
            logger.warning(f"❌ [{request_id}] Formato de archivo no válido: {file.filename}")
            raise HTTPException(status_code=400, detail=f"Archivo {file.filename} no es un archivo .docx o .pdf válido")
    
    # Procesar todos los archivos
    licitaciones_procesadas = []
    archivos_temporales = []
    
    try:
        logger.info(f"📄 [{request_id}] Iniciando procesamiento de {len(licitacion_files)} archivos")
        
        for i, licitacion_file in enumerate(licitacion_files):
            logger.info(f"🔍 [{request_id}] Procesando archivo {i+1}/{len(licitacion_files)}: {licitacion_file.filename}")
            
            # Guardar archivo temporalmente manteniendo la extensión original
            temp_file_id = str(uuid.uuid4())
            extension = os.path.splitext(licitacion_file.filename)[1].lower()
            temp_filename = f"temp_licitacion_{i}_{temp_file_id}{extension}"
            temp_file_path = os.path.join(Config.UPLOAD_DIR, temp_filename)
            archivos_temporales.append(temp_file_path)
            
            logger.info(f"💾 [{request_id}] Guardando archivo temporal: {temp_filename}")
            
            try:
                with open(temp_file_path, "wb") as f:
                    shutil.copyfileobj(licitacion_file.file, f)
                logger.info(f"✅ [{request_id}] Archivo temporal guardado: {temp_filename}")
            except Exception as e:
                logger.error(f"❌ [{request_id}] Error guardando archivo temporal: {e}")
                raise HTTPException(status_code=500, detail=f"Error guardando archivo temporal: {str(e)}")
            
            # Parsear licitación
            try:
                logger.info(f"🔍 [{request_id}] Iniciando parsing de: {licitacion_file.filename}")
                licitacion_data = parse_licitacion_dinamica(temp_file_path)
                licitaciones_procesadas.append({
                    "archivo": licitacion_file.filename,
                    "datos": licitacion_data,
                    "ruta": temp_file_path
                })
                logger.info(f"✅ [{request_id}] Parsing completado: {licitacion_file.filename} - {len(licitacion_data)} secciones")
            except Exception as e:
                logger.error(f"❌ [{request_id}] Error procesando {licitacion_file.filename}: {e}")
                logger.exception("Detalles del error:")
                raise HTTPException(status_code=500, detail=f"Error procesando {licitacion_file.filename}: {str(e)}")
        
        logger.info(f"✅ [{request_id}] Todos los archivos procesados exitosamente")
        logger.info(f"🤖 [{request_id}] Iniciando generación de oferta con IA...")
        
        # Generar oferta usando el método mejorado que calcula todos los parámetros con IA
        resultado_json = ai_generator.generar_oferta_multiple_licitaciones(
            licitaciones=licitaciones_procesadas,
            empresa_nombre=empresa_nombre,
            empresa_descripcion=empresa_descripcion
        )
        
        tiempo_generacion = round(time.time() - start_time, 2)
        
        logger.info(f"🎉 [{request_id}] Oferta generada exitosamente en {tiempo_generacion}s")
        logger.info(f"📊 [{request_id}] Datos históricos usados: {len(ai_generator.ofertas_historicas)} ofertas, {len(ai_generator.licitaciones_historicas)} licitaciones")
        
        # Crear respuesta con metadatos
        response = {
            "id": request_id,
            "archivos_procesados": [lic["archivo"] for lic in licitaciones_procesadas],
            "total_archivos": len(licitaciones_procesadas),
            "empresa": empresa_nombre,
            "tiempo_generacion": tiempo_generacion,
            "datos_historicos_usados": {
                "ofertas_historicas": len(ai_generator.ofertas_historicas),
                "licitaciones_historicas": len(ai_generator.licitaciones_historicas)
            },
            "oferta_json": resultado_json,
            "mensaje": f"Oferta generada exitosamente analizando {len(licitaciones_procesadas)} archivos usando {len(ai_generator.ofertas_historicas)} ofertas históricas como base de conocimiento. Todos los parámetros fueron calculados automáticamente por IA."
        }
        
        logger.info(f"✅ [{request_id}] Respuesta preparada y enviada")
        return response
        
    except Exception as e:
        logger.error(f"❌ [{request_id}] Error general en generación de oferta: {e}")
        logger.exception("Detalles del error:")
        raise HTTPException(status_code=500, detail=f"Error generando oferta: {str(e)}")
    finally:
        # Limpiar archivos temporales
        logger.info(f"🧹 [{request_id}] Limpiando archivos temporales...")
        for temp_file in archivos_temporales:
            if os.path.exists(temp_file):
                try:
                    os.remove(temp_file)
                    logger.debug(f"🗑️ [{request_id}] Archivo temporal eliminado: {temp_file}")
                except Exception as e:
                    logger.warning(f"⚠️ [{request_id}] Error eliminando archivo temporal {temp_file}: {e}")
        logger.info(f"✅ [{request_id}] Limpieza completada")

@app.post("/generar-oferta-estructurada/")
async def generar_oferta_estructurada(
    licitacion_files: List[UploadFile] = File(...),
    empresa_nombre: str = "GUX Technologies",
    empresa_descripcion: str = "",
    nombre_proyecto: str = "Proyecto de Desarrollo Tecnológico",
    cliente: str = "Cliente",
    fecha: str = "2025",
    costo_total: int = 45000000,
    plazo: str = "5 meses"
):
    """Genera una oferta técnica en formato estructurado con secciones organizadas"""
    import time
    start_time = time.time()
    
    if not licitacion_files:
        raise HTTPException(status_code=400, detail="Debe proporcionar al menos un archivo de licitación")
    
    # Validar que todos los archivos sean .docx o .pdf
    for file in licitacion_files:
        if not (file.filename.endswith('.docx') or file.filename.endswith('.pdf')):
            raise HTTPException(status_code=400, detail=f"Archivo {file.filename} no es un archivo .docx o .pdf válido")
    
    # Procesar todos los archivos
    licitaciones_procesadas = []
    archivos_temporales = []
    
    try:
        for i, licitacion_file in enumerate(licitacion_files):
            # Guardar archivo temporalmente manteniendo la extensión original
            temp_file_id = str(uuid.uuid4())
            extension = os.path.splitext(licitacion_file.filename)[1].lower()
            temp_filename = f"temp_licitacion_{i}_{temp_file_id}{extension}"
            temp_file_path = os.path.join(Config.UPLOAD_DIR, temp_filename)
            archivos_temporales.append(temp_file_path)
            
            with open(temp_file_path, "wb") as f:
                shutil.copyfileobj(licitacion_file.file, f)
            
            # Parsear licitación
            try:
                licitacion_data = parse_licitacion_dinamica(temp_file_path)
                licitaciones_procesadas.append({
                    "archivo": licitacion_file.filename,
                    "datos": licitacion_data,
                    "ruta": temp_file_path
                })
            except Exception as e:
                raise HTTPException(status_code=500, detail=f"Error procesando {licitacion_file.filename}: {str(e)}")
        
        # Generar oferta estructurada
        oferta_estructurada = ai_generator.generar_oferta_estructurada(
            licitaciones=licitaciones_procesadas,
            empresa_nombre=empresa_nombre,
            empresa_descripcion=empresa_descripcion,
            nombre_proyecto=nombre_proyecto,
            cliente=cliente,
            fecha=fecha,
            costo_total=costo_total,
            plazo=plazo
        )
        
        tiempo_generacion = round(time.time() - start_time, 2)
        
        # Agregar metadatos
        oferta_estructurada["metadata"] = {
            "id": str(uuid.uuid4()),
            "archivos_procesados": [lic["archivo"] for lic in licitaciones_procesadas],
            "total_archivos": len(licitaciones_procesadas),
            "empresa": empresa_nombre,
            "tiempo_generacion": tiempo_generacion,
            "datos_historicos_usados": {
                "ofertas_historicas": len(ai_generator.ofertas_historicas),
                "licitaciones_historicas": len(ai_generator.licitaciones_historicas)
            },
            "mensaje": f"Oferta estructurada generada exitosamente analizando {len(licitaciones_procesadas)} archivos usando {len(ai_generator.ofertas_historicas)} ofertas históricas como base de conocimiento"
        }
        
        return oferta_estructurada
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error generando oferta: {str(e)}")
    finally:
        # Limpiar archivos temporales
        for temp_file in archivos_temporales:
            if os.path.exists(temp_file):
                os.remove(temp_file)

@app.get("/licitaciones/")
async def listar_licitaciones():
    """Lista todas las licitaciones cargadas"""
    logger.info("📋 Consulta de listado de licitaciones")
    
    licitaciones = []
    archivos_encontrados = 0
    archivos_procesados = 0
    archivos_con_error = 0
    
    for filename in os.listdir(Config.LICITACIONES_DIR):
        if filename.endswith('.docx') or filename.endswith('.pdf'):
            archivos_encontrados += 1
            file_path = os.path.join(Config.LICITACIONES_DIR, filename)
            try:
                logger.debug(f"🔍 Procesando licitación: {filename}")
                licitacion_data = parse_licitacion_dinamica(file_path)
                licitaciones.append({
                    "archivo": filename,
                    "datos": licitacion_data
                })
                archivos_procesados += 1
            except Exception as e:
                logger.warning(f"⚠️ Error procesando licitación {filename}: {e}")
                licitaciones.append({
                    "archivo": filename,
                    "error": str(e)
                })
                archivos_con_error += 1
    
    logger.info(f"✅ Listado completado: {archivos_procesados} procesados, {archivos_con_error} con error, {archivos_encontrados} total")
    return {"licitaciones": licitaciones, "total": len(licitaciones)}

@app.get("/ofertas/")
async def listar_ofertas():
    """Lista todas las ofertas técnicas históricas cargadas"""
    ofertas = []
    
    for filename in os.listdir(Config.OFERTAS_DIR):
        if filename.endswith('.docx') or filename.endswith('.pdf'):
            file_path = os.path.join(Config.OFERTAS_DIR, filename)
            try:
                oferta_data = parse_licitacion_dinamica(file_path)
                ofertas.append({
                    "archivo": filename,
                    "datos": oferta_data
                })
            except Exception as e:
                ofertas.append({
                    "archivo": filename,
                    "error": str(e)
                })
    
    return {"ofertas": ofertas, "total": len(ofertas)}

@app.get("/generadas/")
async def listar_ofertas_generadas():
    """Lista todas las ofertas generadas automáticamente"""
    ofertas_generadas = []
    
    for filename in os.listdir(Config.GENERADAS_DIR):
        if filename.endswith('.docx') or filename.endswith('.pdf'):
            ofertas_generadas.append({
                "archivo": filename,
                "fecha_generacion": os.path.getctime(os.path.join(Config.GENERADAS_DIR, filename))
            })
    
    return {"ofertas_generadas": ofertas_generadas, "total": len(ofertas_generadas)}

@app.get("/descargar/{tipo}/{filename}")
async def descargar_archivo(tipo: str, filename: str):
    """Descarga un archivo específico"""
    
    if tipo == "licitacion":
        file_path = os.path.join(Config.LICITACIONES_DIR, filename)
    elif tipo == "oferta":
        file_path = os.path.join(Config.OFERTAS_DIR, filename)
    elif tipo == "generada":
        file_path = os.path.join(Config.GENERADAS_DIR, filename)
    else:
        raise HTTPException(status_code=400, detail="Tipo de archivo no válido")
    
    if not os.path.exists(file_path):
        raise HTTPException(status_code=404, detail="Archivo no encontrado")
    
    # Determinar el tipo de medio según la extensión del archivo
    extension = os.path.splitext(filename)[1].lower()
    if extension == '.docx':
        media_type = 'application/vnd.openxmlformats-officedocument.wordprocessingml.document'
    elif extension == '.pdf':
        media_type = 'application/pdf'
    else:
        media_type = 'application/octet-stream'
    
    return FileResponse(
        path=file_path,
        filename=filename,
        media_type=media_type
    )

@app.delete("/eliminar/{tipo}/{filename}")
async def eliminar_archivo(tipo: str, filename: str):
    """Elimina un archivo específico"""
    
    if tipo == "licitacion":
        file_path = os.path.join(Config.LICITACIONES_DIR, filename)
    elif tipo == "oferta":
        file_path = os.path.join(Config.OFERTAS_DIR, filename)
    elif tipo == "generada":
        file_path = os.path.join(Config.GENERADAS_DIR, filename)
    else:
        raise HTTPException(status_code=400, detail="Tipo de archivo no válido")
    
    if not os.path.exists(file_path):
        raise HTTPException(status_code=404, detail="Archivo no encontrado")
    
    try:
        os.remove(file_path)
        
        # Recargar datos históricos si se eliminó una oferta
        if tipo == "oferta":
            ai_generator.cargar_datos_historicos(Config.OFERTAS_DIR, Config.LICITACIONES_DIR)
        
        return {"mensaje": f"Archivo {filename} eliminado exitosamente"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error eliminando archivo: {str(e)}")

@app.get("/estado/")
async def obtener_estado():
    """Obtiene el estado actual del sistema"""
    logger.info("📊 Consulta de estado del sistema")
    
    # Contar archivos
    licitaciones_count = len([f for f in os.listdir(Config.LICITACIONES_DIR) if f.endswith('.docx') or f.endswith('.pdf')])
    ofertas_count = len([f for f in os.listdir(Config.OFERTAS_DIR) if f.endswith('.docx') or f.endswith('.pdf')])
    generadas_count = len([f for f in os.listdir(Config.GENERADAS_DIR) if f.endswith('.docx') or f.endswith('.pdf')])
    
    logger.info(f"📁 Archivos en sistema: {licitaciones_count} licitaciones, {ofertas_count} ofertas, {generadas_count} generadas")
    logger.info(f"🤖 IA configurada: {'Sí' if Config.OPENAI_API_KEY else 'No'}")
    logger.info(f"🧠 Modelo actual: {Config.MODEL_NAME}")
    
    return {
        "datos_cargados": {
            "licitaciones": licitaciones_count,
            "ofertas_historicas": ofertas_count,
            "ofertas_generadas": generadas_count
        },
        "ia_configurada": bool(Config.OPENAI_API_KEY),
        "modelo_actual": Config.MODEL_NAME
    }
