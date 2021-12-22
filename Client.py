import scapy
import socket




class Client:
    def __init__(self,ip_address, port):
        self.ip_address = ip_address
        self.port = port
        self.create_udp_socket()



    def create_udp_socket(self):
        self.udp_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.udp_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self.udp_socket.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)
        self.udp_socket.bind(("",self.port))
        while True:
            data, addr = self.udp_socket.recvfrom(1024)
            print(data)



s = Client(1,13117)
