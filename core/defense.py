import subprocess
import platform
import logging

class FirewallManager:
    """
    Manages system firewall rules to block suspicious IPs.
    Supports Windows (netsh) and Linux (iptables).
    """
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)

    def block_ip(self, ip_address: str):
        """
        Blocks traffic from a specific IP address using the OS-native firewall.
        """
        system = platform.system().lower()
        command = []

        try:
            if system == "windows":
                # netsh advfirewall firewall add rule name="GALT_BLOCK_{ip}" dir=in action=block remoteip={ip}
                rule_name = f"GALT_BLOCK_{ip_address}"
                command = [
                    "netsh", "advfirewall", "firewall", "add", "rule",
                    f"name={rule_name}",
                    "dir=in",
                    "action=block",
                    f"remoteip={ip_address}"
                ]
            elif system == "linux":
                # iptables -A INPUT -s {ip} -j DROP
                command = [
                    "iptables", "-A", "INPUT", 
                    "-s", ip_address, 
                    "-j", "DROP"
                ]
            else:
                self.logger.warning(f"Unsupported OS for FirewallManager: {system}")
                return False

            self.logger.info(f"Executing Defense Rule: {' '.join(command)}")
            
            # Execute command
            # Note: subprocess.check_call raises CalledProcessError on non-zero exit code
            subprocess.run(command, check=True, capture_output=True, text=True)
            
            return True

        except subprocess.CalledProcessError as e:
            self.logger.error(f"Failed to block IP {ip_address}: {e}")
            return False
        except Exception as e:
            self.logger.error(f"Error in FirewallManager: {e}")
            return False
