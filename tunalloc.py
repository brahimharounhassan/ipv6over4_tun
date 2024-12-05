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


    # snippet:start vpn
CRAPVPN_HEADER = ">4sHxx"
CRAPVPN_MAGIC = b"crap"
CRAPVPN_HEADER_SIZE = struct.calcsize(CRAPVPN_HEADER)


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
    
    
    def read(self, n: int=1500) -> bytes:
        """
        Args:
            n: bytes to read.
        """
        data = None
        try:
            data = os.read(self.fd, n)
        except IOError as err:
            print("Error :" + os.strerror(err.errno))
            exit(-1)
        return data

    def write(self, data: bytes) -> None:
        try:
            os.write(self.fd, data)
            
        except IOError as err:
            print("Error :" + os.strerror(err.errno))
            exit(-1)
        

class Utils:
    
    def tun_open(self) -> int:
        fd = None
        try:
            fd = os.open("/dev/net/tun", os.O_RDWR)
        except IOError as err:
            print("Alloc tun :" + os.strerror(err.errno))
            print(f"Error: {err}")
            exit(-1)
        return fd

    def read(self, fd: int, n: int=1500) -> bytes:
        """
        Args:
            n: bytes to read.
        """
        data = None
        try:
            data = os.read(fd, n)
        except IOError as err:
            print("Error :" + os.strerror(err.errno))
            print(f"Error: {err}")
            exit(-1)
        return data

    def write(self, fd: int, data: bytes) -> None:
        try:
            os.write(fd, data)
        except IOError as err:
            print("Error :" + os.strerror(err.errno))
            print(f"Error: {err}")
            exit(-1)
        

class Iftun:
    
    def __init__(self):
        self.tun_dev = None
        self.dev = None
        self.tunfd = None
        self.tun_address = None
        self.ipv6_interface_address = None
        self.ipv4_interface_address = None
        self.port = 1234
    
    def set_iptables(self) -> None:
        if self.tun_address is not None:
            os.system(f"sudo iptables -t nat -A POSTROUTING -s {self.ipv4_interface_address} -j MASQUERADE")
            os.system(f"sudo iptables -A FORWARD -i {self.dev} -s {self.ipv4_interface_address} -j ACCEPT")
            os.system(f"sudo iptables -A FORWARD -o {self.dev} -d {self.ipv6_interface_address}-j ACCEPT")

            
    def show_traffic(self):
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
    def __init__(self, address: str, port: int, device:int, proto: str="udp", ip: str="4") -> None:
        self._address = (address, port)
        self._proto = proto
        self._port = port
        _ip = socket.AF_INET if ip == "4" else socket.AF_INET6
        _sock_proto =  socket.SOCK_STREAM if proto == "tcp" else socket.SOCK_DGRAM
        self._server = socket.socket(_ip, _sock_proto) 
        # self._server.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self._device = device
        self._treads = []
        
    def _send_to(self, conn) -> None:
        print(f"One thread launched.")
        syn = b'E\x00\x00,\x00\x01\x00\x00@\x06\x00\xc4\xc0\x00\x02\x02"\xc2\x95Cx\x0c\x00P\xf4p\x98\x8b\x00\x00\x00\x00`\x02\xff\xff\x18\xc6\x00\x00\x02\x04\x05\xb4'
        while True:
            try:
                _data = conn.recv(2048)
                print("donne recu: ", _data)
                if _data:
                    
                    if self._device == 1:
                        print("Writing into standard output.")
                        os.write(self._device, _data)
                    else:
                        try:
                            self._device.write(_data)
                            print("Data sended to tun0.")
                        except:
                            print(f"Enable to write into {self._device}.")
                            conn.close()
                else:
                    print("Empty data")
                    conn.close()
                    break
                    
            except:
                print("Connexion closed.")
                # conn.close()
                break
        
        exit(-1)
                    
        
    def route_traffic_to(self, device: int) -> 'Server':
        self._device = device
        return self
        
    def udp(self):  
        try:
            while True:            
                print("udp connexion.")
                _data, _client_address = self._server.recvfrom(4096)
                print(f"Sending data to {_client_address}")
                if self._device == 1:
                    print("Writing into standard output.")
                    os.write(self._device, _data)
                else:
                    try:
                        self._device.write(_data)
                        print("Data sended to tun0.")
                    except:
                        print(f"Enable to write into {self._device}.")
                        
        except:
            print("UDP data receiving interrupted.")
            
        finally:
            self._server.close()  
               
        
    def tcp(self):
        try:
            while True:
                print("tcp connexion.")
                self._server.listen()
                print("listenning...")
                _conn, _client_address = self._server.accept()
                print(f"Connexion from {_client_address} accepted.")
                
                t = Thread(target=self._send_to, args=(_conn,))
                t.daemon = True
                self._treads.append(t)
                t.start()
                
        except KeyboardInterrupt:
            print("TCP data receiving interrupted.")
            for t in self._treads:
                t.join()
            exit(-1)
    
    def start(self) -> None:
        try:
            self._server.bind(self._address)
            print("Server started:")
            print(f"Start listening on port: {self._address[-1]}")
            if self._proto == "tcp": self.tcp()
            else: self.udp()
        except:
            print(f"Error: can't connect to port: {self._address[-1]}")
            self._server.close()

                
class Client:
    def __init__(self, address: str, port: int, device: int) -> None:
        self._address = (address, port)
        self._device = device
        
        self._client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        
        # self._server.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    def route_traffic_to(self) -> 'Client':
        return self

    def start(self) -> None:
        print("Try to reach the remote host")
        try:
            self._client.connect(self._address)
            print("Connexion established...")
        except:
            print("Connexion impossible.")
        _data = None
        # while True:
        try:
            print("Try to read data from tun0")
            _data = os.read(self._device, 0xFFFF)
            print("Lecture reussi................")
            print(_data)
            self._client.sendall(_data)
        except:
            print("Lecture impossible.")
            # packet = list(os.read(self._device, 2048))
            # os.write(1,_data)
            
            
class Extremity:
    
    def __init__(self, port: int=123):
        self._port = port
    
    def ext_out(self, address: str, device:  int, proto: str, ip):
        _server = Server(address=address, port=self._port, device=device, proto=proto, ip=ip).route_traffic_to(device)
        try:
            _server.start()
        except:
            print("Error launching the server.")
            _server._server.close()
        finally:
            _server._server.close()
    
    def ext_in(self, address, device:  int):

        _client = Client(address=address,port=self._port, device=device)
        _client.start()
           

# if __name__ == "__main__":

""""
IPv6 over IPv4 tunnels are point-to-point tunnels made by encapsulating IPv6 packets within IPv4 headers to carry them over IPv4 routing infrastructures. 

All tunneling mechanisms require that the endpoints of the tunnel run both IPv4 and IPv6 protocol
stacks, that is, endpoints must run in dual-stack mode. A dual stack network is a network in which
all of the nodes are both IPv4 and IPv6 enabled.

As with other tunnel mechanisms, network address translation (NAT) is not allowed along the path of the tunnel.
"""