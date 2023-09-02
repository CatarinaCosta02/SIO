from __future__ import annotations

import base64
import hashlib
import json
import socket
import threading

from datetime import datetime
from enum import Enum
from .keychain import KeyChain
from .utils import *

class Command(Enum):
    JOIN = 'JOIN'
    RESPONSE = 'RESPONSE'
    SIGN_USER = 'SIGN_USER'
    START_GAME = 'START_GAME'
    DISCONNECT = 'DISCONNECT'
    COMMIT_CARD = 'COMMIT_CARD'
    DISQUALIFY = 'DISQUALIFY'
    SHUFFLE_DECK = 'SHUFFLE_DECK'
    SIGN_DECK = 'SIGN_DECK'
    PLAYING_DECK = 'PLAYING_DECK'
    SYMMETRIC_KEY = 'SYMMETRIC_KEY'
    DECKS_KEYS = 'DECKS_KEYS'
    WINNER = 'WINNER'
    REQUEST_LOG = 'REQUEST_LOG'
    REQUEST_USERS = 'REQUEST_USERS'
    REQUEST_DISQUALIFY = 'REQUEST_DISQUALIFY'


class Message:
    """Message Type"""

    def __init__(self, command: Command):
        self.command = command


class JoinMessage(Message):
    """Message used to join the playing area."""

    def __init__(self, sent_by: str, role: str, nickname: str, public_key_pem: bytes, cc_signature: bytes,
                 cc_certificate: bytes):
        super().__init__(Command.JOIN)
        self.sent_by = sent_by
        self.role = role
        self.nickname = nickname
        self.public_key_pem = public_key_pem
        self.cc_signature = cc_signature
        self.cc_certificate = cc_certificate

    def __repr__(self):
        return json.dumps({
            'command': self.command.value,
            'sent_by': self.sent_by,
            'role': self.role,
            'nickname': self.nickname,
            'public_key_pem': base64.b64encode(self.public_key_pem).decode('utf-8'),
            'cc_signature': base64.b64encode(self.cc_signature).decode('utf-8'),
            'cc_certificate': base64.b64encode(self.cc_certificate).decode('utf-8')
        }, sort_keys=True, default=bytes_to_str)


class ResponseMessage(Message):
    """Message used as a response of a given command."""

    def __init__(self, sent_by: str, to_command: Command, status: str, message: str, data: tuple):
        super().__init__(Command.RESPONSE)
        self.sent_by = sent_by
        self.to_command = to_command
        self.status = status
        self.message = message
        self.data = data

    def __repr__(self):
        return json.dumps({
            'command': self.command.value,
            'sent_by': self.sent_by,
            'to_command': self.to_command.value,
            'status': self.status,
            'message': self.message,
            'data': (self.data[0], base64.b64encode(self.data[1]).decode('utf-8')) if self.to_command == Command.SIGN_USER
                else tuple([[sequence,nickname,base64.b64encode(public_key_pem).decode('utf-8'),base64.b64encode(signature).decode('utf-8')] for sequence, nickname, public_key_pem, signature in self.data]) if self.to_command == Command.REQUEST_USERS
                else tuple(self.data)
        }, sort_keys=True, default=bytes_to_str)


class SignUserMessage(Message):
    """Message used for caller to sign a user that joined the playing area."""

    def __init__(self, sent_by: str, sequence: int, nickname: str, public_key_pem: bytes):
        super().__init__(Command.SIGN_USER)
        self.sent_by = sent_by
        self.sequence = sequence
        self.nickname = nickname
        self.public_key_pem = public_key_pem

    def __repr__(self):
        return json.dumps({
            'command': self.command.value,
            'sent_by': self.sent_by,
            'sequence': self.sequence,
            'nickname': self.nickname,
            'public_key_pem': base64.b64encode(self.public_key_pem).decode('utf-8')
        }, sort_keys=True, default=bytes_to_str)


class DisconnectMessage(Message):
    """Message used to inform a disconnection from the playing area."""

    def __init__(self, sent_by: str, nickname: str, reason: str):
        super().__init__(Command.DISCONNECT)
        self.sent_by = sent_by
        self.nickname = nickname
        self.reason = reason

    def __repr__(self):
        return json.dumps({
            'command': self.command.value,
            'sent_by': self.sent_by,
            'nickname': self.nickname,
            'reason': self.reason
        }, sort_keys=True, default=bytes_to_str)


