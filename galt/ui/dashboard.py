import os
import json
import glob
from datetime import datetime
from galt.core.config import get_storage_path
import markdown

def get_html_template(current_data, history_links, logo_path_abs, current_json_path=None):
    # 1. Recolectar Historial
    reports_path = get_storage_path("reports/data")
    if not os.path.exists(reports_path): os.makedirs(reports_path)
    
    json_files = glob.glob(os.path.join(reports_path, "scan_*.json"))
    json_files.sort(key=os.path.getmtime, reverse=True)
    
    # Helper para conversión segura
    def safe_md_to_html(text):
        try:
            if not text: return ""
            return markdown.markdown(text, extensions=['extra', 'nl2br', 'sane_lists'])
        except Exception as e:
            print(f"DEBUG: Error converting markdown: {e}")
            return text
            
    # Ensure logo path is a file URI
    logo_path_abs = os.path.abspath(logo_path_abs)
    logo_uri = f"file:///{logo_path_abs.replace(os.path.sep, '/')}"

    history_data = []

    # 1. Prioridad: Procesar current_data (En memoria, lo más fresco)
    if current_data:
        # Asegurar timestamps para la UI si faltan
        if 'ui_date_full' not in current_data:
            current_data['ui_date_full'] = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        
        # Mapping de orchestrator (ai_analysis -> ai_analysis_markdown)
        if 'ai_analysis' in current_data and 'ai_analysis_markdown' not in current_data:
             current_data['ai_analysis_markdown'] = current_data['ai_analysis']

        # Conversión Markdown -> HTML
        if 'ai_analysis_markdown' in current_data:
             print("DEBUG: Convirtiendo narrativa actual a HTML...")
             current_data['ai_analysis_html'] = safe_md_to_html(current_data['ai_analysis_markdown'])
        
        history_data.append(current_data)

    # 2. Cargar Historial (excluyendo el actual si ya está)
    current_path_abs = os.path.abspath(current_json_path) if current_json_path else None
    
    for f in json_files[:15]:
        # Evitar duplicados si ya procesamos current_data y coincide el path
        if current_path_abs and os.path.abspath(f) == current_path_abs:
            continue
            
        try:
            with open(f, 'r', encoding='utf-8') as file:
                data = json.load(file)
                ts = os.path.getmtime(f)
                data['ui_date_short'] = datetime.fromtimestamp(ts).strftime('%H:%M:%S')
                data['ui_date_full'] = datetime.fromtimestamp(ts).strftime('%Y-%m-%d %H:%M:%S')
                
                # Renderizar Markdown a HTML para la UI
                if 'ai_analysis_markdown' in data and data['ai_analysis_markdown']:
                    data['ai_analysis_html'] = safe_md_to_html(data['ai_analysis_markdown'])
                else:
                    data['ai_analysis_html'] = ""
                    
                history_data.append(data)
        except Exception as e:
            print(f"Error cargando historial {f}: {e}")
            continue

    if not history_data:
        # Si no hay historial, usar current_data
        # Asegurar que current_data tenga el HTML renderizado también
        if 'ai_analysis' in current_data and current_data['ai_analysis']:
             # orchestrator pasa 'ai_analysis' (MD report), mapeamos a lo que espera la UI
             current_data['ai_analysis_markdown'] = current_data['ai_analysis']
             current_data['ai_analysis_html'] = markdown.markdown(
                current_data['ai_analysis'],
                extensions=['extra', 'smarty', 'nl2br']
             )
        
        current_data['ui_date_full'] = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        history_data = [current_data]

    js_payload = json.dumps(history_data)

    return f"""
    <!DOCTYPE html>
    <html lang="es">
    <head>
        <meta charset="UTF-8">
        <title>Galt.ai Security Center</title>
        <link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.4.0/css/all.min.css">
        <script src="https://unpkg.com/feather-icons"></script>
        <style>
            :root {{ --bg: #0f0f13; --sidebar: #18181f; --text: #e0e0e0; --accent: #2dce89; --danger: #f5365c; --warning: #fb6340; }}
            body {{ margin: 0; font-family: 'Segoe UI', system-ui, sans-serif; background: var(--bg); color: var(--text); display: flex; height: 100vh; overflow: hidden; }}
            
            /* Sidebar */
            .sidebar {{ width: 260px; background: var(--sidebar); display: flex; flex-direction: column; border-right: 1px solid #2a2a35; }}
            .brand {{ padding: 25px; text-align: center; border-bottom: 1px solid #2a2a35; cursor: pointer; }}
            .brand img {{ width: 48px; height: 48px; }}
            .brand h2 {{ margin: 10px 0 0; font-size: 14px; letter-spacing: 3px; color: #fff; text-transform: uppercase; }}

            .history-list {{ flex: 1; overflow-y: auto; }}
            .history-item {{ padding: 15px 20px; border-bottom: 1px solid #2a2a35; cursor: pointer; transition: all 0.2s; display: flex; justify-content: space-between; align-items: center; }}
            .history-item:hover {{ background: #22222b; }}
            .history-item.active {{ background: #22222b; border-left: 3px solid var(--accent); }}
            .h-date {{ font-size: 13px; color: #fff; font-weight: 500; }}
            .h-score {{ font-size: 12px; font-weight: bold; padding: 2px 6px; border-radius: 4px; background: #333; }}
            
            /* Scrollbar styling */
            ::-webkit-scrollbar {{ width: 8px; }}
            ::-webkit-scrollbar-track {{ background: #1e1e24; }}
            ::-webkit-scrollbar-thumb {{ background: #333; border-radius: 4px; }}
            ::-webkit-scrollbar-thumb:hover {{ background: #555; }}

            /* Content */
            .content {{ flex: 1; padding: 40px; overflow-y: auto; display: flex; flex-direction: column; position: relative; transition: opacity 0.3s; }}
            .fade-in {{ animation: fadeIn 0.3s ease-in-out; }}
            @keyframes fadeIn {{ from {{ opacity: 0; transform: translateY(5px); }} to {{ opacity: 1; transform: translateY(0); }} }}

            .header-info {{ display: flex; justify-content: space-between; align-items: flex-end; margin-bottom: 30px; border-bottom: 1px solid #333; padding-bottom: 20px; }}
            .report-title {{ font-size: 24px; color: white; margin: 0; }}
            .report-subtitle {{ color: #888; font-size: 14px; margin-top: 5px; }}
            
            /* Cards */
            .grid {{ display: grid; grid-template-columns: 280px 1fr; gap: 30px; align-items: start; }}
            .card {{ background: #18181f; border-radius: 12px; padding: 25px; border: 1px solid #2a2a35; }}
            
            /* Eliminamos height: 100% y usamos height: auto */
            .score-card {{
                display: flex;
                flex-direction: column;
                align-items: center;
                justify-content: center;
                height: auto;
                padding: 40px 20px;
                min-height: auto;
            }}
            .score-big {{ font-size: 80px; font-weight: 800; color: white; text-align: center; line-height: 1; text-shadow: 0 0 20px rgba(0,0,0,0.5); }}
            .score-label {{ text-align: center; color: #888; font-size: 13px; text-transform: uppercase; letter-spacing: 1px; margin-top: 15px; font-weight: 600; }}
            
            .ai-box h3 {{ margin-top: 0; color: var(--accent); display: flex; align-items: center; gap: 10px; }}
            .ai-content {{ line-height: 1.6; color: #ccc; font-size: 15px; }}
            
            /* Fallback Cards */
            .threat-grid {{ display: grid; grid-template-columns: repeat(auto-fill, minmax(280px, 1fr)); gap: 15px; margin-top: 20px; }}
            .threat-card {{ background: #22222b; border: 1px solid #333; border-radius: 8px; padding: 15px; display: flex; gap: 15px; align-items: flex-start; }}
            .threat-icon {{ width: 40px; height: 40px; background: #333; border-radius: 8px; display: flex; align-items: center; justify-content: center; font-size: 18px; color: #fff; flex-shrink: 0; }}
            .threat-body h4 {{ margin: 0 0 5px 0; color: #fff; font-size: 14px; }}
            .threat-body p {{ margin: 0; color: #888; font-size: 12px; line-height: 1.4; }}
            
            .badge {{ padding: 3px 8px; border-radius: 4px; font-size: 10px; font-weight: bold; text-transform: uppercase; display: inline-block; margin-top: 8px; }}
            .badge-high {{ background: rgba(245, 54, 92, 0.2); color: #f5365c; border: 1px solid rgba(245, 54, 92, 0.3); }}
            .badge-medium {{ background: rgba(251, 99, 64, 0.2); color: #fb6340; border: 1px solid rgba(251, 99, 64, 0.3); }}
            .badge-low {{ background: rgba(45, 206, 137, 0.2); color: #2dce89; border: 1px solid rgba(45, 206, 137, 0.3); }}
            
            .empty-state {{ text-align: center; padding: 40px; color: #666; }}
            .empty-state i {{ font-size: 48px; margin-bottom: 20px; color: var(--accent); opacity: 0.5; }}

            /* Raw Data Accordion */
            .accordion {{ margin-top: 40px; border-top: 1px solid #333; padding-top: 20px; }}
            .accordion-btn {{ background: transparent; border: 1px solid #444; color: #888; padding: 8px 15px; border-radius: 4px; cursor: pointer; font-size: 12px; display: flex; align-items: center; gap: 8px; transition: all 0.2s; }}
            .accordion-btn:hover {{ border-color: #666; color: #ccc; }}
            .collapse {{ display: none; margin-top: 15px; }}
            .collapse.show {{ display: block; }}
            pre {{ background: #000; padding: 15px; border-radius: 6px; color: #0f0; font-size: 11px; overflow-x: auto; border: 1px solid #333; }}
            
            /* --- STATES --- */
            .overlay-msg {{ 
                display: none; 
                position: fixed; top: 50%; left: 50%; transform: translate(-50%, -50%);
                background: rgba(15, 15, 19, 0.95); padding: 40px; border-radius: 16px;
                border: 1px solid #fb6340; z-index: 999; text-align: center;
                box-shadow: 0 0 50px rgba(251, 99, 64, 0.2);
            }}
            .overlay-msg h2 {{ color: #fb6340; margin: 0 0 10px 0; font-size: 24px; }}
            
            body.state-scanning .sidebar {{ opacity: 0.5; pointer-events: none; }}
            body.state-scanning .content {{ opacity: 0.5; pointer-events: none; }}
            body.state-scanning .overlay-msg {{ display: block; animation: pulse-border 2s infinite; }}
            
            @keyframes pulse-border {{
                0% {{ box-shadow: 0 0 20px rgba(251, 99, 64, 0.1); }}
                50% {{ box-shadow: 0 0 60px rgba(251, 99, 64, 0.3); }}
                100% {{ box-shadow: 0 0 20px rgba(251, 99, 64, 0.1); }}
            }}
            
            .status-badge {{ background: rgba(255,255,255,0.05); padding: 6px 14px; border-radius: 20px; font-size: 13px; display: flex; align-items: center; gap: 8px; border: 1px solid rgba(255,255,255,0.1); }}
            .dot {{ width: 8px; height: 8px; background: #2dce89; border-radius: 50%; box-shadow: 0 0 10px rgba(45, 206, 137, 0.4); }}
            
            /* AI Badge Specifics */
            .ai-badge-container {{ display: flex; gap: 10px; align-items: center; }}

            /* AI Report Card Styling */
            .ai-report-card {{
                border: 1px solid #ea580c; /* Borde naranja sutil */
                background-color: #1e293b; 
                margin-top: 2rem;
                overflow: hidden; /* Para que el header no se salga */
                padding: 0 !important; /* Reset del padding generico de card */
            }}
            .ai-report-header {{
                display: flex;
                align-items: center;
                gap: 15px;
                background-color: rgba(234, 88, 12, 0.1); 
                padding: 15px 25px;
                border-bottom: 1px solid #ea580c;
            }}
            .ai-icon {{
                 color: #ea580c;
                 width: 24px; height: 24px;
            }}
            .ai-report-header h3 {{
                margin: 0;
                color: #fb923c;
                font-size: 16px;
                text-transform: uppercase;
                letter-spacing: 1px;
            }}

            /* Estilos del contenido Markdown renderizado */
            .ai-report-content {{
                padding: 25px;
                line-height: 1.7; 
                color: #e2e8f0; 
                font-size: 15px;
            }}
            .ai-report-content h1, .ai-report-content h2, .ai-report-content h3 {{
                color: #fb923c; 
                margin-top: 1.5em;
                margin-bottom: 0.8em;
                font-weight: 600;
            }}
            .ai-report-content h1 {{ font-size: 1.8em; border-bottom: 1px solid #333; padding-bottom: 10px; }}
            .ai-report-content h2 {{ font-size: 1.4em; }}
            .ai-report-content h3 {{ font-size: 1.2em; }}
            
            .ai-report-content strong {{
                color: #ffffff; 
                font-weight: 700;
            }}
            .ai-report-content ul, .ai-report-content ol {{
                padding-left: 1.5rem;
                margin-bottom: 1.5em;
            }}
            .ai-report-content li {{
                margin-bottom: 0.5em;
            }}
            .ai-report-content p {{
                margin-bottom: 1.2em;
            }}
            .error-box {{
                background: rgba(245, 54, 92, 0.1);
                border-left: 4px solid #f5365c;
                padding: 15px;
                border-radius: 4px;
            }}
        </style>
    </head>
    <body class="state-idle">
        
        <div class="overlay-msg">
            <h2>🔄 ANALIZANDO...</h2>
            <p style="color:#aaa; font-size: 14px;">El centinela está revisando el sistema.<br>Por favor espere.</p>
        </div>

        <div class="sidebar">
            <div class="brand" onclick="location.reload()">
                <img src="{logo_uri}" alt="Galt.ai">
                <h2>Galt.ai</h2>
            </div>
            <div id="history-container" class="history-list"></div>
        </div>
        
        <div class="content">
            <div id="main-view" class="fade-in">
                <div class="header-info">
                    <div>
                        <h1 class="report-title">Reporte de Seguridad</h1>
                        <div id="report-timestamp" class="report-subtitle">Cargando...</div>
                    </div>
                    <div>
                    <div class="ai-badge-container">
                        <!-- AI Status Badge -->
                        <div id="ai-status-badge" class="status-badge" style="border-color: rgba(255,255,255,0.1);">
                            <div id="ai-status-dot" class="dot" style="background: #999;"></div>
                            <span id="ai-status-text" style="color: #ccc;">IA Estado</span>
                        </div>
                        
                        <!-- System Watchdog Status -->
                        <div id="status-badge" class="status-badge">
                            <div id="status-dot" class="dot"></div>
                            <span id="status-text">Sistema Activo</span>
                        </div>
                    </div>
                    </div>
                </div>

                <div class="grid" style="display: grid; grid-template-columns: 280px 1fr; gap: 30px; align-items: start !important;">
                    <!-- Score Card -->
                    <div class="card score-card">
                        <div id="score-val" class="score-big">--</div>
                        <div id="score-text" class="score-label">Securing...</div>
                    </div>
                    
                    <!-- Content Card -->
                    <div class="card">
                        <!-- AI Analysis or Fallback -->
                        <div id="ai-body" class="ai-content"></div>
                        
                        <!-- Fallback Views -->
                        <div id="fallback-container" style="display:none;"></div>
                    </div>
                </div>

                <!-- Raw Data Accordion -->
                <div class="accordion">
                    <button class="accordion-btn" onclick="toggleRawData()">
                        <i class="fas fa-code"></i> Ver Detalles Técnicos (Raw JSON)
                    </button>
                    <div id="raw-details" class="collapse">
                        <pre id="raw-data"></pre>
                    </div>
                </div>
            </div>
        </div>

        <script>
            const historyData = {js_payload};

            function renderSidebar() {{
                const list = document.getElementById('history-container');
                list.innerHTML = '';
                historyData.forEach((item, index) => {{
                    const el = document.createElement('div');
                    el.className = `history-item ${{index === 0 ? 'active' : ''}}`;
                    el.onclick = () => loadReport(index);
                    el.innerHTML = `
                        <span class="h-date">${{item.ui_date_full}}</span>
                        <span class="h-score" style="color:${{getColor(item.score)}}">${{item.score}}</span>
                    `;
                    list.appendChild(el);
                }});
            }}

            function loadReport(index) {{
                document.querySelectorAll('.history-item').forEach((el, i) => el.classList.toggle('active', i === index));
                
                const data = historyData[index];
                const view = document.getElementById('main-view');
                
                // Reset View
                view.classList.remove('fade-in');
                void view.offsetWidth;
                view.classList.add('fade-in');

                document.getElementById('report-timestamp').innerText = 'Fecha del Escaneo: ' + data.ui_date_full;
                
                // 1. Score Logic
                const scoreEl = document.getElementById('score-val');
                const scoreLabel = document.getElementById('score-text');
                const score = data.score !== undefined ? data.score : 0;
                
                scoreEl.innerText = score;
                scoreEl.style.color = getColor(score);
                
                if(score >= 90) scoreLabel.innerText = "Sistema Seguro";
                else if(score >= 60) scoreLabel.innerText = "Precaución";
                else scoreLabel.innerText = "Estado Crítico";

                // 2. AI Status Label Logic
                const aiStatus = data.ai_status || 'offline';
                const aiBadge = document.getElementById('ai-status-badge');
                const aiText = document.getElementById('ai-status-text');
                const aiDot = document.getElementById('ai-status-dot');
                
                if (aiStatus === 'online') {{
                    aiText.innerText = 'IA Activa (Gemma-3)';
                    aiText.style.color = '#2dce89';
                    aiDot.style.background = '#2dce89';
                    aiBadge.style.borderColor = 'rgba(45, 206, 137, 0.3)';
                }} else if (aiStatus === 'cached') {{
                    aiText.innerText = 'IA Cached';
                    aiText.style.color = '#fb6340';
                    aiDot.style.background = '#fb6340';
                    aiBadge.style.borderColor = 'rgba(251, 99, 64, 0.3)';
                }} else {{
                    aiText.innerText = 'IA Offline (Reglas Locales)';
                    aiText.style.color = '#f5365c';
                    aiDot.style.background = '#f5365c'; // Red
                    aiBadge.style.borderColor = 'rgba(245, 54, 92, 0.3)';
                }}

                // 3. AI vs Fallback Content Logic
                const aiBody = document.getElementById('ai-body');
                const fallbackContainer = document.getElementById('fallback-container');
                
                // Detectar si el AI Analysis tiene contenido válido (no solo whitespace o null)
                let hasAI = data.ai_analysis_markdown && data.ai_analysis_markdown.trim().length > 10;
                
                // Si la IA fallo (ej: 'Modo Offline' en el texto), forzamos fallback
                if(hasAI && (data.ai_analysis_markdown.includes('Modo Offline') || data.ai_analysis_markdown.includes('<div class="error-box">'))) {{
                    // Renderizamos el error de IA pero TAMBIEN el fallback visual
                    aiBody.innerHTML = data.ai_analysis_markdown; 
                    renderFallbackMode(data.findings);
                    fallbackContainer.style.display = 'grid'; // Mostrar grid
                }} 
                else if (hasAI) {{
                    // Happy Path: IA funcionó (Rendered HTML)
                    // Usamos la versión HTML pre-renderizada si existe, sino fallback al MD
                    let htmlContent = data.ai_analysis_html || data.ai_analysis_markdown;
                    
                    aiBody.innerHTML = `
                        <div class="card ai-report-card">
                            <div class="card-header ai-report-header">
                                <i data-feather="cpu" class="ai-icon"></i>
                                <h3>Análisis del CISO Virtual (Gemma-3)</h3>
                            </div>
                            <div class="card-body ai-report-content">
                                ${{htmlContent}}
                            </div>
                        </div>
                    `;
                    // Re-run feather replace for dynamic content
                    setTimeout(() => feather.replace(), 100);
                    
                    fallbackContainer.style.display = 'none';
                }} 
                else {{
                    // Fallback Total: No hay IA
                    aiBody.innerHTML = '';
                    renderFallbackMode(data.findings);
                    fallbackContainer.style.display = 'grid';
                }}

                // 4. Raw Data (Always hidden)
                document.getElementById('raw-data').innerText = JSON.stringify(data, null, 2);
            }}
            
            function renderFallbackMode(findings) {{
                const container = document.getElementById('fallback-container');
                container.innerHTML = '';
                container.className = 'threat-grid';
                
                if (!findings || findings.length === 0) {{
                     container.className = ''; // Remove grid for single center item
                     container.innerHTML = `
                        <div class="empty-state">
                            <i class="fas fa-shield-halved"></i>
                            <h3>Sistema Seguro</h3>
                            <p>No se han detectado amenazas activas en este escaneo.</p>
                        </div>
                     `;
                     return;
                }}
                
                findings.forEach(f => {{
                    // Mapeo de Iconos
                    let icon = 'fa-circle-exclamation';
                    if(f.module === 'sensor_network_discovery') icon = 'fa-wifi';
                    if(f.module === 'sensor_procesos') icon = 'fa-microchip';
                    if(f.module === 'sensor_sistema') icon = 'fa-server';
                    if(f.module === 'sensor_vulnerabilidades') icon = 'fa-bug';
                    
                    // Badge Color
                    let severity = (f.result.severity || 'LOW').toUpperCase();
                    let badgeClass = 'badge-low';
                    if(severity === 'HIGH' || severity === 'CRITICAL') badgeClass = 'badge-high';
                    if(severity === 'MEDIUM') badgeClass = 'badge-medium';
                    
                    const card = document.createElement('div');
                    card.className = 'threat-card';
                    card.innerHTML = `
                        <div class="threat-icon"><i class="fas ${{icon}}"></i></div>
                        <div class="threat-body">
                            <h4>${{f.module.replace('sensor_', '').toUpperCase()}}</h4>
                            <p>${{f.result.details || JSON.stringify(f.result).substring(0, 100)}}</p>
                            <span class="badge ${{badgeClass}}">${{severity}}</span>
                        </div>
                    `;
                    container.appendChild(card);
                }});
            }}

            function getColor(score) {{
                if(score >= 90) return '#2dce89'; // Green
                if(score >= 60) return '#fb6340'; // Orange/Yellow
                return '#f5365c'; // Red
            }}
            
            function toggleRawData() {{
                const el = document.getElementById('raw-details');
                el.classList.toggle('show');
            }}

            if(historyData.length > 0) {{
                renderSidebar();
                loadReport(0);
            }}
            
            // --- HEARTBEAT POLLING SYSTEM ---
            let lastState = '';
            window.updateDashboardState = function(data) {{
                const text = document.getElementById('status-text');
                const dot = document.getElementById('status-dot');
                const badge = document.getElementById('status-badge');
                
                if (data.state === 'SCANNING') {{
                    document.body.classList.add('state-scanning');
                    document.body.classList.remove('state-idle');
                    
                    text.innerText = 'ESCANEANDO...';
                    text.style.color = '#fb6340';
                    dot.style.background = '#fb6340';
                }} else {{
                    document.body.classList.remove('state-scanning');
                    document.body.classList.add('state-idle');
                    
                    text.innerText = 'Sistema Activo';
                    text.style.color = '#e0e0e0';
                    dot.style.background = '#2dce89';
                    
                    if (lastState === 'SCANNING') {{
                         setTimeout(() => location.reload(), 2000);
                    }}
                }}
                lastState = data.state;
            }};

            setInterval(() => {{
                const script = document.createElement('script');
                script.src = 'live_status.js?t=' + Date.now();
                
                // Auto-destrucción al terminar de cargar (éxito)
                script.onload = () => script.remove();
                
                // Auto-destrucción al fallar
                script.onerror = () => script.remove();
                
                document.body.appendChild(script);
            }}, 1500);
            
            // Initialize Feather Icons
            feather.replace();
        </script>
    </body>
    </html>
    """


def generate_history_html(reports_dir):
    """Deprecated."""
    return ""
