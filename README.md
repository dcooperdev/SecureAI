# Galt Security Agent

> **Agente de Ciberseguridad Personal Residente con IA Integrada**

Galt es un sistema **HIDS (Host-Based Intrusion Detection System)** de última generación diseñado para proteger endpoints mediante una arquitectura híbrida de sensores locales, análisis de logs y un cerebro de IA (Gemini).  
Su objetivo es actuar como un **CISO Virtual** que monitorea, analiza y educa al usuario sobre su postura de seguridad en tiempo real.

---

## 🏗️ Arquitectura del Sistema

Galt opera bajo un modelo de "Vigilancia Continua + Análisis Profundo", dividiendo sus operaciones en dos modos de ejecución:

### 1. Flujo de Datos
`Sensores` ➔ `Orquestador` ➔ `Análisis (IA/Offline)` ➔ `Reporte HTML` ➔ `Notificación`

1.  **Sensores**: Scripts autónomos recolectan telemetría (Red, Procesos, Logs).
2.  **Orquestador (`runner.py`)**: Centraliza los datos, calcula el **Security Score** y decide si invocar a la IA.
3.  **Cerebro**: 
    *   **Online**: Google Gemini 2.0 analiza patrones complejos.
    *   **Offline**: Un motor lógico genera reportes cuando no hay internet o para ahorrar cuota.
4.  **Salida**: Se genera un Dashboard HTML interactivo y se alerta al usuario vía System Tray.

### 2. Dualidad de Ejecución
*   **Tiempo Real ("Live")**: Hilos en segundo plano (`NetworkSentinel`) monitorean tráfico al vuelo.
*   **Batch (Agendado)**: El `sentinel.py` ejecuta escaneos profundos cada 1 hora (Plan PRO) o 24 horas (Plan FREE).

---

## 🧩 Módulos Clave

### 🛡️ Network Sentinel (`core/network.py`)
El guardián de la red en tiempo real.
*   Utiliza **Scapy** en modo "Safe Sniffing" (No requiere modo monitor).
*   Detecta anomalías como **TCP SYN Floods** y ataques de desconexión **Wi-Fi Deauth**.
*   Opera en un hilo separado para no bloquear la interfaz principal.

### 🕵️ Log Sentinel (`core/log_watcher.py`)
El auditor forense.
*   Monitoriza los logs del sistema operativo (Event Viewer en Windows, Syslog en Linux).
*   **Función Crítica**: Detecta desconexiones Wi-Fi forzadas que la tarjeta de red no puede ver a nivel de paquetes (la "evidencia física" del ataque).

### 🔥 Firewall Manager (`core/defense.py`)
La capa de respuesta activa.
*   Capaz de interactuar con el Firewall de Windows (o `iptables` en Linux).
*   Bloquea automáticamente IPs detectadas como maliciosas por los centinelas.

### 🗣️ Offline Narrator (`reports/narrator.py`)
El respaldo de inteligencia.
*   Un motor de plantillas lógicas avanzado.
*   Genera explicaciones legibles (Human-Readable) de los hallazgos técnicos cuando la IA no está disponible, garantizando que el usuario siempre entienda qué pasó.

### 🔔 Notifier (`core/notifier.py`)
Sistema de alertas nativo.
*   Envía notificaciones "Toast" del sistema operativo.
*   **Click-to-Open**: Integrado mediante XML en Windows para permitir abrir el Dashboard con un clic.

---

## 👨‍💻 Filosofía de Desarrollo

### "Mock Everything"
El proyecto adopta una estrategia de testing agresiva para garantizar seguridad y velocidad.
*   **Aislamiento Total**: Los tests (`tests/conftest.py`) utilizan `unittest.mock` para interceptar **todas** las llamadas al sistema (red, subprocesos, archivos).
*   **Seguridad**: Ejecutar `pytest` **nunca** enviará paquetes reales a la red ni modificará archivos del sistema operativo.
*   **Eficiencia**: Los tests corren en milisegundos sin necesidad de internet.

### Protección de Cuota
Respetamos los recursos.
*   Implementamos **Rate Limiting** físico en el puente de IA (`bridge.py`).
*   Esto asegura compatibilidad con la capa gratuita de Gemini (15 RPM), previniendo errores de cuota incluso durante pruebas de estrés manuales.

---

## 🚀 Guía de Instalación y Uso

### Requisitos Previos
*   **Python 3.10+**
*   **Npcap** (Solo en Windows, para capacidades de sniffing).
*   Instalar dependencias:
    ```bash
    pip install -r requirements.txt
    ```

### Comandos Principales

#### 🛠️ Desarrollo (Ejecución Manual)
Para correr un análisis completo y generar un reporte bajo demanda:
```bash
python runner.py
```

####  Production (Modo System Tray)
Para iniciar el agente residente en la barra de tareas (Vigilancia 24/7):
```bash
python main.py
```

#### 🧪 Testing
Para verificar la integridad del sistema (Mocked):
```bash
pytest
```

---
**Galt Security Agent** — *Arquitectura Modular para la Ciberseguridad Moderna.*