class StartGameMessage(Message):
    """Message used to start the game."""

    def __init__(self, sent_by: str, public_key_pems: list[tuple[str, bytes]]):
        super().__init__(Command.START_GAME)
        self.sent_by = sent_by
        self.public_key_pems = public_key_pems

    def __repr__(self):
        return json.dumps({
            'command': self.command.value,
            'sent_by': self.sent_by,
            'public_key_pems': [(nickname, base64.b64encode(public_key_pem).decode('utf-8'))
                                for nickname, public_key_pem in self.public_key_pems]
        }, sort_keys=True, default=bytes_to_str)


class CommitCardMessage(Message):
    """Message used to commit a card to the caller and other players."""

    def __init__(self, sent_by: str, numbers: list, numbers_signature: bytes):
        super().__init__(Command.COMMIT_CARD)
        self.sent_by = sent_by
        self.numbers = numbers
        self.numbers_signature = numbers_signature

    def __repr__(self):
        return json.dumps({
            'command': self.command.value,
            'sent_by': self.sent_by,
            'numbers': self.numbers,
            'numbers_signature': base64.b64encode(self.numbers_signature).decode('utf-8')
        }, sort_keys=True, default=bytes_to_str)


class DisqualifyMessage(Message):
    """Message used to disqualify a player."""

    def __init__(self, sent_by: str, nickname: str, reason: str):
        super().__init__(Command.DISQUALIFY)
        self.sent_by = sent_by
        self.nickname = nickname
        self.reason = reason

    def __repr__(self):
        return json.dumps({
            'command': self.command.value,
            'sent_by': self.sent_by,
            'nickname': self.nickname,
            'reason': self.reason
        }, sort_keys=True, default=bytes_to_str)


class ShuffleDeckMessage(Message):
    """Message used to shuffle the deck."""

    def __init__(self, sent_by: str, numbers: list[bytes], numbers_signature: bytes):
        super().__init__(Command.SHUFFLE_DECK)
        self.sent_by = sent_by
        self.numbers = numbers
        self.numbers_signature = numbers_signature

    def __repr__(self):
        return json.dumps({
            'command': self.command.value,
            'sent_by': self.sent_by,
            'numbers': [base64.b64encode(n).decode('utf-8') for n in self.numbers],
            'numbers_signature': base64.b64encode(self.numbers_signature).decode('utf-8')
        }, sort_keys=True, default=bytes_to_str)


class SignDeckMessage(Message):
    """Message used to sign the deck."""

    def __init__(self, sent_by: str, numbers: list[bytes], numbers_signature: bytes):
        super().__init__(Command.SIGN_DECK)
        self.sent_by = sent_by
        self.numbers = numbers
        self.numbers_signature = numbers_signature

    def __repr__(self):
        return json.dumps({
            'command': self.command.value,
            'sent_by': self.sent_by,
            'numbers': [base64.b64encode(n).decode('utf-8') for n in self.numbers],
            'numbers_signature': base64.b64encode(self.numbers_signature).decode('utf-8')
        }, sort_keys=True, default=bytes_to_str)


class PlayingDeckMessage(Message):
    """Message used to announce the playing deck to the playing area."""

    def __init__(self, sent_by: str, numbers: list[bytes], numbers_signature: bytes):
        super().__init__(Command.PLAYING_DECK)
        self.sent_by = sent_by
        self.numbers = numbers
        self.numbers_signature = numbers_signature

    def __repr__(self):
        return json.dumps({
            'command': self.command.value,
            'sent_by': self.sent_by,
            'numbers': [base64.b64encode(n).decode('utf-8') for n in self.numbers],
            'numbers_signature': base64.b64encode(self.numbers_signature).decode('utf-8')
        }, sort_keys=True, default=bytes_to_str)


class SymmetricKeyMessage(Message):
    """Message used to announce the symmetric key."""

    def __init__(self, sent_by: str, symmetric_key: bytes):
        super().__init__(Command.SYMMETRIC_KEY)
        self.sent_by = sent_by
        self.symmetric_key = symmetric_key

    def __repr__(self):
        return json.dumps({
            'command': self.command.value,
            'sent_by': self.sent_by,
            'symmetric_key': base64.b64encode(self.symmetric_key).decode('utf-8')
        }, sort_keys=True, default=bytes_to_str)


