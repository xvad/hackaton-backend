from fastapi import FastAPI, UploadFile, File, HTTPException, BackgroundTasks
from fastapi.responses import FileResponse
from fastapi.middleware.cors import CORSMiddleware
import os
import uuid
import shutil
from typing import List, Dict, Any

from auto_ofertas.config import Config
from auto_ofertas.models import GeneracionRequest, GeneracionResponse, LicitacionData, OfertaTecnicaData
from auto_ofertas.processors.parser import parse_licitacion_dinamica
from auto_ofertas.processors.ai_generator import AIGenerator
from auto_ofertas.processors.generator import generar_oferta_avanzada

# Crear directorios necesarios
Config.create_directories()

app = FastAPI(
    title="API de Generación Automática de Ofertas Técnicas",
    description="API para generar ofertas técnicas automáticamente basadas en licitaciones usando IA",
    version="1.0.0"
)

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

@app.on_event("startup")
async def startup_event():
    """Cargar datos históricos al iniciar la aplicación"""
    try:
        ai_generator.cargar_datos_historicos(Config.OFERTAS_DIR, Config.LICITACIONES_DIR)
        print("✅ Datos históricos cargados correctamente")
    except Exception as e:
        print(f"⚠️ Error cargando datos históricos: {e}")

@app.get("/")
async def root():
    """Endpoint raíz con información del sistema"""
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
    """Carga una licitación en formato Word"""
    if not file.filename.endswith('.docx'):
        raise HTTPException(status_code=400, detail="Solo se aceptan archivos .docx")
    
    # Generar nombre único
    file_id = str(uuid.uuid4())
    filename = f"licitacion_{file_id}.docx"
    file_path = os.path.join(Config.LICITACIONES_DIR, filename)
    
    # Guardar archivo
    with open(file_path, "wb") as f:
        shutil.copyfileobj(file.file, f)
    
    # Parsear licitación
    try:
        licitacion_data = parse_licitacion_dinamica(file_path)
        return {
            "mensaje": "Licitación cargada exitosamente",
            "archivo": filename,
            "datos_extraidos": licitacion_data
        }
    except Exception as e:
        # Eliminar archivo si hay error
        if os.path.exists(file_path):
            os.remove(file_path)
        raise HTTPException(status_code=500, detail=f"Error procesando licitación: {str(e)}")

