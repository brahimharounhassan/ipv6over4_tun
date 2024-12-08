from iftun import Iftun
import sys, os
from extremity import Extremity

            
if __name__ == "__main__":
    tun_name, tun_address, ipv4_src_addr, src_port, ipv4_dst_addr,  dst_port, ipv4_gateway, ipv6_gateway, ipv6_dst_lan = tuple(sys.argv[1:])
    # fc00:1234:ffff::2/64
    # tmp_host = ipv4_src_addr.split("/")[0]
    # idx = tmp_host[-1]
    # print(tmp_host)
    iftun = Iftun()
    iftun.create_vnet_device(tun_name)
    iftun.set_address(tun_address, ipv4_dst_addr, ipv4_gateway, ipv6_gateway, ipv6_dst_lan)
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
        # os.close(tun_fd)
    
    
    
   
    

