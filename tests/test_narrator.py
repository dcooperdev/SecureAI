import pytest
from galt.ui.narrator import OfflineNarrator

class TestOfflineNarrator:
    
    @pytest.fixture
    def narrator(self):
        return OfflineNarrator()

    def test_critical_section(self, narrator):
        """Verify Critical threats appear in the Alert section."""
        data = {
            "score": 40,
            "findings": [
                {
                    "module": "sensor_network_discovery",
                    "result": {"severity": "CRITICAL", "details": "Port 3389 Open on 0.0.0.0"}
                }
            ]
        }
        summary = narrator.generate_summary(data)
        
        assert "🚨 Amenazas Críticas y Altas" in summary
        assert "Port 3389 Open" in summary
        assert "DESCONEXIÓN INMEDIATA" in summary

    def test_network_grouping(self, narrator):
        """Verify that network findings handle structured host data."""
        data = {
            "score": 70,
            "findings": [
                {
                    "module": "sensor_network_discovery",
                    "description": "Network Scan Results",
                    "result": {
                        "severity": "MEDIUM", 
                        "data": [
                            {"ip": "192.168.1.10", "open_ports": [22, 80]},
                            {"ip": "192.168.1.20", "open_ports": [445]}
                        ]
                    }
                }
            ]
        }
        summary = narrator.generate_summary(data)
        
        assert "🛡️ Seguridad de Red" in summary
        assert "IP **192.168.1.10** tiene puertos abiertos: 22, 80" in summary
        assert "IP **192.168.1.20** tiene puertos abiertos: 445" in summary

    def test_system_formatting(self, narrator):
        """Verify System Extractor identifies Defender issues."""
        data = {
            "score": 60,
            "findings": [
                {
                    "module": "sensor_sistema",
                    "result": {"details": "Windows Defender Disabled"}
                }
            ]
        }
        summary = narrator.generate_summary(data)
        
        assert "⚠️ **Antivirus:** Windows Defender Disabled" in summary
        assert "Habilite Windows Defender" in summary

    def test_process_grouping(self, narrator):
        """Verify Process Extractor lists names."""
        data = {
            "score": 80,
            "findings": [
                {"module": "sensor_procesos", "result": {"details": "Suspicious process: miner.exe"}},
                {"module": "sensor_procesos", "result": {"details": "Suspicious process: nc.exe"}}
            ]
        }
        summary = narrator.generate_summary(data)
        
        assert "**miner.exe**" in summary
        assert "**nc.exe**" in summary

    def test_empty_findings(self, narrator):
        data = {"score": 95, "findings": []}
        summary = narrator.generate_summary(data)
        
        assert "Sistema Estable" in summary
        assert "No hay hallazgos técnicos registrados" in summary
