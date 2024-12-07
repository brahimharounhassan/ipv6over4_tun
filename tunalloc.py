import os
from typing import Union
import subprocess
import socket
from threading import Thread
import ipaddress
from fcntl import ioctl
import struct
# Some constants from Linux kernel header if_tun.h
TUNSETIFF = 0x400454ca
IFF_TUN = 0x0001
IFF_NO_PI = 0x1000 # Ignore packet data added by the Linux kernel.
TUNMODE = IFF_TUN


class Interface:
    def __init__(self, dev: str) -> None:
        self.dev = dev
        self.fd = None

    def tun_alloc(self) -> int:
        """Creates TUN (virtual network) device.

        Returns:
            file descriptor used to read/write to device.
        """
        try:
            self.fd = os.open("/dev/net/tun", os.O_RDWR)
        except IOError as err:
            print("Alloc tun :" + os.strerror(err.errno))
            exit(-1)
        
        try:
            if self.fd is not None:
                ifs = ioctl(self.fd, TUNSETIFF, struct.pack("16sH", bytes(self.dev,'utf-8'), TUNMODE))
                # ifs = ioctl(self.fd, TUNSETIFF, struct.pack('16sH', self.dev.encode('ascii'), IFF_TUN | IFF_NO_PI))
        except OSError as err:
            print("Options tun", os.strerror(err.errno))
            exit(-1)
        
        ifname = ifs[:16].strip(b'\x00').decode('utf-8')
        
        
        return self.fd, ifname
    

class Iftun:
    
    def __init__(self):
        self.dev = None
        self.tunfd = None
        self.tun_address = None
        self.ipv6_interface_address = None
        self.ipv4_interface_address = None
    
    def set_iptables(self) -> None:
        if self.tun_address is not None:
            os.system(f"sudo iptables -t nat -A POSTROUTING -s {self.ipv4_interface_address} -j MASQUERADE")
            os.system(f"sudo iptables -A FORWARD -i {self.dev} -s {self.ipv4_interface_address} -j ACCEPT")
            os.system(f"sudo iptables -A FORWARD -o {self.dev} -d {self.ipv6_interface_address}-j ACCEPT")

            
    def show_traffic(self) -> None:
        subprocess.run(("sudo", "tcpdump", "-ni", self.dev))
            
    def up(self) -> None :
        subprocess.run(("sudo", "ip", "link", "set", self.dev, "up", "type", "sit"), check=True)
        # idx = subprocess.run(("ip", "link", "show", "dev", self.dev),stdout=subprocess.PIPE).stdout.decode().split(":")[0]
        # subprocess.run(("sudo", "ip", "link", "set", self.dev,
        #                 "type", "sit"),check=True)
                  
        # subprocess.run(("sudo", "ip", "address", "add", self.remote_address, "peer", self.local_address, "dev", self.dev),check=True)
        # subprocess.run(("sudo", "ip", "-6", "tunnel", "add", "mode", "any", 
        #                 "remote", self.remote_address, 
        #                 "local", self.local_address, 
        #                 "dev", self.dev),check=True)
        # subprocess.run(("sudo", "ip", "link", self.dev, "index", idx), check=True)
        
    def down(self) -> None :
        if self.dev is not None: subprocess.run(("sudo", "ip", "link", "set", self.dev, "down"), check=True)
            
    def set_mtu(self, mtu: int) -> None :
        if self.dev is not None : subprocess.run(("sudo", "ip", "link", "set", self.dev, "mtu", "1500"), check=True)
            
    def create_vnet_device(self, dev: str) -> None:#Union[int, bytes]:
        self.dev = dev
        self.tun_dev = Interface(dev)
        self.tunfd, ifname = self.tun_dev.tun_alloc()

    def set_address(self, tun_address: ipaddress, local: str, remote: str) -> None:
        """Associate address with TUN device."""
        self.tun_address = tun_address
        self.remote_address = remote
        self.local_address = local
        if self.dev is not None : 
            subprocess.run(("sudo", "ip", "address", "add", tun_address, "dev", self.dev), check=True)
            self.up()
            # self.set_iptables()
            subprocess.run(("ip", "address"))

     
class Server:
    def __init__(self, port: int, proto: str="tcp"):
        self.__port = port
        self.__proto = proto
        self.__server = socket.socket(socket.AF_INET6, socket.SOCK_STREAM if self.__proto == "tcp" else socket.SOCK_DGRAM)
        # self._server.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        
    def start(self) -> socket:
        try:
            self.__server.bind(("", self.__port))
            print("Server started:")
            return self.__server   
        
        except Exception as e:
            print(f"Can not connect to port: {self.__port}")
            print(f"On start func (server) --> Error: {e}")
            # self.__server.close()
            exit(0)

                        
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
        self.__server = Server(self.__port, proto=self.__proto).start()
        self.__ext_in()
            
        
    def __ext_in(self) -> None:
        self.__tcp() if self.__proto == "tcp" else self.__udp()
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
    
    
    # def close(self) -> None:
    #     self.__server.close()
    #     self.__client.close()
        
    #     for t in self.__treads:
    #         t.join()
        
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
        while True:
            try:
                __packet = self.__connexion.recv(0xFFFF)  
                print(f"Receiving data from: {self.__connexion.getpeername()[0]}")                     
                if __packet:
                    print("Data: ", __packet)
                else:
                    break
                
            except Exception as e:
                print(f"Enable to read data from {self.__connexion.getpeername()[0]}")
                print(f"On reading data (func run) --> Error: ", e)
                self.__connexion.close()
                break
        exit(0)      
       
        
    def __udp(self) -> None:  
        print("UDP connexion.")
        while True:
            self.__from_ipv6_to_tun()
    
                    
# if __name__ == "__main__":

""""
IPv6 over IPv4 tunnels are point-to-point tunnels made by encapsulating IPv6 packets within IPv4 headers to carry them over IPv4 routing infrastructures. 

All tunneling mechanisms require that the endpoints of the tunnel run both IPv4 and IPv6 protocol
stacks, that is, endpoints must run in dual-stack mode. A dual stack network is a network in which
all of the nodes are both IPv4 and IPv6 enabled.

As with other tunnel mechanisms, network address translation (NAT) is not allowed along the path of the tunnel.
"""