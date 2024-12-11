import unittest
from unittest.mock import patch, MagicMock
from extremity import Extremity
import os
import socket

class TestExtremity(unittest.TestCase):

    def setUp(self):
        self.tun_fd = 100  # Mock file descriptor
        self.tun_address = "2001:db8::1"
        self.src_address = "2001:db8::2"
        self.dst_address = "2001:db8::3"
        self.src_port = 12345
        self.dst_port = 54321
        self.proto = "tcp"
        self.extremity = Extremity(
            tun_address=self.tun_address,
            tun_fd=self.tun_fd,
            src_address=self.src_address,
            dst_address=self.dst_address,
            src_port=self.src_port,
            dst_port=self.dst_port,
            proto=self.proto,
        )

    @patch("os.read")
    def test_ext_in(self, mock_read):
        mock_read.return_value = b"mock_ipv6_packet"
        mock_client = MagicMock()
        self.extremity.processing.encapsulate = MagicMock(return_value=b"encapsulated_packet")

        self.extremity.ext_in(mock_client)

        mock_client.sendall.assert_called_with(b"encapsulated_packet")

    @patch("socket.socket")
    def test_ext_out_tcp(self, mock_socket):
        mock_server = MagicMock()
        mock_socket.return_value = mock_server
        self.extremity.tcp = MagicMock()

        self.extremity.ext_out()

        mock_server.bind.assert_called_with(("", self.src_port))
        self.extremity.tcp.assert_called_once_with(mock_server)

    def test_check_packet_protocol(self):
        ipv4_packet = b'\x45\x00\x00\x3c\x1c\x46\x40\x00\x40\x06\xb1\xe6\xc0\xa8\x01\x02\xc0\xa8\x01\x01'
        result = self.extremity.check_packet_protocol(ipv4_packet)
        self.assertEqual(result, "TCP")

    def test_check_packet_type_ipv4(self):
        ipv4_packet = b'\x45\x00\x00\x3c'
        result = self.extremity.check_packet_type(ipv4_packet)
        self.assertEqual(result, "IPv4")

    def test_check_packet_type_ipv6(self):
        ipv6_packet = b'\x60\x00\x00\x00'
        result = self.extremity.check_packet_type(ipv6_packet)
        self.assertEqual(result, "IPv6")

    @patch("os.write")
    def test_save_to_local_tun(self, mock_write):
        ipv6_packet = b"mock_ipv6_packet"
        self.extremity.save_to_local_tun(ipv6_packet)
        mock_write.assert_called_with(self.tun_fd, ipv6_packet)

    @patch("socket.socket")
    def test_tcp(self, mock_socket):
        mock_server = MagicMock()
        mock_client = MagicMock()
        mock_socket.side_effect = [mock_client, mock_server]

        self.extremity.tcp(mock_server)

        mock_client.connect.assert_called_with((self.dst_address, self.dst_port))

    def test_get_protocol_name_known(self):
        protocol_name = self.extremity._get_protocol_name(0x06)
        self.assertEqual(protocol_name, "TCP")

    def test_get_protocol_name_unknown(self):
        protocol_name = self.extremity._get_protocol_name(0x99)
        self.assertEqual(protocol_name, "Unknown protocol (0x99)")

    def test_identify_tunnel_packet(self):
        packet = b'\x45\x00\x00\x3c\x1c\x46\x40\x00\x40\x29\xb1\xe6\xc0\xa8\x01\x02\xc0\xa8\x01\x01'
        result = self.extremity.identify_tunnel_packet(packet)
        self.assertIn("Tunnel IPv4", result)

    @patch("os.read", side_effect=IOError("Failed to read"))
    def test_ext_in_read_failure(self, mock_read):
        mock_client = MagicMock()
        self.extremity.ext_in(mock_client)
        mock_client.close.assert_called_once()

    @patch("socket.socket")
    def test_udp(self, mock_socket):
        mock_connexion = MagicMock()
        self.extremity.receive_from_ipv6 = MagicMock()

        self.extremity.udp(mock_connexion)

        self.extremity.receive_from_ipv6.assert_called_once_with(mock_connexion)

if __name__ == "__main__":
    unittest.main()
    # python -m unittest test_extremity.py

