# 🚀 API de Generación Automática de Ofertas Técnicas - GUX Technologies

Sistema inteligente para generar ofertas técnicas automáticamente basadas en licitaciones usando IA y siguiendo los estándares institucionales de GUX Technologies y Proyectum.

## ✨ Características

- **📄 Procesamiento de Documentos Word**: Extrae información estructurada de licitaciones y ofertas técnicas
- **🤖 Generación con IA (GPT-4)**: Utiliza OpenAI GPT-4 para generar ofertas técnicas profesionales
- **🏢 Estándares Institucionales**: Sigue la metodología Disciplined Agile Delivery (DAD) y estándares de GUX Technologies
- **📊 API REST Completa**: Endpoints para cargar, generar y gestionar documentos
- **📁 Gestión de Archivos**: Organización automática de licitaciones, ofertas históricas y generadas
- **🔄 JSON Dinámico**: Respuestas que se adaptan a la estructura de cada licitación

## 🏗️ Arquitectura

```
auto_ofertas/
├── config.py              # Configuración del sistema
├── models.py              # Modelos de datos Pydantic
├── main.py                # API FastAPI principal
├── processors/
│   ├── parser.py          # Procesamiento dinámico de documentos Word
│   ├── ai_generator.py    # Generación con IA siguiendo estándares GUX
│   └── generator.py       # Generador de documentos
└── uploads/
    ├── licitaciones/      # Licitaciones cargadas
    ├── ofertas/          # Ofertas técnicas históricas
    └── generadas/        # Ofertas generadas automáticamente
```

## 🚀 Instalación

### 1. Clonar el repositorio
```bash
git clone <tu-repositorio>
cd hackaton-backend
```

### 2. Crear entorno virtual
```bash
python -m venv venv
# En Windows:
venv\Scripts\activate
# En Linux/Mac:
source venv/bin/activate
```

### 3. Instalar dependencias
```bash
pip install -r requirements.txt
```

### 4. Configurar variables de entorno
Crea un archivo `.env` basado en `env_example.txt`:
```bash
# Configuración de OpenAI
OPENAI_API_KEY=tu_api_key_de_openai_aqui

# Configuración del modelo
MODEL_NAME=gpt-4
MAX_TOKENS=4000
TEMPERATURE=0.7
```

### 5. Ejecutar la aplicación
```bash
python run.py
```

La API estará disponible en: http://localhost:8000
Documentación automática: http://localhost:8000/docs

## 📚 Carga de Archivos Históricos

### **Método 1: Carga Automática (Recomendado)**

1. **Crear carpetas de origen:**
   ```
   licitaciones_historicas/    # Coloca aquí tus licitaciones históricas (.docx)
   ofertas_historicas/        # Coloca aquí tus ofertas técnicas aprobadas (.docx)
   ```

2. **Ejecutar script de carga:**
   ```bash
   python cargar_archivos_historicos.py
   ```

### **Método 2: Carga Manual por API**

```bash
# Cargar licitación histórica
curl -X POST "http://localhost:8000/cargar-licitacion/" \
  -H "Content-Type: multipart/form-data" \
  -F "file=@mi_licitacion_historica.docx"

# Cargar oferta técnica histórica
curl -X POST "http://localhost:8000/cargar-oferta/" \
  -H "Content-Type: multipart/form-data" \
  -F "file=@mi_oferta_aprobada.docx"
```

## 🎯 Uso de la API

### 1. Generar Oferta Técnica
```bash
curl -X POST "http://localhost:8000/generar-oferta/" \
  -H "Content-Type: application/json" \
  -d '{
    "licitacion_id": "licitacion_xxxxx.docx",
    "empresa_nombre": "GUX Technologies",
    "empresa_descripcion": "Empresa líder en desarrollo de software y consultoría tecnológica"
  }'
```

### 2. Generar desde Archivo
```bash
curl -X POST "http://localhost:8000/generar-oferta-archivo/" \
  -H "Content-Type: multipart/form-data" \
  -F "licitacion_file=@nueva_licitacion.docx" \
  -F "empresa_nombre=GUX Technologies" \
  -F "empresa_descripcion=Descripción de la empresa"
```

### 3. Generar Analizando Múltiples Archivos (NUEVO)
```bash
curl -X POST "http://localhost:8000/generar-oferta-multiple/" \
  -H "Content-Type: multipart/form-data" \
  -F "licitacion_files=@licitacion1.docx" \
  -F "licitacion_files=@licitacion2.docx" \
  -F "licitacion_files=@licitacion3.docx" \
  -F "empresa_nombre=GUX Technologies" \
  -F "empresa_descripcion=Empresa líder en desarrollo de software" \
  -F "nombre_proyecto=Sistema de Gestión Integral" \
  -F "cliente=Empresa Cliente S.A." \
  -F "fecha=Mayo 2025" \
  -F "costo_total=50000000" \
  -F "plazo=6 meses"
```

### 4. Listar Documentos
```bash
# Listar licitaciones
curl "http://localhost:8000/licitaciones/"

# Listar ofertas históricas
curl "http://localhost:8000/ofertas/"

# Listar ofertas generadas
curl "http://localhost:8000/generadas/"
```

## 🏢 Estándares Institucionales GUX Technologies

El sistema genera ofertas técnicas siguiendo los estándares institucionales:

### **Metodología Disciplined Agile Delivery (DAD)**
- **Inception**: Alineamiento estratégico, definición de objetivos, comprensión del contexto
- **Construction**: Desarrollo iterativo, validación temprana, retroalimentación continua
- **Transition**: Despliegue, traspaso, adopción y cierre controlado
- **Discovery continuo**: Fase transversal para ajustes y nuevas necesidades

