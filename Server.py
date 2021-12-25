import struct
from collections import Counter
import colorama
import scapy
import socket
import time
import threading

from scapy.arch import get_if_addr

HOST_IP= '127.0.0.1'
BROADCAST_DESTINATION_PORT = 13117
MAGIC_COOKIE_APPROVAL = 0xabcddcba
MESSAGE_TYPE_APPROVAL = 0x2
NUMBER_OF_CLIENTS_IN_GAME = 2
MAXIMUM_MESSAGE_SIZE = 1024
GAME_LENGTH = 10
WAIT_FOR_GAME_LENGTH = 3
NO_ANSWER_YET = 0
FIRST_ANSWER_IS_RIGHT = 1
FIRST_ANSWER_IS_WRONG = 2

class Server():
    def __init__(self,ip_address,tcp_port,broadcast_port,destination_port=BROADCAST_DESTINATION_PORT):
        self.ip = ip_address
        print(ip_address)
        print(f"{colorama.Fore.GREEN}Server started, listening on IP address {self.ip}")
        self.integer_lock = threading.Lock()
        self.game_lock = threading.Lock()
        self.event_udp = threading.Event()
        self.event_tcp = threading.Event()
        self.event_two_players = threading.Event()
        self.event_end_game = threading.Event()
        self.reset_game()
        self.score_dictionary = Counter()
        self.broadcast_port = broadcast_port
        self.destination_port = destination_port
        self.tcp_port = tcp_port


        thread = threading.Thread(target=self.create_broadcast_socket)
        thread.start()
        self.create_tcp_listening_socket()

    def reset_game(self):
        self.equation, self.equation_answer = self.equation_generator()
        self.current_clients_names = []
        self.game_status = 0
        self.number_of_clients = 0
        self.score = 0
        self.winner = None
        self.event_udp.clear()
        self.event_two_players.clear()


    def create_broadcast_socket(self):
        # self.bind()
        self.udp_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.udp_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self.udp_socket.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)
        message = struct.pack(">IbH",MAGIC_COOKIE_APPROVAL, MESSAGE_TYPE_APPROVAL, self.tcp_port)
        self.send_message(message)


    def send_message(self,message):
        while True:
            self.udp_socket.sendto(message, ('<broadcast>', self.destination_port))
            #time.sleep(1)
            if self.number_of_clients >= NUMBER_OF_CLIENTS_IN_GAME:
                self.event_udp.wait()
                self.reset_game()
                print(f"{colorama.Fore.GREEN}Game over, sending out offer requests...")

    def create_tcp_listening_socket(self):
        self.tcp_listener = socket.socket(socket.AF_INET,socket.SOCK_STREAM)
        self.tcp_listener.bind((self.ip,self.tcp_port))
        while True:
            self.tcp_listener.listen()
            connection, address = self.tcp_listener.accept() #should we accept him?
            self.integer_lock.acquire()
            if self.number_of_clients < NUMBER_OF_CLIENTS_IN_GAME:
                self.number_of_clients += 1
                thread = threading.Thread(target=self.handle_client, args=(connection,))
                thread.start()
                self.integer_lock.release()
            else:
                self.integer_lock.release()
                connection.send(bytes(f"{colorama.Fore.YELLOW}Sorry, a game is on...\ngo play some football\nbye bye","UTF-8"))
                connection.close()
                #self.event_tcp.wait() # C



    def handle_client(self,connection):
        name = connection.recv(MAXIMUM_MESSAGE_SIZE).decode("UTF-8")
        if name[-1]=="\n":
            self.current_clients_names.append(name[0:-1])
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
        time.sleep(WAIT_FOR_GAME_LENGTH)
        connection.settimeout(GAME_LENGTH)
        stoper = time.time()
        connection.send(bytes(f"{colorama.Fore.YELLOW}Welcome to Quick Maths.\n"
                              f"Player1: {self.current_clients_names[0]}\n"
                              f"Player2: {self.current_clients_names[1]}\n==\n"
                              f"Pleases answer the following question as fast as you can:\n"
                              f"How much is {self.equation}?","UTF-8"))
        try:
            answer=connection.recv(1024).decode("utf-8")
            self.game_lock.acquire()
            if self.game_status == NO_ANSWER_YET:
                self.score = 10 - (time.time() - stoper)
                if answer == self.equation_answer:
                    self.game_status = FIRST_ANSWER_IS_RIGHT
                    self.score_dictionary[name] += self.score
                    self.winner = name
                else:
                    self.game_status = FIRST_ANSWER_IS_WRONG #means wrong answer
                    self.score_dictionary[name] += - self.score
                    self.winner = self.find_winner(name)
                self.game_lock.release()
            else:
                if self.game_status == FIRST_ANSWER_IS_WRONG:
                    self.score_dictionary[name] += self.score
                else:
                    self.score_dictionary[name] += - self.score
                self.game_lock.release()
                self.event_udp.set()

            connection.send(bytes(f"{colorama.Fore.BLUE}Game over!\nThe correct answer was 4! \n\n Congratulations for the winner: {self.winner}","UTF-8"))
        except socket.timeout:
            connection.send(
                bytes(f"{colorama.Fore.BLUE}Game over!\nThe correct answer was 4! \n\n Nobody won you losers!!!", "UTF-8"))
        connection.close()



    def find_winner(self,name):
        winner = [n for n in self.current_clients_names if not n == name]
        if len(winner) == 0:
            return self.current_clients_names[0]
        return winner[0]

    def equation_generator(self):
        return "2+2","4"

s = Server(HOST_IP,2501,broadcast_port=2000)




