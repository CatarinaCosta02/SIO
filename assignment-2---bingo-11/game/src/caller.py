import json
import threading

from time import sleep
from .protocol import *
from .user import User
from .utils import *


class Caller(User):

    def __init__(self, N, parea_addr, parea_port, nickname, prob_cheat, cc, min_players):
        super().__init__(N, parea_addr, parea_port, nickname, prob_cheat, cc)
        self.pdeck.prob_cheat = prob_cheat
        self.min_players = min_players
        self.n_players = 0
        self.n_commited = 0
        self.n_winners = 0
        # Thread to start game
        self.t_sgame = threading.Thread(target=self.start_game)
        self.t_sgame_cancel = threading.Event()

    def new_game(self):
        """Function to create a new game."""

        self.logger.log('[INFO ] Creating new game...')
        self.started = False
        self.n_commited = 0
        self.n_winners = 0
        self.card.clear_user_cards()
        self.deck.reset_numbers()
        self.pdeck.reset_numbers()

        # Create thread to start game if not already exists
        if self.n_players >= self.min_players and not self.t_sgame.is_alive():
            self.t_sgame = threading.Thread(target=self.start_game)
            self.t_sgame_cancel = threading.Event()
            self.t_sgame.start()

    def start_game(self):
        """Thread to start the game."""

        for i in range(5, 0, -1):
            self.logger.log(f'[INFO ] Game will start in {i} seconds...')
            sleep(1)
            if self.t_sgame_cancel.is_set():
                self.logger.log('[INFO ] Game start cancelled.')
                return
        # Send game start message to playing area
        sgame_msg = Protocol.start_game(self.nickname)
        Protocol.send_msg(self.sock, sgame_msg, self.kc, self.logger)

    def run(self):
        """Caller loop."""
        self.logger.log('[INFO ] Caller is running...')

        # Sign nickname and public key with citizen card
        m = bytes(repr(json.dumps({
            'nickname': self.nickname,
            'public_key_pem': self.kc.public_key_pem,
        }, sort_keys=True, default=bytes_to_str)), 'utf-8')
        sm = self.kc.sign_cc(m)
        cert = self.kc.get_cert_cc()

        # Create join message
        join_msg = Protocol.join(self.nickname, 'CALLER', self.nickname, self.kc.public_key_pem, sm, cert)

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
            msg, m, sm = Protocol.recv_msg(self.sock, self.logger)
            if msg.command == Command.RESPONSE and msg.to_command == Command.JOIN and msg.status == 'NOK':
                self.logger.log(f'[INFO ] {msg.message}')
                sleep(1)
                continue

            self.logger.log('[INFO ] Signing own sequence, nickname and public key...')
            # Received sign user message from playing area
            suser_msg = msg
            # Sign sequence, nickname and public key
            m = bytes(repr(json.dumps({
                'sequence': suser_msg.sequence,
                'nickname': suser_msg.nickname,
                'public_key_pem': suser_msg.public_key_pem,
            }, sort_keys=True, default=bytes_to_str)), 'utf-8')
            sm = self.kc.sign(m)
            # Send response of sign user message to playing area
            resp_suser_msg = Protocol.response(self.nickname, Command.SIGN_USER, 'OK', '', (suser_msg.nickname, sm))
            Protocol.send_msg(self.sock, resp_suser_msg, self.kc, self.logger)

            # Receive response to join message from playing area
            resp_join_msg, m, sm = Protocol.recv_msg(self.sock, self.logger)
            if resp_join_msg.to_command == Command.JOIN and resp_join_msg.status == 'OK':
                self.logger.log(f'[INFO ] {resp_join_msg.message}')
                break
            sleep(1)

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
            if msg.command == Command.SIGN_USER:
                self.__sign_user(msg)
            if msg.command == Command.START_GAME:
                self.__start_game(msg)
            if msg.command == Command.DISCONNECT:
                self.__disconnect(msg)
            if self.started:
                if msg.command == Command.COMMIT_CARD:
                    self.__commit_card(msg)
                if msg.command == Command.SIGN_DECK:
                    self.__sign_deck(msg)
                if msg.command == Command.DECKS_KEYS:
                    self.__decks_keys(msg)
                if msg.command == Command.WINNER:
                    self.__winner(msg)
                if msg.command == Command.REQUEST_DISQUALIFY:
                    self.__request_disqualify(msg)

    def __response(self, resp_msg: ResponseMessage):

        if resp_msg.to_command == Command.REQUEST_LOG:
            print_log(resp_msg.data)
        elif resp_msg.to_command == Command.REQUEST_USERS:
            print_users(resp_msg.data)

    def __sign_user(self, suser_msg: SignUserMessage):
        self.logger.log('[INFO ] Signing user sequence, nickname and public key...');
        # Sign sequence, nickname and public key
        m = bytes(repr(json.dumps({
            'sequence': suser_msg.sequence,
            'nickname': suser_msg.nickname,
            'public_key_pem': suser_msg.public_key_pem,
        }, sort_keys=True, default=bytes_to_str)), 'utf-8')
        sm = self.kc.sign(m)
        # Send response of sign user message to playing area
        resp_suser_msg = Protocol.response(self.nickname, Command.SIGN_USER, 'OK', '', (suser_msg.nickname, sm))
        Protocol.send_msg(self.sock, resp_suser_msg, self.kc, self.logger)
        self.n_players += 1

        # Create thread to start game if not already exists
        if self.n_players >= self.min_players and not self.t_sgame.is_alive():
            self.t_sgame = threading.Thread(target=self.start_game)
            self.t_sgame_cancel = threading.Event()
            self.t_sgame.start()

    def __disconnect(self, disc_msg: DisconnectMessage):
        if disc_msg.nickname == self.nickname:
            self.logger.log('[INFO ] You have been disconnected.')
            self.sock.close()
            return
        else:
            self.logger.log(f'[INFO ] User {disc_msg.nickname} disconnected.')
        self.n_players -= 1

        # Cancel thread to start game if not enough players
        if self.n_players < self.min_players and self.t_sgame.is_alive():
            self.t_sgame_cancel.set()
        else:
            # Create a new game
            self.new_game()

    def __start_game(self, sgame_msg: StartGameMessage):
        self.logger.log('[INFO ] Game started!')
        self.started = True

        # Store everyone's public key pem
        for nickname, public_key_pem in sgame_msg.public_key_pems:
            self.kc.set_user_public_key_pem(nickname, public_key_pem)

    def __commit_card(self, ccard_msg: CommitCardMessage):

        # Validate card
        if self.card.validate_numbers(ccard_msg.numbers, ccard_msg.numbers_signature, self.kc,
                                      self.kc.get_user_public_key_pem(ccard_msg.sent_by)):
            # Store card
            self.card.set_user_card(ccard_msg.sent_by, ccard_msg.numbers)
            # Send response of commit card message to playing area
            resp_msg = Protocol.response(self.nickname, Command.COMMIT_CARD, 'OK', '', (ccard_msg.sent_by,))
            Protocol.send_msg(self.sock, resp_msg, self.kc, self.logger)

            self.n_commited += 1
            # Check if all player cards are committed
            if self.n_commited == self.n_players:
                # Generate the symmetric key
                self.kc.generate_symmetric()
                # Encrypt the numbers of the deck
                self.deck.encrypt_numbers(self.kc)
                # Shuffle the deck
                self.deck.shuffle_numbers()
                # Send shuffle deck message to playing area
                shdeck_msg = Protocol.shuffle_deck(self.nickname, self.deck.numbers,
                                                   self.kc.sign(b''.join(self.deck.numbers)))
                Protocol.send_msg(self.sock, shdeck_msg, self.kc, self.logger)
        else:
            # Send disqualify message to playing area
            disq_msg = Protocol.disqualify(self.nickname, ccard_msg.sent_by, 'Invalid card.')
            Protocol.send_msg(self.sock, disq_msg, self.kc, self.logger)

    def __sign_deck(self, sideck_msg: SignDeckMessage):

        public_key_pem = self.kc.get_user_public_key_pem(sideck_msg.sent_by)
        if not self.kc.verify(b''.join(sideck_msg.numbers), sideck_msg.numbers_signature, public_key_pem):
            # Send disqualify message to playing area
            rdisq_msg = Protocol.disqualify(self.nickname, sideck_msg.sent_by, 'Invalid deck signature.')
            Protocol.send_msg(self.sock, rdisq_msg, self.kc, self.logger)

        self.pdeck.numbers = sideck_msg.numbers
        self.pdeck.numbers_signature = self.kc.sign(b''.join(sideck_msg.numbers))
        # Send playing deck message to playing area
        pdeck_msg = Protocol.playing_deck(self.nickname, self.pdeck.numbers, self.pdeck.numbers_signature)
        Protocol.send_msg(self.sock, pdeck_msg, self.kc, self.logger)

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
                # Send disqualify message to playing area
                disq_msg = Protocol.disqualify(self.nickname, nickname, 'Invalid shuffled deck.')
                Protocol.send_msg(self.sock, disq_msg, self.kc, self.logger)
                # Create a new game
                self.new_game()
        self.logger.log(f'[INFO ] Playing deck: {self.pdeck.get_numbers_plaintext()}')

        # Determine the winners
        self.winners = self.pdeck.get_winners(self.card.user_cards)
        self.logger.log(f'[INFO ] Computed winners: {self.winners}')

    def __winner(self, winner_msg: WinnerMessage):

        # Check received winners
        if set(winner_msg.nicknames) == set(self.winners):

            self.n_winners += 1
            # Check if all players computed the winner
            if self.n_winners == self.n_players:
                # Send winner message to playing area
                winner_msg = Protocol.winner(self.nickname, self.winners)
                Protocol.send_msg(self.sock, winner_msg, self.kc, self.logger)
                # Create a new game
                self.new_game()
        else:
            # Send disqualify message to playing area
            disq_msg = Protocol.disqualify(self.nickname, winner_msg.sent_by, 'Invalid winners.')
            Protocol.send_msg(self.sock, disq_msg, self.kc, self.logger)

    def __request_disqualify(self, rdisq_msg: RequestDisqualifyMessage):

        # Send disqualify message to playing area
        disq_msg = Protocol.disqualify(self.nickname, rdisq_msg.nickname, rdisq_msg.reason)
        Protocol.send_msg(self.sock, disq_msg, self.kc, self.logger)
