import click

from src.player import Player


@click.command()
@click.option('-N',           type=int,   default=100,         help='Size of the deck')
@click.option('--parea_addr', type=str,   default='localhost', help='Address of the playing area')
@click.option('--parea_port', type=int,   default=5000,        help='Port of the playing area')
@click.option('--nickname',   type=str,   default='Player',    help='Nickname of the player')
@click.option('--prob_cheat', type=float, default=0.0,         help='Probability of cheating')
@click.option('--cc',         type=bool,  default=False,       help='Use citizen card for authentication')
def main(n, parea_addr, parea_port, nickname, prob_cheat, cc):
    p = Player(n, parea_addr, parea_port, nickname, prob_cheat, cc)
    p.run()


if __name__ == '__main__':
    main()
