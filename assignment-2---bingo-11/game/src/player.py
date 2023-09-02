import json
import threading

from time import sleep
from .protocol import *
from .user import User
from .utils import *


class Player(User):

    def __init__(self, N, parea_addr, parea_port, nickname, prob_cheat, cc):
        super().__init__(N, parea_addr, parea_port, nickname, prob_cheat, cc)
        self.kc.prob_cheat = prob_cheat

    def run(self):
        """Player loop."""
        self.logger.log('[INFO ] Player is running...')

        # Sign nickname and public key with citizen card
        m = bytes(repr(json.dumps({
            'nickname': self.nickname,
            'public_key_pem': self.kc.public_key_pem,
        }, sort_keys=True, default=bytes_to_str)), 'utf-8')
        sm = self.kc.sign_cc(m)
        cert = self.kc.get_cert_cc()

        # Create join message
        join_msg = Protocol.join(self.nickname, 'PLAYER', self.nickname, self.kc.public_key_pem, sm, cert)

        n_attempts = 0
        while True:
            if n_attempts == 5:
                self.logger.log(f'[ERROR] Failed to join playing area after {n_attempts} attempts.')
                exit(1)
            n_attempts += 1

            self.logger.log('[INFO ] Attempting to join playing area...')
            # Send join message to playing area
            Protocol.send_msg(self.sock, join_msg, self.kc, self.logger)

            # Receive response of join message from playing area
            resp_join_msg, m, sm = Protocol.recv_msg(self.sock, self.logger)

            self.logger.log(f'[INFO ] {resp_join_msg.message}')
            if resp_join_msg.to_command == Command.JOIN and resp_join_msg.status == 'OK':
                break
            else:
                sleep(1)
                continue

        # Create a thread to run the game loop
        t0 = threading.Thread(target=self.game_loop)
        t0.start()

        # Create a thread to receive user input
        t1 = threading.Thread(target=self.stdin_loop)
        t1.start()

        t0.join()

    def stdin_loop(self):
        """User input loop."""
        while True:
            cmd = input()
            if self.sock.fileno() == -1:
                return
            self.logger.log(f'[INPUT] Requested command {cmd}')
            if cmd == '/logs':
                # Send request log message to playing area
                rlog_msg = Protocol.request_log(self.nickname)
                Protocol.send_msg(self.sock, rlog_msg, self.kc, self.logger)
            if cmd == '/users':
                # Send request users message to playing area
                rusers_msg = Protocol.request_users(self.nickname)
                Protocol.send_msg(self.sock, rusers_msg, self.kc, self.logger)

    def game_loop(self):
        """Normal game loop."""
        while True:
            msg, m, sm = Protocol.recv_msg(self.sock, self.logger)
            # Playing area disconnected
            if msg is None:
                self.logger.log('[INFO ] Playing area disconnected.')
                self.sock.close()
                return

            # Take appropriate action
            if msg.command == Command.RESPONSE:
                self.__response(msg)
            if msg.command == Command.DISCONNECT:
                self.__disconnect(msg)
            if msg.command == Command.START_GAME:
                self.__start_game(msg)
            if msg.command == Command.COMMIT_CARD:
                self.__commit_card(msg)
            if msg.command == Command.DISQUALIFY:
                self.__disqualify(msg)
            if msg.command == Command.SHUFFLE_DECK:
                self.__shuffle_deck(msg)
            if msg.command == Command.PLAYING_DECK:
                self.__playing_deck(msg)
            if msg.command == Command.DECKS_KEYS:
                self.__decks_keys(msg)
            if msg.command == Command.WINNER:
                self.__winner(msg)

    def __response(self, resp_msg: ResponseMessage):

        if resp_msg.to_command == Command.JOIN:
            self.logger.log(f'[INFO ] {resp_msg.message}')
        elif resp_msg.to_command == Command.REQUEST_LOG:
            print_log(resp_msg.data)
        elif resp_msg.to_command == Command.REQUEST_USERS:
            print_users(resp_msg.data)

    def __disconnect(self, disc_msg: DisconnectMessage):

        if disc_msg.nickname == self.nickname:
            self.logger.log('[INFO ] You have been disconnected.')
            self.sock.close()
            return
        else:
            self.logger.log(f'[INFO ] User {disc_msg.nickname} disconnected.')

    def __start_game(self, sgame_msg: StartGameMessage):
        self.card.clear_user_cards()

        # Store everyone's public key pem
        for nickname, public_key_pem in sgame_msg.public_key_pems:
            self.kc.set_user_public_key_pem(nickname, public_key_pem)

        # Generate card
        self.card.generate_numbers()
        self.card.set_user_card(self.nickname, self.card.numbers)
        # Send commit card message to playing area
        ccard_msg = Protocol.commit_card(self.nickname, self.card.numbers,
                                         self.kc.sign(b''.join([n.to_bytes(4, 'big') for n in self.card.numbers])))
        Protocol.send_msg(self.sock, ccard_msg, self.kc, self.logger)
        self.logger.log(f'[INFO ] Playing card: {self.card.numbers}')

    def __commit_card(self, ccard_msg: CommitCardMessage):

        # Validate card
        if self.card.validate_numbers(ccard_msg.numbers, ccard_msg.numbers_signature, self.kc,
                                      self.kc.get_user_public_key_pem(ccard_msg.sent_by)):
            # Store card
            self.card.set_user_card(ccard_msg.sent_by, ccard_msg.numbers)
            # Send response of commit card message to playing area
            resp_msg = Protocol.response(self.nickname, Command.COMMIT_CARD, 'OK', '', (ccard_msg.sent_by,))
            Protocol.send_msg(self.sock, resp_msg, self.kc, self.logger)
        else:
            # Send response of commit card message to playing area
            resp_msg = Protocol.response(self.nickname, Command.COMMIT_CARD, 'NOK', 'Invalid card.',
                                         (ccard_msg.sent_by,))
            Protocol.send_msg(self.sock, resp_msg, self.kc, self.logger)

    def __disqualify(self, disq_msg: DisqualifyMessage):

        if disq_msg.nickname == self.nickname:
            self.logger.log('[INFO ] You have been disqualified.')
            self.sock.close()
            return
        else:
            self.logger.log(f'[INFO ] User {disq_msg.nickname} disqualified.')

    def __shuffle_deck(self, shdeck_msg):

        # Check deck signature before shuffling
        public_key_pem = self.kc.get_user_public_key_pem(shdeck_msg.sent_by)
        if not self.kc.verify(b''.join(shdeck_msg.numbers), shdeck_msg.numbers_signature, public_key_pem):
            # Send request disqualify message to playing area to disqualify user
            rdisq_msg = Protocol.request_disqualify(self.nickname, shdeck_msg.sent_by, 'Invalid deck signature.')
            Protocol.send_msg(self.sock, rdisq_msg, self.kc, self.logger)

        self.deck.numbers = shdeck_msg.numbers
        # Generate the symmetric key
        self.kc.generate_symmetric()
        # Encrypt the numbers of the deck
        self.deck.encrypt_numbers(self.kc)
        # Shuffle the deck
        self.deck.shuffle_numbers()
        # Send shuffle deck message to playing area
        shdeck_msg = Protocol.shuffle_deck(self.nickname, self.deck.numbers, self.kc.sign(b''.join(self.deck.numbers)))
        Protocol.send_msg(self.sock, shdeck_msg, self.kc, self.logger)

    def __playing_deck(self, pdeck_msg):

        public_key_pem = self.kc.get_user_public_key_pem(pdeck_msg.sent_by)
        if not self.kc.verify(b''.join(pdeck_msg.numbers), pdeck_msg.numbers_signature, public_key_pem):
            self.logger.log('[WARN ] Invalid deck signature from caller.')

        self.pdeck.numbers = pdeck_msg.numbers
        self.pdeck.numbers_signature = pdeck_msg.numbers_signature

        # Send symmetric key message to playing area
        skey_msg = Protocol.symmetric_key(self.nickname, self.kc.symmetric_key)
        Protocol.send_msg(self.sock, skey_msg, self.kc, self.logger)

    def __decks_keys(self, dkeys_msg: DecksKeysMessage):

        # Decrypt the deck using the symmetric key of each user, in the reverse order of the provided list
        for nickname, numbers_shuffed, symmetric_key in reversed(dkeys_msg.decks_keys):
            # Validate deck
            if self.pdeck.validate_numbers(numbers_shuffed):
                # Decrypt playing deck numbers
                self.pdeck.decrypt_numbers(self.kc, symmetric_key)
            else:
                self.logger.log(f'[WARN ] Invalid shuffled deck by user {nickname}.')
        self.logger.log(f'[INFO ] Playing deck: {self.pdeck.get_numbers_plaintext()}')

        # Determine the winners
        self.winners = self.pdeck.get_winners(self.card.user_cards)
        self.logger.log(f'[INFO ] Computed winners: {self.winners}')
        # Send winner message to playing area
        winner_msg = Protocol.winner(self.nickname, self.winners)
        Protocol.send_msg(self.sock, winner_msg, self.kc, self.logger)

    def __winner(self, winner_msg: WinnerMessage):
        self.logger.log(f'[INFO ] Caller winners: {winner_msg.nicknames}')
