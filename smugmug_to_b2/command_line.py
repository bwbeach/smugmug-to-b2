#
# File: command_line
#

import argparse
import json
import os
import sys
import yaml

from .exception import AppError, ConfigReadError
from .smugmug import get_auth_url, set_pin, get_auth_user


def pj(x):
    print(json.dumps(x, indent=4, sort_keys=True))


def get_config():
    """
    Returns a dictionary:

       { 'smugmug' : ( key, secret ), 'b2' : (key, secret) }
    """
    home = os.getenv('HOME')
    config_path = os.path.join(home, '.smugmug-to-b2')
    if not os.path.exists(config_path):
        raise ConfigReadError('ERROR: config file does not exist: ' + config_path)
    try:
        with open(config_path, 'r') as f:
            config_text = f.read()
    except Exception as e:
        raise ConfigReadError('ERROR reading ' + config_path + ': ' + e)
    try:
        config = yaml.load(config_text)
    except Exception as e:
        raise ConfigReadError('ERROR reading yaml from ' + config_path + ': ' + e)
    return config


def authorize_command(config, args):
    print(config)
    smug_mug_config = config['smugmug']
    url = get_auth_url(smug_mug_config['key'], smug_mug_config['secret'])
    print()
    print('Go to this URL, and get a PIN for accessing SmugMug:')
    print()
    print('   ', url)
    print()
    print('When you are done, run this command:')
    print()
    print('     smugmug-to-b2 set-pin <pin>')
    print()


def set_pin_command(config, args):
    smug_mug_config = config['smugmug']
    set_pin(smug_mug_config['key'], smug_mug_config['secret'], args.pin)
    print('PIN successfully stored.')


def stats_command(config, args):
    user = get_auth_user()
    node = user.node
    children = node.children
    for child in children:
        print(child)


def main():
    try:
        config = get_config()
    except AppError as app_error:
        print()
        print(str(app_error), file=sys.stderr)
        return

    parser = argparse.ArgumentParser(
        description='Tool to back up photos from SmugMug to B2',
    )
    subparsers = parser.add_subparsers(title='sub-commands', help='sub-command help')

    authorize_subparser = subparsers.add_parser('authorize')
    authorize_subparser.set_defaults(func=authorize_command)

    set_pin_subparser = subparsers.add_parser('set-pin')
    set_pin_subparser.add_argument('pin')
    set_pin_subparser.set_defaults(func=set_pin_command)

    stats_subparser = subparsers.add_parser('stats')
    stats_subparser.set_defaults(func=stats_command)

    args = parser.parse_args()
    args.func(config['config'], args)

