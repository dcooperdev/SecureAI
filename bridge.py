import os
import json
from google import genai
from dotenv import load_dotenv

# 1. Cargar .env y configurar
load_dotenv()

api_key = os.getenv("GOOGLE_API_KEY")

# The client gets the API key from the environment variable `GEMINI_API_KEY`.
client = genai.Client(api_key=api_key)

SYSTEM_PROMPT = """
Eres Galt.ai, un CISO Virtual para PyMEs.
Traduce datos técnicos JSON a consejos de negocio en ESPAÑOL.
Tono: Profesional y accesible. No uses tecnicismos.
Enfócate en: Dinero, Continuidad del Negocio y Privacidad.
Usa Markdown.
"""

# Datos de prueba
scan_results = [
    {"plugin": "net_scanner", "severity": "info", "impact_hint": "7 dispositivos detectados."},
    {"plugin": "system_scanner", "severity": "low", "impact_hint": "Windows 10 detectado."}
]

response = client.models.generate_content(
    model="gemini-2.5-flash-lite",
    contents=f"Analiza estos hallazgos y genera el reporte:\n\n{json.dumps(scan_results)}"
)

if __name__ == "__main__":
    print("🚀 Generando reporte de Galt.ai (v.Estable)...")
    print("\n" + "="*40 + "\n" + response.text + "\n" + "="*40)
