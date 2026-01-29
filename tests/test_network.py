import pytest
from unittest.mock import MagicMock, patch

import sys
# Mock Scapy imports handled by global conftest, but we import here
from galt.core.network import NetworkSentinel
import galt.core.network

class TestNetworkSentinel:
    
    @pytest.fixture
    def mock_dependencies(self):
        # Patch external calls to prevent errors
        with patch("galt.core.network.sniff"), patch("galt.core.network.get_if_addr"):
            yield

    @pytest.fixture
    def sentinel(self, mock_dependencies):
        with patch("galt.core.network._SCAPY_AVAILABLE", True):
            sentinel = NetworkSentinel()
            # Inject Mocks
            sentinel.firewall = MagicMock()
            sentinel.notifier = MagicMock()
            yield sentinel
            sentinel.stop()

    def test_syn_flood_trigger(self, sentinel, mock_dependencies):
        sentinel.active = True
        
        # USE THE ACTUAL OBJECTS FROM THE MODULE
        # Since we mocked scapy on import, these ARE mocks.
        NetTCP = galt.core.network.TCP
        NetIP = galt.core.network.IP
        
        mock_pkt = MagicMock()
        
        # Strict haslayer logic
        # We must handle specific arguments
        def haslayer_logic(layer):
            # print(f"DEBUG: checking haslayer {layer} vs TCP={NetTCP} IP={NetIP}")
            # print(f"DEBUG: Is match? {layer == NetTCP} or {layer == NetIP}")
            return layer == NetTCP or layer == NetIP
        
        mock_pkt.haslayer.side_effect = haslayer_logic
        
        mock_tcp_layer = MagicMock()
        mock_tcp_layer.flags = 'S'
        mock_ip_layer = MagicMock()
        mock_ip_layer.src = "1.2.3.4"
        
        def get_layer(cls):
            if cls == NetTCP: return mock_tcp_layer
            if cls == NetIP: return mock_ip_layer
            return MagicMock() # generic
        
        mock_pkt.__getitem__.side_effect = get_layer
        
        for i in range(21):
            sentinel.process_packet(mock_pkt)
            
        print(f"DEBUG TRACKER: {dict(sentinel.syn_tracker)}")
        print(f"DEBUG Firewall Calls: {sentinel.firewall.block_ip.call_args_list}")
        
        sentinel.firewall.block_ip.assert_called_with("1.2.3.4")

    def test_wifi_deauth_notify_only(self, sentinel, mock_dependencies):
        sentinel.active = True
        
        NetDeauth = galt.core.network.Dot11Deauth
        
        mock_pkt = MagicMock()
        mock_pkt.haslayer.side_effect = lambda l: l == NetDeauth
        mock_pkt.addr2 = "AA:BB:CC:DD:EE:FF"
        
        sentinel.process_packet(mock_pkt)
        
        sentinel.notifier.send_notification.assert_called()
        sentinel.firewall.block_ip.assert_not_called()
