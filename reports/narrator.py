from typing import List, Dict, Any, Set

class OfflineNarrator:
    """
    Generates human-readable security reports without External AI.
    Provides logic-based summaries, categorized details, and actionable recommendations.
    """

    MODULE_MAP = {
        "sensor_network_discovery": "🛡️ Seguridad de Red",
        "sensor_red": "🛡️ Seguridad de Red",
        "sensor_sistema": "💻 Configuración del Sistema",
        "sensor_procesos": "⚡ Actividad de Procesos",
        "sensor_vulnerabilidades": "🔓 Vulnerabilidades"
    }

    def generate_summary(self, data: Dict[str, Any]) -> str:
        """
        Main entry point to generate the Markdown report.
        """
        score = data.get("score", 0)
        findings = data.get("findings", [])

        # 1. Executive Summary
        intro = self._generate_intro(score)

        # 2. Critical Threats Section
        critical_section = self._generate_critical_section(findings)

        # 3. Technical Breakdown (Categorized)
        breakdown = self._generate_technical_breakdown(findings)

        # 4. Recommended Actions
        actions = self._get_recommended_actions(score, findings)

        # Assemble Markdown
        md = f"{intro}\n\n"
        
        if critical_section:
            md += "### 🚨 Amenazas Críticas y Altas\n\n"
            md += f"{critical_section}\n\n"

        md += "### 📂 Desglose Técnico\n\n"
        md += f"{breakdown}\n\n"
        
        md += "### ✅ Acciones Recomendadas\n\n"
        if actions:
            for action in actions:
                md += f"- {action}\n"
        else:
            md += "- Mantener monitoreo regular.\n"

        return md

    def _generate_intro(self, score: int) -> str:
        status_icon = "🟢"
        if score < 60:
            status_icon = "🔴"
            return (
                f"### {status_icon} ATENCIÓN REQUERIDA (Score: {score})\n\n"
                "**URGENTE:** El análisis detectó amenazas que comprometen la seguridad del sistema. "
                "Revise la sección de amenazas críticas inmediatamente."
            )
        elif score < 90:
            status_icon = "🟠"
            return (
                f"### {status_icon} Precaución (Score: {score})\n\n"
                "El sistema presenta vulnerabilidades moderadas. "
                "Se recomienda atender los hallazgos listados a continuación."
            )
        else:
            return (
                f"### {status_icon} Sistema Estable (Score: {score})\n\n"
                "El sistema se encuentra operativo y seguro. No se detectaron anomalías relevantes."
            )

    def _generate_critical_section(self, findings: List[Dict[str, Any]]) -> str:
        """Filters and formats only HIGH/CRITICAL findings."""
        critical_lines = []
        for f in findings:
            result = f.get("result", {})
            severity = str(result.get("severity", "INFO")).upper()
            
            if severity in ["HIGH", "CRITICAL"]:
                mod_name = self.MODULE_MAP.get(f.get("module"), "Sistema")
                details = self._extract_details_human(f)
                critical_lines.append(f"* **{mod_name}:** {details}")
        
        return "\n".join(critical_lines)

    def _generate_technical_breakdown(self, findings: List[Dict[str, Any]]) -> str:
        """Groups findings by category and applies specialized formatting."""
        if not findings:
            return "_No hay hallazgos técnicos registrados._"

        grouped = {}
        for f in findings:
            mod = f.get("module", "unknown")
            category = self.MODULE_MAP.get(mod, "Otros Hallazgos")
            if category not in grouped:
                grouped[category] = []
            grouped[category].append(f)

        md_output = ""
        
        for category, items in grouped.items():
            md_output += f"\n**{category}**\n"
            
            # Specialized formatters per category
            if "Red" in category:
                md_output += self._format_network_findings(items)
            elif "Sistema" in category:
                md_output += self._format_system_findings(items)
            elif "Procesos" in category:
                md_output += self._format_process_findings(items)
            else:
                # Generic fallback
                for item in items:
                    det = self._extract_details_human(item)
                    md_output += f"* {det}\n"

        return md_output

    def _extract_details_human(self, finding: Dict[str, Any]) -> str:
        """Helper to get text details safely."""
        res = finding.get("result", {})
        return finding.get("description") or res.get("details") or res.get("impact_hint") or "Anomalía detectada."

    # --- Specialized Extractors ---

    def _format_network_findings(self, findings: List[Dict[str, Any]]) -> str:
        lines = []
        open_ports = []
        
        for f in findings:
            text = self._extract_details_human(f)
            
            # Check for structured data FIRST
            res_data = f.get("result", {}).get("data", [])
            if isinstance(res_data, list) and len(res_data) > 0 and isinstance(res_data[0], dict) and "ip" in res_data[0]:
                for host in res_data:
                    ip = host.get("ip", "Unknown")
                    ports = host.get("open_ports", [])
                    if ports:
                        open_ports.extend(ports)
                        lines.append(f"* IP **{ip}** tiene puertos abiertos: {', '.join(map(str, ports))}.")
            
            # Fallback to text parsing if no structured data produced output
            # (Avoid duplication if we already printed the structured data?? 
            # Actually, usually finding is EITHER structured OR text for our sensors
            # But just in case, let's append text only if lines wasn't modified OR make it distinctive)
            # Simplest approach: If we found structured data, we are good. If not, text.
            elif "Port" in text or "puerto" in text.lower():
                 lines.append(f"* {text}")
            else:
                 lines.append(f"* {text}")

        # Summary of common ports if standard
        if open_ports:
            unique_ports = sorted(list(set(open_ports)))
            # Only add summary if we have a lot of noise or for impact context
            if len(lines) > 5:
                 lines.append(f"* **Resumen:** Puertos detectados en la red: {', '.join(map(str, unique_ports))}.")

        return "\n".join(lines) + "\n"

    def _format_system_findings(self, findings: List[Dict[str, Any]]) -> str:
        lines = []
        for f in findings:
            text = self._extract_details_human(f)
            if "Defender" in text:
                lines.append(f"* ⚠️ **Antivirus:** {text}")
            elif "Update" in text or "build" in text.lower():
                lines.append(f"* 🔄 **Actualización:** {text}")
            else:
                lines.append(f"* {text}")
        return "\n".join(lines) + "\n"

    def _format_process_findings(self, findings: List[Dict[str, Any]]) -> str:
        suspicious = []
        for f in findings:
            text = self._extract_details_human(f)
            # Try to extract process name from description if structured
            # Assuming text is something like "Suspicious process: miner.exe"
            if ":" in text:
                suspicious.append(text.split(":")[-1].strip())
            else:
                suspicious.append(text)
        
        if suspicious:
            if len(suspicious) > 5:
                return f"* Se detectaron {len(suspicious)} procesos sospechosos/anómalos.\n"
            return "* Procesos detectados: " + ", ".join(f"**{p}**" for p in suspicious) + ".\n"
        return "* Actividad de procesos verificada.\n"

    def _get_recommended_actions(self, score: int, findings: List[Dict[str, Any]]) -> List[str]:
        actions = []
        
        # 1. Critical Actions
        if score < 50:
            actions.append("**DESCONEXIÓN INMEDIATA**: Desconecte el equipo de la red.")
        
        # 2. Contextual Actions
        modules = set(f.get("module") for f in findings)
        all_text = " ".join([self._extract_details_human(f) for f in findings]).lower()

        # Collect Open Ports specifically
        open_ports = set()
        for f in findings:
             # Check for structured data
            res_data = f.get("result", {}).get("data", [])
            if isinstance(res_data, list):
                for host in res_data:
                     # Duck typing for host dict
                     if isinstance(host, dict):
                         ports = host.get("open_ports", [])
                         if ports:
                             for p in ports: open_ports.add(p)
            
            # Check text fallback (simple regex-like extraction could go here if needed, but structured is preferred)
            # The current setup relies heavily on "sensor_network_discovery" providing structured data.

        if "port" in all_text or "puerto" in all_text or open_ports:
            # Build a SINGLE action string with nested lines
            port_msg = "Cierre puertos no esenciales en el Firewall:"
            if open_ports:
                for p in sorted(list(open_ports)):
                    # Use \n\n or \n + indentation to force render structure
                    # Using <br> might be safer if markdown newlines fail, but let's try strict markdown first:
                    # A list item containing newlines usually needs double space indentation.
                    # But since we are inside a bullet "- ", we want new lines.
                    port_msg += f"\n  • {p}"
            else:
                 port_msg += "\n  • (Verifique puertos 445, 3389, etc)"
            
            actions.append(port_msg)
        
        if "update" in all_text or "sensor_vulnerabilidades" in modules:
            actions.append("Ejecute **Windows Update** y reinicie el sistema.")
            
        if "defender" in all_text:
            actions.append("Habilite Windows Defender o su antivirus corporativo.")

        return actions
