from io import open
import os

import falcon
from falcon_multipart.middleware import MultipartMiddleware
import pytest


application = falcon.API(middleware=MultipartMiddleware())


@pytest.fixture
def app():
    return application


def test_parse_form_as_params(client):

    class Resource:

        def on_post(self, req, resp, **kwargs):
            assert req.get_param('simple') == 'ok'
            assert req.get_param('another_simple') == 'okok'
            assert req.get_param('afile').file.read() == b'filecontent'
            assert req.get_param('afile').filename == 'afile.txt'
            resp.body = 'parsed'
            resp.content_type = 'text/plain'

    application.add_route('/route', Resource())

    resp = client.post('/route', data={'simple': 'ok', 'another_simple': 'okok'},
                       files={'afile': ('filecontent', 'afile.txt')})
    assert resp.status == falcon.HTTP_OK
    assert resp.body == 'parsed'


def test_with_binary_file(client):
    here = os.path.dirname(os.path.realpath(__file__))
    filepath = os.path.join(os.path.dirname(os.path.dirname(here)), 'test_data', 'image.jpg')
    filepath2 = os.path.join(os.path.dirname(os.path.dirname(here)), 'test_data', 'image2.jpg')
    image = open(filepath, 'rb')
    image2 = open(filepath2, 'rb')

    class Resource:

        def on_post(self, req, resp, **kwargs):
            resp.data = req.get_param('afile').file.read()
            assert req.get_param('afile').filename==os.path.join(os.path.dirname(os.path.dirname(here)), 'test_data', 'image.jpg')
            assert req.get_param('afile').type=='image/jpeg'
            resp.content_type = 'image/jpg'

    application.add_route('/route', Resource())

    resp = client.post('/route', data={'simple': 'ok'},
                       files={'afile': image, 'bfile': image2})
    assert resp.status == falcon.HTTP_OK
    image.seek(0)
    assert resp.body == image.read()


def test_parse_multiple_values(client):

    class Resource:

        def on_post(self, req, resp, **kwargs):
            assert req.get_param_as_list('multi') == ['1', '2']
            resp.body = 'parsed'
            resp.content_type = 'text/plain'

    application.add_route('/route', Resource())

    resp = client.post('/route', data={'multi': ['1', '2']},
                       files={'afile': ('filecontent', 'afile.txt')})
    assert resp.status == falcon.HTTP_OK
    assert resp.body == 'parsed'


def test_parse_non_ascii_filename_in_headers(client):

    class Resource:

        def on_post(self, req, resp, **kwargs):
            assert req.get_param('afile').file.read() == b'name,code\nnom,2\n'
            assert req.get_param('afile').filename == 'Na%C3%AFve%20file.txt'
            resp.body = 'parsed'
            resp.content_type = 'text/plain'

    application.add_route('/route', Resource())

    # Simulate browser sending non ascii filename.
    body = ('--boundary\r\nContent-Disposition: '
            'form-data; name="afile"; filename*=utf-8\'\'Na%C3%AFve%20file.txt'
            '\r\nContent-Type: text/csv\r\n\r\nname,code\nnom,2\n\r\n'
            '--boundary--\r\n')
    headers = {'Content-Type': 'multipart/form-data; boundary=boundary'}
    resp = client.post('/route', body=body, headers=headers)
    assert resp.status == falcon.HTTP_OK
    assert resp.body == 'parsed'
