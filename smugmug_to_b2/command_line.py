#
# File: command_line
#

import os
import sys
import yaml


class AppError(Exception):
    def __init__(self, message):
        super(AppError, self).__init__(message)


CONFIG_HELP = """

For both Smugmug and B2, the credentials are a key and a secret.
In B2, the key is called an "application key ID" or "account ID", and the
secret is call an "application key".

The credentials for both should be in ~/.smugmug-to-b2, which is YAML and
should look like this:

config:
  smugmug:
    key: ...
    secret: ...
  b2:
    key: ...
    secret: ...
     
"""
class ConfigReadError(AppError):
    def __str__(self):
        return super(ConfigReadError, self).__str__() + CONFIG_HELP


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


def main():
    try:
        print(get_config())
    except AppError as app_error:
        print()
        print(str(app_error), file=sys.stderr)

