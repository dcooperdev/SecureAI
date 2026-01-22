# 🛡️ Galt.ai - CISO Virtual de Élite para PyMEs (Cross-Platform)

> **Versión**: v2.5 Universal
> **Estado**: Producción / Despliegue Crítico  
> **Soporte de OS**: Windows 10+, Linux (Debian/Ubuntu/CentOS), macOS
> **Descripción**: Plataforma de ciberseguridad autónoma "Agentic AI" diseñada para auditar, monitorear y mitigar riesgos en tiempo real. Actúa como un CISO (Chief Information Security Officer) virtual las 24 horas del día.

---

## 🏗️ Arquitectura Universal

Galt.ai opera bajo una arquitectura descentralizada de **Orquestador + Micro-Sensores** que se adapta nativamente al sistema operativo anfitrión:

1.  **Micro-Sensores Políglotas**: Scripts inteligentes (`sensor_procesos.py`, etc.) que detectan el OS y utilizan comandos nativos para máxima profundidad:
    *   **Windows**: Usa `netstat`, `tasklist`, `wmic`.
    *   **Linux**: Usa `ss`, `ip`, `ps`.
    *   **macOS**: Usa `lsof`, `ifconfig`, `ps`.
2.  **Orquestador (`runner.py`)**: El cerebro del sistema. Ejecuta los sensores en subprocesos aislados usando el intérprete correcto del sistema, agrega la data y consulta a la IA (Gemini 2.5 Pro).
3.  **Visualización Moderna**: Una nueva capa de presentación generaDashboards HTML oscuros e interactivos.
4.  **Bóveda (`/vault`)**: Sistema de persistencia local JSON.

---

## 📋 Requisitos Previos

*   **Python**: Versión 3.10 o superior.
*   **Permisos**: Se recomiendan permisos de **Administrador/Root** para una visibilidad completa de red (puertos listening, procesos de sistema).
*   **API Key**: Una clave válida de Google Gemini (AI Studio).

---

## 🚀 Guía de Instalación Rápida

Hemos simplificado el despliegue a un solo script para sistemas Unix (Linux/macOS) y mantenemos la simplicidad en Windows.

### 🐧 Linux y 🍎 macOS (Automático)

El nuevo instalador `install.sh` se encarga de todo: crea el entorno virtual, instala dependencias y configura tu API Key.

1.  **Ejecutar Instalador**:
    ```bash
    chmod +x install.sh
    ./install.sh
    ```
2.  Sigue las instrucciones en pantalla.

### 🪟 Windows (Manual)

1.  **Crear entorno virtual**:
    ```powershell
    python -m venv venv
    .\venv\Scripts\activate
    ```
2.  **Instalar dependencias**:
    ```powershell
    pip install -r requirements.txt
    ```
3.  **Configurar**: Al ejecutar el agente por primera vez, te pedirá tu API Key si no la encuentra.

---

## 🎮 Guía de Uso

Galt.ai ahora ofrece comandos directos (shortcuts) en Linux/macOS.

### 1. Modo Manual (Auditoría Puntual)

Ejecuta un escaneo completo, genera el Dashboard y actualiza la bóveda.

*   **Linux/macOS**:
    ```bash
    ./galt
    ```
*   **Windows**:
    ```powershell
    python runner.py
    ```

### 2. Modo Centinela (Vigilancia 24/7)

Monitoreo continuo en segundo plano. Solo te notifica si hay cambios drásticos en tu Score de seguridad ("Drift").

*   **Linux/macOS**:
    ```bash
    ./galt-sentinel
    ```
*   **Windows**:
    ```powershell
    python sentinel.py
    ```

### 3. Modo Silencioso (CI/CD)

Para integrar en scripts o cronjobs sin abrir el navegador automáticamente:

```bash
./galt --auto
# o
python runner.py --auto
```

---

## 📊 Nuevo Dashboard

Galt.ai ahora genera un **Dashboard Interactivo** después de cada escaneo:

*   **Ubicación**: `reports/dashboard.html`
*   **Características**:
    *   **Score en Tiempo Real**: Visualización gráfica de tu nivel de seguridad (0-100).
    *   **Informe AI**: Análisis detallado de Gemini con formato Markdown renderizado.
    *   **Exportación de Data**: Acceso directo al JSON crudo (`reports/data/scan_*.json`) para integración con SIEM o Firebase.

---

## 📡 Capacidades del Sensor (Actualizado)

| Sensor | Windows (Comandos) | Linux (Comandos) | macOS (Comandos) | Qué detecta |
| :--- | :--- | :--- | :--- | :--- |
| **Procesos** | `netstat -ano`, `tasklist` | `ss -lntp`, `ps` | `lsof -iTCP`, `ps` | Puertos abiertos, PIDs ocultos, Shadows IT. |
| **Red** | `ipconfig`, `arp` | `ip addr`, `ip neigh` | `ifconfig`, `arp` | Interfaces promiscuas, vecinos de red. |
| **Vulns** | Análisis de puertos | Análisis de puertos | Análisis de puertos | Servicios expuestos (SMB, RDP, SSH viejo). |

---

## 🛠️ Solución de Problemas

*   **Linux/Mac - "Permission Denied"**: Asegúrate de dar permisos de ejecución: `chmod +x galt galt-sentinel`.
*   **"AccessDenied" en sensores**: Galt ve más si corre como `sudo ./galt` o 'Ejecutar como Administrador'.
*   **API Key Error**: Edita el archivo `.env` manualmente si te equivocaste al ingresarla.

---

**© 2026 Galt.ai Security Division.** *Multi-platform Cyber Defense.*
