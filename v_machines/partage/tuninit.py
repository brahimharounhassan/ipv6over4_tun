from tunalloc import Iftun
import sys, os
from extremity import Extremity

            
if __name__ == "__main__":
    tun_name, tun_address, ipv4_src_addr, ipv4_dst_addr, src_port, dst_port = tuple(sys.argv[1:])
    iftun = Iftun()
    
    iftun.create_vnet_device(tun_name)
    iftun.set_address(tun_address)
    tun_dev = iftun.tun_dev
    tun_fd = iftun.tunfd

    traffic = Extremity(tun_address=tun_address, 
                        tun_fd=tun_fd, 
                        src_address=ipv4_src_addr, 
                        dst_address=ipv4_dst_addr, 
                        src_port=int(src_port),
                        dst_port=int(dst_port),
                        proto="tcp")
    
    print(f'The tunnel: "{tun_dev}" with fd: {tun_fd} is created ;)\nEnjoy it.')
    while True: 
        # iftun.from_tun_to(tun_fd, dst=1) # execution: ./config1.sh | hexdump -C
        # iftun.show_traffic()
        traffic.start()
        os.close(tun_fd)
    
    
    
   
    

