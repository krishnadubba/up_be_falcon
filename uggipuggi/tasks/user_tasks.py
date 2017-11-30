from celery.utils.log import get_task_logger

from uggipuggi.celery.celery import celery
from uggipuggi.services.user import get_user
from uggipuggi.services.db_service import get_mongodb_connection
from uggipuggi.controllers.hooks import get_redis_conn
from uggipuggi.controllers.utils.gcloud_utils import upload_image_to_gcs
from uggipuggi.constants import USER, GAE_IMG_SERVER, GCS_USER_BUCKET

logger = get_task_logger(__name__)

@celery.task
def user_display_pic_task(user_id, image_path):
    (status_code, img_url) = upload_image_to_gcs(image_path, GAE_IMG_SERVER, GCS_USER_BUCKET)
    mongo_conn = get_mongodb_connection()
    user = get_user('id', user_id)
    user.update(display_pic=img_url)
    
    redis_user_id_name = USER + user_id
    redis_conn = get_redis_conn()
    redis_conn.hmset(redis_user_id_name, {'display_pic': img_url})
