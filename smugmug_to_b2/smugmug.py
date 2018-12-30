#
# File: smugmug
#

import json
import os
import requests

from rauth import OAuth1Service, OAuth1Session
from urllib.parse import urlsplit, urlunsplit, parse_qsl, urlencode

from .exception import CredentialsError, HttpError

# From https://api.smugmug.com/api/v2/doc/tutorial/oauth/non-web.html:
OAUTH_ORIGIN = 'https://secure.smugmug.com'
REQUEST_TOKEN_URL = OAUTH_ORIGIN + '/services/oauth/1.0a/getRequestToken'
ACCESS_TOKEN_URL = OAUTH_ORIGIN + '/services/oauth/1.0a/getAccessToken'
AUTHORIZE_URL = OAUTH_ORIGIN + '/services/oauth/1.0a/authorize'
API_ORIGIN = 'https://api.smugmug.com'

# PIN path
PIN_PATH = os.path.join(os.getenv('HOME'), '.smugmug-to-b2-access-token')


def _read_json(path):
    with open(path, 'r') as f:
        return json.loads(f.read())


def _write_json(path, data):
    with open(path, 'w') as f:
        f.write(json.dumps(data, indent=4, sort_keys=True))
        f.write('\n')


def _add_auth_params(auth_url, access=None, permissions=None):
    if access is None and permissions is None:
        return auth_url
    parts = urlsplit(auth_url)
    query = parse_qsl(parts.query, True)
    if access is not None:
        query.append(('Access', access))
    if permissions is not None:
        query.append(('Permissions', permissions))
    return urlunsplit((
        parts.scheme,
        parts.netloc,
        parts.path,
        urlencode(query, True),
        parts.fragment))


def _make_service(key, secret):
    """
    Creates an OAUTH service.
    """
    service = OAuth1Service(
        name='smugmug-to-b2',
        consumer_key=key,
        consumer_secret=secret,
        request_token_url=REQUEST_TOKEN_URL,
        access_token_url=ACCESS_TOKEN_URL,
        authorize_url=AUTHORIZE_URL,
        base_url=API_ORIGIN + '/api/v2'
    )
    return service


def get_auth_url(key, secret):
    """
    Returns the URL to visit to authorize access to a smugmug account.
    """
    service = _make_service(key, secret)

    # First, we need a request token and secret, which SmugMug will give us.
    # We are specifying "oob" (out-of-band) as the callback because we don't
    # have a website for SmugMug to call back to.
    rt, rts = service.get_request_token(params={'oauth_callback': 'oob'})

    # Save the request token, because we'll need it after getting the PIN.
    _write_json(PIN_PATH, dict(key=key, secret=secret, request_token=rt, request_token_secret=rts))

    # Second, we need to give the user the web URL where they can authorize our
    # application.
    return _add_auth_params(service.get_authorize_url(rt), access='Full', permissions='Modify')


def set_pin(key, secret, pin):
    """
    Uses the PIN from visiting the auth page to create key/secret.
    """
    # Get the request token and secret that was saved before.
    info = _read_json(PIN_PATH)
    rt = info['request_token']
    rts = info['request_token_secret']
    service = _make_service(key, secret)
    at, ats = service.get_access_token(rt, rts, params={'oauth_verifier': pin})
    _write_json(PIN_PATH, dict(key=key, secret=secret, access_token=at, access_token_secret=ats))


class SmugMug:
    """
    API access to SmugMug.  Assumes that we have an access token in PIN_PATH.
    """
    def __init__(self):
        info = _read_json(PIN_PATH)
        self.key = info['key']
        self.secret = info['secret']
        self.access_token = info['access_token']
        self.access_token_secret = info['access_token_secret']
        self.session = OAuth1Session(
            self.key,
            self.secret,
            access_token=self.access_token,
            access_token_secret=self.access_token_secret)
        self.auth_user = self._get_json('/api/v2!authuser')['Response']['User']

    def get_user(self):
        return self._get_json(self.auth_user['Uri'])

    def _get_json(self, path):
        response = self.session.get(
            API_ORIGIN + path,
            headers={'Accept': 'application/json'}
        )
        return response.json()
