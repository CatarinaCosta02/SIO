import threading


class Profile:
    counter = 0

    def __init__(self, nickname, public_key_pem, cc_signature, cc_certificate, conn, is_player):
        self.sequence = self.__next_sequence_number() if is_player else 0
        self.nickname = nickname
        self.public_key_pem = public_key_pem
        self.cc_signature = cc_signature
        self.cc_certificate = cc_certificate
        self.is_player = is_player

        self.conn = conn
        self.lock = threading.Lock()

        self.signature = None     # Done by the caller: 'sequence, nickname, public_key'
        self.symmetric_key = None # Generated to encrypt each deck
        self.deck = None          # Encrypted deck by this user
        self.deck_signature = None

    def __next_sequence_number(self):
        Profile.counter += 1
        return Profile.counter
