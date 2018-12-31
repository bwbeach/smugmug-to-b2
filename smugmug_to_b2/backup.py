#
# File: backup
#

"""
Syncs the contents of SmugMug to a B2 bucket.
"""

import hashlib


def hash_metadata(caption, date, file_name, keywords, title):
    string_to_hash = '|'.join([caption, date, file_name, keywords, title])
    return hashlib.md5(string_to_hash.encode('utf-8')).hexdigest()[:8]


class SmugMugImage:
    def __init__(self, parent_prefix, image):
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
        return self.b2_path

    def __str__(self):
        return self.b2_path


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
        children = sorted(node.children, key=(lambda c: c.name))
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
