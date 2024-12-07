import os
import subprocess
from fcntl import ioctl
import struct
# Some constants from Linux kernel header if_tun.h



class Interface:
    def __init__(self, dev: str) -> None:
        self.dev = dev
        self.fd = None

    def tun_alloc(self) -> int:
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
    
    # def set_iptables(self) -> None:
    #     if self.tun_address is not None:
    #         os.system(f"sudo iptables -t nat -A POSTROUTING -s {self.ipv4_interface_address} -j MASQUERADE")
    #         os.system(f"sudo iptables -A FORWARD -i {self.dev} -s {self.ipv4_interface_address} -j ACCEPT")
    #         os.system(f"sudo iptables -A FORWARD -o {self.dev} -d {self.ipv6_interface_address}-j ACCEPT")

            
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

    def set_address(self, tun_address: str, local: str, remote: str) -> None:
        """Associate address with TUN device."""
        self.tun_address = tun_address
        self.remote_address = remote
        self.local_address = local
        if self.dev is not None : 
            subprocess.run(("sudo", "ip", "address", "add", tun_address, "dev", self.dev), check=True)
            self.up()
            # self.set_iptables()
            subprocess.run(("ip", "address"))

    def from_tun_to(self, src:int, dst:int) -> None:
        """
         fonction avec deux descripteurs de fichiers en paramètres src et dst, qui, 
         étant donné un descripteur src correspondant à une interface TUN, recopie perpétuellement
        """
        while True:
            data = None
            try:
                data = os.read(src,0xFFFF)
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
                      
  
""""
IPv6 over IPv4 tunnels are point-to-point tunnels made by encapsulating IPv6 packets within IPv4 headers to carry them over IPv4 routing infrastructures. 

All tunneling mechanisms require that the endpoints of the tunnel run both IPv4 and IPv6 protocol
stacks, that is, endpoints must run in dual-stack mode. A dual stack network is a network in which
all of the nodes are both IPv4 and IPv6 enabled.

As with other tunnel mechanisms, network address translation (NAT) is not allowed along the path of the tunnel.
"""