import logging
import argparse

from .utils import load_config, setup_logging
from .bot import start
from .db import SqlBackend

log = logging.getLogger('rich')

def parse_arguments():
    parser = argparse.ArgumentParser()
    parser.add_argument('-d', '--debug', dest='debug', action='store_true', required=False)
    parser.add_argument('-b', '--bot', dest='bot', action='store_true', required=False)
    parser.add_argument('-c', '--config', dest='config', default='config.yaml', required=False)
    return parser.parse_args()


def run():
    args = parse_arguments()
    setup_logging(args.debug)
    log.debug('Load config from %s', args.config)
    config = load_config(args.config)

    if args.bot:
        token = open(config['telegram']['token'], 'rt').read().rstrip()
        backend = SqlBackend(config['sqlite']['path'])
        return start(token, backend, config)
