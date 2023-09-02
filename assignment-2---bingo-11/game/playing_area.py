import click

from src.playing_area import PlayingArea


@click.command()
@click.option('-N',         type=int,  default=100,         help='Size of the deck')
@click.option('--own_addr', type=str,  default='localhost', help='Address of the playing area')
@click.option('--own_port', type=int,  default=5000,        help='Port of the playing area')
@click.option('--log',      type=bool, default=True,        help='Write logs to file')
def main(n, own_addr, own_port, log):
    pa = PlayingArea(n, own_addr, own_port, log)
    pa.run()


if __name__ == '__main__':
    main()
