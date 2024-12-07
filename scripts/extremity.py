import socket
from threading import Thread
import os

class Extremity:
    
    def __init__(self, port: int, tun_fd: int,r_address: str, proto: str="tcp"):
        self.__port = port
        self.__proto = proto
        self.__tun_fd = tun_fd
        self.__server = None
        self.__client = None
        self.__connexion = None
        self.__client_address = None
        self.__r_address = r_address
        self.__treads = []
    
    def start(self) -> None :
        self.__ext_out()
   
    
    def __ext_out(self) -> None:
        self.__server = socket.socket(socket.AF_INET6, socket.SOCK_STREAM if self.__proto.lower() == "tcp" else socket.SOCK_DGRAM)
        try:
            self.__server.bind(("", self.__port))
            print("Server started:")
            self.__ext_in()
        
        except Exception as e:
            print(f"Can not connect to port: {self.__port}")
            print(f"On start func (server) --> Error: {e}")
            self.__server.close()
            exit(1)
            
        
    def __ext_in(self) -> None:
        self.__tcp() if self.__proto.lower() == "tcp" else self.__udp()
        # self.close()
        self.__client.close()
    
            
    def __tcp(self) -> None:
        print("TCP connexion.")
        print(f"Start listening on port: {self.__port}")
        while True:
            try:
                self.__server.listen()
                print("Waiting new connexion...")
                try:
                    self.__connexion, self.__client_address = self.__server.accept()
                    print(f"Connected with: {self.__client_address}")
                        
                    if self.__client_address[0].split(":")[-1] != self.__r_address:
                        t = Thread(target=self.__from_ipv6_to_tun)
                        t.daemon = True
                        t.start()
                        self.__treads.append(t)
                        # self.__ext_in()    
                    else:                         
                        self.__from_ipv4_to_tun()
                except Exception as e:
                    print(f"Enable to establish connexion.")
                    print(f"On tcp func (accept) --> Error: {e}")
                    break

            except Exception as e:
                print("Server stopped.")
                print(f"On tcp func (listen) --> Error: {e}.")
                break
        
                
        print("TCP connexion interrupted.")
        for t in self.__treads:
            t.join()
        self.__server()
        exit(0)
    
  
    def __from_ipv6_to_tun(self) -> None:
        self.__client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        
        try:
            self.__client.connect((self.__r_address, self.__port))
            print(f"Connexion with {self.__r_address} established...")
            
            while True:
                try:
                    if self.__proto.lower() == 'tcp':
                        __packet = self.__connexion.recv(0xFFFF)  
                    else:
                        __packet , self.__client_address = self.__server.recvfrom(0xFFFF)
                    print(f"Receiving data from: {self.__client_address[0]}")
                        
                    if __packet:
                        self.__save_to_local_tun(__packet)
                        self.__send_to_tun_extrimity()
                    else:
                        break
                    
                except Exception as e:
                    print(f"Enable to read data from {self.__client_address[0]}")
                    print(f"On reading data (func run) --> Error: ", e)
                    # self.__connexion.close()
                    break
        except Exception as e:
            print("Connexion impossible.")
            print(f"On host connexion (func __from_ipv6_to_tun) --> Error: {e}")
            # self.__client.close()
            
        # self.close()
        # if self.__client : self.__client.close()
        # if self.__connexion : self.__connexion.close()
        # exit(0)


    def __save_to_local_tun(self, packet: bytes) -> None:
        try:
            os.write(self.__tun_fd, packet)
            print(f"Writing data into local tunnel.")
        except Exception  as e:
            print(f"Enable to write data into local tunnel.")
            print(f"On __write_data_to func --> Error: {e}") 
       
        
    def __send_to_tun_extrimity(self) -> None:
        try:
            __packet = os.read(self.__tun_fd, 0xFFFF)
            print("Reading data from local tunnel")
            if __packet:
                try:
                    self.__client.sendall(__packet)
                    print(f"Data sended from local tunnel to {self.__r_address}")
                except Exception as e:
                    print(f"Impossible  to send data from local to {self.__r_address}")
                    print(f"On sending data (func __send_to_tun_extrimity) --> Error: {e}")
        except:
            print("Impossible to read data from local tunnel.")
            print(f"On reading data (func __send_to_tun_extrimity) --> Error: {e}")
      
        
    def __from_ipv4_to_tun(self) -> None:
        # while True:
        try:
            __packet = self.__connexion.recv(0xFFFF)  
            print(f"Receiving data from: {self.__connexion.getpeername()[0]}")                     
            if __packet:
                print("Data: ", __packet)
            # else:
                # break
            
        except Exception as e:
            print(f"Enable to read data from {self.__connexion.getpeername()[0]}")
            print(f"On reading data (func run) --> Error: ", e)
            self.__connexion.close()
        #         break
        # exit(0)      
       
        
    def __udp(self) -> None:  
        print("UDP connexion.")
        while True:
            self.__from_ipv6_to_tun()
    
             