### **Estructura Recomendada**
1. **Resumen Ejecutivo** - Síntesis del problema, solución, metodología, equipo, diferenciadores
2. **Objetivos y Alcance** - Conexión con desafíos reales del cliente
3. **Solución Propuesta** - Adaptada según tipo de servicio
4. **Metodología de Trabajo** - DAD con mecanismos de control, gestión de riesgos, QA
5. **Plan de Implementación** - Hitos, tiempos, entregables
6. **Organización del Proyecto** - Roles, liderazgo, coordinación
7. **Factores Claves para el Éxito** - Condiciones necesarias del cliente
8. **Presentación de la Empresa** - Antecedentes, experiencia, referencias
9. **Equipo de Trabajo** - Perfiles coherentes con el desafío
10. **Sostenibilidad** - Políticas institucionales
11. **Diversidad e Inclusión** - Compromisos activos

### **Principios Clave**
- Generar valor real para el cliente, no solo cumplir bases formales
- Posicionarse como partner estratégico
- Lenguaje claro, directo y profesional (tercera persona)
- Personalización usando el nombre real de la organización cliente
- Enfoque en resultados tangibles y propuesta de valor concreta

## 🔧 Endpoints Disponibles

| Método | Endpoint | Descripción |
|--------|----------|-------------|
| GET | `/` | Información del sistema |
| POST | `/cargar-licitacion/` | Cargar licitación (DOCX o PDF) |
| POST | `/cargar-oferta/` | Cargar oferta técnica histórica (DOCX o PDF) |
| POST | `/generar-oferta/` | Generar oferta desde licitación existente |
| POST | `/generar-oferta-archivo/` | Generar oferta desde archivo subido |
| POST | `/generar-oferta-multiple/` | Generar oferta analizando múltiples archivos (con parámetros personalizables) |
| GET | `/licitaciones/` | Listar licitaciones cargadas |
| GET | `/ofertas/` | Listar ofertas históricas |
| GET | `/generadas/` | Listar ofertas generadas |
| GET | `/descargar/{tipo}/{filename}` | Descargar archivo |
| DELETE | `/eliminar/{tipo}/{filename}` | Eliminar archivo |
| GET | `/estado/` | Estado del sistema |

## 📁 Estructura de Directorios

```
uploads/
├── licitaciones/          # Licitaciones cargadas (.docx)
├── ofertas/              # Ofertas técnicas históricas (.docx)
└── generadas/            # Ofertas generadas automáticamente (.docx)

licitaciones_historicas/   # Carpeta para cargar licitaciones históricas
ofertas_historicas/       # Carpeta para cargar ofertas técnicas históricas
```

## 🔍 Flujo de Trabajo

### **Opción 1: Licitación Individual**
1. **Cargar Datos Históricos**: Subir ofertas técnicas anteriores y licitaciones históricas
2. **Cargar Licitación**: Subir la licitación a responder
3. **Generar Oferta**: El sistema:
   - Extrae información de la licitación
   - Aplica estándares institucionales de GUX Technologies
   - Genera contenido usando GPT-4
   - Crea JSON dinámico con la misma estructura
4. **Obtener Resultado**: JSON con propuesta técnica profesional

### **Opción 2: Análisis Múltiple (Recomendado)**
1. **Cargar Datos Históricos**: Subir ofertas técnicas anteriores y licitaciones históricas
2. **Cargar Múltiples Licitaciones**: Subir varios archivos de licitación
3. **Generar Oferta Combinada**: El sistema:
   - Analiza todas las licitaciones simultáneamente
   - Combina los mejores elementos de cada una
   - Identifica requisitos comunes y específicos
   - Genera la oferta más completa y robusta
   - Usa el contexto histórico como base de conocimiento
4. **Obtener Resultado**: JSON con la mejor propuesta técnica combinada

## ⚙️ Configuración Avanzada

### Variables de Entorno
```bash
# Servidor
HOST=0.0.0.0
PORT=8000
RELOAD=true

# OpenAI
OPENAI_API_KEY=tu_api_key
MODEL_NAME=gpt-4
MAX_TOKENS=4000
TEMPERATURE=0.7
```

### Personalización del Modelo
Puedes modificar `auto_ofertas/config.py` para ajustar:
- Modelo de IA utilizado
- Parámetros de generación
- Directorios de archivos

## 🐛 Solución de Problemas

### Error: "No se ha configurado OPENAI_API_KEY"
- Crea el archivo `.env` con tu API key de OpenAI
- Obtén una API key en: https://platform.openai.com/api-keys

### Error: "Archivo no encontrado"
- Verifica que el archivo existe en el directorio correcto
- Usa los endpoints de listado para ver archivos disponibles

### Error: "Solo se aceptan archivos .docx"
- Asegúrate de que los archivos estén en formato Word (.docx)
- No se aceptan archivos .doc antiguos

## 📈 Próximas Mejoras

- [ ] Soporte para PDF
- [ ] Base de datos para persistencia
- [ ] Interfaz web
- [ ] Múltiples idiomas
- [ ] Plantillas personalizables
- [ ] Análisis de competitividad
- [ ] Integración con sistemas externos

## 🤝 Contribuir

1. Fork el proyecto
2. Crea una rama para tu feature
3. Commit tus cambios
4. Push a la rama
5. Abre un Pull Request

## 📄 Licencia

Este proyecto está bajo la Licencia MIT. Ver `LICENSE` para más detalles.

## 📞 Soporte

Para soporte técnico o preguntas:
- Abre un issue en GitHub
- Contacta al equipo de desarrollo

---

**¡Genera ofertas técnicas profesionales siguiendo los estándares de GUX Technologies! 🚀** 