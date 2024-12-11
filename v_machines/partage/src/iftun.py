import os
import subprocess
from fcntl import ioctl
import struct
from typing import Union
import logging


# Logs configuration
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")
logger = logging.getLogger(__name__)

BUFFER_SIZE = 4096  

class Interface:
    """
    A class that represents a virtual network interface (TUN device) and provides methods to 
    allocate and configure it for network communication.

    Attributes:
        tun_dev (str): The name of the virtual TUN device.
        fd (int or None): The file descriptor for the TUN device, used for read/write operations.
    """
    
    TUNSETIFF = 0x400454ca # ioctl command to set interface flags
    IFF_TUN = 0x0001 # Flag indicating it's a TUN device
    IFF_NO_PI = 0x1000 # Ignore packet data added by the Linux kernel.
    TUNMODE = IFF_TUN | IFF_NO_PI # Device type: TUN device (not TAP)
    
    def __init__(self, tun_dev: str) -> None:
        """
        Initializes the Interface class with the provided TUN device name.

        Args:
            tun_dev (str): The name of the virtual TUN device to create (e.g., "tun0").
        """
        self.tun_dev = tun_dev
        self.fd = None


    def tun_alloc(self) -> Union[int,bytes]:
        """
        Allocates a TUN (virtual network) device and returns the file descriptor used for read/write operations.

        This method opens the TUN device file (`/dev/net/tun`), creates a virtual network interface with
        the specified name, and configures it using `ioctl` system calls.

        The TUN device is used to send and receive raw IP packets. If an error occurs during allocation or 
        configuration, the method will print an error message and terminate the program.

        Returns:
            Union[int, bytes]: The file descriptor for the TUN device (used to read and write to the device),
            and the name of the created TUN device (e.g., "tun0").

        Raises:
            IOError: If there is an issue opening the `/dev/net/tun` device.
            OSError: If there is an issue configuring the TUN device using `ioctl`.
        """
        # Try to open the TUN device file and get a file descriptor
        try:
            self.fd = os.open("/dev/net/tun", os.O_RDWR)
        except IOError as err:
            logger.error(f"Failed to allocate TUN: {os.strerror(err.errno)}")
            exit(-1)
            
        # Try to configure the TUN device using ioctl
        try:
            if self.fd is not None:
                # Send the ioctl command to set up the device with the desired name and flags
                ifs = ioctl(self.fd, self.TUNSETIFF, struct.pack("16sH", self.tun_dev.encode('utf-8'), self.TUNMODE))
                # ifs = ioctl(self.fd, self.TUNSETIFF, struct.pack('16sH', self.tun_dev.encode('ascii'), self.TUNMODE))
        except OSError as err:
            logger.error(f"Failed to configure TUN device: {os.strerror(err.errno)}")
            exit(-1)
            
        # Extract the name of the created device from the ioctl result
        ifname = ifs[:16].strip(b'\x00').decode('utf-8')
        
        # Return the file descriptor and the device name
        return self.fd, ifname
    

