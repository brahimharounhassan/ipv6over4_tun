
class SixToFourThread(Thread):
    def __init__(self,connnexion: socket, client_address: str,  r_address: str, port: int, fd: int, output: str="Standard output"):
        Thread.__init__(self)
        self.__connexion = connnexion
        self.__r_address = r_address
        self.__tun_fd = fd
        self.__sock = None
        self.__output = output
        self.__port = port
        self.__client_address = client_address
        
        
    def run(self) -> None:
        
        self.__sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        
        try:
            self.__sock.connect((self.__r_address, self.__port))
            print(f"Connexion with {self.__r_address} established...")
            
            while True:
                try:
                    __packet = self.__connexion.recv(0xFFFF)  
                    print(f"Receiving data from: {self.__client_address[0]}")                     
                    if __packet:
                        self.__write_data_to(__packet)
                        self.__send_to_tun_extrimity()
                    else:
                        break
                    
                except Exception as e:
                    print(f"Enable to read data from {self.__client_address[0]}")
                    print(f"On reding data (func run) --> Error: ", e)
                    self.__connexion.close()
                    break
        except Exception as e:
            print("Connexion impossible.")
            print(f"On host connexion (func run) --> Error: {e}")
            self.__sock.close()
            
        
        if self.__sock : self.__sock.close()
        if self.__connexion : self.__connexion.close()
        exit(0)
 
 
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
        


class Client:
    def __init__(self, r_address: str, port: int, tun_fd: int) -> None:
        self.__r_address, self.__port = r_address, port
        self.__tun_fd = tun_fd
        
        self.__client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        
    def start(self) -> None:
        print("Try to reach the remote host")
        try:
            self.__client.connect((self.__r_address, self.__port))
            print("Connexion established...")
        except Exception as e:
            print("Connexion impossible.")
            print(f"On host connexion (func start) --> Error: {e}")
        while True:
            try:
                __packet = os.read(self.__tun_fd, 0xFFFF)
                print("Reading data from tunnel")
                print(__packet)
                try:
                    self.__client.sendall(__packet)
                    print(f"Data sended to {self.__r_address}")
                except Exception as e:
                    print(f"Impossible to send data to {self.__r_address}")
                    print(f"On sending data (func start) --> Error: {e}")
                    break
            except:
                print("Impossible to read data from tunnel.")
                print(f"On reading data (func start) --> Error: {e}")
                break
        self.__client.close()