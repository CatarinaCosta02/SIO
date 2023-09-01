import click

from src.caller import Caller


@click.command()
@click.option('-N',            type=int,   default=100,         help='Size of the deck')
@click.option('--parea_addr',  type=str,   default='localhost', help='Address of the playing area')
@click.option('--parea_port',  type=int,   default=5000,        help='Port of the playing area')
@click.option('--nickname',    type=str,   default='Caller',    help='Nickname of the caller')
@click.option('--prob_cheat',  type=float, default=0.0,         help='Probability of cheating')
@click.option('--cc',          type=bool,  default=False,       help='Use citizen card for authentication')
@click.option('--min_players', type=int,   default=2,           help='Minimum number of players to start a game')
def main(n, parea_addr, parea_port, nickname, prob_cheat, cc, min_players):
    c = Caller(n, parea_addr, parea_port, nickname, prob_cheat, cc, min_players)
    c.run()


if __name__ == '__main__':
    main()