class DecksKeysMessage(Message):
    """Message used to announce the shuffled decks and symmetric keys of each user."""

    def __init__(self, sent_by: str, decks_keys: list[tuple[str, list[bytes], bytes]]):
        super().__init__(Command.DECKS_KEYS)
        self.sent_by = sent_by
        self.decks_keys = decks_keys

    def __repr__(self):
        return json.dumps({
            'command': self.command.value,
            'sent_by': self.sent_by,
            'decks_keys': [(nickname, [base64.b64encode(n).decode('utf-8') for n in numbers],
                            base64.b64encode(symmetric_key).decode('utf-8'))
                           for nickname, numbers, symmetric_key in self.decks_keys]
        }, sort_keys=True, default=bytes_to_str)


class WinnerMessage(Message):
    """Message to announce the winner of the game."""

    def __init__(self, sent_by: str, nicknames: list[str]):
        super().__init__(Command.WINNER)
        self.sent_by = sent_by
        self.nicknames = nicknames

    def __repr__(self):
        return json.dumps({
            'command': self.command.value,
            'sent_by': self.sent_by,
            'nicknames': self.nicknames
        }, sort_keys=True, default=bytes_to_str)


class RequestLogMessage(Message):
    """Message to request the log of the game."""

    def __init__(self, sent_by: str):
        super().__init__(Command.REQUEST_LOG)
        self.sent_by = sent_by

    def __repr__(self):
        return json.dumps({
            'command': self.command.value,
            'sent_by': self.sent_by
        }, sort_keys=True, default=bytes_to_str)


class RequestUsersMessage(Message):
    """Message to request the list of users."""

    def __init__(self, sent_by: str):
        super().__init__(Command.REQUEST_USERS)
        self.sent_by = sent_by

    def __repr__(self):
        return json.dumps({
            'command': self.command.value,
            'sent_by': self.sent_by
        }, sort_keys=True, default=bytes_to_str)

class RequestDisqualifyMessage(Message):
    """Message to request the disqualification of a user."""

    def __init__(self, sent_by: str, nickname: str, reason: str):
        super().__init__(Command.REQUEST_DISQUALIFY)
        self.sent_by = sent_by
        self.nickname = nickname
        self.reason = reason

    def __repr__(self):
        return json.dumps({
            'command': self.command.value,
            'sent_by': self.sent_by,
            'nickname': self.nickname,
            'reason': self.reason
        }, sort_keys=True, default=bytes_to_str)


