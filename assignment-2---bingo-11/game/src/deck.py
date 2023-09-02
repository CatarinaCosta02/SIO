from __future__ import annotations

import random

from .keychain import KeyChain


class Deck:

    def __init__(self, N, prob_cheat=0.0, logger=None):
        self.N = N
        self.prob_cheat = prob_cheat
        self.logger = logger
        self.numbers = [n.to_bytes(16, 'big') for n in range(0, self.N)]
        self.numbers_signature = None

    def reset_numbers(self):
        self.numbers = [n.to_bytes(16, 'big') for n in range(0, self.N)]

    def shuffle_numbers(self):
        random.shuffle(self.numbers)

    def encrypt_numbers(self, kc: KeyChain):
        self.numbers = [kc.encrypt(n) for n in self.numbers]

    def decrypt_numbers(self, kc: KeyChain, key=None):
        self.numbers = [kc.decrypt(n, key) for n in self.numbers]

    def validate_numbers(self, numbers_shuffled: list[bytes]) -> bool:
        # Check repeated numbers
        if len(self.numbers) != len(set(numbers_shuffled)):
            return False
        # Check invalid size
        if len(self.numbers) != self.N:
            return False
        # Check all numbers
        for n in self.numbers:
            if n not in numbers_shuffled:
                return False
        return True

    def get_numbers_plaintext(self) -> list:
        return [int.from_bytes(n, 'big') for n in self.numbers]

    def get_winners(self, user_cards: dict[str, list]) -> list[str]:
        for n in self.get_numbers_plaintext():
            for nickname, card_numbers in user_cards.items():
                user_cards[nickname] = [m for m in card_numbers if m != n]
            winners = [nickname for nickname, card_numbers in user_cards.items() if len(card_numbers) == 0]
            if len(winners) > 0:
                # CHEATING
                if random.random() < self.prob_cheat:
                    losers = [nickname for nickname in user_cards.keys() if nickname not in winners]
                    if len(losers) > 0:
                        i = random.randint(0, len(losers) - 1)
                        winners = [losers[i]]
                        self.logger.log(f'[CHEAT] CHEATING: Choosing different player {losers[i]} as winner.')
                return winners
        return []
