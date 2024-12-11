import socket

class Processing:
    """
    Handles the encapsulation and decapsulation of IPv6 packets within IPv4 packets.

    Attributes:
        ipv4_src (str): The source IPv4 address.
        ipv4_dst (str): The destination IPv4 address.
    """
    def __init__(self, ipv4_src:str, ipv4_dst:str):
        """
        Initializes the Processing class with source and destination IPv4 addresses.

        Args:
            ipv4_src (str): The source IPv4 address.
            ipv4_dst (str): The destination IPv4 address.
        """
        self.ipv4_src = ipv4_src
        self.ipv4_dst = ipv4_dst

    def encapsulate(self, ipv6_packet: bytes):
        """
        Encapsulates an IPv6 packet into an IPv4 packet.

        Args:
            ipv6_packet (bytes): The raw IPv6 packet to be encapsulated.

        Returns:
            bytes: The encapsulated packet with an IPv4 header.
        """
        ipv4_header = IPv4Header(self.ipv4_src, self.ipv4_dst)
        return ipv4_header.build() + ipv6_packet

    def decapsulate(self, encapsulated_packet: bytes):
        """
        Decapsulates an IPv6 packet from an IPv4 packet.

        Args:
            encapsulated_packet (bytes): The encapsulated IPv4 packet containing the IPv6 payload.

        Returns:
            bytes: The raw IPv6 packet extracted from the IPv4 packet.
        """
        # IPv4 header is 20 bytes for a standard header
        return encapsulated_packet[20:]
    
    
class IPv4Header:
    """
    Represents an IPv4 header and provides methods to build and calculate checksums for the header.

    Attributes:
        src_ip (str): The source IPv4 address.
        dst_ip (str): The destination IPv4 address.
        version (int): The IP version (default is 4 for IPv4).
        ihl (int): Internet Header Length (default is 5 for a standard header).
        tos (int): Type of Service (default is 0).
        total_length (int): Total packet length (set to 0; kernel sets this for raw sockets).
        id (int): Packet ID (default is 54321).
        flags_offset (int): Flags and fragment offset (default is 0).
        ttl (int): Time to Live (default is 64).
        protocol (int): Protocol number (default is 41 for IPv6 encapsulation in IPv4).
        checksum (int): Header checksum (default is 0; calculated later).
    """
    def __init__(self, src_ip: str, dst_ip: str):
        """
        Initializes the IPv4Header with source and destination IP addresses.

        Args:
            src_ip (str): The source IPv4 address.
            dst_ip (str): The destination IPv4 address.
        """
        self.src_ip = src_ip
        self.dst_ip = dst_ip
        self.version = 4
        self.ihl = 5
        self.tos = 0
        self.total_length = 0  # Kernel sets this for raw sockets
        self.id = 54321
        self.flags_offset = 0
        self.ttl = 64
        self.protocol = 41  # Protocol number for IPv6 encapsulation in IPv4
        self.checksum = 0  # Kernel sets this for raw sockets

    def build(self):
        """
        Builds the IPv4 header in binary format.

        Returns:
            bytes: The constructed IPv4 header with checksum calculated.
        """
        ver_ihl = (self.version << 4) + self.ihl
        header_without_checksum = (
            ver_ihl.to_bytes(1, 'big') +
            self.tos.to_bytes(1, 'big') +
            self.total_length.to_bytes(2, 'big') +
            self.id.to_bytes(2, 'big') +
            self.flags_offset.to_bytes(2, 'big') +
            self.ttl.to_bytes(1, 'big') +
            self.protocol.to_bytes(1, 'big') +
            self.checksum.to_bytes(2, 'big') +
            socket.inet_aton(self.src_ip) +
            socket.inet_aton(self.dst_ip)
        )
        self.checksum = self.calculate_checksum(header_without_checksum)
        return (
            ver_ihl.to_bytes(1, 'big') +
            self.tos.to_bytes(1, 'big') +
            self.total_length.to_bytes(2, 'big') +
            self.id.to_bytes(2, 'big') +
            self.flags_offset.to_bytes(2, 'big') +
            self.ttl.to_bytes(1, 'big') +
            self.protocol.to_bytes(1, 'big') +
            self.checksum.to_bytes(2, 'big') +
            socket.inet_aton(self.src_ip) +
            socket.inet_aton(self.dst_ip)
        )

    @staticmethod
    def calculate_checksum(header: bytes) -> int:
        """
        Calculates the checksum for the IPv4 header.

        Args:
            header (bytes): The header data for which the checksum is calculated.

        Returns:
            int: The calculated checksum value.
        """
        if len(header) % 2 != 0:
            header += b'\x00'

        checksum = 0
        for i in range(0, len(header), 2):
            word = (header[i] << 8) + header[i + 1]
            checksum += word
            while checksum > 0xFFFF:  # Handle overflow
                checksum = (checksum & 0xFFFF) + (checksum >> 16)

        return ~checksum & 0xFFFF
