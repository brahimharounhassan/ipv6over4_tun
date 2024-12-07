from tunalloc import *
import sys
from extremity import Extremity

            
if __name__ == "__main__":
    print(sys.argv[1:])
    tun_name, local_address, remote_address = tuple(sys.argv[1:])
    # ipv6_address = ipaddress.ip_interface("fc00:1234:3::1/64")
    tun_address = "fc00:1234:ffff::1/64"
    iftun = Iftun()
    
    iftun.create_vnet_device(tun_name)
    iftun.set_address(str(tun_address), str(local_address), str(remote_address))
    dev = iftun.dev
    tun_fd = iftun.tunfd
    
    port = 123
    traffic = Extremity(port=port, tun_fd=tun_fd, r_address=remote_address, proto="tcp")
    print(f'The tunnel: "{dev}" with fd: {tun_fd} is created ;)\nEnjoy it.')
    while True: 
        # iftun.from_tun_to(tun_fd, dst=1) # execution: ./config1.sh | hexdump -C
        traffic.start()
        # traffic.ext_in(remote_address, tun_fd=tun_fd)
    # while True: 
    
    
    
   
    

