from tunalloc import *
import sys


if __name__ == "__main__":
    local_address, remote_address = None, None
    # ipv6_address = ipaddress.ip_interface("fc00:1234:3::1/64")
    tun_address = ipaddress.ip_interface("fc00:1234:ffff::1/64")
    tun_name = str(sys.argv[-1])
    iftun = Iftun()
    if '0' in tun_name:
        local_address = ipaddress.ip_interface("172.16.2.131")
        remote_address = ipaddress.ip_interface("172.16.2.133")
    else :  
        local_address = ipaddress.ip_interface("172.16.2.133")
        remote_address = ipaddress.ip_interface("172.16.2.131")
    
    iftun.create_vnet_device(tun_name)
    iftun.set_address(str(tun_address), str(local_address), str(remote_address))
    tun_dev = iftun.tun_dev
    
    port = 1234
    conn = Extremity(port=port)
    print("tun_fd: ",  tun_dev.fd)
    print(f'The tunnel: "{tun_dev.dev}" is created ;)\nEnjoy it.')
    
    while True: 
        conn.ext_out(address="", device=tun_dev, proto="tcp", ip="6")
    
    
    
   
    

