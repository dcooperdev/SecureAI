import re

class GaltReportFormatter:
    def to_html(self, raw_text: str) -> str:
        if not raw_text:
            return ""

        html_output = []
        # Normalize line breaks and clean initial garbage
        lines = raw_text.split('\n')
        
        in_list = False

        for line in lines:
            # 1. Aggressive line start cleaning (dots, spaces, weird bullets)
            clean = line.strip()
            while clean.startswith('.') or clean.startswith(' '):
                clean = clean[1:].strip()
            
            if not clean:
                continue

            # 2. Detect Headers (###)
            if "###" in clean:
                clean = clean.replace("###", "").strip()
                # Cyan style for titles, with strong top margin
                html_output.append(f"<h3 style='color: #00d2ff; margin-top: 25px; margin-bottom: 10px; font-weight: 600; border-bottom: 1px solid #333; padding-bottom: 5px;'>{clean}</h3>")
                in_list = False
                continue

            # 3. Detect Bold Subtitles (**Text**)
            if clean.startswith("**") and "**" in clean[2:]:
                # Ensure it ends with a colon if it's a title
                if not clean.endswith(":") and not clean.endswith("."):
                    clean += ":"
                clean = clean.replace("**", "") # Remove asterisks to clean
                html_output.append(f"<p style='color: #fff; font-weight: bold; margin-top: 15px; margin-bottom: 5px; margin-left: 10px;'>{clean}</p>")
                in_list = False
                continue

            # 4. Detect Port Arrays [445, 5432] or comma-separated lists
            if "[" in clean and "]" in clean:
                # Extract content from brackets
                start = clean.find("[")
                end = clean.find("]")
                ports_content = clean[start+1:end]
                ports = [p.strip() for p in ports_content.split(',')]
                
                # Text before the bracket
                prefix = clean[:start].strip()
                if prefix:
                    html_output.append(f"<p style='margin-left: 20px; color: #ccc;'>{prefix}</p>")
                
                # Create a nice visual list
                ul_html = "<ul style='margin-left: 40px; background: rgba(255,255,255,0.03); padding: 10px 10px 10px 30px; border-radius: 5px; border-left: 2px solid #fb6340;'>"
                for port in ports:
                    if port:
                        ul_html += f"<li style='color: #e0e0e0; margin-bottom: 4px;'>{port}</li>"
                ul_html += "</ul>"
                html_output.append(ul_html)
                continue

            # 5. Normal text (Indented)
            html_output.append(f"<p style='margin-left: 20px; color: #bbb; line-height: 1.5; margin-bottom: 5px;'>{clean}</p>")

        return f"<div style='font-family: Segoe UI, sans-serif; font-size: 14px;'>{''.join(html_output)}</div>"