@app.post("/cargar-oferta/")
async def cargar_oferta(file: UploadFile = File(...)):
    """Carga una oferta técnica histórica en formato Word"""
    if not file.filename.endswith('.docx'):
        raise HTTPException(status_code=400, detail="Solo se aceptan archivos .docx")
    
    # Generar nombre único
    file_id = str(uuid.uuid4())
    filename = f"oferta_{file_id}.docx"
    file_path = os.path.join(Config.OFERTAS_DIR, filename)

    # Guardar archivo
    with open(file_path, "wb") as f:
        shutil.copyfileobj(file.file, f)
    
    # Parsear oferta
    try:
        oferta_data = parse_licitacion_dinamica(file_path)
        
        # Recargar datos históricos para incluir la nueva oferta
        ai_generator.cargar_datos_historicos(Config.OFERTAS_DIR, Config.LICITACIONES_DIR)
        
        return {
            "mensaje": "Oferta técnica cargada exitosamente",
            "archivo": filename,
            "datos_extraidos": oferta_data
        }
    except Exception as e:
        # Eliminar archivo si hay error
        if os.path.exists(file_path):
            os.remove(file_path)
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
    
    if not licitacion_file.filename.endswith('.docx'):
        raise HTTPException(status_code=400, detail="Solo se aceptan archivos .docx")
    
    # Guardar archivo temporalmente
    temp_file_id = str(uuid.uuid4())
    temp_filename = f"temp_licitacion_{temp_file_id}.docx"
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
    empresa_descripcion: str = "",
    nombre_proyecto: str = "Proyecto de Desarrollo Tecnológico",
    cliente: str = "Cliente",
    fecha: str = "2025",
    costo_total: int = 45000000,
    plazo: str = "5 meses"
):
    """Genera la mejor oferta técnica analizando múltiples archivos de licitación usando contexto histórico"""
    import time
    start_time = time.time()
    
    if not licitacion_files:
        raise HTTPException(status_code=400, detail="Debe proporcionar al menos un archivo de licitación")
    
    # Validar que todos los archivos sean .docx
    for file in licitacion_files:
        if not file.filename.endswith('.docx'):
            raise HTTPException(status_code=400, detail=f"Archivo {file.filename} no es un archivo .docx válido")
    
    # Procesar todos los archivos
    licitaciones_procesadas = []
    archivos_temporales = []
    
    try:
        for i, licitacion_file in enumerate(licitacion_files):
            # Guardar archivo temporalmente
            temp_file_id = str(uuid.uuid4())
            temp_filename = f"temp_licitacion_{i}_{temp_file_id}.docx"
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
        
        # Generar oferta estructurada combinando todas las licitaciones
        resultado_json = ai_generator.generar_oferta_estructurada(
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
        
        # Crear respuesta con metadatos
        response = {
            "id": str(uuid.uuid4()),
            "archivos_procesados": [lic["archivo"] for lic in licitaciones_procesadas],
            "total_archivos": len(licitaciones_procesadas),
            "empresa": empresa_nombre,
            "tiempo_generacion": tiempo_generacion,
            "datos_historicos_usados": {
                "ofertas_historicas": len(ai_generator.ofertas_historicas),
                "licitaciones_historicas": len(ai_generator.licitaciones_historicas)
            },
            "oferta_json": resultado_json,
            "mensaje": f"Oferta generada exitosamente analizando {len(licitaciones_procesadas)} archivos usando {len(ai_generator.ofertas_historicas)} ofertas históricas como base de conocimiento"
        }
        
        return response
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error generando oferta: {str(e)}")
    finally:
        # Limpiar archivos temporales
        for temp_file in archivos_temporales:
            if os.path.exists(temp_file):
                os.remove(temp_file)

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
    
    # Validar que todos los archivos sean .docx
    for file in licitacion_files:
        if not file.filename.endswith('.docx'):
            raise HTTPException(status_code=400, detail=f"Archivo {file.filename} no es un archivo .docx válido")
    
    # Procesar todos los archivos
    licitaciones_procesadas = []
    archivos_temporales = []
    
    try:
        for i, licitacion_file in enumerate(licitacion_files):
            # Guardar archivo temporalmente
            temp_file_id = str(uuid.uuid4())
            temp_filename = f"temp_licitacion_{i}_{temp_file_id}.docx"
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
    licitaciones = []
    
    for filename in os.listdir(Config.LICITACIONES_DIR):
        if filename.endswith('.docx'):
            file_path = os.path.join(Config.LICITACIONES_DIR, filename)
            try:
                licitacion_data = parse_licitacion_dinamica(file_path)
                licitaciones.append({
                    "archivo": filename,
                    "datos": licitacion_data
                })
            except Exception as e:
                licitaciones.append({
                    "archivo": filename,
                    "error": str(e)
                })
    
    return {"licitaciones": licitaciones, "total": len(licitaciones)}

@app.get("/ofertas/")
async def listar_ofertas():
    """Lista todas las ofertas técnicas históricas cargadas"""
    ofertas = []
    
    for filename in os.listdir(Config.OFERTAS_DIR):
        if filename.endswith('.docx'):
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
        if filename.endswith('.docx'):
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
    
    return FileResponse(
        path=file_path,
        filename=filename,
        media_type='application/vnd.openxmlformats-officedocument.wordprocessingml.document'
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
    return {
        "datos_cargados": {
            "licitaciones": len([f for f in os.listdir(Config.LICITACIONES_DIR) if f.endswith('.docx')]),
            "ofertas_historicas": len([f for f in os.listdir(Config.OFERTAS_DIR) if f.endswith('.docx')]),
            "ofertas_generadas": len([f for f in os.listdir(Config.GENERADAS_DIR) if f.endswith('.docx')])
        },
        "ia_configurada": bool(Config.OPENAI_API_KEY),
        "modelo_actual": Config.MODEL_NAME
    }
