import socket

from .card import Card
from .deck import Deck
from .keychain import KeyChain
from .logger import Logger


class User:

    def __init__(self, N, parea_addr, parea_port, nickname, prob_cheat, cc):
        self.N = N
        self.parea_addr = parea_addr
        self.parea_port = parea_port
        self.nickname = nickname
        self.prob_cheat = prob_cheat
        self.card = Card(N, prob_cheat)
        self.deck = Deck(N)
        self.kc = KeyChain(asymmetric_key_size=256, symmetric_key_size=32, cc=cc)
        # Game
        self.started = False
        self.pdeck = Deck(N)
        self.winner = None
        # Logger
        self.logger = Logger(f'{nickname}.log', self.kc, write=False)
        self.kc.logger = self.logger
        self.card.logger = self.logger # For cheats
        self.pdeck.logger = self.logger # For cheats
        # Config
        self.kc.generate_asymmetric()
        self.kc.init_cc()
        # Socket
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.sock.connect((self.parea_addr, self.parea_port))
