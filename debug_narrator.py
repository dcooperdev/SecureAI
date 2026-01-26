from reports.narrator import OfflineNarrator

narrator = OfflineNarrator()
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
print("DEBUG OUTPUT START")
print(summary)
print("DEBUG OUTPUT END")
