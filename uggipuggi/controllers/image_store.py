import io
import os
import re
import uuid
import falcon
import logging
import mimetypes

from uggipuggi.constants import IMG_STORE_PATH

logger = logging.getLogger(__name__)

mimetypes.init()
ALLOWED_IMAGE_TYPES = (
    'image/jpeg',
    'image/png',
)

def validate_image_type(req, resp, resource, params):
    if req.content_type not in ALLOWED_IMAGE_TYPES:
        msg = 'Image type not allowed. Must be PNG or JPEG'
        raise falcon.HTTPBadRequest('Bad request', msg)
    
class Item(object):

    def __init__(self):
        self._image_store = ImageStore(IMG_STORE_PATH)

    def on_get(self, req, resp, id):
        resp.content_type = mimetypes.guess_type(id)[0]
        resp.stream, resp.stream_len = self._image_store.open(id)


class ImageStore(object):

    def __init__(self, storage_path, fopen=io.open):
        self._storage_path = storage_path
        self._fopen = fopen

    def save(self, image_stream, image_name, image_content_type):
        ext = mimetypes.guess_extension(image_content_type)
        if ext == 'jpe':
            ext = 'jpg'
        image_name = '{filename}{ext}'.format(filename=image_name, ext=ext)
        image_path = os.path.join(self._storage_path, image_name)

        with self._fopen(image_path, 'wb') as image_file:
            chunk = image_stream.read()
            image_file.write(chunk)

        return image_path

    def open(self, name):
        image_path = os.path.join(self._storage_path, name)
        logger.debug("Requested image file from file store: %s" %image_path)
        stream = self._fopen(image_path, 'rb')
        stream_len = os.path.getsize(image_path)

        return stream, stream_len