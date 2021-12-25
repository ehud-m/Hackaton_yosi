import random
import struct
from collections import Counter
import colorama
import scapy
import socket
import time
import threading

from scapy.arch import get_if_addr

HOST_IP = '127.0.0.1'
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
TCP_PORT = 2501


class Server():
    def __init__(self, ip_address, tcp_port, destination_port=BROADCAST_DESTINATION_PORT):
        self.ip = ip_address
        print(ip_address)
        print(f"{colorama.Fore.GREEN}Server started, listening on IP address {self.ip}")
        self.integer_lock = threading.Lock()  # lock for number_of_clients
        self.game_lock = threading.Lock()  # lock for recoginize the first player to answer
        self.event_udp = threading.Event()  # wait's untill game is over to broadcast again
        self.event_two_players = threading.Event()  # tell's when 2 players are ready to play
        self.event_score_updater = threading.Event() #to update score dict
        self.reset_game()
        self.score_dictionary = Counter()  # It saves the all time's scores.
        self.destination_port = destination_port
        self.tcp_port = tcp_port
        thread = threading.Thread(target=self.create_broadcast_socket)
        thread.start()
        self.create_tcp_listening_socket()

    def reset_game(self):
        """
        resets game stats
        """
        self.equation, self.equation_answer = self.equation_generator()
        self.current_clients_names = []
        self.game_status = 0
        self.number_of_clients = 0
        self.score = 0
        self.winner = None
        self.event_udp.clear()
        self.event_two_players.clear()
        self.event_score_updater.clear()

    def equation_generator(self):
        """
        :return: an equation to solve and it answer.
        """
        number_1 = random.randint(0, 9)
        number_2 = random.randint(0, 9 - number_1)
        return str(number_2) + "+" + str(number_1), number_2 + number_1

    ########################################################################################################################

    def create_broadcast_socket(self):
        """
        broadcast's offer message with credentials for reliability:
                                                                   MAGIC_COOKIE_APPROVAL, MESSAGE_TYPE_APPROVAL
        """
        self.udp_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.udp_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self.udp_socket.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)
        message = struct.pack(">IbH", MAGIC_COOKIE_APPROVAL, MESSAGE_TYPE_APPROVAL, self.tcp_port)
        self.send_message(message)

    def send_message(self, message):
        """
        broadcasts the offer message

        :param message: flags, credentials and port number
        """
        while True:
            self.udp_socket.sendto(message, ('<broadcast>', self.destination_port))
            # time.sleep(1)
            if self.number_of_clients >= NUMBER_OF_CLIENTS_IN_GAME:
                self.event_udp.wait()
                self.reset_game()
                print(f"{colorama.Fore.GREEN}Game over, sending out offer requests...")

    ########################################################################################################################

    def create_tcp_listening_socket(self):
        """
        create tcp socket and accept client.
        if number of clients exceeded maximum, sends reject message and close connection.
        """
        self.tcp_listener = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.tcp_listener.bind((self.ip, self.tcp_port))
        while True:
            self.tcp_listener.listen()
            connection, address = self.tcp_listener.accept()  # should we accept him?
            self.integer_lock.acquire()
            if self.number_of_clients < NUMBER_OF_CLIENTS_IN_GAME:
                self.run_client_thread(connection)
            else:
                self.send_reject_message(connection)

    def run_client_thread(self, connection):
        self.number_of_clients += 1
        thread = threading.Thread(target=self.handle_client, args=(connection,))
        thread.start()
        self.integer_lock.release()

    def send_reject_message(self, connection):
        self.integer_lock.release()
        connection.send(bytes(f"{colorama.Fore.YELLOW}Sorry, a game is on...\ngo play some football\nbye bye", "UTF-8"))
        connection.close()

    #######################################################################################################################

    def handle_client(self, connection):
        """
        handle one player of equation game
        :param connection: tcp connection
        """
        team_name = connection.recv(MAXIMUM_MESSAGE_SIZE).decode("UTF-8")
        self.set_name(team_name)
        self.wait_for_two_players(connection)
        stopper = time.time()  # for computing answer response time
        try:
            answer = connection.recv(1024).decode("utf-8")
            self.game_lock.acquire() #let only the first to response check if he won
            if self.game_status == NO_ANSWER_YET:
                self.first_to_answer(stopper, answer, team_name)
            else:
                self.second_to_answer(team_name)
            connection.send(bytes(self.generate_winner_message(team_name), "UTF-8"))
        except socket.timeout: #means the game ended in a draw - no one have answered
            connection.send(bytes(self.generate_draw_message(team_name), "UTF-8"))
        connection.close()

    def set_name(self, team_name):
        """
        adds the team name to the list of current game teams
        sets the team name without the space, if the name doesn't followed by the rulles, set as anonymus player.
        :param team_name
        """
        if team_name[-1] == "\n":
            self.current_clients_names.append(team_name[0:-1])
        else:
            self.current_clients_names.append("Anonymous")

    def wait_for_two_players(self, connection):
        """
        waits for two players to connect the game
        :param connection: tcp connection
        """
        self.integer_lock.acquire() #because of the critical section of the number of clients
        if self.number_of_clients < NUMBER_OF_CLIENTS_IN_GAME:
            self.integer_lock.release()
            self.event_two_players.wait()
        else:
            self.integer_lock.release()
            self.event_two_players.set()

        # Number of players is now enough to play the game
        time.sleep(WAIT_FOR_GAME_LENGTH)
        connection.settimeout(GAME_LENGTH)
        connection.send(bytes(f"{colorama.Fore.YELLOW}Welcome to Quick Maths.\n"
                              f"Player1: {self.current_clients_names[0]}\n"
                              f"Player2: {self.current_clients_names[1]}\n==\n"
                              f"Pleases answer the following question as fast as you can:\n"
                              f"How much is {self.equation}?", "UTF-8"))

    def first_to_answer(self, stopper, answer, team_name):
        """
        :param stopper: stopper to calculate score
        :param answer: first team answer
        :param team_name
        """
        self.score = 10 - (time.time() - stopper)
        if answer == self.equation_answer:
            self.game_status = FIRST_ANSWER_IS_RIGHT
            self.score_dictionary[team_name] += self.score
            self.winner = team_name
        else:
            self.game_status = FIRST_ANSWER_IS_WRONG  # means the team that responsed first lost
            self.score_dictionary[team_name] += - self.score
            self.winner = self.find_winner(team_name) #returns other team name
        self.game_lock.release() #let the second player to enter the critical section
        self.event_score_updater.wait() #when the first done updating scores, let the second update also

    def find_winner(self, team_name):
        """
        :param team_name
        :return: the winner team name which is the second team name
        """
        winner = [n for n in self.current_clients_names if not n == team_name]
        if not len(winner)  == 0:
            return self.current_clients_names[0]
        return winner[0]

    def second_to_answer(self, team_name):
        """
        give score to the second player to response
        :param team_name
        """
        if self.game_status == FIRST_ANSWER_IS_WRONG:
            self.score_dictionary[team_name] += self.score
        else:
            self.score_dictionary[team_name] += - self.score
        self.game_lock.release()
        self.event_udp.set() #wake up broadcast
        self.event_score_updater.set() #means the second done updating his score


    def generate_winner_message(self, team_name):
        result = f"{colorama.Fore.BLUE}Game over!\nThe correct answer was {self.equation_answer}! \n\n Congratulations for the winner: {self.winner}\n"
        return result+self.generate_statistics(team_name)

    def generate_statistics(self, team_name):
        result = f"Your score until now: {self.score_dictionary[team_name]}"
        result += f"\nThe GOAT (Greatest Of All Times) of the Equation Game is: {max(self.score_dictionary, key =self.score_dictionary.get)}"
        return result

    def generate_draw_message(self, team_name):
        result = f"{colorama.Fore.BLUE}Game over!\nThe correct answer was {self.equation_answer}!\n\n Nobody won you losers!!!\n"
        return result+self.generate_statistics(team_name)

s = Server(HOST_IP, TCP_PORT)
