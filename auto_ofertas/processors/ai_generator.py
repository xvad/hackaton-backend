import os
import json
import uuid
from typing import Dict, Any, List
from docx import Document
from openai import OpenAI
from ..config import Config
from .parser import parse_licitacion_dinamica

class AIGenerator:
    def __init__(self, modelo_backend: str = None):
        self.client = OpenAI(api_key=Config.OPENAI_API_KEY)
        self.modelo_backend = modelo_backend or Config.MODEL_NAME
        self.ofertas_historicas = []
        self.licitaciones_historicas = []
        
    def cargar_datos_historicos(self, ofertas_dir: str, licitaciones_dir: str):
        """Carga y procesa datos históricos para usar como base de conocimiento"""
        print("📚 Cargando datos históricos...")
        
        # Cargar ofertas técnicas históricas
        ofertas_count = 0
        for filename in os.listdir(ofertas_dir):
            if filename.endswith('.docx'):
                file_path = os.path.join(ofertas_dir, filename)
                try:
                    oferta = parse_licitacion_dinamica(file_path)
                    oferta['archivo_origen'] = filename
                    self.ofertas_historicas.append(oferta)
                    ofertas_count += 1
                except Exception as e:
                    print(f"Error procesando oferta {filename}: {e}")
        
        # Cargar licitaciones históricas
        licitaciones_count = 0
        for filename in os.listdir(licitaciones_dir):
            if filename.endswith('.docx'):
                file_path = os.path.join(licitaciones_dir, filename)
                try:
                    licitacion = parse_licitacion_dinamica(file_path)
                    licitacion['archivo_origen'] = filename
                    self.licitaciones_historicas.append(licitacion)
                    licitaciones_count += 1
                except Exception as e:
                    print(f"Error procesando licitación {filename}: {e}")
        
        print(f"✅ Datos cargados: {ofertas_count} ofertas, {licitaciones_count} licitaciones")

    def generar_oferta_json_dinamico(self, licitacion_path: str, empresa_nombre: str, empresa_descripcion: str = "") -> Dict[str, Any]:
        """Genera una oferta técnica en formato JSON dinámico usando ofertas históricas como base"""
        # Extraer estructura dinámica de la licitación
        licitacion_dict = parse_licitacion_dinamica(licitacion_path)
        
        # Crear prompt con contexto de ofertas históricas
        prompt = self._crear_prompt_con_historico(licitacion_dict, empresa_nombre, empresa_descripcion)
        
        # Llamar a la IA
        respuesta_json = self._generar_json_con_ia(prompt, licitacion_dict)
        return respuesta_json

    def generar_oferta_multiple_licitaciones(self, licitaciones: List[Dict[str, Any]], empresa_nombre: str, empresa_descripcion: str = "") -> Dict[str, Any]:
        """Genera una oferta técnica analizando múltiples licitaciones y combinando la mejor información"""
        
        # Crear prompt con contexto de múltiples licitaciones
        prompt = self._crear_prompt_multiple_licitaciones(licitaciones, empresa_nombre, empresa_descripcion)
        
        # Llamar a la IA
        respuesta_json = self._generar_json_con_ia(prompt, self._obtener_estructura_combinada(licitaciones))
        return respuesta_json

    def generar_oferta_estructurada(self, licitaciones: List[Dict[str, Any]], empresa_nombre: str, empresa_descripcion: str = "", nombre_proyecto: str = "Proyecto", cliente: str = "Cliente", fecha: str = "2025", costo_total: int = 45000000, plazo: str = "5 meses") -> Dict[str, Any]:
        """Genera una oferta técnica en formato estructurado con secciones organizadas"""
        
        # Primero, analizar las licitaciones para entender el proyecto
        analisis_proyecto = self._analizar_licitaciones_detallado(licitaciones)
        
        # Crear prompt específico con el análisis previo
        prompt = self._crear_prompt_estructura_json_mejorado(licitaciones, analisis_proyecto, empresa_nombre, empresa_descripcion, nombre_proyecto, cliente, fecha, costo_total, plazo)
        
        # Generar JSON estructurado usando IA
        try:
            respuesta_json = self._generar_json_estructurado_con_ia(prompt, nombre_proyecto, cliente, fecha, costo_total, plazo, empresa_nombre)
            
            # Mejorar secciones específicas con análisis adicional
            respuesta_json = self._mejorar_secciones_especificas(respuesta_json, analisis_proyecto, licitaciones)
            
            return respuesta_json
        except Exception as e:
            print(f"Error generando JSON estructurado: {e}")
            # Fallback: generar estructura básica con parámetros personalizados
            return self._generar_estructura_fallback(nombre_proyecto, cliente, fecha, costo_total, plazo, empresa_nombre)

    def _determinar_tipo_contenido(self, contenido: str) -> str:
        """Determina el tipo de contenido basado en su estructura"""
        contenido_str = str(contenido).lower()
        
        # Detectar listas
        if any(marker in contenido_str for marker in ["•", "-", "*", "1.", "2.", "3."]):
            return "list"
        
        # Detectar tablas (contenido con estructura de tabla)
        if "|" in contenido_str or "tabla" in contenido_str or "columnas" in contenido_str:
            return "table"
        
        # Por defecto es texto
        return "text"

    def _generar_secciones_adicionales(self, empresa_nombre: str, cliente: str, costo_total: int, plazo: str) -> List[Dict[str, Any]]:
        """Genera secciones adicionales que pueden faltar"""
        secciones_adicionales = []
        
        # Sección de Funcionalidades Clave del Sistema
        secciones_adicionales.append({
            "title": "Funcionalidades Clave del Sistema",
            "type": "text",
            "content": "El sistema considera los siguientes módulos principales:\n\n• Gestor de Competencias: Módulo en el cual el usuario Administrador podrá crear, editar, organizar y actualizar competencias transversales que se evalúan en la institución. Estas competencias estarán alineadas al modelo educativo del cliente y podrán configurarse según niveles formativos, carreras, sedes y campus.\n\n• Gestor de Rúbricas de Evaluación: Módulo en el cual el usuario Administrador podrá crear, agregar, modificar y/o eliminar las distintas rúbricas de evaluación para cada competencia transversal, en cada uno de sus niveles formativos.\n\n• Módulo de Evaluación y Seguimiento: Módulo en el cual tanto los usuarios finales como los supervisores podrán realizar procesos de evaluación y autoevaluación.\n\n• Panel de Control y Reportería Avanzada: Módulo central de gestión estratégica donde el Administrador podrá monitorear el uso del sistema, analizar indicadores clave de desempeño y generar reportes personalizados."
        })
        
        # Sección de Infraestructura Tecnológica
        secciones_adicionales.append({
            "title": "Infraestructura Tecnológica",
            "type": "text",
            "content": "La solución propuesta contempla una infraestructura tecnológica moderna, escalable y segura:\n\n• Backend: Framework Django sobre Python, permitiendo una arquitectura robusta, modular y fácilmente integrable con sistemas existentes.\n\n• Frontend: Desarrollo basado en React con TypeScript, utilizado para la construcción de interfaces de usuario dinámicas, interactivas y reutilizables.\n\n• Base de Datos: Uso combinado de PostgreSQL (para datos estructurados relacionales) y MongoDB (para datos semiestructurados).\n\n• Infraestructura: Implementación sobre servidores Linux utilizando contenedores con Docker y orquestación a través de Kubernetes.\n\n• Integraciones: API RESTful para integración bidireccional con sistemas existentes, autenticación unificada con Microsoft EntraID o sistemas similares."
        })
        
        # Sección de Equipo de Trabajo Asignado (tabla)
        secciones_adicionales.append({
            "title": "Equipo de Trabajo Asignado",
            "type": "table",
            "content": {
                "headers": ["Rol", "Responsabilidades Principales", "Experiencia Requerida"],
                "rows": [
                    ["Project Manager", "Planificación, coordinación y control del proyecto. Interacción directa con el equipo del cliente", "Más de 10 años en gestión de proyectos tecnológicos"],
                    ["Tech Lead / Arquitecto", "Define la arquitectura del sistema, estándares técnicos y lineamientos de integración", "Experiencia en arquitecturas de sistemas educativos"],
                    ["Front-End Developer", "Desarrolla la interfaz de usuario según principios de usabilidad y accesibilidad", "React, TypeScript, diseño responsive"],
                    ["Back-End Developer", "Desarrolla la lógica de negocio, APIs RESTful y control de flujos de datos", "Django, Python, APIs RESTful"],
                    ["UX/UI Designer", "Diseña la experiencia y la interfaz de usuario, intuitiva e inclusiva", "Diseño centrado en usuario, accesibilidad"],
                    ["QA / Tester Funcional", "Diseña y ejecuta pruebas automatizadas y manuales", "Testing automatizado, casos de uso educativos"],
                    ["DevSecOps", "Gestiona entornos en la nube, automatiza despliegues, configura monitoreo", "Docker, Kubernetes, AWS/Azure"]
                ]
            }
        })
        
        # Sección de Metodología de Implementación
        secciones_adicionales.append({
            "title": "Metodología de Implementación",
            "type": "text",
            "content": f"La implementación se realizará bajo la modalidad \"llave en mano\", utilizando un enfoque metodológico basado en Disciplined Agile del PMI:\n\nFase 1 - Inception (1 mes):\n• Refinamiento del alcance y visión del producto\n• Consolidación del equipo multidisciplinario\n• Consolidación de la arquitectura técnica\n• Confirmación del backlog inicial y priorización de requisitos\n\nFase 2 - Construction (3 meses):\n• Desarrollo incremental de los módulos\n• Iteraciones cortas (1-2 semanas) con demostraciones frecuentes\n• Implementación progresiva de las integraciones\n• Pruebas técnicas continuas\n\nFase 3 - Transition (1 mes):\n• Pruebas finales y transferencia tecnológica\n• Capacitación de personal técnico\n• Despliegue en producción\n• Activación de plan de soporte"
        })
        
        # Sección de Garantías y Soporte Post-implementación
        secciones_adicionales.append({
            "title": "Garantías y Soporte Post-implementación",
            "type": "text",
            "content": f"{empresa_nombre} ofrece una política de garantía y soporte post-implementación que asegura la continuidad operativa del sistema:\n\nGarantía Técnica (6 meses):\n• Corrección sin costo de errores funcionales, bugs o defectos atribuibles al código fuente\n• Corrección de errores de configuración en los entornos implementados\n• Revisión y ajuste de integraciones con sistemas institucionales\n• Actualización de la documentación técnica cuando se aplique alguna corrección\n\nSoporte Acompañado:\n• Resolución de consultas operativas y funcionales para usuarios autorizados\n• Acompañamiento en el monitoreo de integraciones y flujos críticos\n• Aplicación de ajustes menores de configuración\n• Participación en reuniones técnicas mensuales\n\nClasificación de Incidencias:\n• Nivel 1 (Crítico): 2 horas hábiles de respuesta\n• Nivel 2 (Medio): 8 horas hábiles de respuesta\n• Nivel 3 (Leve): 24 horas hábiles de respuesta"
        })
        
        # Sección de Tipos de Usuarios y Permisos
        secciones_adicionales.append({
            "title": "Tipos de Usuarios y Permisos",
            "type": "table",
            "content": {
                "headers": ["Perfil de Usuario", "Descripción", "Permisos Principales"],
                "rows": [
                    ["Administrador", "Equipo de gestión institucional, dirección académica o soporte TI", "Crear/editar competencias, gestionar rúbricas, configurar calendarios, supervisar uso del sistema"],
                    ["Jefe de Carrera", "Docente o académico con responsabilidad sobre coordinación de programas", "Visualizar resultados por carrera, participar en evaluaciones, validar autoevaluaciones, acceder a reportes"],
                    ["Estudiante", "Alumnado regular de la institución", "Acceder a competencias definidas, realizar autoevaluaciones, visualizar historial de evaluaciones, recibir retroalimentación"]
                ]
            }
        })
        
        # Sección de Plan de Capacitación
        secciones_adicionales.append({
            "title": "Plan de Capacitación",
            "type": "list",
            "content": [
                "Capacitación funcional: 6 horas distribuidas en 2 a 3 sesiones según perfil",
                "Capacitación técnica (TI): 6 a 8 horas distribuidas en sesiones especializadas",
                "Acompañamiento supervisado: 4 semanas posteriores a la puesta en marcha",
                "Acceso permanente a materiales asincrónicos",
                "Manuales de usuario diferenciados por perfil",
                "Cápsulas de video por funcionalidad clave (2 a 5 minutos)",
                "Documentación técnica estructurada",
                "Entorno de prueba (sandbox) disponible por 30 días",
                "Preguntas frecuentes (FAQ) actualizadas"
            ]
        })
        
        # Sección de Cronograma Detallado del Proyecto
        secciones_adicionales.append({
            "title": "Cronograma Detallado del Proyecto",
            "type": "table",
            "content": {
                "headers": ["Etapa", "Duración", "Actividades Principales", "Entregables"],
                "rows": [
                    ["Inception", "1 mes", "Definición de requerimientos, análisis preliminar, identificación de actores", "Documento de especificación detallado y roadmap del proyecto"],
                    ["Construction", "3 meses", "Desarrollo iterativo-incremental de módulos, integraciones críticas", "Versiones funcionales incrementales de la plataforma"],
                    ["Transition", "1 mes", "Pruebas finales, transferencia tecnológica, capacitación, despliegue", "Solución operativa en ambiente del cliente"]
                ]
            }
        })
        
        # Sección de Inversión y Condiciones de Pago
        secciones_adicionales.append({
            "title": "Inversión y Condiciones de Pago",
            "type": "text",
            "content": f"Costo Total del Proyecto: ${costo_total:,} (pesos chilenos)\n\nDesglose de Costos:\n• Desarrollo de plataforma web: ${int(costo_total * 0.71):,}\n• Integraciones con sistemas institucionales: ${int(costo_total * 0.18):,}\n• Capacitación y transferencia tecnológica: ${int(costo_total * 0.07):,}\n• Documentación y soporte inicial: ${int(costo_total * 0.04):,}\n\nCondiciones de Pago:\n• 30% al inicio del proyecto (firma de contrato)\n• 40% al completar la Fase de Construction\n• 30% al completar la Fase de Transition y aceptación del sistema\n\nGarantías Incluidas:\n• Garantía técnica por 6 meses\n• Soporte post-implementación por 6 meses\n• Actualizaciones de seguridad gratuitas\n• Capacitación completa del equipo técnico"
        })
        
        return secciones_adicionales

    def _crear_prompt_con_historico(self, licitacion_dict: Dict[str, Any], empresa_nombre: str, empresa_descripcion: str) -> str:
        # Preparar ejemplos de ofertas históricas
        ejemplos_ofertas = ""
        if self.ofertas_historicas:
            ejemplos_ofertas = "EJEMPLOS DE OFERTAS HISTÓRICAS EXITOSAS:\n"
            for i, oferta in enumerate(self.ofertas_historicas[:3], 1):  # Usar máximo 3 ejemplos
                ejemplos_ofertas += f"\n--- EJEMPLO {i} ---\n"
                ejemplos_ofertas += f"Archivo: {oferta.get('archivo_origen', 'N/A')}\n"
                for seccion, contenido in oferta.items():
                    if seccion != 'archivo_origen' and contenido:
                        ejemplos_ofertas += f"{seccion}: {str(contenido)[:200]}...\n"
                ejemplos_ofertas += "---\n"
        
        # Preparar ejemplos de licitaciones históricas
        ejemplos_licitaciones = ""
        if self.licitaciones_historicas:
            ejemplos_licitaciones = "EJEMPLOS DE LICITACIONES HISTÓRICAS:\n"
            for i, licitacion in enumerate(self.licitaciones_historicas[:2], 1):  # Usar máximo 2 ejemplos
                ejemplos_licitaciones += f"\n--- LICITACIÓN {i} ---\n"
                ejemplos_licitaciones += f"Archivo: {licitacion.get('archivo_origen', 'N/A')}\n"
                for seccion, contenido in licitacion.items():
                    if seccion != 'archivo_origen' and contenido:
                        ejemplos_licitaciones += f"{seccion}: {str(contenido)[:200]}...\n"
                ejemplos_licitaciones += "---\n"

        return (
            "Eres un experto en generación de ofertas técnicas para GUX Technologies y Proyectum. "
            "Debes generar una propuesta técnica profesional usando las ofertas históricas como base de conocimiento. "
            "\n\n"
            "ESTÁNDARES INSTITUCIONALES A SEGUIR:\n"
            "1. ENFOQUE METODOLÓGICO: Usar Disciplined Agile Delivery (DAD) con fases:\n"
            "   - Inception: Alineamiento estratégico, definición de objetivos, comprensión del contexto\n"
            "   - Construction: Desarrollo iterativo, validación temprana, retroalimentación continua\n"
            "   - Transition: Despliegue, traspaso, adopción y cierre controlado\n"
            "   - Discovery continuo: Fase transversal para ajustes y nuevas necesidades\n"
            "\n"
            "2. ESTRUCTURA RECOMENDADA:\n"
            "   - Resumen Ejecutivo (sintetizar problema, solución, metodología, equipo, diferenciadores)\n"
            "   - Objetivos y Alcance del Servicio (conectar con desafíos reales del cliente)\n"
            "   - Solución Propuesta (adaptar según tipo de servicio)\n"
            "   - Metodología de Trabajo (DAD con mecanismos de control, gestión de riesgos, QA)\n"
            "   - Plan de Implementación/Roadmap (hitos, tiempos, entregables)\n"
            "   - Organización del Proyecto (roles, liderazgo, coordinación)\n"
            "   - Factores Claves para el Éxito (condiciones necesarias del cliente)\n"
            "   - Presentación de la Empresa (antecedentes, experiencia, referencias)\n"
            "   - Equipo de Trabajo y CVs (perfiles coherentes con el desafío)\n"
            "   - Materia de Sostenibilidad (políticas institucionales)\n"
            "   - Política de Diversidad e Inclusión (compromisos activos)\n"
            "\n"
            "3. PRINCIPIOS CLAVE:\n"
            "   - Generar valor real para el cliente, no solo cumplir bases formales\n"
            "   - Posicionarse como partner estratégico\n"
            "   - Usar lenguaje claro, directo y profesional (tercera persona)\n"
            "   - Personalizar usando el nombre real de la organización cliente\n"
            "   - Evitar copiar y pegar sin contexto\n"
            "   - Enfoque en resultados tangibles y propuesta de valor concreta\n"
            "\n"
            "4. DIFERENCIADORES:\n"
            "   - Rigor y alineación con desafíos reales\n"
            "   - Enfoque metodológico ágil y flexible\n"
            "   - Orientación a resultados\n"
            "   - Integración de sostenibilidad, innovación y experiencia\n"
            "\n"
            f"{ejemplos_ofertas}\n"
            f"{ejemplos_licitaciones}\n"
            f"LICITACIÓN A RESPONDER:\n{json.dumps(licitacion_dict, ensure_ascii=False, indent=2)}\n"
            f"EMPRESA: {empresa_nombre}\n"
            f"DESCRIPCIÓN: {empresa_descripcion}\n"
            "\n"
            "INSTRUCCIONES ESPECÍFICAS:\n"
            "1. ANALIZA las ofertas históricas para entender el estilo, estructura y contenido exitoso\n"
            "2. ADAPTA el contenido de las ofertas históricas al contexto de la nueva licitación\n"
            "3. GENERA un JSON que incluya TODAS las secciones de la licitación de entrada\n"
            "4. USA el mismo formato y estructura que las ofertas históricas exitosas\n"
            "5. PERSONALIZA el contenido para la empresa y licitación específica\n"
            "6. ASEGÚRATE de que cada sección tenga contenido sustancial y profesional\n"
            "7. SIGUE los estándares de GUX Technologies en todo el contenido\n"
            "\n"
            "IMPORTANTE: El JSON resultante debe ser COMPLETO y LISTO para generar el documento final. "
            "Cada sección debe tener contenido detallado y profesional, no solo títulos vacíos."
        )

    def _crear_prompt_multiple_licitaciones(self, licitaciones: List[Dict[str, Any]], empresa_nombre: str, empresa_descripcion: str) -> str:
        # Preparar ejemplos de ofertas históricas
        ejemplos_ofertas = ""
        if self.ofertas_historicas:
            ejemplos_ofertas = "EJEMPLOS DE OFERTAS HISTÓRICAS EXITOSAS:\n"
            for i, oferta in enumerate(self.ofertas_historicas[:3], 1):
                ejemplos_ofertas += f"\n--- EJEMPLO {i} ---\n"
                ejemplos_ofertas += f"Archivo: {oferta.get('archivo_origen', 'N/A')}\n"
                for seccion, contenido in oferta.items():
                    if seccion != 'archivo_origen' and contenido:
                        ejemplos_ofertas += f"{seccion}: {str(contenido)[:200]}...\n"
                ejemplos_ofertas += "---\n"
        
        # Preparar información de todas las licitaciones
        info_licitaciones = "LICITACIONES A ANALIZAR:\n"
        for i, licitacion in enumerate(licitaciones, 1):
            info_licitaciones += f"\n--- LICITACIÓN {i}: {licitacion['archivo']} ---\n"
            for seccion, contenido in licitacion['datos'].items():
                if contenido:
                    info_licitaciones += f"{seccion}: {str(contenido)[:300]}...\n"
            info_licitaciones += "---\n"

        return (
            "Eres un experto en generación de ofertas técnicas para GUX Technologies y Proyectum. "
            "Tu tarea es analizar MÚLTIPLES licitaciones y generar la MEJOR oferta técnica combinando "
            "la información más relevante de cada una, usando las ofertas históricas como base de conocimiento. "
            "\n\n"
            "ESTÁNDARES INSTITUCIONALES A SEGUIR:\n"
            "1. ENFOQUE METODOLÓGICO: Usar Disciplined Agile Delivery (DAD) con fases:\n"
            "   - Inception: Alineamiento estratégico, definición de objetivos, comprensión del contexto\n"
            "   - Construction: Desarrollo iterativo, validación temprana, retroalimentación continua\n"
            "   - Transition: Despliegue, traspaso, adopción y cierre controlado\n"
            "   - Discovery continuo: Fase transversal para ajustes y nuevas necesidades\n"
            "\n"
            "2. ESTRUCTURA RECOMENDADA:\n"
            "   - Resumen Ejecutivo (sintetizar problema, solución, metodología, equipo, diferenciadores)\n"
            "   - Objetivos y Alcance del Servicio (conectar con desafíos reales del cliente)\n"
            "   - Solución Propuesta (adaptar según tipo de servicio)\n"
            "   - Metodología de Trabajo (DAD con mecanismos de control, gestión de riesgos, QA)\n"
            "   - Plan de Implementación/Roadmap (hitos, tiempos, entregables)\n"
            "   - Organización del Proyecto (roles, liderazgo, coordinación)\n"
            "   - Factores Claves para el Éxito (condiciones necesarias del cliente)\n"
            "   - Presentación de la Empresa (antecedentes, experiencia, referencias)\n"
            "   - Equipo de Trabajo y CVs (perfiles coherentes con el desafío)\n"
            "   - Materia de Sostenibilidad (políticas institucionales)\n"
            "   - Política de Diversidad e Inclusión (compromisos activos)\n"
            "\n"
            "3. PRINCIPIOS CLAVE:\n"
            "   - Generar valor real para el cliente, no solo cumplir bases formales\n"
            "   - Posicionarse como partner estratégico\n"
            "   - Usar lenguaje claro, directo y profesional (tercera persona)\n"
            "   - Personalizar usando el nombre real de la organización cliente\n"
            "   - Evitar copiar y pegar sin contexto\n"
            "   - Enfoque en resultados tangibles y propuesta de valor concreta\n"
            "\n"
            "4. DIFERENCIADORES:\n"
            "   - Rigor y alineación con desafíos reales\n"
            "   - Enfoque metodológico ágil y flexible\n"
            "   - Orientación a resultados\n"
            "   - Integración de sostenibilidad, innovación y experiencia\n"
            "\n"
            f"{ejemplos_ofertas}\n"
            f"{info_licitaciones}\n"
            f"EMPRESA: {empresa_nombre}\n"
            f"DESCRIPCIÓN: {empresa_descripcion}\n"
            "\n"
            "INSTRUCCIONES ESPECÍFICAS PARA MÚLTIPLES LICITACIONES:\n"
            "1. ANALIZA cada licitación para identificar:\n"
            "   - Requisitos técnicos específicos\n"
            "   - Alcances y objetivos\n"
            "   - Plazos y cronogramas\n"
            "   - Criterios de evaluación\n"
            "   - Especificaciones técnicas\n"
            "\n"
            "2. COMBINA la información más relevante de todas las licitaciones:\n"
            "   - Toma los requisitos más exigentes\n"
            "   - Integra los alcances complementarios\n"
            "   - Considera los plazos más realistas\n"
            "   - Incluye todos los criterios de evaluación\n"
            "\n"
            "3. GENERA una oferta técnica COMPLETA que:\n"
            "   - Responda a TODOS los requisitos identificados\n"
            "   - Use el estilo y estructura de las ofertas históricas exitosas\n"
            "   - Sea coherente y profesional\n"
            "   - Maximice las posibilidades de éxito\n"
            "\n"
            "4. ASEGÚRATE de que la oferta:\n"
            "   - Sea más completa que cualquier licitación individual\n"
            "   - Incluya todos los elementos necesarios\n"
            "   - Siga los estándares de GUX Technologies\n"
            "   - Esté lista para generar el documento final\n"
            "\n"
            "IMPORTANTE: El JSON resultante debe ser la MEJOR oferta posible, "
            "combinando lo mejor de todas las licitaciones analizadas."
        )

    def _obtener_estructura_combinada(self, licitaciones: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Combina las estructuras de todas las licitaciones en una estructura unificada"""
        estructura_combinada = {}
        
        for licitacion in licitaciones:
            for seccion, contenido in licitacion['datos'].items():
                if seccion not in estructura_combinada:
                    estructura_combinada[seccion] = ""
        
        return estructura_combinada

    def _generar_json_con_ia(self, prompt: str, estructura_referencia: Dict[str, Any]) -> Dict[str, Any]:
        try:
            response = self.client.chat.completions.create(
                model=self.modelo_backend,
                messages=[
                    {"role": "system", "content": "Eres un experto en generación de propuestas técnicas para GUX Technologies y Proyectum. Tu tarea es crear ofertas técnicas profesionales basándote en ofertas históricas exitosas y adaptándolas al contexto específico de cada licitación. SIEMPRE debes generar contenido sustancial y profesional para cada sección. NUNCA dejes secciones vacías. Siempre devuelves JSON válido y completo con contenido real."},
                    {"role": "user", "content": prompt}
                ],
                max_tokens=Config.MAX_TOKENS,
                temperature=Config.TEMPERATURE
            )
            contenido = response.choices[0].message.content
            # Buscar el primer bloque JSON en la respuesta
            json_str = self._extraer_json(contenido)
            resultado = json.loads(json_str)
            
            # Verificar que el resultado tenga contenido
            if not self._verificar_contenido(resultado):
                print("⚠️  El resultado está vacío, generando contenido de respaldo...")
                resultado = self._generar_contenido_respaldo(estructura_referencia)
            
            return resultado
        except Exception as e:
            print(f"Error en generación con IA: {e}")
            # Fallback: generar contenido de respaldo
            return self._generar_contenido_respaldo(estructura_referencia)

    def _verificar_contenido(self, resultado: Dict[str, Any]) -> bool:
        """Verifica que el resultado tenga contenido sustancial"""
        if not resultado:
            return False
        
        contenido_total = 0
        secciones_con_contenido = 0
        
        for seccion, contenido in resultado.items():
            if contenido and str(contenido).strip():
                contenido_total += len(str(contenido))
                secciones_con_contenido += 1
        
        # Debe tener al menos 3 secciones con contenido y al menos 1000 caracteres totales
        return secciones_con_contenido >= 3 and contenido_total >= 1000

    def _generar_contenido_respaldo(self, estructura_referencia: Dict[str, Any]) -> Dict[str, Any]:
        """Genera contenido de respaldo cuando la IA falla o devuelve contenido vacío"""
        contenido_respaldo = {}
        
        for seccion in estructura_referencia.keys():
            contenido_respaldo[seccion] = self._generar_contenido_por_seccion(seccion)
        
        return contenido_respaldo

    def _generar_contenido_por_seccion(self, seccion: str) -> str:
        """Genera contenido específico para cada tipo de sección"""
        contenido_base = {
            "INTRODUCCIÓN": "GUX Technologies presenta esta propuesta técnica para responder a los requerimientos especificados en las bases de licitación. Nuestra empresa cuenta con amplia experiencia en el desarrollo e implementación de soluciones tecnológicas innovadoras, con un equipo de profesionales altamente calificados y metodologías probadas que garantizan la entrega de resultados de excelencia. Esta propuesta se fundamenta en un enfoque metodológico basado en Disciplined Agile Delivery (DAD), que permite la adaptabilidad a los cambios y la entrega de valor continuo al cliente.",
            
            "RESUMEN EJECUTIVO": "La presente propuesta técnica de GUX Technologies responde integralmente a los requerimientos establecidos en las bases de licitación. Nuestra solución se fundamenta en metodologías ágiles probadas, tecnologías de vanguardia y un equipo de profesionales con amplia experiencia en proyectos similares. La propuesta incluye un enfoque metodológico basado en Disciplined Agile Delivery (DAD), garantizando la entrega de valor continuo y la adaptabilidad a los cambios del proyecto. El equipo asignado cuenta con más de 20 años de experiencia en desarrollo de productos digitales, con presencia en Latinoamérica y Europa, y especialización en soluciones para instituciones educativas y del sector público.",
            
            "ALCANCE DEL SERVICIO": "El alcance del servicio incluye el análisis detallado de requerimientos, diseño de arquitectura técnica, desarrollo e implementación de la solución, pruebas integrales, capacitación del personal y soporte post-implementación. GUX Technologies se compromete a entregar una solución completa que cumpla con todos los estándares de calidad y funcionalidad especificados. El proyecto contempla el desarrollo de una plataforma web moderna, segura e inclusiva, accesible desde distintos dispositivos y escalable, con funcionalidades de gestión de usuarios, reportes analíticos, integración con sistemas existentes y mecanismos de seguridad robustos.",
            
            "METODOLOGÍA DE TRABAJO": "Nuestra metodología se basa en Disciplined Agile Delivery (DAD) con las siguientes fases: 1) Inception (1 mes): Alineamiento estratégico, definición de objetivos, consolidación del equipo multidisciplinario, consolidación de la arquitectura técnica y confirmación del backlog inicial; 2) Construction (3 meses): Desarrollo iterativo con entregables incrementales, iteraciones cortas de 1-2 semanas con demostraciones frecuentes, implementación progresiva de integraciones y pruebas técnicas continuas; 3) Transition (1 mes): Pruebas finales, transferencia tecnológica, capacitación de personal técnico, despliegue en producción y activación del plan de soporte. Cada fase incluye mecanismos de control de calidad, gestión de riesgos y comunicación continua con el cliente.",
            
            "EQUIPO DE TRABAJO": "El equipo asignado incluye un Project Manager con más de 10 años de experiencia en gestión de proyectos tecnológicos, un Tech Lead/Arquitecto especializado en arquitecturas de sistemas educativos, desarrolladores full-stack con experiencia en React, TypeScript, Django y Python, especialistas en UX/UI con enfoque en diseño centrado en usuario y accesibilidad, profesionales de QA con experiencia en testing automatizado y casos de uso educativos, y un DevSecOps especializado en Docker, Kubernetes y gestión de entornos en la nube. Todos los integrantes cuentan con certificaciones relevantes y experiencia en proyectos similares.",
            
            "PLAZOS": "El proyecto se ejecutará en un plazo de 5 meses, distribuidos en fases incrementales que permitan la validación temprana y la entrega de valor continuo. Los hitos principales incluyen: Fase 1 - Inception (1 mes): Documento de especificación detallado y roadmap del proyecto; Fase 2 - Construction (3 meses): Versiones funcionales incrementales de la plataforma; Fase 3 - Transition (1 mes): Solución operativa en ambiente del cliente. Cada fase incluye entregables funcionales y documentación completa, con revisiones y validaciones continuas con el cliente.",
            
            "ESPECIFICACIONES TÉCNICAS": "La solución se desarrollará utilizando tecnologías modernas y escalables, incluyendo Django sobre Python para el backend, React con TypeScript para el frontend, PostgreSQL y MongoDB para bases de datos, contenedores Docker con orquestación Kubernetes, y arquitecturas en la nube. Se implementarán estándares de seguridad robustos, integración con sistemas existentes mediante APIs RESTful, autenticación unificada, mecanismos de monitoreo y respaldo, y funcionalidades de accesibilidad y usabilidad. La infraestructura será escalable, segura y de alta disponibilidad.",
            
            "GARANTÍAS Y SOPORTE": "GUX Technologies ofrece garantía técnica por 6 meses post-implementación, incluyendo corrección sin costo de errores funcionales, bugs o defectos atribuibles al código fuente, corrección de errores de configuración en los entornos implementados, revisión y ajuste de integraciones con sistemas institucionales, y actualización de la documentación técnica. El soporte incluye resolución de consultas operativas y funcionales para usuarios autorizados, acompañamiento en el monitoreo de integraciones y flujos críticos, aplicación de ajustes menores de configuración, y participación en reuniones técnicas mensuales. Clasificación de incidencias: Nivel 1 (Crítico): 2 horas hábiles de respuesta; Nivel 2 (Medio): 8 horas hábiles de respuesta; Nivel 3 (Leve): 24 horas hábiles de respuesta.",
            
            "EXPERIENCIA Y REFERENCIAS": "GUX Technologies cuenta con más de 20 años de experiencia en desarrollo de soluciones tecnológicas, con presencia en Latinoamérica y Europa. Hemos ejecutado exitosamente proyectos similares para instituciones públicas y privadas, incluyendo: Pontificia Universidad Católica de Chile (Plataforma de Evaluación de Madurez en Gestión TI), Universidad Santo Tomás (Plataforma administrativa con hiperautomatización), Universidad Alberto Hurtado (Plataforma administrativa con hiperautomatización), Universidad de Las Américas (Plataforma para apoyo a personas con discapacidad cognitiva), y Bomberos de Chile (Apoyo integral a la Academia Nacional de Bomberos). El equipo cuenta con especialistas en tecnologías educativas (EdTech), desarrolladores full-stack, arquitectos de software, y especialistas en experiencia de usuario.",
            
            "FACTORES CLAVE PARA EL ÉXITO": "La coordinación y ejecución de entrevistas y focus groups con participación activa del cliente, disponibilidad de APIs y sistemas existentes dentro de los plazos definidos, documentación clara de APIs, ambientes de prueba y autenticación segura, ambientes estables para QA y producción desde etapas tempranas, dedicación de colaboradores clave del cliente para validación y ejecución, gestión de licencias de software, hardware especializado o insumos específicos por parte del cliente, y cumplimiento normativo y alineación con regulaciones vigentes. Estos factores son fundamentales para garantizar el éxito del proyecto y la satisfacción del cliente.",
            
            "INVERSIÓN Y CONDICIONES DE PAGO": "El costo total del proyecto es de $45.000.000 (pesos chilenos), con el siguiente desglose: Desarrollo de plataforma web ($32.000.000), integraciones con sistemas institucionales ($8.000.000), capacitación y transferencia tecnológica ($3.000.000), y documentación y soporte inicial ($2.000.000). Las condiciones de pago son: 30% al inicio del proyecto (firma de contrato), 40% al completar la Fase de Construction, y 30% al completar la Fase de Transition y aceptación del sistema. Las garantías incluidas son: garantía técnica por 6 meses, soporte post-implementación por 6 meses, actualizaciones de seguridad gratuitas, y capacitación completa del equipo técnico."
        }
        
        # Buscar contenido específico o usar contenido genérico
        for clave, contenido in contenido_base.items():
            if clave.lower() in seccion.lower() or seccion.lower() in clave.lower():
                return contenido
        
        # Si no encuentra coincidencia específica, usar contenido genérico más detallado
        return f"GUX Technologies presenta su propuesta técnica para la sección '{seccion}'. Nuestra empresa cuenta con amplia experiencia en el desarrollo de soluciones tecnológicas innovadoras y se compromete a entregar resultados de excelencia que cumplan con todos los requerimientos especificados. El enfoque metodológico incluye mejores prácticas de la industria, tecnologías de vanguardia como Django, React, Python y TypeScript, y un equipo de profesionales altamente calificados con más de 20 años de experiencia en el sector. La propuesta contempla un desarrollo iterativo basado en Disciplined Agile Delivery (DAD), con fases bien definidas que incluyen Inception (1 mes), Construction (3 meses) y Transition (1 mes), garantizando la entrega de valor continuo y la adaptabilidad a los cambios del proyecto."

    def _crear_prompt_estructura_json(self, licitaciones: List[Dict[str, Any]], empresa_nombre: str, empresa_descripcion: str, nombre_proyecto: str, cliente: str, fecha: str, costo_total: int, plazo: str) -> str:
        """Crea un prompt específico para generar la estructura JSON requerida"""
        
        # Preparar información de las licitaciones
        info_licitaciones = "LICITACIONES A ANALIZAR:\n"
        for i, licitacion in enumerate(licitaciones, 1):
            info_licitaciones += f"\n--- LICITACIÓN {i}: {licitacion['archivo']} ---\n"
            for seccion, contenido in licitacion['datos'].items():
                if contenido:
                    info_licitaciones += f"{seccion}: {str(contenido)[:300]}...\n"
            info_licitaciones += "---\n"

        return (
            "Eres un experto en generación de ofertas técnicas para GUX Technologies. "
            "Debes generar una oferta técnica en formato JSON EXACTO con la siguiente estructura:\n\n"
            "{\n"
            '   "projectInfo": {\n'
            '      "name": "Nombre del Proyecto",\n'
            '      "client": "Nombre del Cliente",\n'
            '      "date": "Fecha",\n'
            '      "totalCost": 45000000,\n'
            '      "timeline": "5 meses"\n'
            "   },\n"
            '   "sections": [\n'
            "      {\n"
            '         "id": "1",\n'
            '         "title": "Resumen Ejecutivo",\n'
            '         "type": "text",\n'
            '         "content": "Contenido detallado...",\n'
            '         "pageBreak": true\n'
            "      },\n"
            "      {\n"
            '         "id": "2",\n'
            '         "title": "Alcance del Servicio",\n'
            '         "type": "list",\n'
            '         "content": [\n'
            '            "Elemento 1",\n'
            '            "Elemento 2"\n'
            "         ]\n"
            "      },\n"
            "      {\n"
            '         "id": "3",\n'
            '         "title": "Tipos de Usuarios y Permisos",\n'
            '         "type": "table",\n'
            '         "content": {\n'
            '            "headers": ["Columna 1", "Columna 2"],\n'
            '            "rows": [\n'
            '               ["Dato 1", "Dato 2"]\n'
            "            ]\n"
            "         }\n"
            "      }\n"
            "   ],\n"
            '   "styling": {\n'
            '      "primaryColor": "#2563eb",\n'
            '      "secondaryColor": "#1e40af",\n'
            '      "fontFamily": "Arial, sans-serif"\n'
            "   }\n"
            "}\n\n"
            "TIPOS DE CONTENIDO:\n"
            "- 'text': Para párrafos largos de texto (mínimo 500 caracteres por sección)\n"
            "- 'list': Para listas de elementos (array de strings, mínimo 5 elementos)\n"
            "- 'table': Para tablas con headers y rows (mínimo 3 filas)\n\n"
            "SECCIONES OBLIGATORIAS CON CONTENIDO DETALLADO:\n"
            "1. Resumen Ejecutivo (text, pageBreak: true) - Mínimo 800 caracteres\n"
            "2. Alcance del Servicio (list) - Mínimo 7 elementos detallados\n"
            "3. Funcionalidades Clave del Sistema (text, pageBreak: true) - Mínimo 1000 caracteres\n"
            "4. Tipos de Usuarios y Permisos (table) - Mínimo 3 filas con 3 columnas\n"
            "5. Infraestructura Tecnológica (text, pageBreak: true) - Mínimo 800 caracteres\n"
            "6. Equipo de Trabajo Asignado (table) - Mínimo 6 filas con roles detallados\n"
            "7. Metodología de Implementación (text, pageBreak: true) - Mínimo 1000 caracteres\n"
            "8. Garantías y Soporte Post-implementación (text) - Mínimo 800 caracteres\n"
            "9. Plan de Capacitación (list) - Mínimo 8 elementos\n"
            "10. Experiencia y Referencias (text, pageBreak: true) - Mínimo 800 caracteres\n"
            "11. Factores Clave para el Éxito (list) - Mínimo 6 elementos\n"
            "12. Cronograma Detallado del Proyecto (table) - Mínimo 3 filas con etapas\n"
            "13. Inversión y Condiciones de Pago (text) - Mínimo 600 caracteres\n\n"
            "REQUISITOS DE CALIDAD:\n"
            "- Cada sección debe tener contenido sustancial y profesional\n"
            "- Usar lenguaje técnico apropiado pero comprensible\n"
            "- Incluir detalles específicos y ejemplos concretos\n"
            "- Personalizar el contenido para el cliente específico\n"
            "- Seguir los estándares de GUX Technologies\n"
            "- Generar contenido original, no copiado\n\n"
            f"INFORMACIÓN DEL PROYECTO:\n"
            f"- Nombre: {nombre_proyecto}\n"
            f"- Cliente: {cliente}\n"
            f"- Fecha: {fecha}\n"
            f"- Costo Total: ${costo_total:,}\n"
            f"- Plazo: {plazo}\n"
            f"- Empresa: {empresa_nombre}\n"
            f"- Descripción: {empresa_descripcion}\n\n"
            f"{info_licitaciones}\n"
            "INSTRUCCIONES ESPECÍFICAS:\n"
            "1. Analiza DETALLADAMENTE las licitaciones para entender todos los requerimientos\n"
            "2. Genera contenido PROFESIONAL, DETALLADO y EXTENSO para cada sección\n"
            "3. Usa el formato JSON exacto especificado\n"
            "4. Incluye TODAS las secciones obligatorias con contenido sustancial\n"
            "5. Personaliza el contenido para el cliente específico mencionado\n"
            "6. Asegúrate de que el JSON sea válido y completo\n"
            "7. Usa pageBreak: true para secciones importantes\n"
            "8. Genera contenido ORIGINAL y PROFESIONAL, no solo títulos vacíos\n"
            "9. Cada sección debe tener al menos el mínimo de caracteres especificado\n"
            "10. Incluye detalles técnicos, metodológicos y de implementación\n\n"
            "IMPORTANTE: Devuelve SOLO el JSON, sin texto adicional antes o después. "
            "El contenido debe ser PROFESIONAL, DETALLADO y COMPLETO."
        )

    def _generar_json_estructurado_con_ia(self, prompt: str, nombre_proyecto: str = "Proyecto", cliente: str = "Cliente", fecha: str = "2025", costo_total: int = 45000000, plazo: str = "5 meses", empresa_nombre: str = "GUX Technologies") -> Dict[str, Any]:
        """Genera JSON estructurado usando IA con el formato específico requerido"""
        try:
            response = self.client.chat.completions.create(
                model=self.modelo_backend,
                messages=[
                    {"role": "system", "content": "Eres un experto en generación de ofertas técnicas para GUX Technologies. Tu tarea es crear ofertas técnicas en formato JSON estructurado con projectInfo, sections y styling. SIEMPRE devuelves JSON válido y completo con contenido real y profesional. NUNCA dejes secciones vacías."},
                    {"role": "user", "content": prompt}
                ],
                max_tokens=Config.MAX_TOKENS,
                temperature=Config.TEMPERATURE
            )
            contenido = response.choices[0].message.content
            json_str = self._extraer_json(contenido)
            resultado = json.loads(json_str)
            
            # Verificar que tenga la estructura correcta
            if not self._verificar_estructura_json(resultado):
                print("⚠️  La estructura JSON no es correcta, generando estructura de respaldo...")
                print(f"   - Secciones encontradas: {len(resultado.get('sections', []))}")
                print(f"   - projectInfo presente: {'projectInfo' in resultado}")
                print(f"   - styling presente: {'styling' in resultado}")
                
                # Intentar extraer información del resultado parcial
                project_info = resultado.get("projectInfo", {})
                return self._generar_estructura_fallback(
                    project_info.get("name", nombre_proyecto),
                    project_info.get("client", cliente),
                    project_info.get("date", fecha),
                    project_info.get("totalCost", costo_total),
                    project_info.get("timeline", plazo),
                    empresa_nombre
                )
            
            print("✅ Estructura JSON válida generada correctamente")
            return resultado
        except Exception as e:
            print(f"Error en generación de JSON estructurado: {e}")
            print("🔄 Generando estructura de respaldo debido al error...")
            # Generar estructura de respaldo en caso de error
            return self._generar_estructura_fallback(
                nombre_proyecto,
                cliente,
                fecha,
                costo_total,
                plazo,
                empresa_nombre
            )

    def _verificar_estructura_json(self, resultado: Dict[str, Any]) -> bool:
        """Verifica que el JSON tenga la estructura correcta y contenido suficiente"""
        if not resultado:
            return False
        
        # Verificar que tenga projectInfo
        if "projectInfo" not in resultado:
            return False
        
        # Verificar que tenga sections
        if "sections" not in resultado or not isinstance(resultado["sections"], list):
            return False
        
        # Verificar que tenga styling
        if "styling" not in resultado:
            return False
        
        # Verificar que tenga al menos 5 secciones (más flexible)
        if len(resultado["sections"]) < 5:
            return False
        
        # Verificar que cada sección tenga id, title, type y content
        contenido_total = 0
        secciones_con_contenido = 0
        
        for seccion in resultado["sections"]:
            if not all(key in seccion for key in ["id", "title", "type", "content"]):
                return False
            
            # Verificar contenido mínimo (más flexible)
            contenido = seccion["content"]
            if contenido:
                if seccion["type"] == "text":
                    contenido_str = str(contenido)
                    if len(contenido_str) < 100:  # Mínimo 100 caracteres para texto (más flexible)
                        continue  # No fallar, solo no contar esta sección
                    contenido_total += len(contenido_str)
                    secciones_con_contenido += 1
                elif seccion["type"] == "list":
                    if isinstance(contenido, list) and len(contenido) >= 2:  # Mínimo 2 elementos (más flexible)
                        contenido_total += sum(len(str(item)) for item in contenido)
                        secciones_con_contenido += 1
                    else:
                        continue  # No fallar, solo no contar esta sección
                elif seccion["type"] == "table":
                    if isinstance(contenido, dict) and "headers" in contenido and "rows" in contenido:
                        if len(contenido["rows"]) >= 1:  # Mínimo 1 fila (más flexible)
                            contenido_total += 50  # Valor mínimo para tablas
                            secciones_con_contenido += 1
                        else:
                            continue  # No fallar, solo no contar esta sección
                    else:
                        continue  # No fallar, solo no contar esta sección
        
        # Debe tener al menos 3 secciones con contenido y al menos 2000 caracteres totales (más flexible)
        return secciones_con_contenido >= 3 and contenido_total >= 2000

    def _generar_estructura_fallback(self, nombre_proyecto: str, cliente: str, fecha: str, costo_total: int, plazo: str, empresa_nombre: str) -> Dict[str, Any]:
        """Genera una estructura JSON de respaldo con el formato requerido"""
        return {
            "projectInfo": {
                "name": nombre_proyecto,
                "client": cliente,
                "date": fecha,
                "totalCost": costo_total,
                "timeline": plazo
            },
            "sections": [
                {
                    "id": "1",
                    "title": "Resumen Ejecutivo",
                    "type": "text",
                    "content": f"La presente propuesta responde a la necesidad de {cliente} de contar con un servicio especializado para el desarrollo e implementación de un sistema tecnológico integral, que permita optimizar sus procesos de manera sistemática, integrada y basada en datos.\n\nEsta solución tiene por objetivo fortalecer los procesos institucionales, entregando herramientas tecnológicas que contribuyan a la mejora continua de la calidad operacional. La propuesta contempla el diseño e implementación de una plataforma web alojada en la nube, desarrollada bajo un enfoque modular que incluye funcionalidades clave como: gestión de usuarios y permisos, evaluación y seguimiento de procesos, visualización de indicadores clave a través de un panel de control, e integración bidireccional con sistemas existentes.",
                    "pageBreak": True
                },
                {
                    "id": "2",
                    "title": "Alcance del Servicio",
                    "type": "list",
                    "content": [
                        "Desarrollar una plataforma web alojada en la nube, moderna, segura e inclusiva, accesible desde distintos dispositivos y escalable",
                        "Diseñar e implementar mecanismos de gestión y reporte de procesos, aplicables a distintos niveles organizacionales",
                        "Incorporar un sistema flexible de creación, gestión y aplicación de configuraciones, ajustado a los criterios institucionales",
                        "Proporcionar funcionalidades de acceso personalizado para distintos perfiles de usuarios",
                        "Facilitar la gestión mediante una interfaz intuitiva que fomente la eficiencia operacional",
                        "Generar reportes analíticos y visualizaciones de indicadores clave de desempeño",
                        "Permitir la incorporación de ajustes funcionales y mejoras en el sistema sin interrupciones de servicio"
                    ]
                },
                {
                    "id": "3",
                    "title": "Funcionalidades Clave del Sistema",
                    "type": "text",
                    "content": "El sistema considera los siguientes módulos principales:\n\n• Gestor de Usuarios: Módulo en el cual el usuario Administrador podrá crear, editar, organizar y actualizar perfiles de usuarios que operan en la institución. Estos perfiles estarán alineados al modelo organizacional del cliente y podrán configurarse según niveles jerárquicos, departamentos, sedes y campus.\n\n• Gestor de Configuraciones: Módulo en el cual el usuario Administrador podrá crear, agregar, modificar y/o eliminar las distintas configuraciones del sistema para cada funcionalidad, en cada uno de sus niveles operacionales.\n\n• Módulo de Gestión y Seguimiento: Módulo en el cual tanto los usuarios finales como los supervisores podrán realizar procesos de gestión y seguimiento.\n\n• Panel de Control y Reportería Avanzada: Módulo central de gestión estratégica donde el Administrador podrá monitorear el uso del sistema, analizar indicadores clave de desempeño y generar reportes personalizados.",
                    "pageBreak": True
                },
                {
                    "id": "4",
                    "title": "Tipos de Usuarios y Permisos",
                    "type": "table",
                    "content": {
                        "headers": ["Perfil de Usuario", "Descripción", "Permisos Principales"],
                        "rows": [
                            ["Administrador", "Equipo de gestión institucional, dirección o soporte TI", "Crear/editar usuarios, gestionar configuraciones, configurar calendarios, supervisar uso del sistema"],
                            ["Supervisor", "Personal con responsabilidad sobre coordinación de procesos", "Visualizar resultados por área, participar en evaluaciones, validar procesos, acceder a reportes"],
                            ["Usuario Final", "Personal regular de la institución", "Acceder a funcionalidades definidas, realizar gestiones, visualizar historial, recibir retroalimentación"]
                        ]
                    }
                },
                {
                    "id": "5",
                    "title": "Infraestructura Tecnológica",
                    "type": "text",
                    "content": "La solución propuesta contempla una infraestructura tecnológica moderna, escalable y segura:\n\n• Backend: Framework Django sobre Python, permitiendo una arquitectura robusta, modular y fácilmente integrable con sistemas existentes.\n\n• Frontend: Desarrollo basado en React con TypeScript, utilizado para la construcción de interfaces de usuario dinámicas, interactivas y reutilizables.\n\n• Base de Datos: Uso combinado de PostgreSQL (para datos estructurados relacionales) y MongoDB (para datos semiestructurados).\n\n• Infraestructura: Implementación sobre servidores Linux utilizando contenedores con Docker y orquestación a través de Kubernetes.\n\n• Integraciones: API RESTful para integración bidireccional con sistemas existentes, autenticación unificada con Microsoft EntraID o sistemas similares.",
                    "pageBreak": True
                },
                {
                    "id": "6",
                    "title": "Equipo de Trabajo Asignado",
                    "type": "table",
                    "content": {
                        "headers": ["Rol", "Responsabilidades Principales", "Experiencia Requerida"],
                        "rows": [
                            ["Project Manager", "Planificación, coordinación y control del proyecto. Interacción directa con el equipo del cliente", "Más de 10 años en gestión de proyectos tecnológicos"],
                            ["Tech Lead / Arquitecto", "Define la arquitectura del sistema, estándares técnicos y lineamientos de integración", "Experiencia en arquitecturas de sistemas empresariales"],
                            ["Front-End Developer", "Desarrolla la interfaz de usuario según principios de usabilidad y accesibilidad", "React, TypeScript, diseño responsive"],
                            ["Back-End Developer", "Desarrolla la lógica de negocio, APIs RESTful y control de flujos de datos", "Django, Python, APIs RESTful"],
                            ["UX/UI Designer", "Diseña la experiencia y la interfaz de usuario, intuitiva e inclusiva", "Diseño centrado en usuario, accesibilidad"],
                            ["QA / Tester Funcional", "Diseña y ejecuta pruebas automatizadas y manuales", "Testing automatizado, casos de uso empresariales"],
                            ["DevSecOps", "Gestiona entornos en la nube, automatiza despliegues, configura monitoreo", "Docker, Kubernetes, AWS/Azure"]
                        ]
                    }
                },
                {
                    "id": "7",
                    "title": "Metodología de Implementación",
                    "type": "text",
                    "content": "La implementación se realizará bajo la modalidad \"llave en mano\", utilizando un enfoque metodológico basado en Disciplined Agile del PMI:\n\nFase 1 - Inception (1 mes):\n• Refinamiento del alcance y visión del producto\n• Consolidación del equipo multidisciplinario\n• Consolidación de la arquitectura técnica\n• Confirmación del backlog inicial y priorización de requisitos\n\nFase 2 - Construction (3 meses):\n• Desarrollo incremental de los módulos\n• Iteraciones cortas (1-2 semanas) con demostraciones frecuentes\n• Implementación progresiva de las integraciones\n• Pruebas técnicas continuas\n\nFase 3 - Transition (1 mes):\n• Pruebas finales y transferencia tecnológica\n• Capacitación de personal técnico\n• Despliegue en producción\n• Activación de plan de soporte",
                    "pageBreak": True
                },
                {
                    "id": "8",
                    "title": "Garantías y Soporte Post-implementación",
                    "type": "text",
                    "content": f"{empresa_nombre} ofrece una política de garantía y soporte post-implementación que asegura la continuidad operativa del sistema:\n\nGarantía Técnica (6 meses):\n• Corrección sin costo de errores funcionales, bugs o defectos atribuibles al código fuente\n• Corrección de errores de configuración en los entornos implementados\n• Revisión y ajuste de integraciones con sistemas institucionales\n• Actualización de la documentación técnica cuando se aplique alguna corrección\n\nSoporte Acompañado:\n• Resolución de consultas operativas y funcionales para usuarios autorizados\n• Acompañamiento en el monitoreo de integraciones y flujos críticos\n• Aplicación de ajustes menores de configuración\n• Participación en reuniones técnicas mensuales\n\nClasificación de Incidencias:\n• Nivel 1 (Crítico): 2 horas hábiles de respuesta\n• Nivel 2 (Medio): 8 horas hábiles de respuesta\n• Nivel 3 (Leve): 24 horas hábiles de respuesta"
                },
                {
                    "id": "9",
                    "title": "Plan de Capacitación",
                    "type": "list",
                    "content": [
                        "Capacitación funcional: 6 horas distribuidas en 2 a 3 sesiones según perfil",
                        "Capacitación técnica (TI): 6 a 8 horas distribuidas en sesiones especializadas",
                        "Acompañamiento supervisado: 4 semanas posteriores a la puesta en marcha",
                        "Acceso permanente a materiales asincrónicos",
                        "Manuales de usuario diferenciados por perfil",
                        "Cápsulas de video por funcionalidad clave (2 a 5 minutos)",
                        "Documentación técnica estructurada",
                        "Entorno de prueba (sandbox) disponible por 30 días",
                        "Preguntas frecuentes (FAQ) actualizadas"
                    ]
                },
                {
                    "id": "10",
                    "title": "Experiencia y Referencias",
                    "type": "text",
                    "content": f"{empresa_nombre} cuenta con más de 20 años de experiencia en desarrollo de productos digitales, con presencia en Latinoamérica y Europa. Experiencia relevante en el sector empresarial:\n\n• Pontificia Universidad Católica de Chile: Plataforma de Evaluación de Madurez en Gestión TI\n• Universidad Santo Tomás: Plataforma administrativa con hiperautomatización\n• Universidad Alberto Hurtado: Plataforma administrativa con hiperautomatización\n• Universidad de Las Américas: Plataforma para apoyo a personas con discapacidad cognitiva\n• Bomberos de Chile: Apoyo integral a la Academia Nacional de Bomberos\n\nEl equipo cuenta con especialistas en tecnologías empresariales, desarrolladores full-stack, arquitectos de software, y especialistas en experiencia de usuario. Se posee una sólida trayectoria en el diseño e implementación de soluciones para instituciones públicas y privadas en Chile y Latinoamérica.",
                    "pageBreak": True
                },
                {
                    "id": "11",
                    "title": "Factores Clave para el Éxito",
                    "type": "list",
                    "content": [
                        "Coordinación y ejecución de entrevistas y focus groups con participación activa del cliente",
                        "Disponibilidad de APIs y sistemas existentes dentro de los plazos definidos",
                        "Documentación clara de APIs, ambientes de prueba y autenticación segura",
                        "Ambientes estables para QA y producción desde etapas tempranas",
                        "Dedicación de colaboradores clave del cliente para validación y ejecución",
                        "Gestión de licencias de software, hardware especializado o insumos específicos por parte del cliente",
                        "Cumplimiento normativo y alineación con regulaciones vigentes en Chile"
                    ]
                },
                {
                    "id": "12",
                    "title": "Cronograma Detallado del Proyecto",
                    "type": "table",
                    "content": {
                        "headers": ["Etapa", "Duración", "Actividades Principales", "Entregables"],
                        "rows": [
                            ["Inception", "1 mes", "Definición de requerimientos, análisis preliminar, identificación de actores", "Documento de especificación detallado y roadmap del proyecto"],
                            ["Construction", "3 meses", "Desarrollo iterativo-incremental de módulos, integraciones críticas", "Versiones funcionales incrementales de la plataforma"],
                            ["Transition", "1 mes", "Pruebas finales, transferencia tecnológica, capacitación, despliegue", "Solución operativa en ambiente del cliente"]
                        ]
                    }
                },
                {
                    "id": "13",
                    "title": "Inversión y Condiciones de Pago",
                    "type": "text",
                    "content": f"Costo Total del Proyecto: ${costo_total:,} (pesos chilenos)\n\nDesglose de Costos:\n• Desarrollo de plataforma web: ${int(costo_total * 0.71):,}\n• Integraciones con sistemas institucionales: ${int(costo_total * 0.18):,}\n• Capacitación y transferencia tecnológica: ${int(costo_total * 0.07):,}\n• Documentación y soporte inicial: ${int(costo_total * 0.04):,}\n\nCondiciones de Pago:\n• 30% al inicio del proyecto (firma de contrato)\n• 40% al completar la Fase de Construction\n• 30% al completar la Fase de Transition y aceptación del sistema\n\nGarantías Incluidas:\n• Garantía técnica por 6 meses\n• Soporte post-implementación por 6 meses\n• Actualizaciones de seguridad gratuitas\n• Capacitación completa del equipo técnico"
                }
            ],
            "styling": {
                "primaryColor": "#2563eb",
                "secondaryColor": "#1e40af",
                "fontFamily": "Arial, sans-serif"
            }
        }

    def _analizar_licitaciones_detallado(self, licitaciones: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Analiza detalladamente las licitaciones para entender el proyecto"""
        print("🔍 Analizando licitaciones para entender el proyecto...")
        
        # Preparar contenido de todas las licitaciones con mejor estructura
        contenido_completo = ""
        for i, licitacion in enumerate(licitaciones, 1):
            contenido_completo += f"\n=== LICITACIÓN {i}: {licitacion['archivo']} ===\n"
            
            # Agregar contenido por secciones
            for seccion, contenido in licitacion['datos'].items():
                contenido_str = str(contenido)
                if contenido_str and len(contenido_str.strip()) > 10:
                    contenido_completo += f"\n--- SECCIÓN: {seccion} ---\n"
                    contenido_completo += f"{contenido_str}\n"
            
            contenido_completo += "=== FIN LICITACIÓN ===\n"
        
        # Si no hay contenido sustancial, usar fallback
        if len(contenido_completo.strip()) < 100:
            print("⚠️ Contenido insuficiente para análisis detallado")
            return self._analisis_fallback()
        
        prompt_analisis = f"""
        Eres un experto en análisis de licitaciones y propuestas técnicas. 
        Analiza DETALLADAMENTE las siguientes licitaciones y extrae TODA la información clave del proyecto.
        
        LICITACIONES A ANALIZAR:
        {contenido_completo}
        
        INSTRUCCIONES DETALLADAS:
        1. NOMBRE DEL CLIENTE: Busca en títulos, encabezados, referencias, headers, footers
        2. SECTOR: Identifica si es bancario, educativo, salud, retail, gobierno, etc.
        3. OBJETIVO PRINCIPAL: ¿Qué quiere lograr el cliente específicamente?
        4. ALCANCE: ¿Qué incluye y qué no incluye el proyecto?
        5. REQUISITOS TÉCNICOS: Tecnologías, plataformas, integraciones mencionadas
        6. TIPO DE SISTEMA: ¿Es web, móvil, desktop, híbrido, etc.?
        7. USUARIOS FINALES: ¿Quiénes usarán el sistema? (empleados, clientes, estudiantes, etc.)
        8. FUNCIONALIDADES: ¿Qué debe hacer el sistema específicamente?
        9. PLAZOS: Tiempos mencionados para desarrollo o implementación
        10. CRITERIOS DE EVALUACIÓN: ¿Cómo se evaluará la propuesta?
        11. CONTEXTO: ¿Por qué necesita esta solución? ¿Qué problema resuelve?
        12. PRESUPUESTO: ¿Hay información sobre costos o presupuesto?
        13. INTEGRACIONES: ¿Con qué sistemas debe integrarse?
        14. SEGURIDAD: ¿Hay requisitos específicos de seguridad?
        15. CAPACITACIÓN: ¿Se requiere capacitación o transferencia de conocimiento?
        
        Devuelve un JSON con la siguiente estructura:
        {{
            "nombre_cliente": "Nombre específico del cliente (ej: Banco Santander, Universidad de Chile, Hospital Regional)",
            "sector": "Sector específico (ej: bancario, educativo, salud, retail, gobierno)",
            "objetivo_principal": "Descripción clara y específica del objetivo del proyecto",
            "alcance": "Alcance detallado del proyecto, qué incluye y qué no",
            "requisitos_tecnicos": ["Lista detallada de requisitos técnicos"],
            "tipo_sistema": "Tipo de sistema o solución requerida",
            "usuarios_finales": ["Lista específica de usuarios finales del sector"],
            "funcionalidades_especificas": ["Lista detallada de funcionalidades requeridas"],
            "plazos": "Plazos específicos mencionados",
            "criterios_evaluacion": ["Criterios de evaluación identificados"],
            "contexto_proyecto": "Contexto detallado: por qué el cliente necesita esta solución",
            "presupuesto": "Información sobre presupuesto si está disponible",
            "integraciones": ["Sistemas con los que debe integrarse"],
            "requisitos_seguridad": ["Requisitos de seguridad específicos"],
            "capacitacion": "Requisitos de capacitación o transferencia de conocimiento",
            "resumen_proyecto": "Resumen ejecutivo completo del proyecto incluyendo cliente, sector y objetivo"
        }}
        
        IMPORTANTE: 
        - Busca EXHAUSTIVAMENTE el nombre del cliente en todo el documento
        - Identifica el sector basándote en el contexto y terminología específica
        - Analiza CADA SECCIÓN de cada licitación para extraer información
        - Si no encuentras información específica, infiere basándote en el contexto
        - Sé ESPECÍFICO y DETALLADO en cada campo
        - Incluye TODA la información técnica relevante encontrada
        - Menciona funcionalidades específicas del sector identificado
        """
        
        try:
            response = self.client.chat.completions.create(
                model=self.modelo_backend,
                messages=[
                    {"role": "system", "content": "Eres un experto en análisis de licitaciones y propuestas técnicas. Tu tarea es analizar detalladamente las licitaciones y extraer toda la información clave del proyecto."},
                    {"role": "user", "content": prompt_analisis}
                ],
                max_tokens=2000,
                temperature=0.3
            )
            
            contenido = response.choices[0].message.content
            json_str = self._extraer_json(contenido)
            analisis = json.loads(json_str)
            
            print(f"✅ Análisis completado: {analisis.get('objetivo_principal', 'N/A')[:100]}...")
            return analisis
            
        except Exception as e:
            print(f"⚠️ Error en análisis detallado: {e}")
            return self._analisis_fallback()

    def _analisis_fallback(self) -> Dict[str, Any]:
        """Análisis de fallback cuando no se puede hacer análisis detallado"""
        return {
            "nombre_cliente": "Cliente",
            "sector": "Tecnología",
            "objetivo_principal": "Desarrollo de sistema tecnológico",
            "alcance": "Implementación de solución integral",
            "requisitos_tecnicos": ["Sistema web", "Base de datos", "Interfaz de usuario"],
            "tipo_sistema": "Sistema web",
            "usuarios_finales": ["Usuarios finales"],
            "funcionalidades_especificas": ["Gestión de datos", "Reportes"],
            "plazos": "5 meses",
            "criterios_evaluacion": ["Calidad técnica", "Experiencia"],
            "contexto_proyecto": "Necesidad de modernización tecnológica",
            "presupuesto": "No especificado",
            "integraciones": ["Sistemas existentes"],
            "requisitos_seguridad": ["Estándares de seguridad"],
            "capacitacion": "Capacitación de usuarios",
            "resumen_proyecto": "Proyecto de desarrollo tecnológico"
        }

    def _crear_prompt_estructura_json_mejorado(self, licitaciones: List[Dict[str, Any]], analisis_proyecto: Dict[str, Any], empresa_nombre: str, empresa_descripcion: str, nombre_proyecto: str, cliente: str, fecha: str, costo_total: int, plazo: str) -> str:
        """Crea un prompt mejorado con análisis previo del proyecto"""
        
        # Preparar información de las licitaciones
        info_licitaciones = "LICITACIONES A ANALIZAR:\n"
        for i, licitacion in enumerate(licitaciones, 1):
            info_licitaciones += f"\n--- LICITACIÓN {i}: {licitacion['archivo']} ---\n"
            for seccion, contenido in licitacion['datos'].items():
                if contenido:
                    info_licitaciones += f"{seccion}: {str(contenido)[:300]}...\n"
            info_licitaciones += "---\n"

        return (
            "Eres un experto en generación de ofertas técnicas para GUX Technologies. "
            "Debes generar una oferta técnica en formato JSON EXACTO con la siguiente estructura:\n\n"
            "{\n"
            '   "projectInfo": {\n'
            '      "name": "Nombre del Proyecto",\n'
            '      "client": "Nombre del Cliente",\n'
            '      "date": "Fecha",\n'
            '      "totalCost": 45000000,\n'
            '      "timeline": "5 meses"\n'
            "   },\n"
            '   "sections": [\n'
            "      {\n"
            '         "id": "1",\n'
            '         "title": "Resumen Ejecutivo",\n'
            '         "type": "text",\n'
            '         "content": "Contenido detallado...",\n'
            '         "pageBreak": true\n'
            "      }\n"
            "   ],\n"
            '   "styling": {\n'
            '      "primaryColor": "#2563eb",\n'
            '      "secondaryColor": "#1e40af",\n'
            '      "fontFamily": "Arial, sans-serif"\n'
            "   }\n"
            "}\n\n"
            "ANÁLISIS PREVIO DEL PROYECTO:\n"
            f"• Cliente: {analisis_proyecto.get('nombre_cliente', 'N/A')}\n"
            f"• Sector: {analisis_proyecto.get('sector', 'N/A')}\n"
            f"• Objetivo Principal: {analisis_proyecto.get('objetivo_principal', 'N/A')}\n"
            f"• Alcance: {analisis_proyecto.get('alcance', 'N/A')}\n"
            f"• Tipo de Sistema: {analisis_proyecto.get('tipo_sistema', 'N/A')}\n"
            f"• Usuarios Finales: {', '.join(analisis_proyecto.get('usuarios_finales', []))}\n"
            f"• Funcionalidades Específicas: {', '.join(analisis_proyecto.get('funcionalidades_especificas', []))}\n"
            f"• Requisitos Técnicos: {', '.join(analisis_proyecto.get('requisitos_tecnicos', []))}\n"
            f"• Contexto del Proyecto: {analisis_proyecto.get('contexto_proyecto', 'N/A')}\n"
            f"• Resumen del Proyecto: {analisis_proyecto.get('resumen_proyecto', 'N/A')}\n\n"
            "TIPOS DE CONTENIDO:\n"
            "- 'text': Para párrafos largos de texto (mínimo 500 caracteres por sección)\n"
            "- 'list': Para listas de elementos (array de strings, mínimo 5 elementos)\n"
            "- 'table': Para tablas con headers y rows (mínimo 3 filas)\n\n"
            "SECCIONES OBLIGATORIAS CON CONTENIDO DETALLADO:\n"
            "1. Resumen Ejecutivo (text, pageBreak: true) - Mínimo 800 caracteres\n"
            "2. Alcance del Servicio (list) - Mínimo 7 elementos detallados\n"
            "3. Funcionalidades Clave del Sistema (text, pageBreak: true) - Mínimo 1000 caracteres\n"
            "4. Tipos de Usuarios y Permisos (table) - Mínimo 3 filas con 3 columnas\n"
            "5. Infraestructura Tecnológica (text, pageBreak: true) - Mínimo 800 caracteres\n"
            "6. Equipo de Trabajo Asignado (table) - Mínimo 6 filas con roles detallados\n"
            "7. Metodología de Implementación (text, pageBreak: true) - Mínimo 1000 caracteres\n"
            "8. Garantías y Soporte Post-implementación (text) - Mínimo 800 caracteres\n"
            "9. Plan de Capacitación (list) - Mínimo 8 elementos\n"
            "10. Experiencia y Referencias (text, pageBreak: true) - Mínimo 800 caracteres\n"
            "11. Factores Clave para el Éxito (list) - Mínimo 6 elementos\n"
            "12. Cronograma Detallado del Proyecto (table) - Mínimo 3 filas con etapas\n"
            "13. Inversión y Condiciones de Pago (text) - Mínimo 600 caracteres\n\n"
            "REQUISITOS ESPECÍFICOS:\n"
            "- El Resumen Ejecutivo debe mencionar específicamente el CLIENTE y su SECTOR\n"
            "- El Resumen Ejecutivo debe explicar claramente el objetivo del proyecto analizado\n"
            "- Las Funcionalidades Clave deben describir específicamente las funcionalidades identificadas en las licitaciones\n"
            "- El Alcance del Servicio debe basarse en el alcance real identificado\n"
            "- Personalizar TODO el contenido para el CLIENTE ESPECÍFICO y su SECTOR\n"
            "- Usar la información técnica específica identificada\n"
            "- Incluir detalles sobre usuarios finales específicos del sector\n"
            "- Mencionar el contexto y por qué el cliente necesita esta solución\n\n"
            f"INFORMACIÓN DEL PROYECTO:\n"
            f"- Nombre: {nombre_proyecto}\n"
            f"- Cliente: {cliente}\n"
            f"- Fecha: {fecha}\n"
            f"- Costo Total: ${costo_total:,}\n"
            f"- Plazo: {plazo}\n"
            f"- Empresa: {empresa_nombre}\n"
            f"- Descripción: {empresa_descripcion}\n\n"
            f"{info_licitaciones}\n"
            "INSTRUCCIONES ESPECÍFICAS:\n"
            "1. Usa el análisis previo para entender EXACTAMENTE el proyecto\n"
            "2. Genera contenido ESPECÍFICO y RELEVANTE para el proyecto analizado\n"
            "3. Personaliza cada sección con la información real de las licitaciones\n"
            "4. Asegúrate de que las Funcionalidades Clave describan el sistema real requerido\n"
            "5. Usa el formato JSON exacto especificado\n"
            "6. Incluye TODAS las secciones obligatorias con contenido sustancial\n"
            "7. Genera contenido ORIGINAL y PROFESIONAL\n"
            "8. Cada sección debe tener al menos el mínimo de caracteres especificado\n\n"
            "IMPORTANTE: El contenido debe ser ESPECÍFICO para el proyecto analizado, no genérico."
        )

    def _mejorar_secciones_especificas(self, respuesta_json: Dict[str, Any], analisis_proyecto: Dict[str, Any], licitaciones: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Mejora secciones específicas con análisis adicional"""
        print("🔧 Mejorando secciones específicas...")
        
        # Mejorar Resumen Ejecutivo
        if "sections" in respuesta_json:
            for seccion in respuesta_json["sections"]:
                if seccion["title"] == "Resumen Ejecutivo" and seccion["type"] == "text":
                    seccion["content"] = self._mejorar_resumen_ejecutivo(seccion["content"], analisis_proyecto)
                
                elif seccion["title"] == "Funcionalidades Clave del Sistema" and seccion["type"] == "text":
                    seccion["content"] = self._mejorar_funcionalidades_clave(seccion["content"], analisis_proyecto, licitaciones)
                
                elif seccion["title"] == "Alcance del Servicio" and seccion["type"] == "list":
                    seccion["content"] = self._mejorar_alcance_servicio(seccion["content"], analisis_proyecto)
        
        return respuesta_json

    def _mejorar_resumen_ejecutivo(self, contenido_actual: str, analisis_proyecto: Dict[str, Any]) -> str:
        """Mejora el resumen ejecutivo con información específica del proyecto"""
        prompt = f"""
        Mejora el siguiente resumen ejecutivo para que sea más específico y relevante al proyecto analizado.
        
        ANÁLISIS DEL PROYECTO:
        • Cliente: {analisis_proyecto.get('nombre_cliente', 'N/A')}
        • Sector: {analisis_proyecto.get('sector', 'N/A')}
        • Objetivo: {analisis_proyecto.get('objetivo_principal', 'N/A')}
        • Alcance: {analisis_proyecto.get('alcance', 'N/A')}
        • Tipo de Sistema: {analisis_proyecto.get('tipo_sistema', 'N/A')}
        • Usuarios: {', '.join(analisis_proyecto.get('usuarios_finales', []))}
        • Contexto: {analisis_proyecto.get('contexto_proyecto', 'N/A')}
        
        RESUMEN ACTUAL:
        {contenido_actual}
        
        INSTRUCCIONES:
        1. Mantén la estructura profesional
        2. MENCIONA ESPECÍFICAMENTE el nombre del CLIENTE en el primer párrafo
        3. MENCIONA el SECTOR específico (bancario, educativo, salud, etc.)
        4. Incluye específicamente el objetivo del proyecto analizado
        5. Menciona el tipo de sistema y sector específicos
        6. Incluye información sobre usuarios finales específicos del sector
        7. Explica por qué el cliente necesita esta solución
        8. Haz el contenido más específico y menos genérico
        9. Mantén al menos 800 caracteres
        
        IMPORTANTE: El primer párrafo debe mencionar claramente el cliente y su sector.
        
        Devuelve SOLO el texto mejorado, sin explicaciones adicionales.
        """
        
        try:
            response = self.client.chat.completions.create(
                model=self.modelo_backend,
                messages=[
                    {"role": "system", "content": "Eres un experto en redacción de propuestas técnicas. Mejora el contenido para que sea específico y relevante."},
                    {"role": "user", "content": prompt}
                ],
                max_tokens=1000,
                temperature=0.3
            )
            
            return response.choices[0].message.content.strip()
        except Exception as e:
            print(f"⚠️ Error mejorando resumen ejecutivo: {e}")
            return contenido_actual

    def _mejorar_funcionalidades_clave(self, contenido_actual: str, analisis_proyecto: Dict[str, Any], licitaciones: List[Dict[str, Any]]) -> str:
        """Mejora las funcionalidades clave con información específica del proyecto"""
        
        # Preparar información específica de las licitaciones
        info_especifica = ""
        for licitacion in licitaciones:
            for seccion, contenido in licitacion['datos'].items():
                if any(palabra in seccion.upper() for palabra in ['FUNCIONALIDAD', 'REQUISITO', 'CARACTERÍSTICA', 'MÓDULO']):
                    info_especifica += f"{seccion}: {contenido}\n"
        
        prompt = f"""
        Mejora la sección de Funcionalidades Clave del Sistema para que describa específicamente las funcionalidades requeridas en el proyecto analizado.
        
        ANÁLISIS DEL PROYECTO:
        • Cliente: {analisis_proyecto.get('nombre_cliente', 'N/A')}
        • Sector: {analisis_proyecto.get('sector', 'N/A')}
        • Objetivo: {analisis_proyecto.get('objetivo_principal', 'N/A')}
        • Tipo de Sistema: {analisis_proyecto.get('tipo_sistema', 'N/A')}
        • Funcionalidades Identificadas: {', '.join(analisis_proyecto.get('funcionalidades_especificas', []))}
        • Requisitos Técnicos: {', '.join(analisis_proyecto.get('requisitos_tecnicos', []))}
        
        INFORMACIÓN ESPECÍFICA DE LAS LICITACIONES:
        {info_especifica}
        
        CONTENIDO ACTUAL:
        {contenido_actual}
        
        INSTRUCCIONES:
        1. MENCIONA el CLIENTE y su SECTOR en la introducción
        2. Describe específicamente las funcionalidades identificadas en las licitaciones
        3. Incluye módulos específicos del sistema requerido para el sector
        4. Menciona características técnicas específicas
        5. Relaciona las funcionalidades con el objetivo del proyecto y el sector
        6. Haz el contenido más específico y menos genérico
        7. Mantén al menos 1000 caracteres
        8. Usa la información técnica específica identificada
        9. Adapta las funcionalidades al contexto del sector del cliente
        
        IMPORTANTE: El contenido debe ser específico para el cliente y su sector.
        
        Devuelve SOLO el texto mejorado, sin explicaciones adicionales.
        """
        
        try:
            response = self.client.chat.completions.create(
                model=self.modelo_backend,
                messages=[
                    {"role": "system", "content": "Eres un experto en análisis de sistemas y funcionalidades. Describe específicamente las funcionalidades requeridas."},
                    {"role": "user", "content": prompt}
                ],
                max_tokens=1500,
                temperature=0.3
            )
            
            return response.choices[0].message.content.strip()
        except Exception as e:
            print(f"⚠️ Error mejorando funcionalidades clave: {e}")
            return contenido_actual

    def _mejorar_alcance_servicio(self, contenido_actual: list, analisis_proyecto: Dict[str, Any]) -> list:
        """Mejora el alcance del servicio con información específica del proyecto"""
        
        prompt = f"""
        Mejora la lista del Alcance del Servicio para que sea específica al proyecto analizado.
        
        ANÁLISIS DEL PROYECTO:
        • Cliente: {analisis_proyecto.get('nombre_cliente', 'N/A')}
        • Sector: {analisis_proyecto.get('sector', 'N/A')}
        • Objetivo: {analisis_proyecto.get('objetivo_principal', 'N/A')}
        • Alcance: {analisis_proyecto.get('alcance', 'N/A')}
        • Tipo de Sistema: {analisis_proyecto.get('tipo_sistema', 'N/A')}
        • Usuarios Finales: {', '.join(analisis_proyecto.get('usuarios_finales', []))}
        
        ALCANCE ACTUAL:
        {contenido_actual}
        
        INSTRUCCIONES:
        1. Personaliza cada elemento para el CLIENTE ESPECÍFICO y su SECTOR
        2. Incluye detalles específicos del alcance identificado
        3. Menciona usuarios finales específicos del sector
        4. Incluye requisitos técnicos específicos
        5. Haz el contenido más específico y menos genérico
        6. Mantén al menos 7 elementos
        7. Usa la información específica del proyecto analizado
        8. Adapta el alcance al contexto del sector del cliente
        
        IMPORTANTE: Cada elemento debe ser específico para el cliente y su sector.
        
        Devuelve SOLO la lista mejorada en formato JSON array, sin explicaciones adicionales.
        """
        
        try:
            response = self.client.chat.completions.create(
                model=self.modelo_backend,
                messages=[
                    {"role": "system", "content": "Eres un experto en definición de alcances de proyectos. Personaliza el alcance para proyectos específicos."},
                    {"role": "user", "content": prompt}
                ],
                max_tokens=800,
                temperature=0.3
            )
            
            contenido = response.choices[0].message.content.strip()
            # Extraer la lista del JSON
            import re
            match = re.search(r'\[.*\]', contenido, re.DOTALL)
            if match:
                return json.loads(match.group(0))
            else:
                return contenido_actual
                
        except Exception as e:
            print(f"⚠️ Error mejorando alcance del servicio: {e}")
            return contenido_actual

    def _extraer_json(self, texto: str) -> str:
        """Extrae el primer bloque JSON de un texto"""
        import re
        match = re.search(r'\{[\s\S]*\}', texto)
        if match:
            return match.group(0)
        raise ValueError("No se encontró JSON en la respuesta de la IA") 