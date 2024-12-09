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
    
    def len_header_in(self):
        pass
    
    def len_header_out(self):
        pass
    
    def create_ipv4_header(self, src_ip: str, dst_ip: str, payload_length: int, protocol:int=41) -> bytes:
        version = 4
        ihl = 5  # Header length in 32-bit words
        version_ihl = (version << 4) + ihl
        tos = 0  # Type of Service
        total_length = 20 + payload_length  # Header + payload
        identification = 54321
        flags_fragment_offset = 0  # No fragmentation
        ttl = 64  # Time to Live
        checksum = 0  # Checksum placeholder
        src_ip = socket.inet_aton(src_ip)
        dst_ip = socket.inet_aton(dst_ip)

        # Construire l'en-tête IPv4 sans checksum
        ipv4_header = struct.pack(
        "!BBHHHBBH4s4s",
        version_ihl, tos, total_length, identification, flags_fragment_offset,
        ttl, protocol, checksum, src_ip, dst_ip)

        # Calculer le checksum
        checksum = self.calculate_checksum(ipv4_header)

        # Recréer l'en-tête IPv4 avec le checksum
        ipv4_header = struct.pack(
            "!BBHHHBBH4s4s",
            version_ihl, tos, total_length, identification, flags_fragment_offset,
            ttl, protocol, checksum, src_ip, dst_ip
        )
        
        return ipv4_header


    def create_tcp_header(self, src_ip: str, dst_ip: str, src_port: int, dst_port: int, payload: bytes) -> bytes:
        """Créer un en-tête TCP avec une charge utile."""
        seq_number = 0
        ack_number = 0
        data_offset = 5  # Header length in 32-bit words
        reserved = 0
        flags = 2  # SYN flag
        window_size = 5840
        checksum = 0
        urgent_pointer = 0

        tcp_header = struct.pack(
            "!HHLLBBHHH",
            src_port, dst_port, seq_number, ack_number,
            (data_offset << 4) + reserved, flags, window_size,
            checksum, urgent_pointer
        )

        # Pseudo-en-tête pour le calcul du checksum TCP
        pseudo_header = struct.pack(
            "!4s4sBBH",
            socket.inet_aton(src_ip), socket.inet_aton(dst_ip),
            0, 6, len(tcp_header) + len(payload)
        )

        checksum = self.calculate_checksum(pseudo_header + tcp_header + payload)
    
        # Recréer l'en-tête TCP avec le checksum
        tcp_header = struct.pack(
            "!HHLLBBHHH",
            src_port, dst_port, seq_number, ack_number,
            (data_offset << 4) + reserved, flags, window_size,
            checksum, urgent_pointer
        )

        return tcp_header
        
        
    def encapsulate_ipv6_in_tcp_ipv4(self, src_ipv4: str, dst_ipv4: str, src_port: int, dst_port: int, ipv6_packet: bytes) -> bytes:
        """Encapsuler un paquet IPv6 dans TCP sur IPv4."""
        # ipv6_packet = self.head_len_in(ipv6_packet)
        tcp_header = self.create_tcp_header(src_ipv4, dst_ipv4, src_port, dst_port, ipv6_packet)
        payload_length = len(tcp_header) + len(ipv6_packet)
        ipv4_header = self.create_ipv4_header(src_ipv4, dst_ipv4, payload_length)
        ipv4_packet = ipv4_header + tcp_header + ipv6_packet
        return ipv4_packet
    
    # def head_auto(self, packet: bytes) -> bytes:
        

    def head_len_in(self, packet: bytes) -> bytes:
        # Calculer la taille du paquet IPv6 (sans les en-têtes)
        packet_size = len(packet)
        
        # Créer un en-tête de 2 octets pour la taille du paquet
        size_header = struct.pack("!H", packet_size)  # !H = unsigned short (2 octets)
        
        # Ajouter la taille au début du paquet IPv6
        return size_header + packet


class Decapsulate:
    
    def __init__(self) -> 'Decapsulate':
        pass

    def parse_ipv4_header(self, packet: bytes) -> dict:
        """Analyser un en-tête IPv4."""
        """Parse un en-tête IPv4 brut et retourne ses champs."""
        ipv4_header = packet[:20]
        unpacked = struct.unpack("!BBHHHBBH4s4s", ipv4_header)
        version_ihl = unpacked[0]
        version = version_ihl >> 4
        ihl = (version_ihl & 0xF) * 4
        total_length = unpacked[2]
        protocol = unpacked[6]
        src_ip = socket.inet_ntoa(unpacked[8])
        dst_ip = socket.inet_ntoa(unpacked[9])
        return {
            "version": version,
            "ihl": ihl,
            "total_length": total_length,
            "protocol": protocol,
            "src_ip": src_ip,
            "dst_ip": dst_ip,
        }
       
        
    def parse_tcp_header(self, packet: bytes, offset: int)-> Union[dict,int]:
        """Analyser un en-tête TCP."""
        tcp_header = packet[offset:offset + 20]
        unpacked = struct.unpack("!HHLLBBHHH", tcp_header)
        src_port = unpacked[0]
        dst_port = unpacked[1]
        sequence = unpacked[2]
        acknowledgment = unpacked[3]
        data_offset = (unpacked[4] >> 4) * 4
        flags = unpacked[5]
        return {
            "src_port": src_port,
            "dst_port": dst_port,
            "sequence": sequence,
            "acknowledgment": acknowledgment,
            "data_offset": data_offset,
            "flags": flags,
        }, offset + data_offset
       
        
    def decapsulate_ipv6_from_ipv4(self, packet: bytes) -> dict:
        """Décapsuler un paquet IPv6 encapsulé dans un paquet IPv4 via TCP."""
        # Analyse de l'en-tête IPv4
        ipv4_info = self.parse_ipv4_header(packet)
        # if ipv4_info["protocol"] != 6:  # Vérifie si le protocole est TCP (6)
        #     raise ValueError("Le paquet n'est pas un paquet TCP.")
        
        # Analyse de l'en-tête TCP
        tcp_info, payload_offset = self.parse_tcp_header(packet, ipv4_info["ihl"])

        # Extraction de la charge utile IPv6
        ipv6_packet = packet[payload_offset:]
        return {
            "ipv4_info": ipv4_info,
            "tcp_info": tcp_info,
            "ipv6_packet": ipv6_packet
            # "ipv6_packet": self.head_len_out(ipv6_packet),
            }
        
    
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
        