class Iftun:
    """
    A class to manage a TUN (virtual network) device and perform network operations like setting up,
    managing traffic, and configuring routing for IPv4 and IPv6 traffic.

    Attributes:
        tun_dev (str or None): The name of the TUN device (e.g., 'tun0').
        tunfd (int or None): The file descriptor for the TUN device used for reading and writing.
    """
    
    def __init__(self) -> 'Iftun':
        """
        Initializes the Iftun object with no device name or file descriptor.
        """
        self.tun_dev = None
        self.tunfd = None
        self.ifname = None
                  
            
    def up(self) -> None :
        """
        Brings the TUN device up (enables the device for use).
        
        This method uses the `ip` command to bring the device online. It runs the 
        command `ip link set <device> up` to enable the device. If any error occurs 
        during this process, it prints the error and exits the program.
        """
        if not self.tun_dev:
            logger.error("TUN device not specified.")
            return
        try:
            subprocess.run(["sudo", "ip", "link", "set", self.tun_dev, "up"], check=True)
            logger.info(f"TUN device '{self.tun_dev}' is now up.")
        except subprocess.CalledProcessError as e:
            logger.error(f"Failed to bring TUN device up: {e}")
            exit(-1)
  
            
    def check_exist_cmd(self, command: list[str], value: str) -> bool:
        """
        Checks if a certain entry exists in the result of a command.

        Args:
            command (list or tuple): The command to run (e.g., `["ip", "-6", "route", "show"]`).
            value (str): The string to check for in the command's output.

        Returns:
            bool: True if the value is found in the output, False otherwise.
            
        If the entry is found, a message is printed indicating that the entry exists. If not, it
        prints a message indicating the absence of the entry.
        """
        try:
            result = subprocess.run(
                command,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                check=True)
            
            if value in result.stdout.decode():
                logger.info(f"The entry '{value}' already exists.")
                return True
            else:
                logger.info(f"The entry '{value}' does not exist.")
                return False
        except subprocess.CalledProcessError as e:
            logger.error(f"Error while checking command: {e}")
            return False


    def down(self) -> None :
        """
        Brings the TUN device down (disables the device).
        
        This method shuts down the TUN device by running the `ip link set <device> down` 
        and deletes the associated IP address. If there are any errors during this process, 
        the error is printed and the program exits.
        """
        if not self.tun_dev:
            logger.error("TUN device not specified.")
            return
        try:
            subprocess.run(["sudo", "ip", "link", "set", self.tun_dev, "down"], check=True)
            logger.info(f"TUN device '{self.tun_dev}' is now down.")
        except subprocess.CalledProcessError as e:
            logger.error(f"Failed to bring TUN device down: {e}")

            
    def set_mtu(self, mtu: int) -> None :
        """
        Sets the MTU (Maximum Transmission Unit) for the TUN device.
        
        This method sets the MTU for the TUN device using the `ip link set` command.
        
        Args:
            mtu (int): The MTU value to set for the TUN device.
        """
        
        if not self.tun_dev:
            logger.error("TUN device not specified.")
            return
        try:
            subprocess.run(["sudo", "ip", "link", "set", self.tun_dev, "mtu", str(mtu)], check=True)
            logger.info(f"MTU set to {mtu} for device '{self.tun_dev}'.")
        except subprocess.CalledProcessError as e:
            logger.error(f"Failed to set MTU: {e}")
    
            
    def create_vnet_device(self, tun_dev: str) -> None:#Union[int, bytes]:
        """
        Creates a virtual network device (TUN device) with the given name.

        This method allocates a TUN device by calling the `tun_alloc` method from the `Interface` class. 
        The device is named according to the `tun_dev` parameter.
        
        Args:
            tun_dev (str): The name of the TUN device to create (e.g., 'tun0').
        """
        self.tun_dev = tun_dev
        self.tunfd, self.ifname = Interface(self.tun_dev).tun_alloc()


    def set_address(self, tun_address:str, ipv4_dst: str, ipv4_gw: str, ipv6_gw: str, ipv6_dst: str) -> None:
        """
        Sets the address configuration for the TUN device and configures routing for IPv4 and IPv6.

        This method adds the provided address to the TUN device, brings the device up, and configures 
        IPv6 and IPv4 routes to the specified destination addresses and gateways.
        
        Args:
            tun_address (str): The address to assign to the TUN device (e.g., '10.0.0.1/24').
            ipv4_dst_addr (str): The destination IPv4 address.
            ipv4_gateway (str): The IPv4 gateway address.
            ipv6_gateway (str): The IPv6 gateway address.
            ipv6_dst_lan_addr (str): The destination IPv6 LAN address.
        """
        if not self.tun_dev:
            logger.error("TUN device not specified.")
            return
        try:
            subprocess.run(["sudo", "ip", "address", "add", tun_address, "dev", self.tun_dev], check=True)
            self.up()

            if not self.check_exist_cmd(["ip", "-6", "route", "show"], ipv6_gw) or not self.check_exist_cmd(["ip", "-6", "route", "show"], ipv6_dst):
                subprocess.run(["sudo", "ip", "-6", "route", "add", ipv6_dst, "via", ipv6_gw], check=True)

            if not self.check_exist_cmd(["ip", "route", "show"], ipv4_gw) or not self.check_exist_cmd(["ip", "route", "show"], ipv4_dst):
                subprocess.run(["sudo", "ip", "route", "add", ipv4_dst, "via", ipv4_gw, "dev", "eth1"], check=True)

            # subprocess.run(["sudo", "ip", "-6", "neigh", "flush", "state", "STALE"], check=True)
            subprocess.run(["sudo", "ip", "-6", "neigh", "flush", "all"], check=True)

            logger.info("Address and routes configured successfully.")
        except subprocess.CalledProcessError as e:
            logger.error(f"Failed to set address: {e}")
            exit(-1)
            
        subprocess.run(["ip", "address"])
        subprocess.run(["ip", "-6", "r"])


    def set_iptables(self, ipv4_src_addr: str, src_port:int,  ipv4_dst_addr: str, dst_port, ipv6_gateway: str) -> None:        
        """
        Configures IPv6 ICMP rules for Neighbor Discovery Protocol (NDP) by adding specific ip6tables rules.

        This method adds rules to the system's IPv6 firewall (using `ip6tables`) to accept important ICMPv6 message types that 
        are required for NDP functionality. These messages are used for operations like neighbour discovery, router 
        advertisement, and other essential IPv6 operations.

        The following ICMPv6 message types are allowed:
        - Type 135: Neighbor Solicitation
        - Type 136: Neighbor Advertisement
        - Type 133: Router Solicitation
        - Type 134: Router Advertisement
        - Type 137: Redirect
        - Type 128: Echo Request (ping)
        - Type 129: Echo Reply (ping)

        The method attempts to add the appropriate ip6tables rules for each of these ICMPv6 types. If successful, a log message
        is recorded indicating that the rules have been successfully configured. If an error occurs during the process, 
        an error log is generated with details about the failure.

        Raises:
            subprocess.CalledProcessError: If the ip6tables command fails, an exception is raised and logged.

        Example:
            self.set_iptables()

        Notes:
            - The method requires root privileges to modify ip6tables, so it uses `sudo` to execute the commands.
            - It is important to ensure that these rules are persistent across system reboots, typically by using a tool like
            `iptables-persistent` or manually saving the iptables configuration.
        """
        icmp_types = ["135", "136", "133", "134", "137", "128", "129"]
        try:
            for icmp_type in icmp_types:
                subprocess.run(["sudo", "ip6tables", "-A", "INPUT", "-p", "ipv6-icmp", "--icmpv6-type", icmp_type, "-j", "ACCEPT"], check=True)
            logger.info("IP6Tables rules for ICMP configured successfully.")
        except subprocess.CalledProcessError as e:
            logger.error(f"Failed to configure iptables: {e}")
        for iface in ["eth2", self.tun_dev]:
            try:    
                subprocess.run(("sudo", "ip6tables", "-t", "nat", "-A", "POSTROUTING", "-o", iface, "-j", "MASQUERADE"),check=True)
                
                subprocess.run(("sudo", "ip6tables", "-A", "INPUT", "-i", self.tun_dev, "-p", "ipv6", "-j", "ACCEPT" ),check=True)
                subprocess.run(("sudo", "ip6tables", "-A", "OUTPUT", "-o", self.tun_dev, "-p", "ipv6", "-j", "ACCEPT" ),check=True)
                
                subprocess.run(("sudo", "iptables", "-A", "INPUT", "-i", self.tun_dev ,"-p", "ipv6", "-s", ipv4_src_addr, "-j", "ACCEPT"  ),check=True)
                subprocess.run(("sudo", "iptables", "-A", "OUTPUT", "-o", self.tun_dev ,"-p", "ipv6", "-s", ipv4_src_addr, "-j", "ACCEPT"  ),check=True)
                
                subprocess.run(("sudo", "iptables", "-A", "INPUT", "-i", self.tun_dev ,"-p", "ipv6", "-d", ipv4_dst_addr, "-j", "ACCEPT"  ),check=True)
                subprocess.run(("sudo", "iptables", "-A", "OUTPUT", "-o", self.tun_dev ,"-p", "ipv6", "-d", ipv4_dst_addr, "-j", "ACCEPT"  ),check=True)
                
                subprocess.run(("sudo", "ip6tables", "-A", "INPUT", "-p", "icmpv6", "--icmpv6-type", "echo-request", "-j", "ACCEPT"),check=True)
                
                subprocess.run(("sudo", "ip6tables", "-A", "OUTPUT", "-o", self.tun_dev, "-p", "tcp", "-d", ipv6_gateway, "--dport", "123:65535",
                                "--sport", str(src_port), "!", "--syn", "-j", "ACCEPT" ),check=True)
                subprocess.run(("sudo", "ip6tables", "-A", "INPUT", "-i", self.tun_dev, "-p", "tcp", "-d", ipv6_gateway, "--dport", "123:65535",
                                "--sport", str(src_port), "!", "--syn", "-j", "ACCEPT" ),check=True)
                
                subprocess.run(("sudo", "ip6tables", "-A", "OUTPUT", "-o", self.tun_dev, "-p", "tcp", "-s", ipv6_gateway, "--dport", "123:65535",
                                "--sport",str(dst_port), "!", "--syn", "-j", "ACCEPT" ),check=True)
                subprocess.run(("sudo", "ip6tables", "-A", "INPUT", "-i", self.tun_dev, "-p", "tcp", "-s", ipv6_gateway, "--dport", "123:65535",
                                "--sport", str(dst_port), "!", "--syn", "-j", "ACCEPT" ),check=True)
                
                subprocess.run(("sudo", "ip6tables", "-A", "FORWARD", "-i", self.tun_dev, "-o", "eth1", "-j", "ACCEPT"),check=True)
                subprocess.run(("sudo", "ip6tables", "-A", "FORWARD", "-i", self.tun_dev, "-o", "eth2", "-j", "ACCEPT"),check=True)
                subprocess.run(("sudo", "ip6tables", "-A", "FORWARD", "-i", "eth2", "-o", self.tun_dev, "-j", "ACCEPT"),check=True)
                subprocess.run(("sudo", "ip6tables", "-A", "FORWARD", "-i", "eth1", "-o", self.tun_dev, "-j", "ACCEPT"),check=True)
            except subprocess.CalledProcessError as e:
                logging.error(f"On func set_iptables --> Error : {e}")
                exit(0)


    def from_tun_to(self, src:int, dst:int) -> None:
        """
        Reads data from the TUN device (src descriptor) and writes it to another descriptor (dst).
        
        This function continuously reads data from the source descriptor (the TUN device) and sends it
        to the destination descriptor. This function helps with transferring network packets from the TUN 
        device to another network interface or socket.

        Args:
            src (int): The source file descriptor (e.g., the TUN device).
            dst (int): The destination file descriptor to send the data to.
        """
        while True:
            data = None
            try:
                data = os.read(src,BUFFER_SIZE)
                os.write(dst, data)
                logger.info(f"Data forwarded from descriptor {src} to {dst}.")
            except OSError as e:
                logger.error(f"Data transfer failed: {e}")
                break
                      
   