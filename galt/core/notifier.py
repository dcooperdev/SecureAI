
import sys
import subprocess
import shutil
from pathlib import Path

class Notifier:
    def send_notification(self, title: str, message: str, click_action: str = None):
        """
        Sends a cross-platform desktop notification.
        :param click_action: Optional path to a file to open when clicked.
        """
        try:
            if sys.platform == "win32":
                self._notify_windows(title, message, click_action)
            elif sys.platform == "darwin":
                self._notify_macos(title, message)
            elif sys.platform.startswith("linux"):
                self._notify_linux(title, message)
            else:
                self._fallback(title, message)
        except Exception as e:
            # print(f"DEBUG NOTIFIER ERROR: {e}") 
            self._fallback(title, message)

    def _notify_windows(self, title: str, message: str, click_action: str = None):
        # 1. Prepare Protocol Launch URI
        launch_attr = ""
        if click_action:
            try:
                uri = Path(click_action).absolute().as_uri()
                launch_attr = f'launch="{uri}" activationType="protocol"'
            except:
                pass

        # 2. Build XML
        # Escape for XML
        safe_title = title.replace('<', '&lt;').replace('>', '&gt;')
        safe_msg = message.replace('<', '&lt;').replace('>', '&gt;')
        
        toast_xml = f"""
        <toast {launch_attr}>
            <visual>
                <binding template="ToastGeneric">
                    <text>{safe_title}</text>
                    <text>{safe_msg}</text>
                </binding>
            </visual>
        </toast>
        """

        # 3. PowerShell Command using WinRT APIs
        # We use a trick to load the XML into a XmlDocument and create the toast
        ps_script = f"""
        $xml = @'
{toast_xml}
'@
        $appId = 'Galt.Security.Agent'
        
        # Load WinRT Types
        [Windows.UI.Notifications.ToastNotificationManager, Windows.UI.Notifications, ContentType=WindowsRuntime] | Out-Null
        [Windows.Data.Xml.Dom.XmlDocument, Windows.Data.Xml.Dom.XmlDocument, ContentType=WindowsRuntime] | Out-Null
        
        $toastXml = New-Object Windows.Data.Xml.Dom.XmlDocument
        $toastXml.LoadXml($xml)
        
        $toast = [Windows.UI.Notifications.ToastNotification]::new($toastXml)
        [Windows.UI.Notifications.ToastNotificationManager]::CreateToastNotifier($appId).Show($toast)
        """
        
        # Execute
        subprocess.run(["powershell.exe", "-Command", f"& {{ {ps_script} }}"], check=True)

    def _notify_linux(self, title: str, message: str):
        if shutil.which("notify-send"):
            subprocess.run(["notify-send", title, message], check=True)
        else:
            self._fallback(title, message)

    def _notify_macos(self, title: str, message: str):
        # Escape quotes for AppleScript
        safe_title = title.replace('"', '\\"')
        safe_msg = message.replace('"', '\\"')
        script = f'display notification "{safe_msg}" with title "{safe_title}"'
        subprocess.run(["osascript", "-e", script], check=True)

    def _fallback(self, title: str, message: str):
        print(f"[🔔] Galt: {title} - {message}")
