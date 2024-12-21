from iftun import Iftun
import sys, os
from extremity import Extremity


            
if __name__ == "__main__":    
    """
    This script configures and starts a virtual network device (TUN interface) 
    for handling IPv4 and IPv6 traffic, and then establishes a traffic handler 
    using the `Extremity` class to manage network communication.

    It performs the following tasks:
    1. Initializes a TUN interface with a specified name and IP configuration.
    2. Sets up IP routing and iptables rules for traffic management.
    3. Creates a `traffic` object using the `Extremity` class to manage the tunnel's 
    data traffic.
    4. Prints confirmation about the created tunnel device.
    5. Starts the traffic handling loop where data is processed continuously.

    Required command-line arguments:
    - tun_name: Name of the TUN interface.
    - tun_address: The address of the TUN interface.
    - ipv4_src_addr: Source IPv4 address for traffic routing.
    - src_port: Source port for communication.
    - ipv4_dst_addr: Destination IPv4 address for routing traffic.
    - dst_port: Destination port for communication.
    - ipv4_gateway: IPv4 gateway for routing.
    - ipv6_gateway: IPv6 gateway for routing.
    - ipv6_dst_lan: IPv6 destination LAN address.

    Usage:
        python <script_name> <tun_name> <tun_address> <ipv4_src_addr> <src_port> 
            <ipv4_dst_addr> <dst_port> <ipv4_gateway> <ipv6_gateway> <ipv6_dst_lan>

    Example:
        python config_tun.py tun0 192.168.1.1 192.168.1.2 8080 192.168.1.3 9090 
            192.168.1.254 fc00:1234:abcd::1 fc00:1234:abcd::2
    """
    # Command-line arguments are captured as a tuple
    tun_name, tun_address, ipv4_src_addr, src_port, ipv4_dst_addr,  dst_port, ipv4_gateway, ipv6_gateway, ipv6_dst_lan = tuple(sys.argv[1:])
    
    # Initialize the Iftun object to manage the virtual network device
    iftun = Iftun()
    
    # Create the virtual network tunnel device with the given name
    iftun.create_vnet_device(tun_name)
    
    # Set the network addresses and gateway information for the tunnel
    iftun.set_address(tun_address, ipv4_dst_addr, ipv4_gateway, ipv6_gateway, ipv6_dst_lan)
    
    # Set up iptables rules if enabled
    iftun.set_iptables(ipv4_src_addr, src_port, ipv4_dst_addr, dst_port, ipv6_gateway)
   
    # Retrieve the created tunnel device and file descriptor
    tun_dev = iftun.tun_dev
    tun_fd = iftun.tunfd
    ifname = iftun.ifname

    # Initialize the Extremity object to manage and handle the traffic in the tunnel
    traffic = Extremity(tun_address=tun_address, 
                        tun_fd=tun_fd, 
                        src_address=ipv4_src_addr, 
                        dst_address=ipv4_dst_addr, 
                        src_port=int(src_port),
                        dst_port=int(dst_port),
                        proto="tcp")
    # Print a confirmation message indicating that the tunnel has been created successfully
    print(f'The tunnel: "{ifname}" with fd: {tun_fd} is created ;)\nEnjoy it.')
    
    # Enter an infinite loop to handle the traffic
    while True: 
        # Monitoring traffic on standard output
        # iftun.from_tun_to(tun_fd, dst=1) # execution: ./config1.sh | hexdump -C
        # iftun.show_traffic()
        
        # Start the traffic handling process using the Extremity object
        traffic.start()
        
        # Bring the TUN device down (disables the device).
        # iftun.down()
       
        # Close the tunnel file descriptor (typically done when terminating the process)
        os.close(tun_fd)
        break
    
    
    
   
    

    
   
    
