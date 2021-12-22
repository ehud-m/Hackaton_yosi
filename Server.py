import scapy
import socket
import time




Host = '192.168.0.1'
port = 9376 #listening port


class Server():


    def __init__(self,ip_address,broadcast_port,destination_port=13117):
        self.ip = ip_address
        self.broadcast_port = broadcast_port
        self.destination_port = destination_port

        self.create_broadcast_socket()
        # create_tcp_listening_socket()



    def create_broadcast_socket(self):
        # self.bind()

        self.udp_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.udp_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)

        self.udp_socket.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)


    def send_message(self,message):
        while True:
            self.udp_socket.sendto(message, ('<broadcast>', self.destination_port))
            print("sent")
            time.sleep(1)



s = Server(1,2000)
s.send_message((b"asdfasdfsdf"))



