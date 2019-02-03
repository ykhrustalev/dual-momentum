import argparse

import yaml

from dm import db
from dm.fetch import do_fetch
from dm.suggest import do_suggest

DEFAULT_CONFIG = 'settings.yml'


def get_config(path):
    with open(path)as f:
        return yaml.load(f)


def parse_args():
    parser = argparse.ArgumentParser()
    parser.add_argument('--conf', default=DEFAULT_CONFIG)
    parser.add_argument('--fetch', action='store_true', default=False)
    parser.add_argument('--suggest', action='store_true', default=False)

    return parser.parse_args()


def main():
    args = parse_args()

    conf = get_config(args.conf)
    db_manager = db.Manager(conf['database'])

    if args.fetch:
        do_fetch(conf, db_manager)

    if args.suggest:
        do_suggest(conf, db_manager)
