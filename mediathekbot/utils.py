import logging
import yaml
from rich.logging import RichHandler


def secs_to_hhmmss(secs):
    mins, secs = divmod(secs, 60)
    hours, mins = divmod(mins, 60)
    return '{:02d}:{:02d}:{:02d}'.format(hours, mins, secs)


def setup_logging(debug):
    """\
    Configures the rich logger
    """
    FORMAT = '%(asctime)s [%(levelname)s] %(message)s'
    logging.basicConfig(
        level=logging.DEBUG if debug else logging.INFO,
        format=FORMAT,
        datefmt='[%Y-%m-%d %H:%M:%S]',
        handlers=[RichHandler(markup=False)]
    )


def load_config(path):
    """\
    Opens the file and tries to parse the yaml data
    """
    with open(path, 'rb') as cfg:
        return yaml.load(cfg, Loader=yaml.SafeLoader)
