# Project 2 - Secure Game

## Considerations

- In the following chapters, the root refers to the directory `game/`.

## Dependencies

This game was developed using **Python3.8** and requires the following
dependencies (see [Installation](#installation) section):

- click (8.1.3)
- cryptography (38.0.1)
- PyKCS11 (1.5.11)

## Installation

- Run `pip3 install virtualenv` to install the module `virtualenv`.
- Run `virtualenv venv` in root to create a virtual environment.
- Run `source venv/bin/activate` in root to enter the virtual environment.
- Run `pip3 install -r requirements.txt` to install all project dependencies.

### How to use virtual smartcards
- Follow the instructions [here](https://sweet.ua.pt/jpbarraca/course/sio-2223/lab-cc/#virtual-smartcard) to install virtual smartcards.
- Run `systemctl stop pcscd` and `sudo pcscd -f -d` to start the daemon.
- Run `./vicc -t PTEID -v` in `virtualsmartcard/src/vpicc` to start the virtual smartcard.

## Running the game

- Run `source venv/bin/activate` in root to enter the virtual environment.

### 1. Running the playing area

- Run `python3 playing_area.py` in root to start the playing area.
  - `--N` Size of the deck (default: 100).
  - `--own_addr` Address of the playing area (default: localhost).
  - `--own_port` Port of the playing area (default: 5000).
  - `--log` Write logs to file (default: True).

### 2. Running the caller

- Run `python3 caller.py` in root to start the caller.
  - `--N` Size of the deck (default: 100).
  - `--parea_addr` Address of the playing area (default: localhost).
  - `--parea_port` Port of the playing area (default: 5000).
  - `--nickname` Nickname of the caller (default: Caller).
  - `--prob_cheat` Probability of cheating (default: 0.0).
  - `--cc` Use citizen card for authentication (default: False).
  - `--min_players` Minimum number of players to start a game (default: 2).
- Available commands: `/logs`, `/users`
- Available cheats: Choosing certain player as winner.

### 3. Running the player(s)

- Run `python3 player.py` in root to start the player.
  - `--N` Size of the deck (default: 100).
  - `--parea_addr` Address of the playing area (default: localhost).
  - `--parea_port` Port of the playing area (default: 5000).
  - `--nickname` Nickname of the player (default: Player).
  - `--prob_cheat` Probability of cheating (default: 0.0).
  - `--cc` Use citizen card for authentication (default: False). (default: False).
- Available commands: `/logs`, `/users`
- Available cheats: Changing a random byte in the signature; Adding a repeated number in the card. 
- **Note:** Players must have distinct nicknames to be able to join the game.


## Ending the game

- Stop the scripts using `CTRL+C` in terminal.
- Run `deactivate` in root to exit the virtual environment.
