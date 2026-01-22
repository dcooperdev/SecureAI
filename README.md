# 🛡️ Galt.ai - CISO Virtual de Élite para PyMEs (Cross-Platform)

> **Versión**: v3.0 Universal
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

## 🚀 Guía de Instalación

Ofrecemos dos métodos de instalación: **Binarios (Rápido)** y **Código Fuente (Desarrollador)**.

### Opción A: Binarios (Recomendado para Usuarios Finales)

1.  Ve a la sección de **[Releases](https://github.com/dcooperdev/SecureAI/releases)** en GitHub.
2.  Descarga el instalador o script apropiado para tu OS:
    *   **Windows**: Descarga y ejecuta `GaltAI_Setup_v3.0.exe`.
        *   Instalará el agente como una aplicación nativa.
        *   Creará accesos directos en el Escritorio.
    *   **Linux/macOS**: Descarga el archivo comprimido o clona el repo y ejecuta:
        ```bash
        ./install.sh
        ```

### Opción B: Código Fuente (Desarrolladores)

Si prefieres ejecutarlo manualmente o contribuir al proyecto:

1.  **Clonar Repo**:
    ```bash
    git clone https://github.com/dcooperdev/SecureAI.git
    cd SecureAI
    ```
2.  **Crear entorno virtual**:
    ```bash
    # Windows
    python -m venv venv
    .\venv\Scripts\activate

    # Linux/Mac
    python3 -m venv venv
    source venv/bin/activate
    ```
3.  **Instalar dependencias**:
    ```bash
    pip install -r requirements.txt
    ```
4.  **Configurar**: Crea un archivo `.env` con tu `GOOGLE_API_KEY`.

---

## 🎮 Guía de Uso

### 1. Aplicación Instalada (Windows)

Si usaste el instalador `.exe`:
*   Haz doble clic en el icono **"Galt.ai Security Suite"** en tu escritorio.
*   Esto abrirá la consola de monitoreo en **Modo Centinela**.

### 2. Línea de Comandos (Linux/Mac/Devs)

*   **Modo Manual (Auditoría Puntual)**:
    Escaneo único, genera reporte y dashboard.
    ```bash
    # Linux/Mac (Install Script)
    ./galt
    # Windows/Dev
    python runner.py
    ```

*   **Modo Centinela (Vigilancia 24/7)**:
    Monitoreo continuo en segundo plano. Escanea cada HORA (Plan PRO) o cada 24 HORAS (Plan FREE).
    ```bash
    # Linux/Mac
    ./galt-sentinel
    # Windows/Dev
    python sentinel.py
    ```

*   **Modo Silencioso (CI/CD)**:
    Útil para cronjobs. No abre el navegador automáticamente.
    ```bash
    ./galt --auto
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

## 📡 Capacidades y Planes

El agente detecta automáticamente tu nivel de suscripción (simulado por ahora).

| Plan | Frecuencia de Escaneo | Características |
| :--- | :--- | :--- |
| **FREE** | Cada 24 Horas | Escaneo Básico, Dashboard Local. |
| **PRO** | Cada 1 Hora | Deep Scan (Procesos Ocultos), Alertas Inmediatas. |
| **PIONEER**| Cada 1 Hora | Acceso anticipado a features (Beta). |

---

## 🛠️ Solución de Problemas

*   **Linux/Mac - "Permission Denied"**: Asegúrate de dar permisos de ejecución: `chmod +x galt galt-sentinel`.
*   **"AccessDenied" en sensores**: Galt ve más si corre como `sudo ./galt` o 'Ejecutar como Administrador'.
*   **API Key Error**: Edita el archivo `.env` manualmente si te equivocaste al ingresarla o re-ejecuta el instalador.

---

**© 2026 Galt.ai Security Division.** *Multi-platform Cyber Defense.*
