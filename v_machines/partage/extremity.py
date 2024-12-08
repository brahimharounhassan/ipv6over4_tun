import socket
from threading import Thread
import os
from processing import *

class Extremity:
    
    def __init__(self,tun_address:str, tun_fd: int, src_address: str, dst_address: str, src_port: int, dst_port: int, proto: str="tcp") -> 'Extremity':
        self.src_port = src_port
        self.dst_port = dst_port
        self.proto = proto
        self.tun_fd = tun_fd
        self.dst_address = dst_address
        self.src_address = src_address
        self.treads = []
        self.tun_address = tun_address
        self.connected_client = {}
        
        self.server = None
        self.client = None
        self.connexion = None
        self.client_address = None
        
        self.encapsulate = Encapsulate()
        self.decapsulate = Decapsulate()
    
    
    def start(self) -> None :
        self.ext_out()
   
    
    def ext_out(self) -> None:
        self.server = socket.socket(socket.AF_INET6, socket.SOCK_STREAM if self.proto.lower() == "tcp" else socket.SOCK_DGRAM)
        try:
            self.server.bind(("", self.src_port))
            print(f"Server started --> listening on port: {self.src_port}")
            self.ext_in()
        
        except Exception as e:
            print(f"Can not connect to port: {self.src_port}")
            print(f"On start func (server) --> Error: {e}")
            self.server.close()
            exit(0)
            
        
    def ext_in(self) -> None:
        self.tcp() if self.proto.lower() == "tcp" else self.udp()
        self.server.close()
        self.client.close()
        os.close(self.tun_fd)
        exit(1)
    
            
    def tcp(self) -> None:
        print("TCP connexion.")
        self.client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        
        while True:
            try:
                self.server.listen()
                print("Waiting new connexion...")
                try:
                    self.connexion, self.client_address = self.server.accept()
                    print(f"Connected with: {self.client_address}")
                    if self.client_address[0].split(":")[-1] != self.dst_address:
                        t = Thread(target=self.receive_from_ipv6)
                        t.daemon = True
                        t.start()
                        self.treads.append(t)
                        
                    else: 
                        self.from_ipv4_to_tun()
                        # t = Thread(target=self.from_ipv4_to_tun)
                        # t.daemon = True
                        # t.start()
                        # self.treads.append(t)    
                         
                except Exception as e:
                    print(f"Enable to establish connexion.")
                    print(f"On tcp func (accept) --> Error: {e}")
                    break

            except Exception as e:
                print("Server stopped.")
                print(f"On tcp func (listen) --> Error: {e}.")
                break
                
        print("TCP connexion interrupted.")
        for t in self.treads:
            t.join()
        self.server()
        exit(0)
  
    
    def receive_from_ipv6(self) -> None:
        print("Ipv6 Receiver  Thread launched...")
        if not self.connected_client or not (self.dst_address, self.dst_port) in self.connected_client.keys():
            self.connected_client[(self.dst_address, self.dst_port)] = self.client
            try:
                self.client.connect((self.dst_address, self.dst_port))
                print(f"Connexion with {self.dst_address} established...")
            except Exception as e:
                print("Connexion impossible.")
                print(f"On host connexion (func receive_from_ipv6) --> Error: {e}")

        while True:
            try:
                if self.proto.lower() == 'tcp':
                    ipv6_packet = self.connexion.recv(0xFFFF)  
                else:
                    ipv6_packet , self.client_address = self.server.recvfrom(0xFFFF)
                    print(f"Receiving data from: {self.client_address[0]}")
                    
                if ipv6_packet:
                    self.save_to_local_tun(ipv6_packet=ipv6_packet)
                    self.send_to_tun_extrimity()
                else:
                    del self.connected_client
                    break
                
            except Exception as e:
                print(f"Enable to read data from {self.client_address[0]}")
                print(f"On reading data (func run) --> Error: {e}",)
                del self.connected_client
                break
        exit(0)

        
    def save_to_local_tun(self, ipv6_packet: bytes) -> None:
        try:
            os.write(self.tun_fd, ipv6_packet)
            print(f"Writing data into local tunnel.")
            
        except Exception  as e:
            print(f"Enable to write data into local tunnel.")
            print(f"On save_to_local_tun func --> Error: {e}") 
       
 
    def send_to_tun_extrimity(self) -> None:
        try:
            ipv6_packet = os.read(self.tun_fd, 0xFFFF)
            print("Reading data from local tunnel")
            if ipv6_packet:
                ipv4_header = self.encapsulate.encapsulate_ipv6_in_tcp_ipv4(
                    self.src_address,
                    self.dst_address, 
                    self.src_port, 
                    self.dst_port, 
                    ipv6_packet)
                encapsulated_packet = ipv4_header + ipv6_packet
                try:
                    self.client.sendall(encapsulated_packet)
                    print(f"Data sended from local tunnel to {self.dst_address}")
                except Exception as e:
                    print(f"Impossible  to send data from local to {self.dst_address}")
                    print(f"On sending data (func send_to_tun_extrimity) --> Error: {e}")
                    exit(0)        
        except Exception as e:
            print("Impossible to read data from local tunnel.")
            print(f"On reading data (func send_to_tun_extrimity) --> Error: {e}")
                

    def from_ipv4_to_tun(self) -> None:
        print("Ipv4 Receiver  Thread launched...")
        while True:
            try:
                encapsulated_packet = self.connexion.recv(0xFFFF)  
                print(f"Receiving data from: {self.connexion.getpeername()[0]}")                    
                if encapsulated_packet:
                    decapsulated_packet = self.decapsulate.decapsulate_ipv6_from_ipv4(encapsulated_packet)
                    print("Paquet IPv4 analysé :", decapsulated_packet["ipv4_info"])
                    print("En-tête TCP analysé :", decapsulated_packet["tcp_info"])
                    print("Paquet IPv6 encapsulé :", decapsulated_packet["ipv6_packet"])
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
        print("UDP connexion.")
        while True:
            self.receive_from_ipv6()
    
             