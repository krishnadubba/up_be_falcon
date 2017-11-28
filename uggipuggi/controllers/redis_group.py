# -*- coding: utf-8 -*-

from __future__ import absolute_import
import time
import falcon
import logging
import requests
from bson import json_util, ObjectId
from google.cloud import storage as gc_storage

from uggipuggi.libs.error import HTTPBadRequest
from uggipuggi.constants import GROUP, GROUP_MEMBERS, USER_GROUPS, GCS_GROUP_BUCKET, \
                                GAE_IMG_SERVER
from uggipuggi.controllers.hooks import deserialize, serialize, supply_redis_conn
from uggipuggi.messaging.group_kafka_producers import group_kafka_item_put_producer, \
                   group_kafka_item_post_producer, group_kafka_item_delete_producer, \
          group_kafka_collection_post_producer, group_kafka_collection_delete_producer 


logger = logging.getLogger(__name__)

@falcon.before(supply_redis_conn)
@falcon.after(serialize)
class Collection(object):
    def __init__(self):
        self.kafka_topic_name = 'group_collection'
        self.gcs_client = gc_storage.Client()            
        self.gcs_bucket = self.gcs_client.bucket(GCS_GROUP_BUCKET)

        if not self.gcs_bucket.exists():
            logger.debug("GCS Bucket %s does not exist, creating one" %GCS_GROUP_BUCKET)
            self.gcs_bucket.create()

    @falcon.before(deserialize)
    def on_get(self, req, resp):
        # Get all groups of user
        req.kafka_topic_name = '_'.join([self.kafka_topic_name, req.method.lower()])
        user_groups_id = USER_GROUPS + req.user_id
        resp.body['user_groups'] = list(req.redis_conn.smembers(user_groups_id))
        resp.status = falcon.HTTP_FOUND
        
    #@falcon.before(deserialize_create)
    @falcon.before(deserialize)
    @falcon.after(group_kafka_collection_post_producer)
    def on_post(self, req, resp):
        req.kafka_topic_name = '_'.join([self.kafka_topic_name, req.method.lower()])
        # Get new group ID
        group_id = str(req.redis_conn.incr(GROUP))
        logger.debug('New group id created: %s' %group_id)
        group_id_name = GROUP + group_id
        group_members_id_name = GROUP_MEMBERS + group_id
        
        img_data = req.get_param('group_pic')
        res = requests.post(GAE_IMG_SERVER + '/img_post', 
                            files={'img': img_data.file}, 
                            data={'gcs_bucket': GCS_GROUP_BUCKET,
                                  'file_name': group_id_name + '_' + 'group_pic.jpg',
                                  'file_type': img_data.type
                                 })
        logger.debug(res.status_code)
        logger.debug(res.text)
        img_url = ''
        if repr(res.status_code) == falcon.HTTP_OK.split(' ')[0]:
            img_url = res.text
            logger.debug("Group_pic public url:")
            logger.debug(img_url)
        else:                    
            logger.error("Group_pic upload to cloud storage failed!")
            raise HTTPBadRequest(title='Group_pic upload failed', 
                                 description='Group_pic upload to cloud storage failed!')        

        pipeline = req.redis_conn.pipeline(True)        
        pipeline.hmset(group_id_name, {
            'group_name'  : req.get_param('group_name'),
            'group_pic'   : img_url,
            'created_time': time.time(),
            'admin'       : req.user_id
        })
                
        # Get group members list
        group_members_list = req.get_param_as_list('member_id')
        # Add admin (current user) to group_members        
        group_members_list.append(req.user_id)
        # Add members to the groups' members list
        pipeline.sadd(group_members_id_name, *group_members_list)
        
        # Add this group to set of groups a user belongs to
        # Note that now group_members_list include admin
        for member_id in group_members_list:
            user_groups_id = USER_GROUPS + member_id
            pipeline.sadd(user_groups_id, group_id_name)        
        
        pipeline.execute()
        resp.body = {"group_id": group_id}
        resp.status = falcon.HTTP_CREATED
        
    @falcon.before(deserialize)
    @falcon.after(group_kafka_collection_delete_producer)
    def on_delete(self, req, resp):
        req.kafka_topic_name = '_'.join([self.kafka_topic_name, req.method.lower()])
        logger.debug("Deleting group data in database ...")
        group_id_name = GROUP + req.params['query']['group_id']
        admin = req.redis_conn.hget(group_id_name, 'admin')
        if admin != req.user_id:
            logger.debug("User is not the admin: %s , %s" %(admin, req.user_id))
            resp.status = falcon.HTTP_UNAUTHORIZED
            return
        else:
            group_members_id_name = GROUP_MEMBERS + group_id
            pipeline = req.redis_conn.pipeline(True)
            group_keys = req.redis_conn.hgetall(group_id_name).keys()
            req.redis_conn.hdel(group_id_name, *group_keys)
            group_members = req.redis_conn.smembers(group_members_id_name)
            
            # Remove this group from all members group list
            for member in group_members:
                user_groups_id = USER_GROUPS + member
                pipeline.srem(user_groups_id, group_id_name)
            
            # Now remove all group members
            pipeline.srem(group_members_id_name, *group_members)
            pipeline.execute()
            logger.debug("Deleted group data in database")
            resp.status = falcon.HTTP_OK        


