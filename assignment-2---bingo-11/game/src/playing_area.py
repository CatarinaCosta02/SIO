from __future__ import annotations

import json
import selectors
import socket
import threading

from .keychain import KeyChain
from .logger import Logger
from .profile import Profile
from .protocol import *
from .utils import *


class PlayingArea:

    def __init__(self, N, addr, port, log):
        self.N = N
        self.addr = addr
        self.port = port
        self.nickname = 'parea'
        self.kc = KeyChain(asymmetric_key_size=256, symmetric_key_size=32)
        # Users
        self.callers = ['Caller', 'CallerJr'] # Citizens eligible to be callers
        self.profiles = []  # Includes caller and players
        self.plock = threading.Lock()
        # Game
        self.started = False
        self.pdeck = []
        self.pdeck_signature = None
        self.keyed = 0
        # Logger
        self.logger = Logger(f'{self.nickname}.log', self.kc, write=log)
        self.kc.logger = self.logger
        # Config
        self.kc.generate_asymmetric()
        # Socket
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self.sock.bind((self.addr, self.port))
        self.sock.listen(11)  # 11 concurrent users (1 caller + 10 players)
        # Selector
        self.sel = selectors.DefaultSelector()
        self.sel.register(self.sock, selectors.EVENT_READ, self.accept)

    def accept(self, sock):
        """Accept new connection."""
        conn, addr = sock.accept()
        # Create thread to handle user connection
        t = threading.Thread(target=self.read, args=[conn])
        t.start()

    def read(self, conn: socket.socket):
        """Read data from connection."""
        this_p = None # User profile of this connection
        while True:
            if this_p:
                conn.recv(1) # Wait for data
                with this_p.lock:
                    msg, m, sm = Protocol.recv_msg(conn, self.logger, consumed_flag=True)
            else:
                msg, m, sm = Protocol.recv_msg(conn, self.logger)
            # User disconnected
            if msg is None:
                if this_p:
                    self.logger.log(f'[INFO ] User {this_p.nickname} disconnected.')
                    # Send disconnect message to every user
                    disc_msg = Protocol.disconnect(self.nickname, this_p.nickname)
                    for p in self.profiles:
                        Protocol.send_msg(p.conn, disc_msg, self.kc, self.logger)
                    # Remove user profile
                    self.rem_profile(this_p.nickname)
                conn.close()
                return

            if this_p and not msg.command == Command.JOIN:
                public_key_pem = this_p.public_key_pem
            else:
                public_key_pem = msg.public_key_pem

            # Check signature
            if not self.kc.verify(m, sm, public_key_pem):
                if this_p and this_p.is_player:
                    # Send message to caller to disqualify player
                    rdisq_msg = Protocol.request_disqualify(self.nickname, this_p.nickname, 'Invalid signature.')
                    Protocol.send_msg(self.get_caller().conn, rdisq_msg, self.kc, self.logger)
                elif this_p and not this_p.is_player:
                    # Send message to caller to disconnect
                    disc_msg = Protocol.disconnect(self.nickname, this_p.nickname, 'Invalid signature.')
                    for p in self.profiles:
                        Protocol.send_msg(p.conn, disc_msg, self.kc, self.logger)
                    # Remove caller profile
                    self.rem_profile(this_p.nickname)
                    this_p.conn.close()
                elif msg.command == Command.JOIN:
                    # Send response of join message to user
                    resp_msg = Protocol.response(self.nickname, Command.JOIN, 'NOK', 'Invalid signature.')
                    Protocol.send_msg(conn, resp_msg, self.kc, self.logger)
                    continue
                else:
                    # Disconnect players
                    for p in self.get_players():
                        # Send message to player to disconnect
                        disc_msg = Protocol.disconnect(self.nickname, p.nickname, 'Invalid signature.')
                        Protocol.send_msg(p.conn, disc_msg, self.kc, self.logger)
                        # Remove player profile
                        self.rem_profile(p.nickname)
                        p.conn.close()
                # End the game
                self.started = False
                continue

           # Take appropriate action
            if msg.command == Command.JOIN:
                this_p = self.__join(conn, msg)
            if msg.command == Command.RESPONSE:
                self.__response(msg)
            if msg.command == Command.START_GAME:
                self.__start_game(msg)
            if msg.command == Command.DISQUALIFY:
                self.__disqualify(msg)
            if msg.command == Command.REQUEST_LOG:
                self.__request_log(msg)
            if msg.command == Command.REQUEST_USERS:
                self.__request_users(msg)
            if self.started:
                if msg.command == Command.COMMIT_CARD:
                    self.__commit_card(msg)
                if msg.command == Command.SHUFFLE_DECK:
                    self.__shuffle_deck(msg)
                if msg.command == Command.PLAYING_DECK:
                    self.__playing_deck(msg)
                if msg.command == Command.SYMMETRIC_KEY:
                    self.__symmetric_key(msg)
                if msg.command == Command.WINNER:
                    self.__winner(msg)
                if msg.command == Command.REQUEST_DISQUALIFY:
                    self.__request_disqualify(msg)

    def __join(self, conn, join_msg: JoinMessage) -> Profile | None:
        is_player = join_msg.role == 'PLAYER'
        if not is_player:
            self.started = False

        # Check if game already started
        if self.started:
            resp_msg = Protocol.response(self.nickname, Command.JOIN, 'NOK', 'Game already started.')
            Protocol.send_msg(conn, resp_msg, self.kc, self.logger)
            return None

        # Check for users with the same nickname
        if join_msg.nickname in [p.nickname for p in self.profiles]:
            resp_join_msg = Protocol.response(self.nickname, Command.JOIN, 'NOK', 'Nickname already in use.')
            Protocol.send_msg(conn, resp_join_msg, self.kc, self.logger)
            return None

        # Check if user is using a caller reseved nickname
        if is_player and join_msg.nickname in self.callers:
            resp_join_msg = Protocol.response(self.nickname, Command.JOIN, 'NOK', 'Nickname is not permitted.')
            Protocol.send_msg(conn, resp_join_msg, self.kc, self.logger)
            return None

        # Check if user can be caller
        if not is_player and join_msg.nickname not in self.callers:
            resp_join_msg = Protocol.response(self.nickname, Command.JOIN, 'NOK', 'Not eligible to be caller.')
            Protocol.send_msg(conn, resp_join_msg, self.kc, self.logger)
            return None

        # Check for already existing caller
        if not is_player and self.get_caller():
            resp_join_msg = Protocol.response(self.nickname, Command.JOIN, 'NOK', 'Caller already exists.')
            Protocol.send_msg(conn, resp_join_msg, self.kc, self.logger)
            return None

        # Check for callers
        if is_player and not self.get_caller():
            resp_join_msg = Protocol.response(self.nickname, Command.JOIN, 'NOK', 'No caller available.')
            Protocol.send_msg(conn, resp_join_msg, self.kc, self.logger)
            return None

        # Check validity of CC signature
        m = bytes(repr(json.dumps({
            'nickname': join_msg.nickname,
            'public_key_pem': join_msg.public_key_pem,
        }, sort_keys=True, default=bytes_to_str)), 'utf-8')
        if not self.kc.verify_cc(m, join_msg.cc_signature, join_msg.cc_certificate):
            resp_join_msg = Protocol.response(self.nickname, Command.JOIN, 'NOK', 'Invalid CC signature.')
            Protocol.send_msg(conn, resp_join_msg, self.kc, self.logger)
            return None

        # Create user profile
        p = Profile(join_msg.nickname, join_msg.public_key_pem, join_msg.cc_signature, join_msg.cc_certificate, conn,
                    is_player)

        # Assign user profile to caller or player
        if not is_player:
            self.set_caller(p)
        else:
            self.add_profile(p)

        # Send sign user message to caller
        suser_msg = Protocol.sign_user(self.nickname, p.sequence, p.nickname, p.public_key_pem)
        with self.get_caller().lock:
            Protocol.send_msg(self.get_caller().conn, suser_msg, self.kc, self.logger)
        return p

    def __response(self, resp_msg: ResponseMessage):

        if resp_msg.to_command == Command.SIGN_USER:
            p = self.get_profile(resp_msg.data[0])
            if resp_msg.status == 'OK':
                # Save the signature in profile
                p.signature = resp_msg.data[1]
                # Send response of join message to user
                resp_join_msg = Protocol.response(self.nickname, Command.JOIN, 'OK',
                                                  f'Joined with nickname {p.nickname}.')
                with p.lock:
                    Protocol.send_msg(p.conn, resp_join_msg, self.kc, self.logger)
                self.logger.log(f'[INFO ] User {p.nickname} joined.')
                # Resign player profiles if it was a new caller that joined
                if not p.is_player:
                    for pl in self.get_players():
                        suser_msg = Protocol.sign_user(self.nickname, pl.sequence, pl.nickname, pl.public_key_pem)
                        with pl.lock:
                            Protocol.send_msg(p.conn, suser_msg, self.kc, self.logger)
            else:
                # Send response of join message to user
                resp_join_msg = Protocol.response(self.nickname, Command.JOIN, 'NOK', 'Unable to sign user.')
                with p.lock:
                    Protocol.send_msg(p.conn, resp_join_msg, self.kc, self.logger)
                # Remove the profile
                self.rem_profile(p.nickname)
        elif resp_msg.to_command == Command.COMMIT_CARD:
            if resp_msg.status == 'NOK':
                self.logger.log(f'[INFO ] {resp_msg.message}')

    def __start_game(self, sgame_msg: StartGameMessage):
        self.started = True
        self.pdeck = []
        self.pdeck_signature = None
        self.keyed = 0

        # Send start game message to all users with everyone's public key pem
        sgame_msg = Protocol.start_game(self.nickname, [(p.nickname, p.public_key_pem) for p in self.profiles])
        for p in self.profiles:
            with p.lock:
                Protocol.send_msg(p.conn, sgame_msg, self.kc, self.logger)
        self.logger.log(f'[INFO ] Game started with players {[p.nickname for p in self.get_players()]}.')

    def __commit_card(self, ccard_msg: CommitCardMessage):
        self.logger.log(f'[INFO ] Player {ccard_msg.sent_by} commited card {ccard_msg.numbers}.')

        # Forward commit card message to caller and other players
        for p in [self.get_caller()] + [pl for pl in self.get_players() if pl.nickname != ccard_msg.sent_by]:
            with p.lock:
                Protocol.send_msg(p.conn, ccard_msg, self.kc, self.logger)

    def __disqualify(self, disq_msg: DisqualifyMessage):
        self.logger.log(f'[INFO ] Player {disq_msg.nickname} disqualified.')

        # Forward disqualify message to all players
        for p in self.get_players():
            with p.lock:
                Protocol.send_msg(p.conn, disq_msg, self.kc, self.logger)
        # Remove the disqualified player from the game
        self.rem_profile(disq_msg.nickname)
        # End the game
        self.started = False

    def __shuffle_deck(self, shdeck_msg: ShuffleDeckMessage):
        self.logger.log(f'[INFO ] User {shdeck_msg.sent_by} shuffled deck.')

        # Store deck and signature on user profile
        p = self.get_profile(shdeck_msg.sent_by)
        p.deck = shdeck_msg.numbers
        p.deck_signature = shdeck_msg.numbers_signature

        # Send the deck to the next user to shuffle
        p = self.get_profile_next(p)
        if p:
            with p.lock:
                Protocol.send_msg(p.conn, shdeck_msg, self.kc, self.logger)
        # Send it to the caller to finally sign it
        else:
            sideck_msg = Protocol.sign_deck(shdeck_msg.sent_by, shdeck_msg.numbers, shdeck_msg.numbers_signature)
            with self.get_caller().lock:
                Protocol.send_msg(self.get_caller().conn, sideck_msg, self.kc, self.logger)

    def __playing_deck(self, pdeck_msg: PlayingDeckMessage):

        # Store deck and signature on playing area
        self.pdeck = pdeck_msg.numbers
        self.pdeck_signature = pdeck_msg.numbers_signature

        # Forward playing deck message to all players
        for p in self.get_players():
            with p.lock:
                Protocol.send_msg(p.conn, pdeck_msg, self.kc, self.logger)

    def __symmetric_key(self, skey_msg: SymmetricKeyMessage):
        self.logger.log(f'[INFO ] User {skey_msg.sent_by} symmetric key: {skey_msg.symmetric_key.hex()}.')

        # Store symmetric key on user profile
        p = self.get_profile(skey_msg.sent_by)
        p.symmetric_key = skey_msg.symmetric_key
        self.keyed += 1

        # Send decks keys message if all users have sent their symmetric key
        if self.keyed == len(self.profiles):
            dkeys_msg = Protocol.decks_keys(self.nickname, [(p.nickname, p.deck, p.symmetric_key) for p in self.profiles])
            for p in self.profiles:
                with p.lock:
                    Protocol.send_msg(p.conn, dkeys_msg, self.kc, self.logger)

    def __winner(self, winner_msg: WinnerMessage):

        # Forward winner message from a player to the caller
        if winner_msg.sent_by != self.get_caller().nickname:
            self.logger.log(f'[INFO ] Player {winner_msg.sent_by} winners: {winner_msg.nicknames}.')
            with self.get_caller().lock:
                Protocol.send_msg(self.get_caller().conn, winner_msg, self.kc, self.logger)
        # Forward winner message from the caller to all players
        elif winner_msg.sent_by == self.get_caller().nickname:
            self.logger.log(f'[INFO ] Caller winners: {winner_msg.nicknames}.')
            for p in self.get_players():
                with p.lock:
                    Protocol.send_msg(p.conn, winner_msg, self.kc, self.logger)
            # End the game
            self.started = False

    def __request_log(self, rlog_msg: RequestLogMessage):
        self.logger.log(f'[INFO ] User {rlog_msg.sent_by} requested log.')

        # Get the log
        log = self.logger.get_all()
        # Send log message to user
        p = self.get_profile(rlog_msg.sent_by)
        log_msg = Protocol.response(rlog_msg.sent_by, Command.REQUEST_LOG, 'OK', '', tuple(log))
        with p.lock:
            Protocol.send_msg(p.conn, log_msg, self.kc, self.logger)

    def __request_users(self, rusers_msg: RequestUsersMessage):
        self.logger.log(f'[INFO ] User {rusers_msg.sent_by} requested users.')

        # Get the users
        users = []
        for profile in self.profiles:
            users += [[profile.sequence, profile.nickname, profile.public_key_pem, profile.signature]]
        # Send users message to user
        p = self.get_profile(rusers_msg.sent_by)
        users_msg = Protocol.response(rusers_msg.sent_by, Command.REQUEST_USERS, 'OK', '', tuple(users))
        with p.lock:
            Protocol.send_msg(p.conn, users_msg, self.kc, self.logger)
            
    def __request_disqualify(self, rdisq_msg: RequestDisqualifyMessage):
        self.logger.log(f'[INFO ] User {rdisq_msg.sent_by} requested disqualify.')

        # Forward request disqualify message to caller
        with self.get_caller().lock:
            Protocol.send_msg(self.get_caller().conn, rdisq_msg, self.kc, self.logger)

    def get_caller(self):
        return self.profiles[0] if self.profiles and self.profiles[0].sequence == 0 else None

    def set_caller(self, p: Profile):
        self.logger.log(f'[INFO ] Caller set to {p.nickname}.')
        with self.plock:
            if not self.get_caller():
                self.profiles.insert(0, p)
            else:
                self.profiles[0] = p

    def rem_caller(self):
        self.logger.log(f'[INFO ] Caller removed.')
        with self.plock:
            if self.get_caller():
                self.profiles.pop(0)

    def get_players(self):
        return [p for p in self.profiles if p.sequence > 0]

    def get_profile(self, nickname) -> Profile:
        return next((p for p in self.profiles if p.nickname == nickname), None)

    def get_profile_next(self, p: Profile):
        for i in range(len(self.profiles)):
            if self.profiles[i].sequence == p.sequence:
                if i < len(self.profiles) - 1:
                    return self.profiles[i + 1]
        return None

    def add_profile(self, p: Profile):
        self.logger.log(f'[INFO ] User {p.nickname} added.')
        with self.plock:
            self.profiles.append(p)

    def rem_profile(self, nickname):
        self.logger.log(f'[INFO ] User {nickname} removed.')
        with self.plock:
            self.profiles = [p for p in self.profiles if p.nickname != nickname]

    def run(self):
        """Playing area loop."""
        self.logger.log('[INFO ] Playing area is running...')

        while True:
            events = self.sel.select()
            for key, mask in events:
                callback = key.data
                callback(key.fileobj)
