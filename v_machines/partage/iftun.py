import os
import subprocess
from fcntl import ioctl
import struct
from typing import Union
# Some constants from Linux kernel header if_tun.h


BUFFER_SIZE = 4096  

class Interface:
    def __init__(self, tun_dev: str) -> None:
        self.tun_dev = tun_dev
        self.fd = None

    def tun_alloc(self) -> Union[int,bytes]:
        """Creates TUN (virtual network) device.

        Returns:
            file descriptor used to read/write to device.
        """
        TUNSETIFF = 0x400454ca
        IFF_TUN = 0x0001
        IFF_NO_PI = 0x1000 # Ignore packet data added by the Linux kernel.
        TUNMODE = IFF_TUN
        
        try:
            self.fd = os.open("/dev/net/tun", os.O_RDWR)
        except IOError as err:
            print("Alloc tun :" + os.strerror(err.errno))
            exit(-1)
        
        try:
            if self.fd is not None:
                ifs = ioctl(self.fd, TUNSETIFF, struct.pack("16sH", bytes(self.tun_dev,'utf-8'), TUNMODE))
                # ifs = ioctl(self.fd, TUNSETIFF, struct.pack('16sH', self.tun_dev.encode('ascii'), IFF_TUN | IFF_NO_PI))
        except OSError as err:
            print("Options tun", os.strerror(err.errno))
            exit(-1)
        
        ifname = ifs[:16].strip(b'\x00').decode('utf-8')
        
        
        return self.fd, ifname
    

class Iftun:
    
    def __init__(self) -> 'Iftun':
        self.tun_dev = None
        self.tunfd = None
        self.ipv6_dst_lan_addr = None
        self.ipv6_dst_tun_addr = None
        self.ipv4_dev = None           
    
          
    def show_traffic(self) -> None:
        subprocess.run(("sudo", "tcpdump", "-ni", self.tun_dev))
        subprocess.run(("sudo", "tcpdump", "-ni", "eth1"))
        subprocess.run(("sudo", "tcpdump", "-ni", "eth2"))
          
            
    def up(self) -> None :
        try:
            subprocess.run(("sudo", "ip", "link", "set", self.tun_dev, "up"), check=True)
        except subprocess.CalledProcessError as e:
            print(f"On func up --> Error : {e}")
            exit(-1)
  
            
    def check_exist_cmd(self, command: list | tuple, value: str) -> bool:
        try:
            result = subprocess.run(
                command,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                check=True)
            
            if value in result.stdout.decode():
                print(f"The entry {value} already exist.")
                return True
            else:
                print(f"The entry  {value} not exist.")
                return False
        except subprocess.CalledProcessError as e:
            print(f"On fun check_exist_cmd Error --> Eror : {e}")
            return False


    def down(self) -> None :
        if self.tun_dev is not None: 
            try:
                subprocess.run(("sudo", "ip", "address", "del", self.tun_address, "dev", self.tun_dev), check=True)
                subprocess.run(("sudo", "ip", "link", "set", self.tun_dev, "down"), check=True)
            except subprocess.CalledProcessError as e:
                print(f"On func down --> Error : {e}")
                exit(-1)

            
    def set_mtu(self, mtu: int) -> None :
        if self.tun_dev is not None : subprocess.run(("sudo", "ip", "link", "set", self.tun_dev, mtu, "1500"), check=True)
    
            
    def create_vnet_device(self, tun_dev: str) -> None:#Union[int, bytes]:
        self.tun_dev = tun_dev
        self.tunfd, _ = Interface(self.tun_dev).tun_alloc()


    def set_address(self, tun_address:str, ipv4_dst_addr: str, ipv4_gateway:str,ipv6_gateway: str, ipv6_dst_lan_addr : str) -> None:
        """Associate address with TUN device."""
        if self.tun_dev is not None : 
            try:
                subprocess.run(("sudo", "ip", "address", "add", tun_address, "dev", self.tun_dev), check=True)
                self.up()
            except subprocess.CalledProcessError as e:
                print(f"On func set_address --> Error : {e}")
                exit(-1)           
        if  self.check_exist_cmd(("ip", "-6", "route", "show"),  ipv6_gateway) == False or self.check_exist_cmd(("ip", "-6", "route", "show"),  ipv6_dst_lan_addr) == False:
            subprocess.run(("sudo", "ip", "-6", "route", "add", ipv6_dst_lan_addr, "via", ipv6_gateway, "dev", self.tun_dev), check=True)
        if self.check_exist_cmd(("ip", "route", "show"),  ipv4_gateway) == False or self.check_exist_cmd(("ip", "route", "show"),  ipv4_dst_addr ) == False :
            try:
                subprocess.run(("sudo", "ip", "route", "add", ipv4_dst_addr ,"via", ipv4_gateway, "dev", "eth1"), check=True)
            except subprocess.CalledProcessError as e:
                print(f"On func set_address --> Error : {e}")
                exit(-1) 
        
        subprocess.run(("ip", "address"))


    def from_tun_to(self, src:int, dst:int) -> None:
        """
         fonction avec deux descripteurs de fichiers en paramètres src et dst, qui, 
         étant donné un descripteur src correspondant à une interface TUN, recopie perpétuellement
        """
        while True:
            data = None
            try:
                data = os.read(src,BUFFER_SIZE)
                print("Reading data from tun")
                try:
                    print(f"Data send to descriptor {dst}.")
                    os.write(dst, data)
                except Exception as e :
                    print(f"Enable to send data to descriptor {dst}.")
                    print(f"On from_tun_to func (write) --> Error: {e}")
                    break
            except Exception as e:
                print("Enable to read data from tun.")
                print(f"On from_tun_to func (read) --> Error: {e}")
                break
                      
  