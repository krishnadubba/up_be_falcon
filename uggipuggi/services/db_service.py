from __future__ import absolute_import
import os 
import builtins
from mongoengine import connection

from conf import get_config
      

def get_mongodb_connection():
    env = os.environ.get('UGGIPUGGI_BACKEND_ENV', 'docker_compose')
    config = get_config(env)
    
    # get all config values about DB
    db_config = config['mongodb']  # map
    
    db_name = db_config.get('name')
    
    attr_map = {'host': 'str', 'port': 'int', 'username': 'str', 'password': 'str'}
    
    kwargs = {}
    for key, typ in attr_map.items():
        typecast_fn = getattr(builtins, typ)
        # cast the value from db_config accordingly if key-value pair exists
        kwargs[key] = typecast_fn(db_config.get(key)) if db_config.get(key) else None
    
    #kwargs['alias'] = 'default_celery'
    #connection.disconnect('mongo_celery')  # disconnect previous default connection if any
    connection.disconnect('default')  # disconnect previous default connection if any
    return connection.connect(db_name, **kwargs)