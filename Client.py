import struct

import scapy
import socket




class Client:
    def __init__(self,ip_address, port,team_name):
        self.ip_address = ip_address
        self.port = port
        self.create_udp_socket()
        self.team_name = team_name
        print("Client started, listening for offer requests...")



    def create_udp_socket(self):
        self.udp_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.udp_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self.udp_socket.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)
        self.udp_socket.bind(("",self.port))
        message, address = self.udp_socket.recvfrom(1024)
        print(f"Received offer from {address[0]},attempting to connect...")
        self.connect(message,address)

    def connect(self,message,address):
        self.tcp_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        magic_cookie, message_type, server_port = struct.unpack(">IbH",message)
        print(address[0])
        self.tcp_socket.connect((socket.gethostbyname(socket.gethostname())d,server_port))
        self.tcp_socket.send(f"{self.team_name}\n")
    #     self.play()
    #
    # def play(self):






s = Client(1,13117,"sdfa")
