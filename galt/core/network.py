import threading
import time
import logging
from collections import defaultdict
import sys

# Optional Dependency Management
try:
    from scapy.all import sniff, IP, TCP, Dot11Deauth, get_if_addr, conf
    _SCAPY_AVAILABLE = True
except ImportError:
    _SCAPY_AVAILABLE = False

# Local Imports
try:
    from galt.core.defense import FirewallManager
    from galt.core.notifier import Notifier
except ImportError:
    # Fallback for when running directly or in tests without full context
    sys.path.append("../..") 
    from galt.core.defense import FirewallManager
    from galt.core.notifier import Notifier

class NetworkSentinel(threading.Thread):
    def __init__(self, daemon=True):
        super().__init__(daemon=daemon)
        self.logger = logging.getLogger("Galt.NetworkSentinel")
        self.active = False
        self.syn_tracker = defaultdict(list)
        self.firewall = FirewallManager()
        self.notifier = Notifier()
        
        # Thresholds
        self.SYN_LIMIT = 20
        self.TIME_WINDOW = 2.0  # Seconds

    def run(self):
        if not _SCAPY_AVAILABLE:
            self.logger.warning("Scapy not installed. NetworkSentinel disabled.")
            return

        self.active = True
        self.logger.info("🛡️ Network Sentinel Started (Background)")

        try:
            # 1. Auto-config Local IP for filter
            # conf.iface might differ, using get_if_addr(conf.iface) matches active route
            try:
                my_ip = get_if_addr(conf.iface)
                # Strict BPF filter to reduce load: Only TCP meant for me
                bpf_filter = f"dst host {my_ip} and tcp"
            except Exception as e:
                self.logger.error(f"Could not determine local IP: {e}. Sniffing all TCP.")
                bpf_filter = "tcp"

            self.logger.info(f"   > Filter applied: {bpf_filter}")

            # 2. Start Sniffing
            # store=False: Don't keep packets in RAM
            # monitor=False: Promiscuous mode only (Safe for standard WiFi/Ethernet)
            sniff(
                filter=bpf_filter,
                store=False, 
                prn=self.process_packet,
                monitor=False,
                stop_filter=lambda x: not self.active
            )
            
        except Exception as e:
            self.logger.error(f"CRITICAL SCAPY ERROR: {e}")
            self.logger.warning("NetworkSentinel stopped due to driver/permission error.")
            # Likely Npcap missing on Windows or not root on Linux 
            
        self.active = False

    def process_packet(self, pkt):
        if not self.active: return

        current_time = time.time()

        # --- Vector 1: TCP SYN Flood Detection ---
        if pkt.haslayer(TCP) and pkt.haslayer(IP):
            # Check for SYN flag ONLY (0x02)
            # Flags can be object or int, checking 'S' string representation safe in Scapy
            if pkt[TCP].flags == 'S': 
                src_ip = pkt[IP].src
                
                # Cleanup old timestamps
                self.syn_tracker[src_ip] = [t for t in self.syn_tracker[src_ip] if current_time - t < self.TIME_WINDOW]
                
                # Add new
                self.syn_tracker[src_ip].append(current_time)
                
                # Check Threshold
                if len(self.syn_tracker[src_ip]) > self.SYN_LIMIT:
                    self._trigger_defense(src_ip, "TCP SYN Flood")
                    # Clear tracker to prevent spamming actions
                    del self.syn_tracker[src_ip]

        # --- Vector 2: Wi-Fi Deauth Detection (Best Effort) ---
        # Note: Usually requires Monitor Mode, but some drivers leak frames.
        if pkt.haslayer(Dot11Deauth):
            try:
                # Dot11 Address 2 is usually the sender (AP or Attacker spoofing AP)
                attacker_mac = pkt.addr2 
                self.logger.warning(f"⚠️ WiFi Deauth Frame detected from {attacker_mac}!")
                
                # We do NOT block MACs via Firewall (Layer 3), just notify.
                self.notifier.send_notification(
                    "⚠️ Ataque Wi-Fi Detectado", 
                    f"Posible Deauth Flood desde MAC: {attacker_mac}"
                )
            except AttributeError:
                pass

    def _trigger_defense(self, ip, attack_type):
        self.logger.critical(f"🚨 ATTACK CONFIRMED: {attack_type} from {ip}")
        
        # 1. BLOCK
        success = self.firewall.block_ip(ip)
        
        # 2. NOTIFY
        status = "Bloqueado" if success else "Fallo al Bloquear"
        self.notifier.send_notification(
            f"🛡️ Galt Defense: {attack_type}",
            f"IP: {ip}\nAcción: {status}"
        )

    def stop(self):
        self.active = False
