import struct
from collections import Counter

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
        self.game_lock = threading.Lock()
        self.event_udp = threading.Event()
        self.event_tcp = threading.Event()
        self.reset_game()
        self.score_dictionary = Counter()
        self.broadcast_port = broadcast_port
        self.destination_port = destination_port
        self.tcp_port = tcp_port
        self.integer_lock = threading.Lock()
        self.event_two_players = threading.Event()
        thread = threading.Thread(target=self.create_broadcast_socket)
        thread.start()
        self.create_tcp_listening_socket()

    def reset_game(self):
        self.equation, self.equation_answer = self.equation_generator()
        self.current_clients_names = []
        self.got_answer_from_client = 0
        self.number_of_clients = 0
        self.score = 0
        self.winner = None
        self.event_udp.clear()


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
            time.sleep(1)
            if self.number_of_clients >= 2:
                self.event_udp.wait()
                self.reset_game()
                print("Game over, sending out offer requests...")

    def create_tcp_listening_socket(self):
        self.tcp_listener = socket.socket(socket.AF_INET,socket.SOCK_STREAM)
        self.tcp_listener.bind((self.ip,self.tcp_port))
        while True:
            self.tcp_listener.listen()
            connection, address = self.tcp_listener.accept() #should we accept him?
            self.integer_lock.acquire()
            if self.number_of_clients < 2:
                self.number_of_clients += 1
                thread = threading.Thread(target=self.handle_client, args=(connection,))
                thread.start()
                self.integer_lock.release()
            else:
                self.integer_lock.release()
                connection.send(b"Sorry, a game is on...")
                connection.send(b"go play some football")
                connection.send(b"bye bye")
                connection.close()
                #self.event_tcp.wait() # C



    def handle_client(self,connection):
        name = connection.recv(1024).decode("UTF-8")
        if name[-1]=="\n":
            self.current_clients_names.append(name)
        else:
            self.current_clients_names.append("Anonymous")
        self.integer_lock.acquire()
        if self.number_of_clients<2:
            self.integer_lock.release()
            self.event_two_players.wait()
        else:
            self.integer_lock.release()
            self.event_two_players.set()
        #two players
        time.sleep(3)
        stoper = time.time()
        connection.send(bytes(f"Welcome to Quick Maths.\n"
                              f"Player1: {self.current_clients_names[0]}\n"
                              f"Player2: {self.current_clients_names[1]}\n==\n"
                              f"Pleases answer the following question as fast as ypu can:\n"
                              f"How much is {self.equation}?","UTF-8"))
        answer=connection.recv(1024).decode("utf-8")
        self.game_lock.acquire()
        if self.got_answer_from_client == 0:
            self.score = 10 - (time.time() - stoper)

            if answer == self.equation_answer:
                self.got_answer_from_client = 1
                self.score_dictionary[name] += self.score
                self.winner = name
            else:
                self.got_answer_from_client = 2 #means wrong answer
                self.score_dictionary[name] += - self.score
                self.winner = self.find_winner(name)
        elif self.got_answer_from_client == 2:
            self.score_dictionary[name] += self.score
        else:
            self.score_dictionary[name] += - self.score
        self.game_lock.release()

        connection.send(bytes(f"Game over!\nThe correct answer was 4! \n\n Congratulations for the winner: {self.winner}","UTF-8"))
        connection.close()
        self.event_udp.set()


    def find_winner(self,name):
        return [n for n in self.current_clients_names if not n == name][0]



    def equation_generator(self):
        return "2+2","4"

s = Server("127.0.0.1",2500,broadcast_port=2000)




