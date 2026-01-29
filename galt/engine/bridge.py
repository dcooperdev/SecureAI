import os
import json
import time
import logging
from google import genai
from google.api_core import exceptions
from dotenv import load_dotenv
from galt.core.config import LLM_MODEL

# Configurar logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class Bridge:
    def __init__(self, data_dir=None):
        load_dotenv()
        self.api_key = os.getenv("GOOGLE_API_KEY")
        # Por defecto usar vault/ o galt/data/
        self.data_dir = data_dir or os.path.join(os.getcwd(), "vault")
        if not os.path.exists(self.data_dir):
            os.makedirs(self.data_dir)
            
        self.state_file = os.path.join(self.data_dir, "last_scan_state.json")
        self.client = None
        if self.api_key:
            try:
                self.client = genai.Client(api_key=self.api_key)
            except Exception as e:
                logger.error(f"Error inicializando Gemini Client: {e}")

    def _clean_for_comparison(self, data):
        """
        Limpia los datos para la comparación (Diff), eliminando timestamps
        y campos que cambian en cada ejecución sin afectar la seguridad.
        """
        if isinstance(data, list):
            return [self._clean_for_comparison(item) for item in data]
        elif isinstance(data, dict):
            new_dict = {}
            for k, v in data.items():
                # Ignorar campos de tiempo o IDs únicos efímeros
                if k in ["timestamp", "time", "date", "scan_id", "epoch", "ui_date_short", "ui_date_full", "pid"]:
                    continue
                new_dict[k] = self._clean_for_comparison(v)
            return new_dict
        else:
            return data

    def _load_state(self):
        if os.path.exists(self.state_file):
            try:
                with open(self.state_file, 'r', encoding='utf-8') as f:
                    return json.load(f)
            except Exception as e:
                logger.error(f"Error cargando estado anterior: {e}")
        return None

    def _save_state(self, findings, score, narrative):
        try:
            state = {
                "findings": findings,
                "score": score,
                "narrative": narrative,
                "timestamp": time.time()
            }
            with open(self.state_file, 'w', encoding='utf-8') as f:
                json.dump(state, f, ensure_ascii=False, indent=2)
        except Exception as e:
            logger.error(f"Error guardando estado: {e}")

    def get_analysis(self, current_findings, current_score):
        """
        Flujo principal:
        1. Carga estado anterior.
        2. Compara (Diff).
        3. Decide si llamar a AI o usar caché.
        4. Retorna resultado + metadata de estado.
        """
        last_state = self._load_state()
        
        # --- 1. Lógica de Comparación (Diff) ---
        has_changed = True
        improvement_msg = ""
        
        clean_current = self._clean_for_comparison(current_findings)
        
        if last_state:
            last_score = last_state.get("score", 0)
            clean_last = self._clean_for_comparison(last_state.get("findings", []))
            
            # Comparar exactitud de datos y score
            # Convertimos a string json ordenado para comparar estructuras complejas
            current_str = json.dumps(clean_current, sort_keys=True)
            last_str = json.dumps(clean_last, sort_keys=True)
            
            if current_str == last_str and current_score == last_score:
                has_changed = False
            
            # Detectar mejora
            if current_score > last_score:
                improvement_msg = f"El usuario mejoró su seguridad (Score subió de {last_score} a {current_score}). Identifica qué cambió y felicítalo explicando el beneficio."

        # --- 2. Decision Making ---
        
        # CASO A: Cache Hit
        if not has_changed and last_state and last_state.get("narrative"):
            logger.info("Smart Cache: Sin cambios detectados. Reutilizando narrativa.")
            return {
                "markdown": last_state["narrative"],
                "ai_status": "cached", # 🟠 IA Cached (usaremos 'cached' para UI)
                "score": current_score,
                "used_cache": True
            }

        # CASO B: Cambios o Cache Miss -> Llamar a IA
        logger.info(f"Cambios detectados (Changed={has_changed}, Improvement={bool(improvement_msg)}). Solicitando análisis a Gemini...")
        
        prompt_context = "Analiza estos hallazgos de seguridad."
        if improvement_msg:
            prompt_context += f"\n\nNOTA DE CONTEXTO: {improvement_msg}"
        elif last_state:
            prompt_context += f"Cambios detectados respecto al escaneo anterior."

        try:
            if not self.client:
                raise ValueError("Cliente Gemini no inicializado (Falta API Key)")

            response = self._call_gemini(clean_current, current_score, prompt_context)
            narrative = response
            
            # Guardar nuevo estado
            self._save_state(current_findings, current_score, narrative)
            
            return {
                "markdown": narrative,
                "ai_status": "online", # 🟢 IA Online
                "score": current_score,
                "used_cache": False
            }

        except Exception as e:
            logger.error(f"Fallo en llamada a IA: {e}")
            # CASO C: Fallback / Error
            fallback_narrative = self._get_fallback_narrative(current_score, e)
            return {
                "markdown": fallback_narrative,
                "ai_status": "offline", # 🔴 IA No Disponible

                "score": current_score,
                "error": str(e)
            }

    def _call_gemini(self, findings, score, context_msg):
        # Sistema de Prompting
        system_prompt = f"""
        Eres Galt.ai, un CISO Virtual para PyMEs.
        Tu misión es traducir datos técnicos JSON a consejos de negocio en ESPAÑOL.
        
        SCORE ACTUAL: {score}/100
        
        REGLAS:
        1. Tono: Profesional, directo y accesible. Evita jerga innecesaria.
        2. Prioridad: Enfócate en Dinero (Impacto financiero), Continuidad del Negocio y Privacidad.
        3. Formato: Usa Markdown robusto (negritas para énfasis, listas para pasos).
        4. Si el Score es bajo, sé urgente pero constructivo.
        5. {context_msg}
        """
        
        content = f"DATOS TÉCNICOS:\n{json.dumps(findings, indent=2)}"
        
        response = self.client.models.generate_content(
            model=LLM_MODEL,
            contents=system_prompt + "\n\n" + content
        )
        return response.text

    def _get_fallback_narrative(self, score, error=None):
        """
        Genera una narrativa offline basada en reglas estáticas en lugar de mostrar errores.
        """
        logger.warning(f"Generando narrativa offline. Razón: {error}")
        
        narrative = ""
        
        if score < 60:
            narrative = """
            ### ⚠️ MODO OFFLINE: Riesgos Críticos Detectados
            
            El sistema de IA no está disponible temporalmente, pero el análisis estático ha detectado **configuraciones peligrosas**.
            
            **ACCIONES INMEDIATAS RECOMENDADAS:**
            1. Revise los puertos abiertos (especialmente 445, 3389).
            2. Verifique si hay software obsoleto.
            3. Consulte la pestaña "Detalles Técnicos" para ver los hallazgos exactos.
            """
        elif score < 90:
            narrative = """
            ### 🟠 MODO OFFLINE: Riesgo Moderado
            
            El sistema opera con reglas locales. Se han detectado algunos problemas de configuración que reducen su nivel de seguridad.
            
            **Recomendación:**
            - Cierre puertos no utilizados.
            - Mantenga su firewall activo.
            """
        else:
            narrative = """
            ### ✅ MODO OFFLINE: Sistema Seguro
            
            Según las reglas estáticas locales, su sistema parece estar limpio y configurado correctamente.
            
            *La inteligencia artificial se reconectará automáticamente cuando esté disponible para un análisis más profundo.*
            """
            
        return narrative

if __name__ == "__main__":
    # Test rápido
    b = Bridge()
    print("Testing Bridge...")
    res = b.get_analysis([{"test": 1}], 80)
    print(res)
