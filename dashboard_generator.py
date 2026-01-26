import os
import json
import glob
from datetime import datetime
from config import get_storage_path

def get_html_template(current_data, history_links, logo_path_abs, current_json_path=None):
    # 1. Recolectar Historial
    reports_path = os.path.join(get_storage_path("reports"), "data")
    json_files = glob.glob(os.path.join(reports_path, "scan_*.json"))
    json_files.sort(key=os.path.getmtime, reverse=True)
    
    # 2. Force inclusion of the current file if provided (Real-time consistency)
    if current_json_path:
        current_json_path = os.path.abspath(current_json_path)
        if current_json_path not in [os.path.abspath(f) for f in json_files]:
            # Prepend it if glob missed it (filesystem race condition)
            json_files.insert(0, current_json_path)
    
    history_data = []
    
    # Ensure logo path is a file URI
    logo_path_abs = os.path.abspath(logo_path_abs)
    logo_uri = f"file:///{logo_path_abs.replace(os.path.sep, '/')}"

    # Cargar top 15 reportes
    for f in json_files[:15]:
        try:
            with open(f, 'r', encoding='utf-8') as file:
                data = json.load(file)
                ts = os.path.getmtime(f)
                data['ui_date_short'] = datetime.fromtimestamp(ts).strftime('%H:%M:%S')
                data['ui_date_full'] = datetime.fromtimestamp(ts).strftime('%Y-%m-%d %H:%M:%S')
                history_data.append(data)
        except: continue

    if not history_data:
        current_data['ui_date_full'] = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        history_data = [current_data]

    js_payload = json.dumps(history_data)

    return f"""
    <!DOCTYPE html>
    <html lang="es">
    <head>
        <meta charset="UTF-8">
        <title>Galt.ai Security Center</title>
        <style>
            :root {{ --bg: #0f0f13; --sidebar: #18181f; --text: #e0e0e0; --accent: #2dce89; }}
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
            
            .refresh-btn {{ background:#333; color:white; border:none; padding:8px 15px; cursor:pointer; border-radius:4px; font-size:12px; }}
            .refresh-btn:hover {{ background:#444; }}

            /* Cards */
            .grid {{ display: grid; grid-template-columns: 250px 1fr; gap: 30px; }}
            .card {{ background: #18181f; border-radius: 12px; padding: 25px; border: 1px solid #2a2a35; }}
            
            .score-big {{ font-size: 64px; font-weight: bold; color: white; text-align: center; line-height: 1; }}
            .score-label {{ text-align: center; color: #666; font-size: 12px; text-transform: uppercase; letter-spacing: 1px; margin-top: 10px; }}
            
            .ai-box h3 {{ margin-top: 0; color: var(--accent); display: flex; align-items: center; gap: 10px; }}
            .ai-content {{ line-height: 1.6; color: #ccc; font-size: 15px; }}
            
            /* Error Box Styling */
            .error-box {{ background: #2d1b1b; border-left: 4px solid #f5365c; padding: 15px; border-radius: 4px; color: #ffadad; }}
            
            pre {{ background: #000; padding: 15px; border-radius: 6px; color: #0f0; font-size: 11px; overflow-x: auto; margin-top: 20px; }}
            
            /* --- STATES --- */
            /* Scanning State Overlay */
            .overlay-msg {{ 
                display: none; 
                position: fixed; top: 50%; left: 50%; transform: translate(-50%, -50%);
                background: rgba(15, 15, 19, 0.95); padding: 40px; border-radius: 16px;
                border: 1px solid #fb6340; z-index: 999; text-align: center;
                box-shadow: 0 0 50px rgba(251, 99, 64, 0.2);
            }}
            .overlay-msg h2 {{ color: #fb6340; margin: 0 0 10px 0; font-size: 24px; }}
            
            /* Pulse Animation for Scanning */
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
            
            /* Scanning pulsing dot */
            @keyframes pulse-red {{ 0% {{ box-shadow: 0 0 0 0 rgba(251, 99, 64, 0.7); }} 70% {{ box-shadow: 0 0 0 10px rgba(251, 99, 64, 0); }} 100% {{ box-shadow: 0 0 0 0 rgba(251, 99, 64, 0); }} }}
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
                        <div id="status-badge" class="status-badge">
                            <div id="status-dot" class="dot"></div>
                            <span id="status-text">Sistema Activo</span>
                        </div>
                    </div>
                </div>

                <div class="grid">
                    <div class="card">
                        <div id="score-val" class="score-big">--</div>
                        <div class="score-label">Global Score</div>
                    </div>
                    <div class="card">
                        <div class="ai-box">
                            <div id="ai-body" class="ai-content"></div>
                        </div>
                    </div>
                </div>

                <div style="margin-top: 30px;">
                    <h4 style="color:#666">Raw Data Inspector</h4>
                    <pre id="raw-data"></pre>
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
                
                view.classList.remove('fade-in');
                void view.offsetWidth;
                view.classList.add('fade-in');

                document.getElementById('report-timestamp').innerText = 'Fecha del Escaneo: ' + data.ui_date_full;
                
                const scoreEl = document.getElementById('score-val');
                const score = data.score !== undefined ? data.score : 0;
                scoreEl.innerText = score;
                scoreEl.style.color = getColor(score);
                
                let analysis = data.ai_analysis_markdown || data.ai_analysis || 'Sin análisis disponible.';
                document.getElementById('ai-body').innerHTML = analysis;
                document.getElementById('raw-data').innerText = JSON.stringify(data, null, 2);
            }}

            function getColor(score) {{
                if(score >= 80) return '#2dce89';
                if(score >= 50) return '#fb6340';
                return '#f5365c';
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
                    dot.style.animation = 'pulse-red 1s infinite';
                    badge.style.borderColor = '#fb6340';
                }} else {{
                    document.body.classList.remove('state-scanning');
                    document.body.classList.add('state-idle');
                    
                    text.innerText = 'Sistema Activo • ' + data.timestamp;
                    text.style.color = '#e0e0e0';
                    dot.style.background = '#2dce89';
                    dot.style.animation = 'none';
                    badge.style.borderColor = 'rgba(255,255,255,0.1)';
                    
                    if (lastState === 'SCANNING') {{
                        console.log("Scan finished. Reloading...");
                        setTimeout(() => location.reload(), 2000);
                    }}
                }}
                lastState = data.state;
            }};

            // Poll every 1.5 seconds
            setInterval(() => {{
                const script = document.createElement('script');
                script.src = 'live_status.js?t=' + Date.now();
                document.body.appendChild(script);
                script.onload = () => script.remove();
                script.onerror = () => script.remove();
            }}, 1500);
            
        </script>
    </body>
    </html>
    """

def generate_history_html(reports_dir):
    """Deprecated."""
    return ""