class Protocol:

    @classmethod
    def join(cls, sent_by: str, role: str, nickname: str, public_key_pem: bytes, cc_signature: bytes,
             cc_certificate: bytes) -> JoinMessage:
        return JoinMessage(sent_by, role, nickname, public_key_pem, cc_signature, cc_certificate)

    @classmethod
    def response(cls, sent_by: str, to_command: Command, status: str, message: str,
                 data: tuple = ()) -> ResponseMessage:
        return ResponseMessage(sent_by, to_command, status, message, data)

    @classmethod
    def sign_user(cls, sent_by: str, sequence: int, nickname: str, public_key_pem: bytes) -> SignUserMessage:
        return SignUserMessage(sent_by, sequence, nickname, public_key_pem)

    @classmethod
    def disconnect(cls, sent_by: str, nickname: str, reason: str = '') -> DisconnectMessage:
        return DisconnectMessage(sent_by, nickname, reason)

    @classmethod
    def start_game(cls, sent_by: str, public_key_pems: list[tuple[str, bytes]] = []) -> StartGameMessage:
        return StartGameMessage(sent_by, public_key_pems)

    @classmethod
    def commit_card(cls, sent_by: str, numbers: list, numbers_signature: bytes) -> CommitCardMessage:
        return CommitCardMessage(sent_by, numbers, numbers_signature)

    @classmethod
    def disqualify(cls, sent_by: str, nickname: str, reason: str) -> DisqualifyMessage:
        return DisqualifyMessage(sent_by, nickname, reason)

    @classmethod
    def shuffle_deck(cls, sent_by: str, numbers: list[bytes], numbers_signature: bytes) -> ShuffleDeckMessage:
        return ShuffleDeckMessage(sent_by, numbers, numbers_signature)

    @classmethod
    def sign_deck(cls, sent_by: str, numbers: list[bytes], numbers_signature: bytes) -> SignDeckMessage:
        return SignDeckMessage(sent_by, numbers, numbers_signature)

    @classmethod
    def playing_deck(cls, sent_by: str, numbers: list[bytes], numbers_signature: bytes) -> PlayingDeckMessage:
        return PlayingDeckMessage(sent_by, numbers, numbers_signature)

    @classmethod
    def symmetric_key(cls, sent_by: str, symmetric_key: bytes) -> SymmetricKeyMessage:
        return SymmetricKeyMessage(sent_by, symmetric_key)

    @classmethod
    def decks_keys(cls, sent_by: str, decks_keys: list[tuple[str, list[bytes], bytes]]) -> DecksKeysMessage:
        return DecksKeysMessage(sent_by, decks_keys)

    @classmethod
    def winner(cls, sent_by: str, nicknames: list[str]) -> WinnerMessage:
        return WinnerMessage(sent_by, nicknames)

    @classmethod
    def request_log(cls, sent_by: str) -> RequestLogMessage:
        return RequestLogMessage(sent_by)

    @classmethod
    def request_users(cls, sent_by: str) -> RequestUsersMessage:
        return RequestUsersMessage(sent_by)

    @classmethod
    def request_disqualify(cls, sent_by: str, nickname: str, reason: str = '') -> RequestDisqualifyMessage:
        return RequestDisqualifyMessage(sent_by, nickname, reason)

    @classmethod
    def serialize(cls, msg: Message) -> bytes:
        return bytes(repr(msg), 'utf-8')

    @classmethod
    def unserialize(cls, msg: bytes) -> dict:
        return json.loads(msg, object_hook=str_to_bytes)

    @classmethod
    def send_msg(cls, conn: socket.socket, msg: Message, kc: KeyChain, logger) -> (Message, bytes, bytes):
        """Sends thought a connection a serialized Message object."""
        if conn.fileno() == -1:
            return
        # Flag to indicate there is a message
        flag = bytes(1)
        # Serialize message
        m: bytes = Protocol.serialize(msg)
        # Sign message
        sm: bytes = kc.sign(m)
        # Length of message
        m_len: bytes = (256 + len(m)).to_bytes(4, 'big')
        # Send message
        conn.sendall(flag + m_len + sm + m)

        logger.log(f'[PROTO] Sent {msg.command.value} message.')

    @classmethod
    def recv_msg(cls, conn: socket.socket, logger, consumed_flag=False) -> (Message, bytes, bytes):
        if conn.fileno() == -1:
            return None, None, None
        if not consumed_flag:
            conn.recv(1)

        m_len = int.from_bytes(conn.recv(4), 'big')
        if m_len == 0:
            return None, None, None

        sm: bytes = conn.recv(256)  # Signature
        if len(sm) != 256:
            return None, None, None

        m: bytes = cls.__recvall(conn, m_len - 256)
        if m is None:
            return None, None, None
        d = Protocol.unserialize(m)

        if 'command' not in d:
            raise ProtocolBadFormat(m)

        logger.log(f'[PROTO] Received {d["command"]} message from {d["sent_by"]}.')

        if d['command'] == Command.JOIN.value and 'sent_by' in d and 'role' in d and 'nickname' in d and 'public_key_pem' in d and 'cc_signature' in d and 'cc_certificate' in d:
            msg = Protocol.join(d['sent_by'], d['role'], d['nickname'], base64.b64decode(d['public_key_pem'].encode('utf-8')), base64.b64decode(d['cc_signature'].encode('utf-8')), base64.b64decode(d['cc_certificate'].encode('utf-8')))
        elif d['command'] == Command.RESPONSE.value and 'sent_by' in d and 'to_command' in d and 'status' in d and 'message' in d and 'data' in d:
            if d['to_command'] == Command.SIGN_USER.value:
                msg = Protocol.response(d['sent_by'], Command(d['to_command']), d['status'], d['message'], (d['data'][0], base64.b64decode(d['data'][1].encode('utf-8'))))
            elif d['to_command'] == Command.REQUEST_USERS.value:
                msg = Protocol.response(d['sent_by'], Command(d['to_command']), d['status'], d['message'], tuple([[sequence,nickname,base64.b64decode(public_key_pem.encode('utf-8')),base64.b64decode(signature.encode('utf-8'))] for sequence, nickname, public_key_pem, signature in d['data']]))
            else:
                msg = Protocol.response(d['sent_by'], Command(d['to_command']), d['status'], d['message'], tuple(d['data']))
        elif d['command'] == Command.SIGN_USER.value and 'sent_by' in d and 'sequence' in d and 'nickname' in d and 'public_key_pem' in d:
            msg = Protocol.sign_user(d['sent_by'], d['sequence'], d['nickname'],  base64.b64decode(d['public_key_pem'].encode('utf-8')))
        elif d['command'] == Command.DISCONNECT.value and 'sent_by' in d and 'nickname' in d and 'reason' in d:
            msg = Protocol.disconnect(d['sent_by'], d['nickname'], d['reason'])
        elif d['command'] == Command.START_GAME.value and 'sent_by' in d and 'public_key_pems' in d:
            msg = Protocol.start_game(d['sent_by'], [(nickname, base64.b64decode(public_key_pem.encode('utf-8'))) for nickname, public_key_pem in d['public_key_pems']])
        elif d['command'] == Command.COMMIT_CARD.value and 'sent_by' in d and 'numbers' in d and 'numbers_signature' in d:
            msg = Protocol.commit_card(d['sent_by'], d['numbers'], base64.b64decode(d['numbers_signature'].encode('utf-8')))
        elif d['command'] == Command.DISQUALIFY.value and 'sent_by' in d and 'nickname' in d and 'reason' in d:
            msg = Protocol.disqualify(d['sent_by'], d['nickname'], d['reason'])
        elif d['command'] == Command.SHUFFLE_DECK.value and 'sent_by' in d and 'numbers' in d and 'numbers_signature' in d:
            msg = Protocol.shuffle_deck(d['sent_by'], [base64.b64decode(n.encode('utf-8')) for n in d['numbers']], base64.b64decode(d['numbers_signature'].encode('utf-8')))
        elif d['command'] == Command.SIGN_DECK.value and 'sent_by' in d and 'numbers' in d and 'numbers_signature' in d:
            msg = Protocol.sign_deck(d['sent_by'], [base64.b64decode(n.encode('utf-8')) for n in d['numbers']], base64.b64decode(d['numbers_signature'].encode('utf-8')))
        elif d['command'] == Command.PLAYING_DECK.value and 'sent_by' in d and 'numbers' in d and 'numbers_signature' in d:
            msg = Protocol.playing_deck(d['sent_by'], [base64.b64decode(n.encode('utf-8')) for n in d['numbers']], base64.b64decode(d['numbers_signature'].encode('utf-8')))
        elif d['command'] == Command.SYMMETRIC_KEY.value and 'sent_by' in d and 'symmetric_key' in d:
            msg = Protocol.symmetric_key(d['sent_by'], base64.b64decode(d['symmetric_key'].encode('utf-8')))
        elif d['command'] == Command.DECKS_KEYS.value and 'sent_by' in d and 'decks_keys' in d:
            msg = Protocol.decks_keys(d['sent_by'], [(nickname, [base64.b64decode(n.encode('utf-8')) for n in numbers], base64.b64decode(symmetric_key.encode('utf-8'))) for nickname, numbers, symmetric_key in d['decks_keys']])
        elif d['command'] == Command.WINNER.value and 'sent_by' in d and 'nicknames' in d:
            msg = Protocol.winner(d['sent_by'], d['nicknames'])
        elif d['command'] == Command.REQUEST_LOG.value and 'sent_by' in d:
            msg = Protocol.request_log(d['sent_by'])
        elif d['command'] == Command.REQUEST_USERS.value and 'sent_by' in d:
            msg = Protocol.request_users(d['sent_by'])
        elif d['command'] == Command.REQUEST_DISQUALIFY.value and 'sent_by' in d and 'nickname' in d and 'reason' in d:
            msg = Protocol.request_disqualify(d['sent_by'], d['nickname'], d['reason'])
        else:
            raise ProtocolBadFormat(m)
        return msg, m, sm

    @classmethod
    def __recvall(cls, conn: socket.socket, n: int) -> bytes:
        """Receives n bytes through a connection."""
        data = bytearray()
        while len(data) < n:
            pack = conn.recv(n - len(data))
            if not pack:
                return None
            data.extend(pack)
        return bytes(data)  # Immutable


class ProtocolBadFormat(Exception):
    """Exception when source message is not Protocol."""

    def __init__(self, original_msg: bytes = None):
        """Store original message that triggered exception."""
        self.original = original_msg

    @property
    def original_msg(self) -> str:
        """Retrieve original message as a string."""
        return self.original.decode('utf-8')
