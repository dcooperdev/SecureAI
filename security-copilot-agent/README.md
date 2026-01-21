# 🛡️ Galt.ai - CISO Virtual de Élite para PyMEs

> **Versión**: v2.0 Pro  
> **Estado**: Producción / Despliegue Crítico  
> **Descripción**: Plataforma de ciberseguridad autónoma "Agentic AI" diseñada para auditar, monitorear y mitigar riesgos en tiempo real en entornos Windows. Actúa como un CISO (Chief Information Security Officer) virtual las 24 horas del día.

---

## 🏗️ Arquitectura

Galt.ai opera bajo una arquitectura descentralizada de **Orquestador + Micro-Sensores**:

1.  **Micro-Sensores**: Scripts ligeros en Python (`sensor_*.py`) que se ejecutan de forma independiente para recolectar telemetría específica (red, procesos, vulnerabilidades).
2.  **Orquestador (`runner.py`)**: El cerebro del sistema. Ejecuta los sensores, agrega la data, realiza análisis de deriva ("Drift Analysis") y consulta a la IA (Gemini 2.5 Pro) para generar reportes estratégicos.
3.  **Bóveda (`/vault`)**: Sistema de persistencia local que almacena el estado de seguridad histórico para detectar cambios sutiles (puertos abiertos recientemente, nuevos procesos).

---

## 📋 Requisitos Previos

Antes de desplegar Galt.ai, asegúrese de cumplir con lo siguiente:

*   **Sistema Operativo**: Windows 10/11 o Windows Server (2016+).
*   **Python**: Versión 3.10 o superior instalada y agregada al PATH.
*   **Permisos**: Se requieren permisos de **Administrador** para que los sensores puedan realizar escaneos profundos de red (netstat) y procesos del sistema.
*   **Conectividad**: Acceso a Internet para consultar la API de Google Gemini.

---

## 🚀 Guía de Instalación

Siga estos pasos para desplegar el agente en menos de 2 minutos.

### 1. Clonar el Repositorio

```bash
git clone https://github.com/dcooperdev/Galt.ai.git
cd Galt.ai
```

### 2. Crear Entorno Virtual (Recomendado)

Aísla las dependencias del proyecto para evitar conflictos.

```bash
python -m venv venv
.\venv\Scripts\activate
```

### 3. Instalar Dependencias

```bash
pip install -r requirements.txt
```

---

## 🔑 Configuración del Entorno (.env)

**CRÍTICO**: Galt.ai requiere una clave de API válida de Google Gemini para funcionar. Esta configuración se gestiona a través de un archivo `.env` en la raíz del proyecto.

1.  Cree un archivo llamado `.env` en la carpeta principal (`f:\Projects\SecureIA\security-copilot-agent`).
2.  Obtenga su API Key gratuita en [Google AI Studio](https://aistudio.google.com/).
3.  Pegue el siguiente contenido en el archivo `.env`:

```ini
# --- Galt.ai Configuration ---

# API Key de Google Gemini (Requerido)
GOOGLE_API_KEY=tu_api_key_secreta_aqui

# Intervalo de escaneo para el modo Centinela (en segundos)
# 3600 = 1 hora.
SCAN_INTERVAL_SECONDS=3600

# Nivel de detalle de logs (DEBUG, INFO, WARNING, ERROR)
LOG_LEVEL=INFO
```

> **⚠️ NOTA DE SEGURIDAD**: Nunca suba el archivo `.env` al repositorio de control de versiones. Asegúrese de que `.env` esté incluido en su archivo `.gitignore`.

---

## 🎮 Guía de Uso

Galt.ai puede operar en dos modos principales:

### 1. Modo Manual (Auditoría Puntual)

Ejecute un escaneo completo bajo demanda. Ideal para revisiones diarias o respuesta a incidentes.

```bash
python runner.py
```

*   El sistema ejecutará todos los sensores.
*   Generará un reporte en la carpeta `/reports`.
*   Actualizará el estado de seguridad en `/vault`.

### 2. Modo Centinela (Monitoreo 24/7)

Inicia un proceso persistente que ejecuta auditorías periódicas automáticamente (definido por `SCAN_INTERVAL_SECONDS`).

```bash
python sentinel.py
```

### Estructura de Carpetas Clave

*   **`/reports`**: Aquí encontrará los informes ejecutivos en formato Markdown (`Galt_Report_YYYYMMDD_...md`).
*   **`/vault`**: Contiene `security_state.json` (último estado conocido) y `history_log.jsonl` (historial de eventos). **No elimine estos archivos**; son vitales para el Análisis de Deriva.

---

## 📡 Descripción de Sensores

Galt.ai v2 incluye un arsenal de sensores especializados:

| Sensor | Propósito | Telemetría Clave |
| :--- | :--- | :--- |
| **`sensor_procesos.py`** | **Inteligencia de Procesos** | Mapeo de puertos a PIDs, detección de procesos ocultos, monitoreo de conexiones salientes (C2). |
| **`sensor_network_discovery.py`** | **Reconocimiento de Red** | Escaneo de subred local, detección de "Sistemas Espejo" (vecinos con mismos puertos abiertos), Fingerprinting de servicios. |
| **`sensor_vulnerabilidades.py`** | **Análisis de Superficie** | Escaneo rápido de puertos críticos (445, 3389, 5432) y correlación básica de CVEs. |
| **`sensor_sistema.py`** | **Perfilado de Host** | Información del OS, versión de Kernel, usuario activo y uptime. |
| **`sensor_red.py`** | **Estado de Red Local** | Interfaces activas, IPs locales, Gateway y métricas de tráfico. |

---

## 🛠️ Solución de Problemas (Quick Wins)

*   **Error "AccessDenied" en procesos**: Asegúrese de correr la terminal como **Administrador**.
*   **Error 404/403 en API**: Verifique que su `GOOGLE_API_KEY` en el archivo `.env` sea correcta y tenga saldo/quota disponible.
*   **Reporte sin "Acciones"**: Galt.ai requiere contexto. Si el sistema es seguro, no sugerirá correcciones agresivas.

---

**© 2026 Galt.ai Security Division.** *La seguridad no es una característica, es un estado mental.*
