import socket
from threading import Thread, Lock
import os
from processing import *

BUFFER_SIZE = 4096  

class Extremity:
    
    def __init__(self,tun_address:str, tun_fd: int, src_address: str, dst_address: str, src_port: int, dst_port: int, proto: str="tcp") -> 'Extremity':
        self.src_port = src_port
        self.dst_port = dst_port
        self.proto = proto.lower()
        self.tun_fd = tun_fd
        self.dst_address = dst_address
        self.src_address = src_address
        self.threads = []
        self.tun_address = tun_address
        self.connected_client = {}
        self.connected_client_lock = Lock()
        
        self.encapsulate = Encapsulate()
        self.decapsulate = Decapsulate()
        
    def start(self) -> None :
        self.ext_out()
        self.close_all()
        
   
    def ext_out(self) -> None:
        """Initialize the server socket and start listening."""
        
        try:
            server = socket.socket(socket.AF_INET6, socket.SOCK_STREAM if self.proto == "tcp" else socket.SOCK_DGRAM)
            server.bind(("", self.src_port))
                        
            self.tcp(server) if self.proto == "tcp" else self.udp(server)
        
        except Exception as e:
            print(f"Can not connect to port: {self.src_port}")
            print(f"On ext_out func (server) --> Error: {e}")
            server.close()
            
        
    def ext_in(self, client) -> None:
        """Handle incoming connections based on protocol."""
        
        """Send data from the local tunnel to the remote endpoint."""
        print("Ipv6 writer Thread launched...")
            
        while True:
            try:
                ipv6_packet = os.read(self.tun_fd, BUFFER_SIZE)
                if ipv6_packet:
                    ipv4_header = self.encapsulate.encapsulate_ipv6_in_tcp_ipv4(
                        self.src_address,
                        self.dst_address, 
                        ipv6_packet)
                    encapsulated_packet = ipv4_header + ipv6_packet
                    if encapsulated_packet:
                        client.sendall(encapsulated_packet)
                        print(f"Data sended from local tunnel to {self.dst_address}")
                else:
                    break
            except Exception as e:
                print(f"Impossible to send data to {self.dst_address}:")
                print(f"On reading data (func send_to_tun_extrimity) --> Error: {e}")
                break
            
        client.close()
        exit(1)

    def tcp(self, server) -> None:
        """Handle TCP connections."""                                                                                                                           
        
        print("TCP connection mode.")       
        print(f"Server {self.proto} started --> listening on port: {self.src_port}")
        client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        while True:                                                                                                                         
            print("Waiting for new connections...")
            try:
                client.connect((self.dst_address, self.dst_port))
                print("Connexion established with: ", self.dst_address)
                writer = Thread(target=self.ext_in,args=(client,))
                writer.daemon = True
                writer.start()
                self.threads.append(writer)
            except Exception as e:
                pass


            server.listen()
            connexion, client_address = server.accept()
            
            print(f"Connected with: {client_address}")
            if client_address[0].split(":")[-1] != self.dst_address:
                reader = Thread(target=self.receive_from_ipv6, args=(connexion,))
                reader.daemon = True
                reader.start()
                self.threads.append(reader)
                
                writer = Thread(target=self.ext_in,args=(client,))
                writer.daemon = True
                writer.start()
                self.threads.append(writer)

            else: 
                t = Thread(target=self.from_ipv4_to_tun, args=(connexion,))
                t.daemon = True
                t.start()
                self.threads.append(t)
                
    
    def receive_from_ipv6(self, connexion) -> None:
        """Receive data from the IPv6 client."""
        
        print("Ipv6 reader Thread launched...")
        print(f"Receiving data from: {connexion.getpeername()[0]}")
        while True:
            try:
                ipv6_packet = connexion.recv(BUFFER_SIZE) if self.proto == "tcp" else connexion.recvfrom(BUFFER_SIZE)[0]
                    
                if ipv6_packet:
                    print("Packet type: ", self.check_packet_type(ipv6_packet))
                    self.save_to_local_tun(ipv6_packet=ipv6_packet)
                else:
                    break
                    
            except Exception as e:
                print(f"Enable to read data from {connexion.getpeername()[0]}")
                print(f"On reading data (func run) --> Error: {e}",)
                break
        connexion.close()
        
    def save_to_local_tun(self, ipv6_packet) -> None:
        """Write the IPv6 packet to the local tunnel."""
        try:
            os.write(self.tun_fd, ipv6_packet)
            print(f"Ipv6 wrote into local tunnel.")
        except Exception as e:
            print(f"Enable to write data into local tunnel.")
            print(f"On save_to_local_tun func --> Error: {e}") 
                   

    def from_ipv4_to_tun(self, client_connexion) -> None:
        """Receive and process encapsulated IPv6 packets from IPv4."""
        
        print("Ipv4 Receiver  Thread launched...")
        print(f"Receiving data from: {client_connexion.getpeername()[0]}")                    
        while True:
            try:
                encapsulated_packet = client_connexion.recv(BUFFER_SIZE)  
                print("IPv4 data received:", encapsulated_packet)
                if encapsulated_packet:
                    print(self.identify_tunnel_packet(encapsulated_packet))
                    decapsulated_packet = self.decapsulate.decapsulate_ipv6_from_ipv4(encapsulated_packet)
                    ipv4_header = decapsulated_packet["ipv4_header"]
                    ipv6_packet = decapsulated_packet["ipv6_packet"]
                    
                    print(f"Decapsulated IPv4 header: {ipv4_header}")
                    print("Decapsulated IPv6: ", ipv6_packet)
                    
                    self.save_to_local_tun(ipv6_packet)
                    
                else: 
                    break
                
            except Exception as e:
                print(f"Enable to read data from {client_connexion.getpeername()[0]}")
                print(f"On reading data (func run) --> Error: ", e)
                break
        client_connexion.close()
       
        
    def udp(self, connexion) -> None:  
        """Handle UDP communication."""
        
        print("UDP connexion.")
        self.receive_from_ipv6(connexion)
     
        
    def close_all(self) -> None:
        """Clean up resources."""
        self.join_threads()


    def join_threads(self) -> None:
        """Wait for all threads to finish."""
        for t in self.threads:
            t.join()
    
     
    def check_packet_protocol(self, packet: bytes) -> str:
        if len(packet) < 20:  
            return "Invalid IPv4 packet"
        
        ipv4_header = packet[:20]
    
        header_fields = struct.unpack('!BBHHHBBH4s4s', ipv4_header)
        protocol = header_fields[6]
            
        # protocol = packet[9]  
        if protocol == 0x01:
            return "ICMP"
        elif protocol == 0x02:
            return "IGMP"
        elif protocol == 0x06:
            return "TCP"
        elif protocol == 0x11:
            return "UDP"
        elif protocol == 0x29:
            return "ENCAP"
        elif protocol == 0x59:
            return "OSPF"
        elif protocol == 0x84:
            return "SCTP"
        else:
            return f"Unknown protocol (0x{protocol:02x})"
        
  
    def check_packet_type(self, packet: bytes) -> str:
        if len(packet) < 1:
            return "Unknown (empty packet)"
        
        version = packet[0] >> 4  
        if version == 4:
            return "IPv4"
        elif version == 6:
            return "IPv6"
        else:
            return "Unknown type"
 
        
    def identify_tunnel_packet(self, packet: bytes) -> str:
        if len(packet) < 20:  # Check the min length of IPv4 packet
            return "Invalid packet"

        # Analyse the IPv4 protocol
        outer_protocol = self.check_packet_protocol(packet)
        if outer_protocol == "ENCAP":
            inner_type = self.check_packet_type(packet)
            return f"Tunnel IPv4 -> {inner_type}"
        return f"Non-tunnelled {outer_protocol}"
        
             