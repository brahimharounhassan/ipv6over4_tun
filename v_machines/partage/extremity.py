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
        self.treads = []
        self.tun_address = tun_address
        self.connected_client = {}
        self.connected_client_lock = Lock()
        
        self.server = None
        self.client = None
        self.connexion = None
        self.client_address = None
        
        self.encapsulate = Encapsulate()
        self.decapsulate = Decapsulate()
        
    
    
    def start(self) -> None :
        self.ext_out()
   
    
    def ext_out(self) -> None:
        """Initialize the server socket and start listening."""
        self.server = socket.socket(socket.AF_INET6, socket.SOCK_STREAM if self.proto == "tcp" else socket.SOCK_DGRAM)
        try:
            self.server.bind(("", self.src_port))
            print(f"Server started --> listening on port: {self.src_port}")
            self.ext_in()
        
        except Exception as e:
            print(f"Can not connect to port: {self.src_port}")
            print(f"On start func (server) --> Error: {e}")
            self.close_all()
            exit(1)
            
        
    def ext_in(self) -> None:
        """Handle incoming connections based on protocol."""
        self.tcp() if self.proto == "tcp" else self.udp()
        self.close_all()
    
            
    def tcp(self) -> None:
        """Handle TCP connections."""                                                                                                                           
        
        print("TCP connection mode.")
        self.client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        
        while True:                                                                                                                         
            try:
                self.server.listen()
                print("Waiting for new connections...")
                try:
                    self.connexion, self.client_address = self.server.accept()
                    print(f"Connected with: {self.client_address}")
                    if self.client_address[0].split(":")[-1] != self.dst_address:
                        t = Thread(target=self.receive_from_ipv6)
                        t.daemon = True
                        t.start()
                        self.treads.append(t)
                        
                    else: 
                        
                        # self.from_ipv4_to_tun()
                        t = Thread(target=self.from_ipv4_to_tun)
                        t.daemon = True
                        t.start()
                        self.treads.append(t)    
                         
                except Exception as e:
                    print(f"Enable to establish connexion.")
                    print(f"On tcp func (accept) --> Error: {e}")
                    break

            except Exception as e:
                print("Server stopped.")
                print(f"On tcp func (listen) --> Error: {e}.")
                break
                
        print("TCP connexion interrupted.")
        self.join_threads()
  
    
    def receive_from_ipv6(self) -> None:
        """Receive data from the IPv6 client."""
        
        self.add_client(self.dst_address, self.dst_port)
        
        print("Ipv6 Receiver  Thread launched...")
        # if not self.connected_client or not (self.dst_address, self.dst_port) in self.connected_client.keys():
        #     self.connected_client[(self.dst_address, self.dst_port)] = self.client
        try:
            self.client.connect((self.dst_address, self.dst_port))
            print(f"Connexion with {self.dst_address} established...")
        except Exception as e:
            print("Connexion impossible.")
            print(f"On host connexion (func receive_from_ipv6) --> Error: {e}")

        while True:
            try:
                ipv6_packet = self.connexion.recv(BUFFER_SIZE) if self.proto == "tcp" else self.server.recvfrom(BUFFER_SIZE)[0]
                print(f"Receiving data from: {self.client_address[0]}")
                    
                if ipv6_packet:
                    print( self.check_packet_type(ipv6_packet))
                    self.save_to_local_tun(ipv6_packet=ipv6_packet)
                    self.send_to_tun_extrimity()
                else:
                    self.remove_client(self.dst_address, self.dst_port)
                    break
                
            except Exception as e:
                print(f"Enable to read data from {self.client_address[0]}")
                print(f"On reading data (func run) --> Error: {e}",)
                self.remove_client(self.dst_address, self.dst_port)
                break
        exit(0)

        
    def save_to_local_tun(self, ipv6_packet: bytes) -> None:
        """Write the IPv6 packet to the local tunnel."""
        
        try:
            os.write(self.tun_fd, ipv6_packet)
            print(f"Writing data into local tunnel.")
            
        except Exception  as e:
            print(f"Enable to write data into local tunnel.")
            print(f"On save_to_local_tun func --> Error: {e}") 
       
 
    def send_to_tun_extrimity(self) -> None:
        """Send data from the local tunnel to the remote endpoint."""
        try:
            ipv6_packet = os.read(self.tun_fd, BUFFER_SIZE)
            print("Reading data from local tunnel")
            if ipv6_packet:
                ipv4_header = self.encapsulate.encapsulate_ipv6_in_tcp_ipv4(
                    self.src_address,
                    self.dst_address, 
                    self.src_port, 
                    self.dst_port, 
                    ipv6_packet)
                encapsulated_packet = ipv4_header + ipv6_packet
                # try:
                self.client.sendall(encapsulated_packet)
                print(f"Data sended from local tunnel to {self.dst_address}")
                # except Exception as e:
                #     print(f"Impossible  to send data from local to {self.dst_address}")
                #     print(f"On sending data (func send_to_tun_extrimity) --> Error: {e}")
                #     exit(0)        
        except Exception as e:
            print("Impossible to send data to {self.dst_address}:")
            print(f"On reading data (func send_to_tun_extrimity) --> Error: {e}")
                

    def from_ipv4_to_tun(self) -> None:
        """Receive and process encapsulated IPv6 packets from IPv4."""
        
        print("Ipv4 Receiver  Thread launched...")
        while True:
            try:
                encapsulated_packet = self.connexion.recv(BUFFER_SIZE)  
                print(f"Receiving data from: {self.connexion.getpeername()[0]}")                    
                if encapsulated_packet:
                    decapsulated_packet = self.decapsulate.decapsulate_ipv6_from_ipv4(encapsulated_packet)
                    print(self.check_packet_type(encapsulated_packet))
                    print(self.identify_tunnel_packet(encapsulated_packet))
                    print("Decapsulated IPv4 header:", decapsulated_packet["ipv4_info"])
                    
                    print("IPv4 header :", decapsulated_packet["ipv4_info"])
                    print("TCP header :", decapsulated_packet["tcp_info"])
                    print("Decapsulated IPv6:", decapsulated_packet["ipv6_packet"])
                    self.save_to_local_tun(decapsulated_packet["ipv6_packet"])
                else:
                    break
                
            except Exception as e:
                print(f"Enable to read data from {self.connexion.getpeername()[0]}")
                print(f"On reading data (func run) --> Error: ", e)
                self.connexion.close()
                break
        exit(0)    
       
        
    def udp(self) -> None:  
        """Handle UDP communication."""
        
        print("UDP connexion.")
        self.receive_from_ipv6()
     
        
    def close_all(self) -> None:
        """Clean up resources."""
        if self.server:
            self.server.close()
        if self.client:
            self.client.close()
        if self.tun_fd:
            os.close(self.tun_fd)
        self.join_threads()


    def join_threads(self) -> None:
        """Wait for all threads to finish."""
        for t in self.threads:
            t.join()
    
            
    def add_client(self, address: str, port: int) -> None:
        """Add a client to the connected clients list."""
        with self.connected_client_lock:
            if (address, port) not in self.connected_client:
                self.client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                self.client.connect((address, port))
                self.connected_client[(address, port)] = self.client
                print(f"Client added: {address}:{port}")
   
                
    def remove_client(self, address: str, port: int) -> None:
        """Remove a client from the connected clients list."""
        with self.connected_client_lock:
            if (address, port) in self.connected_client:
                self.connected_client[(address, port)].close()
                del self.connected_client[(address, port)]
                print(f"Client removed: {address}:{port}")
  
    
    def check_packet_protocol(self, packet: bytes) -> str:
        if len(packet) < 20:  
            return "Invalid IPv4 packet"
        
        protocol = packet[9]  
        if protocol == 0x06:
            return "TCP"
        elif protocol == 0x11:
            return "UDP"
        elif protocol == 0x01:
            return "ICMP"
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
        if len(packet) < 20:  # Vérification de la taille minimale d'un packet IPv4
            return "Invalid packet"

        # Analyser le protocole IPv4
        outer_protocol = self.check_packet_protocol(packet)
        if outer_protocol == "TCP":
            # Supposons que le contenu TCP encapsule IPv6
            encapsulated = packet[20:]  # Ignorer les 20 octets de l'en-tête IPv4
            inner_type = self.check_packet_type(encapsulated)
            return f"Tunnel IPv4 -> {inner_type}"
        return f"Non-tunnelled {outer_protocol}"
        
             