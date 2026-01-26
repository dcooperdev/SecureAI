import os
from datetime import datetime
import shutil

def get_html_template(data, history_links, logo_path_abs):
    # Ensure logo path uses forward slashes for HTML compatibility even on Windows
    logo_uri = f"file:///{logo_path_abs.replace(os.path.sep, '/')}"
    
    return f"""
    <!DOCTYPE html>
    <html lang="es">
    <head>
        <meta charset="UTF-8">
        <title>Galt.ai Security Panel</title>
        <style>
            body {{ display: flex; margin: 0; font-family: 'Segoe UI', sans-serif; height: 100vh; background: #f4f4f9; }}
            .sidebar {{ width: 260px; background: #1a1a2e; color: #fff; display: flex; flex-direction: column; border-right: 1px solid #16213e; }}
            .brand {{ padding: 20px; text-align: center; background: #162447; }}
            .brand img {{ max-width: 80px; height: auto; display: block; margin: 0 auto 10px; }}
            .brand h2 {{ margin: 0; font-size: 1.2rem; color: #00d4ff; text-transform: uppercase; letter-spacing: 1px; }}
            .history-list {{ overflow-y: auto; flex: 1; }}
            .history_header {{ padding: 15px 20px; color: #7a7a9e; font-size: 0.8rem; font-weight: bold; letter-spacing: 0.5px; }}
            .history-item {{ padding: 12px 20px; border-bottom: 1px solid #24243e; color: #a0a0a0; text-decoration: none; display: block; transition: 0.2s; font-size: 0.9rem; }}
            .history-item:hover {{ background: #1f4068; color: #fff; padding-left: 25px; }}
            .content {{ flex: 1; padding: 40px; overflow-y: auto; }}
            .score-card {{ background: white; padding: 30px; border-radius: 12px; box-shadow: 0 4px 15px rgba(0,0,0,0.05); text-align: center; margin-bottom: 30px; }}
            .score-circle {{ width: 120px; height: 120px; background: conic-gradient(#00d4ff {data.get('score',0)}%, #eee 0); border-radius: 50%; margin: 0 auto; display: flex; align-items: center; justify-content: center; position: relative; }}
            .score-circle::after {{ content: '{data.get('score',0)}'; position: absolute; background: white; width: 100px; height: 100px; border-radius: 50%; display: flex; align-items: center; justify-content: center; font-size: 2.5rem; font-weight: bold; color: #1a1a2e; }}
            .report-body {{ background: white; padding: 40px; border-radius: 12px; box-shadow: 0 4px 15px rgba(0,0,0,0.05); color: #333; line-height: 1.6; }}
            h1, h2, h3 {{ color: #1a1a2e; }}
            code {{ background: #f0f0f5; padding: 2px 5px; border-radius: 4px; color: #d63384; font-family: monospace; }}
            pre {{ background: #1a1a2e; color: #e0e0e0; padding: 15px; border-radius: 8px; overflow-x: auto; }}
        </style>
    </head>
    <body>
        <div class="sidebar">
            <div class="brand">
                <img src="{logo_uri}" alt="Galt.ai Logo">
                <h2>Galt.ai</h2>
            </div>
            <div class="history-list">
                <div class="history_header">HISTORIAL DE ESCANEOS</div>
                {history_links}
            </div>
        </div>
        <div class="content">
            <div class="score-card">
                <h3>Postura de Seguridad</h3>
                <div class="score-circle"></div>
                <p style="margin-top: 15px; color: #666;">ID Cliente: {data.get('client_id','UNKNOWN')}</p>
                <small style="color: #999;">Generado: {datetime.now().strftime('%Y-%m-%d %H:%M')}</small>
            </div>
            <div class="report-body">
                {data.get('ai_analysis', '<h3>Sin análisis de IA disponible.</h3>')}
            </div>
        </div>
    </body>
    </html>
    """

def generate_history_html(reports_dir):
    """Generates the HTML string for sidebar history links."""
    links = ""
    try:
        # List .html files, sort by date desc
        files = [f for f in os.listdir(reports_dir) if f.endswith('.html')]
        files.sort(key=lambda x: os.path.getmtime(os.path.join(reports_dir, x)), reverse=True)
        
        for f in files[:20]: # Show last 20
            # Friendly Name: scan_YYYYMMDD_HHMMSS.html -> YYYY-MM-DD HH:MM
            name = f.replace("scan_", "").replace(".html", "")
            try:
                dt = datetime.strptime(name, "%Y%m%d_%H%M%S")
                label = dt.strftime("%Y-%m-%d %H:%M")
            except:
                label = name
            
            links += f'<a href="{f}" class="history-item">{label}</a>'
    except Exception as e:
        links = f'<div style="padding:10px; color: red;">Error: {e}</div>'
    return links
