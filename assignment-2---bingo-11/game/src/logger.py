import hashlib
import threading
from datetime import datetime

from .keychain import KeyChain


class Logger:
    n_log = 1
    last = None
    lock = threading.Lock()

    def __init__(self, fname: str, kc: KeyChain, write: bool = False):
        self.fname = fname
        self.kc = kc
        self.write = write

    def log(self, msg: str):
        """Logs a message."""

        with self.lock:
            if self.write:
                with open(f'{self.fname}', 'a+') as f:
                    if Logger.n_log == 1:
                        # Clear previous log
                        f.seek(0)
                        f.truncate(0)
                        # Write header
                        Logger.last = 'sequence, timestamp, hash(prev_entry), text, signature'
                        f.write(Logger.last + '\n')
                    # Compute missing data
                    hash_prev = hashlib.sha256(Logger.last.encode()).hexdigest()
                    msg_str = f'\"{msg}\"'
                    msg_sign = self.kc.sign(bytes(msg, 'utf-8')).hex()
                    # Write new log entry
                    entry = ', '.join(
                        [str(Logger.n_log), str(datetime.timestamp(datetime.now())), hash_prev, msg_str, msg_sign])
                    f.write(entry + '\n')
                    # Update variables
                    Logger.n_log += 1
                    Logger.last = entry
            # Print new log entry
            print(msg)

    def get_all(self):
        """Returns all the logs."""

        log = []
        with self.lock:
            with open(f'{self.fname}', 'r') as f:
                for line in f:
                    log.append(line.strip())
        return log
