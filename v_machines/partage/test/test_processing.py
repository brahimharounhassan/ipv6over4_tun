import unittest
from unittest.mock import patch
import socket
from processing import Processing, IPv4Header

class TestProcessing(unittest.TestCase):

    def setUp(self):
        self.processor = Processing("192.168.1.1", "192.168.1.2")
        self.sample_ipv6_packet = b"\x60\x00\x00\x00\x00\x06\x3a\x40"  # Sample minimal IPv6 packet header

    def test_encapsulate(self):
        result = self.processor.encapsulate(self.sample_ipv6_packet)
        self.assertTrue(result.startswith(socket.inet_aton("192.168.1.1")))  # Check source IP
        self.assertTrue(result.endswith(self.sample_ipv6_packet))  # Ensure payload is intact

    def test_decapsulate(self):
        encapsulated_packet = self.processor.encapsulate(self.sample_ipv6_packet)
        result = self.processor.decapsulate(encapsulated_packet)
        self.assertEqual(result, self.sample_ipv6_packet)  # Check that original payload matches


class TestIPv4Header(unittest.TestCase):

    def setUp(self):
        self.src_ip = "192.168.1.1"
        self.dst_ip = "192.168.1.2"
        self.header = IPv4Header(self.src_ip, self.dst_ip)

    def test_build(self):
        result = self.header.build()
        self.assertEqual(len(result), 20)  # Standard IPv4 header length
        self.assertEqual(result[0] >> 4, 4)  # Ensure version is IPv4
        self.assertEqual(result[0] & 0x0F, 5)  # Ensure IHL is 5

    def test_calculate_checksum(self):
        with patch("socket.inet_aton", side_effect=lambda x: b"\xc0\xa8\x01\x01" if x == "192.168.1.1" else b"\xc0\xa8\x01\x02"):
            header_data = self.header.build()
            calculated_checksum = self.header.calculate_checksum(header_data[:20])
            self.assertEqual(calculated_checksum, self.header.checksum)  # Check if checksum matches

if __name__ == "__main__":
    unittest.main()

    # python -m unittest testp_processing.py