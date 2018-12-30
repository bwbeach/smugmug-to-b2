#
# File: exception
#

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


class CredentialsError(AppError):
    def __init__(self, service):
        super(CredentialsError, self).__init__('Access denied to %s.  Check your credentials' % (service,))


class HttpError(AppError):
    pass
