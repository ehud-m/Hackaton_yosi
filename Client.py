import struct
import socket
import keyboard
import colorama
from threading import Timer

MAGIC_COOKIE_APPROVAL = 0xabcddcba
MESSAGE_TYPE_APPROVAL = 0x2



class Client:
    def __init__(self, ip_address, port, team_name):
        self.ip_address = ip_address
        self.port = port
        self.team_name = team_name

        print(f"{colorama.Fore.GREEN}Client started, listening for offer requests...")
        self.create_udp_socket()

    def create_udp_socket(self):
        self.udp_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.udp_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self.udp_socket.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)
        self.udp_socket.bind(("", self.port))
        while True:
            message, address = self.udp_socket.recvfrom(1024)
            print(f"{colorama.Fore.GREEN}Received offer from {address[0]},attempting to connect...")
            magic_cookie, message_type, server_port = struct.unpack(">IbH", message)
            if magic_cookie == MAGIC_COOKIE_APPROVAL and message_type == MESSAGE_TYPE_APPROVAL:
                self.connect(address, server_port) # connect TCP

    def connect(self, address, server_port):
        self.tcp_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

        print(address[0])
        self.tcp_socket.connect(('127.0.0.1', server_port))
        self.tcp_socket.send(bytes(self.team_name + "\n","utf-8"))
        self.play()

    def play(self):
        print(self.tcp_socket.recv(1024).decode("utf-8"))
        answer = keyboard.read_key()
        try:
            self.tcp_socket.send(bytes(answer,"utf-8"))
        except ConnectionAbortedError:
            print("FOOOOOOOOOLLLLLLLL!!!!!")
        print(self.tcp_socket.recv(1024).decode("utf-8"))
        print(f"{colorama.Fore.GREEN}Server disconnected, listening for offer requests...")
        self.tcp_socket.close()


s = Client(1, 13117, "Yuri400")
