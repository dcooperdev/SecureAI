import re
from typing import Final

def sanitize(text: str) -> str:
    """
    Sanitizes PII, user paths, and IP addresses from the input text.
    """
    # 1. Windows Paths: C:\Users\Username -> C:\Users\[USER]
    # No trailing backslash enforcement
    text = re.sub(r'(C:\\Users\\[^\\]+)', r'C:\\Users\\[USER]', text, flags=re.IGNORECASE)
    
    # 2. Linux Paths: /home/username -> /home/[USER]
    text = re.sub(r'(/home/[^/]+)', r'/home/[USER]', text)
    
    # 3. IPv4 Addresses: 192.168.1.5 -> [IP]
    # Simple regex for IPv4 (0-255.0-255.0-255.0-255)
    # Using a slightly robust pattern to avoid matching version numbers tightly if possible, 
    # but for safety, we redact anything looking like an IP.
    ip_pattern = r'\b(?:\d{1,3}\.){3}\d{1,3}\b'
    text = re.sub(ip_pattern, '[IP]', text)
    
    # 4. Hostnames (Heuristic based on "Host: <name>" pattern as discussed in tests)
    # or just generic hostnames? 
    # Proactive approach: Redact computer names in UNC paths \\SERVER\Share -> \\[HOST]\Share
    text = re.sub(r'\\\\([^\\]+)', r'\\\\[HOST]', text)
    
    return text
