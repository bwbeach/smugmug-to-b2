#
# File: smugmug
#

import json
import hashlib
import os
import requests_oauthlib
import urllib

from pathlib import Path
from rauth import OAuth1Service
from typing import Dict
from urllib.parse import urlsplit, urlunsplit, parse_qsl, urlencode

from .exception import AppError, HttpError

# From https://api.smugmug.com/api/v2/doc/tutorial/oauth/non-web.html:
OAUTH_ORIGIN = 'https://secure.smugmug.com'
REQUEST_TOKEN_URL = OAUTH_ORIGIN + '/services/oauth/1.0a/getRequestToken'
ACCESS_TOKEN_URL = OAUTH_ORIGIN + '/services/oauth/1.0a/getAccessToken'
AUTHORIZE_URL = OAUTH_ORIGIN + '/services/oauth/1.0a/authorize'
API_ORIGIN = 'https://api.smugmug.com'

# PIN path
PIN_PATH = Path(os.getenv('HOME'), '.smugmug-to-b2-access-token')


def pj(x):
    print(json.dumps(x, indent=4, sort_keys=True))


def _read_json_dict(path: Path) -> Dict:
    with path.open('r') as f:
        return json.load(f)


def _write_json_dict(path: Path, data: Dict) -> None:
    with path.open('w') as f:
        json.dump(data, f, indent=4, sort_keys=True)


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
    _write_json_dict(PIN_PATH, dict(key=key, secret=secret, request_token=rt, request_token_secret=rts))

    # Second, we need to give the user the web URL where they can authorize our
    # application.
    return _add_auth_params(service.get_authorize_url(rt), access='Full', permissions='Modify')


def set_pin(key, secret, pin):
    """
    Uses the PIN from visiting the auth page to create key/secret.
    """
    # Get the request token and secret that was saved before.
    info = _read_json_dict(PIN_PATH)
    rt = info['request_token']
    rts = info['request_token_secret']
    service = _make_service(key, secret)
    at, ats = service.get_access_token(rt, rts, params={'oauth_verifier': pin})
    _write_json_dict(PIN_PATH, dict(key=key, secret=secret, access_token=at, access_token_secret=ats))


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
    next_path = path + '?count=20'
    while next_path is not None:
        one_batch = _get_json(session, next_path)
        if result is None:
            result = one_batch
        else:
            list_field = result['Locator']
            result[list_field].extend(one_batch[list_field])
        if 'Pages' not in one_batch:
            break
        pages = one_batch['Pages']
        next_path = pages.get('NextPage')
    if 'Pages' in result:
        del result['Pages']
    return result


class BaseObject:
    def __init__(self, session, data):
        self.session = session
        self.data = data

    def _get_from_my_uri(self, uri_name):
        uris = self.data['Uris']
        if uri_name not in uris:
            pj(self.data)
        path = uris[uri_name]['Uri']
        data = _get_paged_json(self.session, path)
        object_type = data['Locator']
        if data['LocatorType'] == 'Object':
            return self.make_object(self.session, object_type, data[object_type])
        elif data['LocatorType'] == 'Objects':
            return list(
                self.make_object(self.session, object_type, object_data)
                for object_data in data.get(object_type, [])
            )

    def __str__(self):
        return self.data['Uri']

    @classmethod
    def make_object(cls, session, object_type, object_data):
        if object_type == 'Album':
            return Album(session, object_data)
        elif object_type == 'AlbumImage':
            return AlbumImage(session, object_data)
        elif object_type == 'LargestVideo':
            return LargestVideo(session, object_data)
        elif object_type == 'Node':
            return Node(session, object_data)
        elif object_type == 'User':
            return User(session, object_data)
        else:
            raise AppError('unknown object type: ' + object_type)

    def _get_required(self, field):
        if field not in self.data:
            pj(self.data)
        return self.data[field]


class User(BaseObject):
    @property
    def node(self):
        return self._get_from_my_uri('Node')


class Node(BaseObject):
    @property
    def children(self):
        assert self.has_children
        assert not self.has_album
        return self._get_from_my_uri('ChildNodes')

    @property
    def has_children(self):
        return self.data['HasChildren']

    @property
    def name(self):
        return self.data['Name']

    @property
    def has_album(self):
        return 'Album' in self.data['Uris']

    @property
    def album(self):
        return self._get_from_my_uri('Album')


class Album(BaseObject):
    @property
    def images(self):
        return self._get_from_my_uri('AlbumImages')


def bytes_from_url(session, url, expected_byte_count=None, expected_md5=None):
    response = session.get(url)
    if response.status_code != 200:
        raise HttpError('status = %d %s' % (response.status_code, response.text,))
    response.raw.decode_content = True  # force undo transport encoding (like gzip)
    content_bytes = response.content
    md5_hash = hashlib.md5(content_bytes).hexdigest()
    if expected_byte_count is not None:
        assert len(content_bytes) == expected_byte_count
    if expected_md5 is not None:
        assert md5_hash == expected_md5
    return content_bytes


class AlbumImage(BaseObject):

    @property
    def content(self):
        try:
            fmt = self.data['Format']
            if fmt == 'JPG':
                return bytes_from_url(self.session, self.archived_uri, self.byte_count, self.archived_md5)
            elif fmt == 'MP4':
                largest_video = self.largest_video
                return largest_video.content
            else:
                raise Exception('unknown format: ' + fmt)
        except Exception:
            pj(self.data)
            raise

    @property
    def archived_md5(self):
        return self._get_required('ArchivedMD5')

    @property
    def archived_uri(self):
        return self._get_required('ArchivedUri')

    @property
    def byte_count(self):
        return self._get_required('ArchivedSize')

    @property
    def caption(self):
        return self._get_required('Caption')

    @property
    def date(self):
        return self._get_required('Date')

    @property
    def file_name(self):
        return self._get_required('FileName')

    @property
    def largest_video(self):
        return self._get_from_my_uri('LargestVideo')

    @property
    def keywords(self):
        return self._get_required('Keywords')

    @property
    def title(self):
        return self._get_required('Title')


class LargestVideo(BaseObject):
    """
    Gets the contents of a LargestVideo contained in an AlbumImage.

    https://dgrin.com/discussion/261504/api-v2-0-no-method-to-download-original-images-videos
    """
    @property
    def content(self):
        return bytes_from_url(self.session, self.url, self.size, self.md5)

    @property
    def url(self):
        return self._get_required('Url')

    @property
    def size(self):
        return self._get_required('Size')

    @property
    def md5(self):
        return self._get_required('MD5')


def get_auth_user():
    info = _read_json_dict(PIN_PATH)
    key = info['key']
    secret = info['secret']
    access_token = info['access_token']
    access_token_secret = info['access_token_secret']
    session = requests_oauthlib.OAuth1Session(
        client_key=key,
        client_secret=secret,
        resource_owner_key=access_token,
        resource_owner_secret=access_token_secret
    )
    return BaseObject.make_object(session, 'User', _get_json(session, '/api/v2!authuser')['User'])
