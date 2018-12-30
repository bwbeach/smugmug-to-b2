#
# File: smugmug
#

import json
import os
import urllib

from rauth import OAuth1Service, OAuth1Session
from urllib.parse import urlsplit, urlunsplit, parse_qsl, urlencode

from .exception import AppError, CredentialsError, HttpError

# From https://api.smugmug.com/api/v2/doc/tutorial/oauth/non-web.html:
OAUTH_ORIGIN = 'https://secure.smugmug.com'
REQUEST_TOKEN_URL = OAUTH_ORIGIN + '/services/oauth/1.0a/getRequestToken'
ACCESS_TOKEN_URL = OAUTH_ORIGIN + '/services/oauth/1.0a/getAccessToken'
AUTHORIZE_URL = OAUTH_ORIGIN + '/services/oauth/1.0a/authorize'
API_ORIGIN = 'https://api.smugmug.com'

# PIN path
PIN_PATH = os.path.join(os.getenv('HOME'), '.smugmug-to-b2-access-token')


def pj(x):
    print(json.dumps(x, indent=4, sort_keys=True))


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


def _get_json(session, path):
    response = session.get(API_ORIGIN + path, headers={'Accept': 'application/json'})
    if response.status_code != 200:
        if response.status_code == 401:
            message = json.loads(response.text)['Message']
            print(urllib.parse.unquote(message))
        raise HttpError('status %d: %s' % (response.status_code, response.text,))
    else:
        return response.json()['Response']


def _get_paged_json(session, path):
    result = None
    next_path = path + '?count=5'
    while next_path is not None:
        print('AAA', next_path)
        one_batch = _get_json(session, next_path)
        print(sorted(one_batch.keys()))
        if result is None:
            result = one_batch
        else:
            list_field = result['Locator']
            result[list_field].append(one_batch.list_field)
        if 'Pages' not in one_batch:
            break
        pages = one_batch['Pages']
        next_path = pages.get('NextPage')
        pj(pages)
        print(next_path)
    if 'Pages' in result:
        del result['Pages']
    return result


class BaseObject:
    def __init__(self, session, data):
        self.session = session
        self.data = data

    def _get_object(self, path):
        data = _get_json(self.session, path)
        assert data['LocatorType'] == 'Object'
        object_type = data['Locator']
        object_data = data[object_type]
        return self.make_object(self.session, object_type, object_data)

    def _get_object_list(self, path):
        data = _get_paged_json(self.session, path)
        assert data['LocatorType'] == 'Objects'
        object_type = data['Locator']
        return list(
            self.make_object(self.session, object_type, object_data)
            for object_data in data[object_type]
        )

    def __str__(self):
        return self.data['Uri']

    @classmethod
    def make_object(self, session, object_type, object_data):
        if object_type == 'Node':
            return Node(session, object_data)
        elif object_type == 'User':
            return User(session, object_data)
        else:
            raise AppError('unknown object type: ' + object_type)


class User(BaseObject):
    @property
    def node(self):
        return self._get_object(self.data['Uris']['Node']['Uri'])


class Node(BaseObject):
    @property
    def children(self):
        return self._get_object_list(self.data['Uris']['ChildNodes']['Uri'])


def get_auth_user():
    info = _read_json(PIN_PATH)
    key = info['key']
    secret = info['secret']
    access_token = info['access_token']
    access_token_secret = info['access_token_secret']
    session = OAuth1Session(key, secret, access_token=access_token, access_token_secret=access_token_secret)
    return BaseObject.make_object(session, 'User', _get_json(session, '/api/v2!authuser')['User'])
