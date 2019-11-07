#!/usr/bin/env python
#-*- coding: utf-8 -*-
"""
* @ Scout for Python
##############################################################################
# Author: YWJT / ZhiQiang Koo                                                #
# Modify: 2019-11-06                                                         #
##############################################################################
# This program is distributed under the "Artistic License" Agreement         #
# The LICENSE file is located in the same directory as this program. Please  #
# read the LICENSE file before you make copies or distribute this program    #
##############################################################################
"""


import sys
sys.path.append("..")
import os, sys
import pprint
import pymongo
from pymongo import MongoClient

 
class CacheServer(object):
    """
    cacheUtil
    """
 
    def __init__(self):
        """
        初始化
        """
        self._host = 'localhost'
        self._port = '6666'
        self._database = 'Scout'
        pass
 
    def create_or_connect_cache(self):
        """
        返回数据库实例、同步
        :return:
        """
        try:
            uri = "mongodb://{0}:{1}/?authSource={2}".format(self._host, self._port, self._database)
            client = MongoClient(uri)
            return client[self._database]
        except Exception as e:
            print(e)
            raise


    def create_index(self, collection, key, expire_time):
        """
        设定文档的ttl失效时间
        :param collection:
        :param key:
        :param expire_time:
        """
        return collection.create_index([(key, pymongo.ASCENDING)], expireAfterSeconds=expire_time)

 
    def get_collection(self, dbmobj, collection_name):
        """
        判断集合是否已存在
        返回输入的名称对应的集合
        :param collection_name:
        :return:
        """
        collist = dbmobj.list_collection_names()
        if collection_name in collist:
            try:
                return collection_name
            except Exception as e:
                raise
        else:
            return None

    def find_aggregate(self, collection, pipeline=[]):
        """
        mongodb的聚合类似于管道操作，通过多个构件来组成一个管道：filter, project, group, sort, limit, skip
        """
        return collection.aggregate(pipeline)
 
    def find_one(self, collection, **kwargs):
        """
        按条件查询单个doc,如果传入集合为空将返回默认数据
        :param collection:
        :param kwargs:
        :return:
        """
        result_obj = collection.find_one(kwargs)
        return result_obj
 
    def find_all(self, collection, limit=None, skip=0):
        """
        查询传入条件集合和全部数据
        :return:
        """
        cursor = collection.find()
        cursor.skip(skip).limit(limit)
        return cursor
 
    def find_conditions(self, collection, limit=0, **kwargs):
        """
        按条件查询，并做返回条数限制
        :param collection:
        :param limit:
        :param kwargs:
        :return:
        """
        # return collection.find(kwargs).limit(limit)
        if limit == 0:
            # cursor = collection.find(kwargs).sort('i').skip(0)
            cursor = collection.find(kwargs).skip(0)
        else:
            cursor = collection.find(kwargs).sort('i').limit(limit).skip(0)
        return cursor
 
    def count(self, collection, kwargs={}):
        """
        返回查询的条数
        :param collection:
        :param kwargs:
        :return:
        """
        n = collection.count_documents(kwargs)
        # n = db.test_collection.count_documents({'i': {'$gt': 1000}})
        print('%s documents in collection' % n)
        return n
 
    def replace_id(self, collection, condition={}, new_doc={}):
        """
        通过ID进行更新，没有记录会插入
        :param collection:
        :param condition:
        :param new_doc:
        :return:
        """
        _id = condition['_id']
        old_document = collection.find_one(condition)
        if old_document:
            collection.replace_one({'_id': _id}, new_doc)
            return 0
        else:
            collection.insert_one(new_doc)
            return 1
 
    def update(self, collection, condition={}, new_part={}):
        """
        进行替换部分内容
        :param collection: 
        :param condition: 
        :param new_part: 
        :return: 
        """
        result = collection.update_one(condition, {'$set': new_part})
        print('updated %s document' % result.modified_count)
        new_document = collection.find_one(condition)
        print('document is now %s' % pprint.pformat(new_document))
 
    def replace(self, collection, condition={}, new_doc={}):
        """
        分步骤通过一定条件进行替换部分内容
        :param collection:
        :param condition:
        :param new_doc:
        :return:
        """
        old_document = collection.find_one(condition)
        _id = old_document['_id']
        result = collection.replace_one({'_id': _id}, new_doc)
        print('replaced %s document' % result.modified_count)
        new_document = collection.find_one({'_id': _id})
        print('document is now %s' % pprint.pformat(new_document))
        
    def update_many(self, collection, condition={}, new_part={}):
        """
        批量更新
        :param collection:
        :param condition:
        :param new_part:
        :return:
        """
        # result4 = collection.update_many({'i': {'$gt': 100}}, {'$set': {'key': 'value'}})
        result = collection.update_many(condition, {'$set': new_part})
        print('updated %s document' % result.modified_count)
 
    def insert_one(self, collection, new_doc={}):
        """
        单条插入
        :param collection:
        :param new_doc:
        :return:
        """
        try:
            result = collection.insert_one(new_doc)
            #print('inserted_id %s' % repr(result.inserted_id))
            return result
        except Exception as e:
            return str(e)
 
    def insert_many(self, collection, new_doc=[]):
        """
        批量添加
        :param collection:
        :param need_insert_dict_many:
        :return:
        """
        try:
            result = collection.insert_many(new_doc)
            #print('inserted %d docs' % (len(result.inserted_ids),))
            return 'ok'
        except Exception as e:
            return str(e)
 
    def delete_many(self, collection, condition={}):
        """
        批量删除
        :param collection:
        :param condition:
        :return:
        """
        # print('%s documents before calling delete_many()' % n)
        #n = collection.count_documents({})
        #print('%s documents before calling delete_many()' % n)
        # result4 = collection.delete_many({'i': {'$gte': 1000}})
        result = collection.delete_many(condition)
        #n = collection.count_documents({})
        #print('%s documents after calling delete_many()' % n)
        return result

