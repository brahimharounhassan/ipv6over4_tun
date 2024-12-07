from tunalloc import *
import sys


def from_tun_to(src:int, dst:int) -> None:
    
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
        
            
def test(fd) -> None:
    s = socket.socket(socket.AF_INET6, socket.SOCK_STREAM)
    port = 123
    s.bind(('', port))

    while True:
        s.listen()
        print("Listen")
        con, _ = s.accept()
        print("connexion etablie")
        while True:
            data    = con.recv(1024)
            print("Donne recu", data.decode("utf-8"))
            print(data)
            os.write(fd,data)
            print("donnee ecrite")
            os.write(1, os.read(fd,1024))
    #     con.close()
    # s.close()
            
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
    traffic = Extremity(port=port, tun_fd=tun_fd, r_address=remote_address)
    print(f'The tunnel: "{dev}" with fd: {tun_fd} is created ;)\nEnjoy it.')
    while True: 
        traffic.start()
        # traffic.ext_in(remote_address, tun_fd=tun_fd)
    # while True: 
    

    
   
    
