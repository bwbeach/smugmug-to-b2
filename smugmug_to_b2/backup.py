#
# File: backup
#

"""
Syncs the contents of SmugMug to a B2 bucket.
"""

import hashlib

from .util import ordered_zip


def hash_metadata(caption, date, file_name, keywords, title):
    string_to_hash = '|'.join([caption, date, file_name, keywords, title])
    return hashlib.md5(string_to_hash.encode('utf-8')).hexdigest()[:8]


class SmugMugImage:
    def __init__(self, parent_prefix, image):
        self.image = image
        self.archived_md5 = image.archived_md5
        self.archived_url = image.archived_uri
        self.caption = image.caption
        self.date = image.date
        self.file_name= image.file_name
        self.keywords = image.keywords
        self.title = image.title
        parts = self.file_name.split('.')
        meta_hash = hash_metadata(self.caption, self.date, self.file_name, self.keywords, self.title)
        self.b2_path = parent_prefix + '.'.join(parts[:-1]) + '.' + meta_hash + '.' + parts[-1]

    def __repr__(self):
        return 'SM:' + self.b2_path

    def __str__(self):
        return repr(self)

    @property
    def archived_bytes(self):
        return self.image.archived_bytes


def all_smugmug_images(node, is_root=True, parent_prefix=''):
    """
    Yields all of the SmugMugImages stored in SmugMug
    :param node:
    :param is_root:
    :param parent_prefix:
    :return:
    """
    # Build the file name prefix to use for children
    if is_root:
        my_prefix = ''
    else:
        my_prefix = parent_prefix + node.name + '/'

    # We expect nodes to never have both children and an album.
    # They might have neither
    has_children = node.has_children
    has_album = node.has_album
    assert not (has_children and has_album)

    # Yield all of the images in all children
    if has_children:
        children = sorted(node.children, key=(lambda c: c.name + '/'))
        for child in children:
            for image in all_smugmug_images(child, False, my_prefix):
                yield image

    # Yield all of the images in an album:
    if has_album:
        images = [
            SmugMugImage(my_prefix, image)
            for image in node.album.images
        ]
        images.sort(key=(lambda i: i.b2_path))
        for image in images:
            yield image

class B2Image:
    def __init__(self, b2_path):
        self.b2_path = b2_path

    def __repr__(self):
        return 'B2:' + self.b2_path

    def __str__(self):
        return repr(self)


def all_b2_images(b2_bucket):
    for file_version_info, _ in b2_bucket.ls('', recursive=True):
        yield B2Image(file_version_info.file_name)


def backup(top_node, bucket):
    for a, b in ordered_zip(all_smugmug_images(top_node), all_b2_images(bucket), key=lambda x: x.b2_path):
        if a is None:
            print('HIDE    ', b.b2_path)
            bucket.hide_file(b.b2_path)
        if b is None:
            print('DOWNLOAD', a.b2_path)
            image_bytes = a.archived_bytes
            print('UPLOAD  ', a.b2_path)
            file_infos = dict(
                caption=a.caption,
                date=a.date,
                file_name=a.file_name,
                keywords=a.keywords,
                title=a.title
            )
            bucket.upload_bytes(
                data_bytes=image_bytes,
                file_name=a.b2_path,
                file_infos=file_infos
            )
