import socket
from threading import Thread, Lock
import os
from concurrent.futures import ThreadPoolExecutor
import logging
from processing import Processing

from queue import Queue
# Logs configuration
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")
logger = logging.getLogger(__name__)

BUFFER_SIZE = 4096  # fixed value of bueffer size

class Extremity:
    """
    This class represents an endpoint in a communication system using tunnels (IPv6 encapsulated within IPv4 or direct IPv6 communication).
    It handles both IPv6 and IPv4 traffic, utilizing TCP or UDP protocols for communication between the local system and remote servers.

    Attributes:
        src_port (int): Source port for the local system.
        dst_port (int): Destination port for the remote system.
        proto (str): Protocol to use ('tcp' or 'udp').
        tun_fd (int): File descriptor for the tunnel interface.
        dst_address (str): Destination address (IPv6).
        src_address (str): Source address (IPv6).
        threads (list): List of active threads for concurrent operations.
        tun_address (str): The tunnel's IP address.
        connected_client (dict): Dictionary of connected clients.
        connected_client_lock (Lock): Lock for managing thread-safe access to connected clients.
        encapsulate (Encapsulate): Encapsulation handler for IPv6 within IPv4.
        decapsulate (Decapsulate): Decapsulation handler for extracting IPv6 from IPv4.
    """
    
    def __init__(self,tun_address:str, tun_fd: int, src_address: str, dst_address: str, src_port: int, dst_port: int, proto: str="tcp") -> None:
        """
        Initializes the Extremity object with necessary parameters for communication and tunnel handling.

        Args:
            tun_address (str): Tunnel interface address (IPv6).
            tun_fd (int): File descriptor for the tunnel interface.
            src_address (str): Source address (IPv6).
            dst_address (str): Destination address (IPv6).
            src_port (int): Source port for local system communication.
            dst_port (int): Destination port for remote communication.
            proto (str): Protocol to be used ('tcp' or 'udp').
        """
        self.src_port = src_port
        self.dst_port = dst_port
        self.proto = proto.lower()
        self.tun_fd = tun_fd
        self.dst_address = dst_address
        self.src_address = src_address
        self.threads = []
        self.tun_address = tun_address
        self.connected_client = {}
        
        self.processing = Processing(self.src_address, self.dst_address)
        
        # Thread pool for handling multiple concurrent connections
        self.executor = ThreadPoolExecutor(max_workers=10)
        
        # Synchronization
        self.tun_lock = Lock()  # To control access to the tunnel
        self.tun_read_queue = Queue()  # Queue for sequential reading
        self.tun_write_queue = Queue()  # Queue for sequential writing

    def start(self) -> None:
        """
            Starts the execution of the main tasks of the process.

            This method submits two functions to a background executor:
            - `handle_tun_read`: handles reading data from the TUN device.
            - `handle_tun_write`: handles writing data to the TUN device.

            It then calls `ext_out` to perform additional operations 
            (such as notifying or handling external outputs) and finishes 
            by calling `join_threads`, which waits for all submitted tasks 
            to complete.

            :return: None
        """
        self.executor.submit(self.handle_tun_read)
        self.executor.submit(self.handle_tun_write)
        self.ext_out()
        self.join_threads()
    

    def handle_tun_read(self) -> None:
        """
            Continuously reads data from the tunnel and processes it in a thread-safe manner.

            This method reads IPv6 packets from the tunnel's file descriptor using a lock to ensure
            thread safety. Each packet is added to a queue for subsequent handling or forwarding.

            Behavior:
                - Acquires a lock to safely access the tunnel file descriptor.
                - Adds each packet read to the `tun_read_queue` for further processing.
                - Logs successful reads and any errors encountered.

            Raises:
                Logs any exception encountered during the read operation.
        """
        while True:
            with self.tun_lock:
                try:
                    ipv6_packet = os.read(self.tun_fd, BUFFER_SIZE)
                    if ipv6_packet:
                        self.tun_read_queue.put(ipv6_packet)
                        logger.info("Read a packet from the tunnel.")
                except Exception as e:
                    logger.error(f"Error while reading from the tunnel: {e}")
                    break


    def handle_tun_write(self) -> None:
        """
            Continuously writes data to the tunnel from a thread-safe queue.

            This method retrieves IPv6 packets from the `tun_write_queue` and writes them to the
            tunnel's file descriptor using a lock to ensure thread safety.

            Behavior:
                - Retrieves packets from the `tun_write_queue`.
                - Acquires a lock to safely write packets to the tunnel.
                - Logs successful writes and any errors encountered.

            Raises:
                Logs any exception encountered during the write operation.
        """
        while True:
            try:
                ipv6_packet = self.tun_write_queue.get()
                with self.tun_lock:
                    os.write(self.tun_fd, ipv6_packet)
                    logger.info("Wrote a packet to the tunnel.")
            except Exception as e:
                logger.error(f"Error while writing to the tunnel: {e}")
                break
            
            
    def ext_in(self, client: socket.socket) -> None:
        """
            Handles incoming connections and sends data from the local tunnel to the remote endpoint.

            Args:
                client (socket.socket): The client connection to the remote endpoint.
        """
        logger.info("Ipv6 writer Thread launched...")
        
        while True:
            try:
                ipv6_packet = self.tun_read_queue.get()
                if ipv6_packet:
                    encapsulated_packet = self.processing.encapsulate(ipv6_packet)
                    client.sendall(encapsulated_packet)
                    logger.info(f"Data sent from local tunnel to {self.dst_address}")
                    
            except Exception as e:
                logger.error(f"Failed to send data to {self.dst_address}: {e}")
                break
        client.close()
    
        
   
    def ext_out(self) -> None:
        """
            Initializes the server socket (TCP/UDP) and starts listening for incoming connections 
            and handles protocol-specific logic for either TCP or UDP communication.

            This method is responsible for delegating the appropriate handling 
            mechanism based on the protocol specified for the connection (TCP or UDP).
            Depending on the value of self.proto, it calls either the tcp method 
            for handling TCP connections or the udp method for handling UDP connections.

            Args:
                server (socket.socket): The server socket object used to handle incoming 
                                    client connections. The socket is passed to either
                                    the tcp or udp method for further processing.
        """
        
        try:
            server = socket.socket(socket.AF_INET6, socket.SOCK_STREAM if self.proto == "tcp" else socket.SOCK_DGRAM)
            # server.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            
            server.bind(("", self.src_port))
            
            self.tcp(server) if self.proto == "tcp" else self.udp(server)
        
        except socket.error as e:
            logger.error(f"Cannot connect to port: {self.src_port} - {e}")
            
        finally:
            server.close()
             


    def tcp(self, server: socket.socket) -> None:
        """
            Handles TCP connections, establishes connections with remote server, and manages multiple threads for
            reading and writing data.

            Args:
                server (socket.socket): The server socket for handling incoming TCP connections.
        """                                                                                                                        
        
        logger.info(f"TCP connection mode started on {self.src_port}")
        
        client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        while True:
            
            try:
                client.connect((self.dst_address, self.dst_port))
                logger.info(f"Connexion established with: {self.dst_address}")                
                self.executor.submit(self.ext_in, client)
            except Exception as e:
                pass
            
            server.listen()
            connexion, conn_address = server.accept()
            logger.info(f"Connected with: {conn_address}")
            
            if conn_address[0].split(":")[-1] != self.dst_address:
                # Launch a thread to handle receiving data and sending data over the IPv6 interface
                self.executor.submit(self.receive_from_ipv6, connexion)
                
                
            else: 
                # If the client's address matches the destination address, it is assumed to be an IPv4 connection
                # and requires a different treatment (such as conversion to a tunnel).
                self.executor.submit(self.from_ipv4_to_tun, connexion)
                
            self.executor.submit(self.ext_in, client)
            
            
    def receive_from_ipv6(self, connexion: socket.socket) -> None:
        """
        Continuously receives IPv6 packets from an established client connection.

        This method reads data from the specified IPv6 connection and adds the received packets
        to a thread-safe queue for writing to the tunnel. It ensures proper handling of exceptions
        and logs relevant events for monitoring purposes.

        Args:
            connexion (socket.socket): The active socket connection from which IPv6 packets are received.

        Behavior:
            - Adds each received packet to the `tun_write_queue` for further processing.
            - Logs successful packet reception and queuing.
            - Closes the connection upon completion or in case of an error.

        Raises:
            Logs any exception encountered during packet reception.
        """
        logger.info(f"Receiving data from {connexion.getpeername()[0]}")
        while True:
            try:
                ipv6_packet = connexion.recv(BUFFER_SIZE)
                if ipv6_packet:
                    self.tun_write_queue.put(ipv6_packet)
                    logger.info("IPv6 packet received and added to the write queue.")
                else:
                    break
            except Exception as e:
                logger.error(f"Error while receiving data: {e}")
                break
        connexion.close()
       
        
    def save_to_local_tun(self, ipv6_packet: bytes) -> None:
        """
        Writes the IPv6 packet to the local tunnel interface.

        Args:
            ipv6_packet (bytes): The IPv6 packet to be written to the tunnel.
        """
        try:
            os.write(self.tun_fd, ipv6_packet)
            logger.info("IPv6 packet written to local tunnel.")
        except IOError as e:
            logger.error(f"Failed to write data to local tunnel: {e}")
                   

    def from_ipv4_to_tun(self, client_connexion: socket.socket) -> None:
        """
        Receives and processes encapsulated IPv6 packets from IPv4 and saves them to the local tunnel.

        Args:
            client_connexion (socket.socket): The connection from which IPv4 encapsulated packets are received.
        """
        logger.info(f"Receiving IPv4 data from {client_connexion.getpeername()[0]}")
        
        while True:
            try:
                encapsulated_packet = client_connexion.recv(BUFFER_SIZE)  
                if encapsulated_packet:
                    logger.info(self.identify_tunnel_packet(encapsulated_packet))
                    
                    decapsulated_packet = self.processing.decapsulate(encapsulated_packet)
                    
                    # self.tun_write_queue.put(decapsulated_packet)
                    self.save_to_local_tun(decapsulated_packet)
                    
                else: 
                    break
                
            except socket.error as e:
                logger.error(f"Failed to read data from {client_connexion.getpeername()[0]}: {e}")
                break
        client_connexion.close()
       
        
    def udp(self, connexion: socket.socket) -> None:  
        """
        Handles UDP communication and receives data from the IPv6 client.

        Args:
            connexion (socket.socket): The client connection for UDP communication.
        """
        logger.info("UDP connection mode.")
        self.receive_from_ipv6(connexion)
     
            
    def join_threads(self) -> None:
        """
        Waits for all active threads to finish execution.
        """            
        for t in self.executor._threads:
            t.join()
    
     
    def check_packet_protocol(self, packet: bytes) -> str:
        """
        Identifies the protocol of the given IPv4 packet.

        Args:
            packet (bytes): The IPv4 packet to check.

        Returns:
            str: The protocol type (e.g., "ICMP", "TCP", "UDP", etc.).
        """
        if len(packet) < 20:  
            return "Invalid IPv4 packet"
        
        protocol = packet[9]
        return self._get_protocol_name(protocol)
 
        
    def _get_protocol_name(self, protocol: int) -> str:
        """
        Maps a protocol byte (integer) to its human-readable protocol name.

        This method takes a protocol byte (as an integer) and maps it to a human-readable
        protocol name using a predefined mapping. If the protocol byte is not found in the
        mapping, it returns a string indicating that the protocol is unknown.

        Args:
            protocol (int): The protocol byte (integer) representing a network protocol 
                            (e.g., 0x01 for ICMP, 0x06 for TCP, etc.).

        Returns:
            str: A human-readable string representing the protocol name, or an 
                "Unknown protocol" message if the protocol is not in the map.

        Example:
            _get_protocol_name(0x06) -> "TCP"
            _get_protocol_name(0x99) -> "Unknown protocol (0x99)"
        """
        protocol_map = {
            0x01: "ICMP",
            0x02: "IGMP",
            0x06: "TCP",
            0x11: "UDP",
            0x29: "ENCAP",
            0x59: "OSPF",
            0x84: "SCTP",
        }
        return protocol_map.get(protocol, f"Unknown protocol (0x{protocol:02x})")


    def check_packet_type(self, packet: bytes) -> str:
        """
        Determines if the given packet is IPv4 or IPv6.

        Args:
            packet (bytes): The packet to check.

        Returns:
            str: The type of packet (either "IPv4" or "IPv6").
        """
        if len(packet) < 1:
            return "Unknown (empty packet)"
        
        version = packet[0] >> 4  
        return "IPv4" if version == 4 else "IPv6" if version == 6 else "Unknown type"

        
    def identify_tunnel_packet(self, packet: bytes) -> str:
        """
        Identifies whether the packet is an encapsulated IPv6 packet within an IPv4 packet.

        Args:
            packet (bytes): The IPv4 packet to analyze.

        Returns:
            str: Description of the packet type (tunneled or not).
        """
        if len(packet) < 20: # Minimum length for IPv4 packet
            return "Invalid packet"

        # Analyse the IPv4 protocol
        outer_protocol = self.check_packet_protocol(packet)
        if outer_protocol == "ENCAP":
            inner_type = self.check_packet_type(packet)
            return f"Tunnel IPv4 -> {inner_type}"
        return f"Non-tunnelled {outer_protocol}"
        
             
