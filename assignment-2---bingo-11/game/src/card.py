import random

from .keychain import KeyChain


class Card:

    def __init__(self, N, prob_cheat=0.0, logger=None):
        self.N = N
        self.size = N // 4
        self.prob_cheat = prob_cheat
        self.logger = logger
        self.numbers = None
        self.user_cards = {}

    def generate_numbers(self):
        self.numbers = random.sample(list(range(0, self.N)), self.size)
        # CHEATING
        if random.random() < self.prob_cheat:
            i = random.randint(0, self.size - 1)
            self.numbers[(i+1)%self.size] = self.numbers[i]
            self.logger.log(f'[CHEAT] CHEATING: Adding a repeated number ({self.numbers[i]}) in the card.')

    def validate_numbers(self, numbers: list, numbers_signature: bytes, kc: KeyChain, public_key_pem: bytes) -> bool:
        # Check repeated numbers
        if len(numbers) != len(set(numbers)):
            return False
        # Check invalid size
        if len(numbers) != self.size:
            return False
        # Check numbers signature
        if not kc.verify(b''.join([n.to_bytes(4, 'big') for n in numbers]), numbers_signature, public_key_pem):
            return False
        return True

    def get_user_card(self, nickname: str):
        return self.user_cards[nickname]

    def set_user_card(self, nickname: str, numbers: list):
        self.user_cards[nickname] = numbers

    def clear_user_cards(self):
        self.user_cards = {}
