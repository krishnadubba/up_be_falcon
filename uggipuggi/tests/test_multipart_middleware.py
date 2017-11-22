from io import open
import os, sys

import falcon
from falcon_multipart.middleware import MultipartMiddleware
import pytest
import six
from time import gmtime, strftime
from PIL import Image
from io import BytesIO, StringIO
from google.cloud import storage as gc_storage

sys.path.append(os.path.dirname(os.path.dirname(sys.path[0])))

application = falcon.API(middleware=MultipartMiddleware())
GCS_USER_BUCKET = 'gcs_user_temp_bucket'

@pytest.fixture
def app():
    return application


#def test_parse_form_as_params(client):

    #class Resource:

        #def on_post(self, req, resp, **kwargs):
            #assert req.get_param('simple') == 'ok'
            #assert req.get_param('another_simple') == 'okok'
            #assert req.get_param('afile').file.read() == b'filecontent'
            #assert req.get_param('afile').filename == 'afile.txt'
            #resp.body = 'parsed'
            #resp.content_type = 'text/plain'

    #application.add_route('/route', Resource())

    #resp = client.post('/route', data={'simple': 'ok', 'another_simple': 'okok'},
                       #files={'afile': ('filecontent', 'afile.txt')})
    #assert resp.status == falcon.HTTP_OK
    #assert resp.body == 'parsed'


def test_with_binary_file(client):
    here = os.path.dirname(os.path.realpath(__file__))
    filepath = os.path.join(os.path.dirname(os.path.dirname(here)), 'test_data', 'image.jpg')
    filepath2 = os.path.join(os.path.dirname(os.path.dirname(here)), 'test_data', 'image2.jpg')
    image = open(filepath, 'rb')
    image2 = open(filepath2, 'rb')

    class Resource:

        def on_post(self, req, resp, **kwargs):
            client = gc_storage.Client()            
            size = (64, 64)
            resp.data = req.get_param('afile').file.read()
            pil_image = Image.open(BytesIO(resp.data))
            pil_image.thumbnail(size)
            
            byte_io = BytesIO()            
            pil_image.save(byte_io, format='JPEG')            
            byte_str = byte_io.getvalue()
            
            bucket = client.bucket(GCS_USER_BUCKET)
            if not bucket.exists():
                print ("GCS Bucket %s does not exist, creating one" %GCS_USER_BUCKET)
                bucket.create()
                
            print ('==================================') 
            print (strftime("%a, %d %b %Y %H:%M:%S +0000", gmtime()))
            
            for i in range(10):
                display_pic_gcs_filename = 'display_pic_%d.jpg'%i
                blob = bucket.blob(display_pic_gcs_filename)
                blob.upload_from_string(resp.data, content_type='image/jpeg')
                blob.make_public()            
    
                thumb_display_pic_gcs_filename = 'display_pic_thumb_%d.jpg'%i
                thumb_blob = bucket.blob(thumb_display_pic_gcs_filename)
                thumb_blob.upload_from_string(byte_str, content_type='image/jpeg')
                
                thumb_blob.make_public()
            print (strftime("%a, %d %b %Y %H:%M:%S +0000", gmtime()))
            print ('==================================')    
            
            thumb_url = thumb_blob.public_url
            if isinstance(thumb_url, six.binary_type):
                thumb_url = thumb_url.decode('utf-8')

            print (thumb_url)
            assert req.get_param('afile').filename==os.path.join(os.path.dirname(os.path.dirname(here)), 'test_data', 'image.jpg')
            assert req.get_param('afile').type=='image/jpeg'
            resp.content_type = 'image/jpg'

    application.add_route('/route', Resource())

    resp = client.post('/route', data={'simple': 'ok'},
                       files={'afile': image, 'bfile': image2})
    assert resp.status == falcon.HTTP_OK
    image.seek(0)
    assert resp.body == image.read()


#def test_parse_multiple_values(client):

    #class Resource:

        #def on_post(self, req, resp, **kwargs):
            #assert req.get_param_as_list('multi') == ['1', '2']
            #resp.body = 'parsed'
            #resp.content_type = 'text/plain'

    #application.add_route('/route', Resource())

    #resp = client.post('/route', data={'multi': ['1', '2']},
                       #files={'afile': ('filecontent', 'afile.txt')})
    #assert resp.status == falcon.HTTP_OK
    #assert resp.body == 'parsed'


#def test_parse_non_ascii_filename_in_headers(client):

    #class Resource:

        #def on_post(self, req, resp, **kwargs):
            #assert req.get_param('afile').file.read() == b'name,code\nnom,2\n'
            #assert req.get_param('afile').filename == 'Na%C3%AFve%20file.txt'
            #resp.body = 'parsed'
            #resp.content_type = 'text/plain'

    #application.add_route('/route', Resource())

    ## Simulate browser sending non ascii filename.
    #body = ('--boundary\r\nContent-Disposition: '
            #'form-data; name="afile"; filename*=utf-8\'\'Na%C3%AFve%20file.txt'
            #'\r\nContent-Type: text/csv\r\n\r\nname,code\nnom,2\n\r\n'
            #'--boundary--\r\n')
    #headers = {'Content-Type': 'multipart/form-data; boundary=boundary'}
    #resp = client.post('/route', body=body, headers=headers)
    #assert resp.status == falcon.HTTP_OK
    #assert resp.body == 'parsed'
