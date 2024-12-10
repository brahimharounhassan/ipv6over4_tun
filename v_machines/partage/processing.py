import socket
import struct
from typing import Union

class Encapsulate:
    def __init__(self) -> 'Encapsulate':
        pass
    
    def calculate_checksum(self, data: bytes) -> int:
        """Calculer le checksum pour l'en-tête IPv4."""
        if len(data) % 2:
            data += b'\x00'
        checksum = sum(struct.unpack("!%dH" % (len(data) // 2), data))
        checksum = (checksum >> 16) + (checksum & 0xFFFF)
        checksum += (checksum >> 16)
        return ~checksum & 0xFFFF
    
    def calculate_checksum2(self, data: bytes) -> int:
        s = 0
        for i in range(0, len(data), 2):
            w = (data[i] << 8) + (data[i+1] if i+1 < len(data) else 0)
            s += w
        s = (s >> 16) + (s & 0xFFFF)
        s += (s >> 16)
        return ~s & 0xFFFF
    
    
    def create_ipv4_header(self, src_ip: str, dst_ip: str, ipv6_paquet: int, protocol:int=41) -> bytes:
        version = 4
        ihl = 5  # Header length in 32-bit words
        version_ihl = (version << 4) + ihl
        # version_ihl = (version << 4) | 5  # Version 4, Header Length = 5 (20 octets)
        dscp = 0  # Type of Service
        total_length = 20 + len(ipv6_paquet)  # Header + payload
        identification = 0 #54321
        flags_fragment_offset = 0  # No fragmentation
        ttl = 64  # Time to Live
        header_checksum = 0  # Checksum placeholder
        src_ip = socket.inet_aton(src_ip) # binary format conversion
        dst_ip = socket.inet_aton(dst_ip)

        # build  IPv4 header without checksum
        ipv4_header = struct.pack(
        "!BBHHHBBH4s4s",
        version_ihl, dscp, total_length, identification, flags_fragment_offset,
        ttl, protocol, header_checksum, src_ip, dst_ip)

        # Checksum calculation
        header_checksum = self.calculate_checksum2(ipv4_header)

        # Rebuild the IPv4 header with checksum
        ipv4_header = struct.pack(
            "!BBHHHBBH4s4s",
            version_ihl, dscp, total_length, identification, flags_fragment_offset,
            ttl, protocol, header_checksum, src_ip, dst_ip
        )
        
        return ipv4_header
        
        
    def encapsulate_ipv6_in_tcp_ipv4(self, src_ipv4: str, dst_ipv4: str, ipv6_packet: bytes) -> bytes:
        """Encapsulate an ipv6 packet into IPv4."""
        ipv4_header = self.create_ipv4_header(src_ipv4, dst_ipv4, ipv6_packet)
        ipv4_packet = ipv4_header + ipv6_packet
        return ipv4_packet
        

    def head_len_in(self, packet: bytes) -> bytes:
        # Calculer la taille du paquet IPv6 (sans les en-têtes)
        packet_size = len(packet)
        
        # Créer un en-tête de 2 octets pour la taille du paquet
        size_header = struct.pack("!H", packet_size)  # !H = unsigned short (2 octets)
        
        # Ajouter la taille au début du paquet IPv6
        return size_header + packet


    
    def head_auto(self, packet: bytes) -> bytes:
        pass


class Decapsulate:
    
    def __init__(self) -> 'Decapsulate':
        pass

    def decapsulate_ipv6_from_ipv4(self, ipv4_packet: bytes) -> dict:
        ipv4_header = ipv4_packet[:20]
        ipv6_packet = ipv4_packet[20:]
        unpacked = struct.unpack("!BBHHHBBH4s4s", ipv4_header)
        protocol = unpacked[6]
        if protocol != 41:
            # raise ValueError("It's not an IPv6 packet encapsulated")
            print("It's not an IPv6 packet encapsulated")
        return {'ipv6_packet': ipv6_packet, 'ipv4_header': ipv4_header}      
        
    
    def head_len_out(self, packet: bytes) -> bytes:
        
        # Extraire les 2 premiers octets qui contiennent la taille
        size_header = packet[:2]
        
        # Dépackager la taille du paquet (2 octets)
        packet_size = struct.unpack("!H", size_header)[0]
        
        # Extraire le paquet IPv6 sans les 2 octets de taille
        ipv6_packet = packet[2:]
        
        # Vérifier si la taille est correcte (facultatif)
        if len(ipv6_packet) != packet_size:
            raise ValueError("La taille du paquet ne correspond pas à la taille attendue.")
        
        return ipv6_packet
        
