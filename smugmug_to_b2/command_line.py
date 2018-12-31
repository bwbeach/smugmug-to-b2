#
# File: command_line
#

import argparse
import json
import os
import sys
import yaml

from .backup import all_b2_images, all_smugmug_images, backup
from .exception import AppError, ConfigReadError
from .smugmug import get_auth_url, set_pin, get_auth_user

from b2.account_info.in_memory import InMemoryAccountInfo
from b2.api import B2Api
from b2.cache import InMemoryCache


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



def list_smug_mug(config, args):
    user = get_auth_user()
    for i in all_smugmug_images(user.node):
        print(i)


def get_bucket(config):
    b2_config = config['b2']
    account_info = InMemoryAccountInfo()
    b2_api = B2Api(account_info=account_info, cache=InMemoryCache())
    b2_api.authorize_account('production', b2_config['key'], b2_config['secret'])
    return b2_api.get_bucket_by_name(b2_config['bucket'])

def list_b2(config, args):
    bucket = get_bucket(config)
    for i in all_b2_images(bucket):
        print(i)


def backup_command(config, args):
    # The 'ls' method on B2 buckets requires that the prefix end with '/'
    assert args.prefix == '' or args.prefix.endswith('/'), 'prefix must end with "/"'
    node = get_auth_user().node
    bucket = get_bucket(config)
    backup(node, bucket, args.prefix)


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

    list_b2_subparser = subparsers.add_parser('list-b2')
    list_b2_subparser.set_defaults(func=list_b2)

    list_smug_mug_subparser = subparsers.add_parser('list-smug-mug')
    list_smug_mug_subparser.set_defaults(func=list_smug_mug)

    backup_subparser = subparsers.add_parser('backup')
    backup_subparser.add_argument('--prefix', default='')
    backup_subparser.set_defaults(func=backup_command)

    args = parser.parse_args()
    args.func(config['config'], args)

