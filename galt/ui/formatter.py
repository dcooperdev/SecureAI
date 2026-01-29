import re

class GaltReportFormatter:
    def to_html(self, raw_text: str) -> str:
        if not raw_text:
            return ""

        html_output = []
        # Normalizar saltos de línea y limpiar basura inicial
        lines = raw_text.split('\n')
        
        in_list = False

        for line in lines:
            # 1. Limpieza agresiva de inicio de línea (Puntos, espacios, bullets raros)
            clean = line.strip()
            while clean.startswith('.') or clean.startswith(' '):
                clean = clean[1:].strip()
            
            if not clean:
                continue

            # 2. Detectar Headers (###)
            if "###" in clean:
                clean = clean.replace("###", "").strip()
                # Estilo Cyan para títulos, con margen superior fuerte
                html_output.append(f"<h3 style='color: #00d2ff; margin-top: 25px; margin-bottom: 10px; font-weight: 600; border-bottom: 1px solid #333; padding-bottom: 5px;'>{clean}</h3>")
                in_list = False
                continue

            # 3. Detectar Subtítulos con Negrita (**Texto**)
            if clean.startswith("**") and "**" in clean[2:]:
                # Asegurar que termine en dos puntos si es un título
                if not clean.endswith(":") and not clean.endswith("."):
                    clean += ":"
                clean = clean.replace("**", "") # Quitamos los asteriscos para limpiar
                html_output.append(f"<p style='color: #fff; font-weight: bold; margin-top: 15px; margin-bottom: 5px; margin-left: 10px;'>{clean}</p>")
                in_list = False
                continue

            # 4. Detectar Arrays de Puertos [445, 5432] o listas por comas
            if "[" in clean and "]" in clean:
                # Extraer contenido de los corchetes
                start = clean.find("[")
                end = clean.find("]")
                ports_content = clean[start+1:end]
                ports = [p.strip() for p in ports_content.split(',')]
                
                # Texto antes del bracket
                prefix = clean[:start].strip()
                if prefix:
                    html_output.append(f"<p style='margin-left: 20px; color: #ccc;'>{prefix}</p>")
                
                # Crear lista visual bonita
                ul_html = "<ul style='margin-left: 40px; background: rgba(255,255,255,0.03); padding: 10px 10px 10px 30px; border-radius: 5px; border-left: 2px solid #fb6340;'>"
                for port in ports:
                    if port:
                        ul_html += f"<li style='color: #e0e0e0; margin-bottom: 4px;'>{port}</li>"
                ul_html += "</ul>"
                html_output.append(ul_html)
                continue

            # 5. Texto normal (Indentado)
            html_output.append(f"<p style='margin-left: 20px; color: #bbb; line-height: 1.5; margin-bottom: 5px;'>{clean}</p>")

        return f"<div style='font-family: Segoe UI, sans-serif; font-size: 14px;'>{''.join(html_output)}</div>"
