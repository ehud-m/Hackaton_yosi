import struct
import socket
import keyboard
import colorama
from threading import Timer

"""Approve only messages that contains this values"""
MAGIC_COOKIE_APPROVAL = 0xabcddcba
MESSAGE_TYPE_APPROVAL = 0x2


class Client:
    """
    Client that's playing equation game
    """

    def __init__(self, port, team_name):
        """
        :param port: The port number of client app.
        :param team_name: client team name.
        """
        self.port = port
        self.team_name = team_name

        print(f"{colorama.Fore.GREEN}Client started, listening for offer requests...")
        while True:
            try:
                self.create_udp_socket()  # if UDP listen failed, start broadcast again.
            except:
                continue

    def create_udp_socket(self):
        """
        listen for request's
        """
        udp_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        udp_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        udp_socket.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)
        udp_socket.bind(("", self.port))

        while True:
            message, address = udp_socket.recvfrom(1024)
            print(f"{colorama.Fore.GREEN}Received offer from {address[0]},attempting to connect...")
            magic_cookie, message_type, server_port = struct.unpack(">IbH", message)
            if magic_cookie == MAGIC_COOKIE_APPROVAL and message_type == MESSAGE_TYPE_APPROVAL:  # verify reliable message
                self.connect(address, server_port)  # connect via TCP

    def connect(self, address, server_port):
        """
        :param address: sender address
        :param server_port: server listening port
        """
        self.tcp_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.tcp_socket.connect(('127.0.0.1', server_port))
        self.tcp_socket.send(bytes(self.team_name + "\n", "utf-8"))
        self.play()

    def play(self):
        """
        equation gameplay
        """
        print(self.tcp_socket.recv(1024).decode("utf-8"))

        answer = keyboard.read_key()
        try:
            self.tcp_socket.send(bytes(answer, "utf-8"))
        except ConnectionAbortedError:
            print("FOOOOOOOOOLLLLLLLL!!!!!")
        try:
            print(self.tcp_socket.recv(1024).decode("utf-8"))
        except:
            print(f"{colorama.Fore.RED}Server sends bad args, lets continue")
        print(f"{colorama.Fore.GREEN}Server disconnected, listening for offer requests...")
        try:
            self.tcp_socket.close()
        except:
            None


s = Client(1, 13117, "Yuri400")
