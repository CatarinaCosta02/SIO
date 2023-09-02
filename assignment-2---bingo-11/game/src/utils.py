from __future__ import annotations

import base64


def bytes_to_str(obj):
    """Used in json.dumps() as 'default' argument."""
    if isinstance(obj, bytes):
        return obj.decode('utf-8', 'ignore')
    return obj


def str_to_bytes(obj):
    """Used in json.loads() as 'object_hook' argument."""
    if isinstance(obj, str) and obj.startswith('b\'') and obj.endswith('\''):
        return bytes(obj[2:-1], 'utf-8', 'ignore')
    return obj


def print_log(log: tuple[str]):
    """Used to print log from playing area."""
    for entry in log:
        print(entry)


def print_users(users: tuple[list[int, str, bytes, bytes]]):
    """Used to print users from playing area."""
    for sequence, nickname, public_key_pem, signature in users:
        print(f'{sequence:2} | {nickname:15} | {base64.b64encode(public_key_pem).decode("utf-8")} | {base64.b64encode(signature).decode("utf-8")}')
