import os
import falcon
import requests
from uggipuggi.constants import FILE_EXT_MAP

def upload_image_to_gcs(image_path, gae_server, gcs_bucket):
    # Note that we don't check here if the bucket exists or not
    img_stream = open(image_path, 'rb')
    res = requests.post(gae_server, 
                        files={'img': img_stream}, 
                        data={'gcs_bucket': gcs_bucket,
                              'file_name': os.path.basename(image_path), 
                              'file_type': FILE_EXT_MAP[image_path.split('.')[-1]]
                              })
    if repr(res.status_code) == falcon.HTTP_OK.split(' ')[0]:
        return (res.status_code, res.text)
    else:
        return (res.status_code, None)