@falcon.before(supply_redis_conn)
@falcon.after(serialize)
class Item(object):
    def __init__(self):
        self.kafka_topic_name = 'group_item'
        self.gcs_client = gc_storage.Client()            
        self.gcs_bucket = self.gcs_client.bucket(GCS_GROUP_BUCKET)

        if not self.gcs_bucket.exists():
            logger.debug("GCS Bucket %s does not exist, creating one" %GCS_GROUP_BUCKET)
            self.gcs_bucket.create()

    @falcon.before(deserialize)
    #@falcon.after(group_kafka_item_get_producer)
    def on_get(self, req, resp, id):
        req.kafka_topic_name = '_'.join([self.kafka_topic_name, req.method.lower()])
        group_id_name = GROUP + id
        group_members_id_name = GROUP_MEMBERS + id
        resp.body = req.redis_conn.hgetall(group_id_name)
        # Should we also get members?                
        # This is a get request, so body in req.params
        if 'members' in req.params['query']:
            resp.body['members'] = list(req.redis_conn.smembers(group_members_id_name))
                
        resp.status = falcon.HTTP_FOUND
        
    @falcon.before(deserialize)
    @falcon.after(group_kafka_item_delete_producer)    
    def on_delete(self, req, resp, id):
        # Delete a member
        req.kafka_topic_name = '_'.join([self.kafka_topic_name, req.method.lower()])
        logger.debug("Deleting member from group data in database ...")
        group_id_name = GROUP + id
        admin = req.redis_conn.hget(group_id_name, 'admin')
        if admin != req.user_id:
            logger.debug("User is not the admin: %s , %s" %(admin, req.user_id))
            resp.status = falcon.HTTP_UNAUTHORIZED
            return
        else:
            group_members_id_name = GROUP_MEMBERS + group_id            
            pipeline = req.redis_conn.pipeline(True)
            pipeline.srem(group_members_id_name, *req.params['query']['member_id'])
            # Remove this group from this member's group list
            for group_member in req.params['query']['member_id']:
                user_groups_id = USER_GROUPS + group_member
                pipeline.srem(user_groups_id, group_id_name)
            pipeline.execute()
            logger.debug("Deleted member from group data in database")
            resp.status = falcon.HTTP_OK

    #@falcon.before(deserialize_update)
    @falcon.before(deserialize)
    @falcon.after(group_kafka_item_put_producer)
    def on_put(self, req, resp, id):        
        req.kafka_topic_name = '_'.join([self.kafka_topic_name, req.method.lower()])
        logger.debug("Finding group in database ... %s" %repr(id))
        group_id_name = GROUP + id
        admin = req.redis_conn.hget(group_id_name, 'admin')
        if admin != req.user_id:
            logger.debug("User is not the admin: %s , %s" %(admin, req.user_id))
            resp.status = falcon.HTTP_UNAUTHORIZED
            return
        else:
            pipeline = req.redis_conn.pipeline(True)
            if 'multipart/form-data' in req.content_type:
                img_data = req.get_param('group_pic')
                res = requests.post(GAE_IMG_SERVER + '/img_post', 
                                    files={'img': img_data.file}, 
                                    data={'gcs_bucket': GCS_GROUP_BUCKET,
                                          'file_name': group_id_name + '_' + 'group_pic.jpg',
                                          'file_type': img_data.type
                                         })
                logger.debug(res.status_code)
                logger.debug(res.text)
                if repr(res.status_code) == falcon.HTTP_OK.split(' ')[0]:
                    img_url = res.text
                    logger.debug("Group_pic public url:")
                    logger.debug(img_url)
                    pipeline.hset(group_id_name, 'group_pic', img_url)
                else:                    
                    logger.error("Group_pic upload to cloud storage failed!")
                    raise HTTPBadRequest(title='Group_pic upload failed', 
                                         description='Group_pic upload to cloud storage failed!')
            else:    
                for key in req.params['body']:
                    pipeline.hset(group_id_name, key, req.params['body'][key])
            pipeline.execute()
        logger.debug("Updated group data in database")
        resp.status = falcon.HTTP_OK

    @falcon.before(deserialize)
    @falcon.after(group_kafka_item_post_producer)
    def on_post(self, req, resp, id):
        # Add a member to group
        req.kafka_topic_name = '_'.join([self.kafka_topic_name, req.method.lower()])
        logger.debug("Adding member to group in database ... %s" %repr(id))
        group_id_name = GROUP + id
        admin = req.redis_conn.hget(group_id_name, 'admin')
        if admin != req.user_id:
            logger.debug("User is not the admin: %s , %s" %(admin, req.user_id))
            resp.status = falcon.HTTP_UNAUTHORIZED
            return
        else:
            group_members_id_name = GROUP_MEMBERS + id
            logger.debug("Adding members to the group: ")
            pipeline = req.redis_conn.pipeline(True)
            pipeline.sadd(group_members_id_name, *req.params['body']['member_id'])
            for member in req.params['body']['member_id']:
                user_groups_id = USER_GROUPS + member
                pipeline.srem(user_groups_id, group_id_name)                            
            pipeline.execute()
        logger.debug("Added members to group in database")
        resp.status = falcon.HTTP_OK