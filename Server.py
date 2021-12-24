import struct

import scapy
import socket
import time
import threading

from scapy.arch import get_if_addr

Host = '192.168.0.1'
port = 9376 #listening port


class Server():


    def __init__(self,ip_address,tcp_port,broadcast_port,destination_port=13117):
        self.ip = ip_address
        print(ip_address)
        print(f"Server started, listening on IP address {self.ip}")
        self.broadcast_port = broadcast_port
        self.destination_port = destination_port
        self.tcp_port = tcp_port
        self.number_of_clients = 0
        self.lock = threading.Lock()
        self.event_udp = threading.Event()
        self.event_tcp = threading.Event()
        thread = threading.Thread(target=self.create_broadcast_socket)
        thread.start()

        self.create_tcp_listening_socket()



    def create_broadcast_socket(self):
        # self.bind()
        self.udp_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.udp_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self.udp_socket.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)

        message = struct.pack(">IbH",0xabcddcba, 0x2, self.tcp_port)
        self.send_message(message)


    def send_message(self,message):
        while True:
            self.udp_socket.sendto(message, ('<broadcast>', self.destination_port))
            # print("sent")
            time.sleep(1)
            if self.number_of_clients >= 2:
                self.event_udp.wait()

    def create_tcp_listening_socket(self):
        self.tcp_listener = socket.socket(socket.AF_INET,socket.SOCK_STREAM)
        self.tcp_listener.bind(('127.0.0.1',self.tcp_port))
        while True:
            self.tcp_listener.listen()
            connection, address = self.tcp_listener.accept() #should we accept him?
            self.lock.acquire()
            if self.number_of_clients < 2:
                self.number_of_clients += 1
                thread = threading.Thread(target=self.handle_client, args=(connection))
                thread.start()
                self.lock.release()
            else:
                self.lock.release()
                connection.send("Sorry, a game is on...")
                connection.send("go play some football")
                connection.send("bye bye")
                connection.close()
                self.event_tcp.wait()




    def handle_client(self,connection):
        print(connection.recv(1024))



s = Server(socket.gethostbyname(socket.gethostname()),2500,broadcast_port=2000)




