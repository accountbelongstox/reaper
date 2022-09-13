from kernel.base.base import *
from pymongo import MongoClient
import redis
import json
import os
import pickle
import operator
import sqlite3
from lxml import etree
import requests
import sqlite3

class DbCommon(BaseClass):
    __mongodb = None
    __redis = None
    __db_list = []
    __db_name = "base_py_mongodb"
    __db = None
    __db_prefix = "pr_"
    __sqlite3 = None

    # 自动创建数据库
    def main(self, args):
        if self.__sqlite3 != None:
            return self.__sqlite3
        if self.__sqlite3 == None:
            args="module_name.db"
            con = sqlite3.connect(args)
            self.__sqlite3 = con
        return self.__sqlite3



    def __init__(self,args):
        pass


    def connect(self):
        if self.__db != None:
            return self.__db
        if self.__mongodb == None:
            self.__mongodb = MongoClient('mongodb://localhost:27017/')
        self.__db = self.__mongodb[self.__db_name]
        return self.__db

    def connect_redis(self):
        if self.__redis == None:
            #self.__redis = redis.StrictRedis(host='localhost', port=6379, db=0)
            pool = redis.ConnectionPool(host='localhost', port=6379, db=0)
            self.__redis = redis.Redis(connection_pool=pool)
        return self.__redis


    def serialization(self,obj,file_path=None,override=False):
        print(f"serialization {file_path}")
        if not ( os.path.exists(file_path) and os.path.isfile(file_path) ):
            file_path = self.get_serialization_default_dir(file_path)
        if os.path.exists(file_path) and os.path.isfile(file_path) and override == False:
            old_obj = self.unserialization(file_path)
            if type(old_obj) == dict and type(obj) == dict:
                for k,v in obj.items():
                    old_obj[k] = v
            elif type(old_obj) == list and type(obj) == list:
                for new_data_item in obj:
                    exist_in_list = False
                    for old_item in old_obj:
                        exist_of_item = operator.eq(new_data_item, old_item)
                        if exist_of_item == True:
                            exist_in_list = exist_of_item
                            break
                    if not exist_in_list:
                        print(f"serialization add list as {new_data_item} in {file_path}")
                        old_obj.append(new_data_item)
            else:
                print(f"serialization Not supported data type: {type(obj)}")
                old_obj = obj
            obj = old_obj
        print(f"serialization data to {file_path}")
        file = open(file_path,'wb+')
        pickle.dump(obj,file,pickle.HIGHEST_PROTOCOL)

    def unserialization(self,file_path=None):
        print(f"unserialization data from {file_path}")
        if not ( os.path.exists(file_path) and os.path.isfile(file_path) ):
            file_path = self.get_serialization_default_dir(file_path)
        if os.path.exists(file_path) and os.path.isfile(file_path):
            file = open(file_path,'rb')
            try:
                obj = pickle.load(file)
                return obj
            except:
                return None
        else:
            return None

    def get_serialization_default_dir(self,file_path=None):
        if file_path == None:
            file_path = "public_data_serialization.config"
        core_data_dir = self.config_common.get_config("config",f"data_dir")
        cwd = self.getcwd()
        file_path= os.path.join(cwd,f"{core_data_dir}/{file_path}")
        return file_path

    def set_redis(self,dicts):
        redisdb = self.connect_redis()
        if type(dicts) != list:
            dicts = [dicts]
        for dic_itme in dicts:
            for k,v in dic_itme.items():

                if type(v) == list:
                    if len(v) > 0 : redisdb.lpush(k, *v)
                elif type(v) == set:
                    if len(v) > 0 :redisdb.sadd(k, *v)
                else:
                    if k.startswith('list'):
                        if len(v) > 0 :redisdb.lpush(k, v)
                    elif k.startswith('set'):
                        if len(v) > 0 :redisdb.sadd(k, v)
                    else:
                        redisdb.set(k,v)

    def remove_redis(self,key):
        redisdb = self.connect_redis()
        redisdb.delete(key)

    def get_redis_list(self,key,condition=[0,-1]):
        redisdb = self.connect_redis()
        datas = redisdb.lrange(key,*condition)
        if datas != None:
            datas = [t.decode("utf-8") for t in datas]
        return datas

    def get_redis_set(self,key):
        redisdb = self.connect_redis()
        datas = redisdb.smembers(key)
        return datas


    def get_redis(self,key,condition=[0,-1]):
        if key.startswith('list'):
            datas = self.get_redis_list(key,condition)
        elif key.startswith('set'):
            datas = self.get_redis_set(key)
        else:
            redisdb = self.connect_redis()
            datas = redisdb.get(key)
            if datas !=None:
                datas = json.loads(datas)
        return datas

    def save_data_to(self,collection_name,data):
        print("save_data_to",type(data))
        collection = self.create_collection(collection_name)
        if type(data) == dict:
            x = collection.insert_one(data)
            print(f" save_data_toinsert {len(x.inserted_id)} item")
        elif type(data) == list and len(list) > 0:
            x = collection.insert_many(data)
            print(f" save_data_toinsert {len(x.inserted_ids)} item")
        else:
            print("save_data_to => not support format")

    def read_data_to(self,collection_name,condition):

        collection = self.create_collection(collection_name)

        if "limit" in condition:
            new_con = {}
            for k,v in condition.items():
                if k != "limit":
                    new_con[k] = v
            result = collection.find(new_con).limit(condition["limit"])
        else:
            result = collection.find(condition)
        datas = []
        for data in result:
            datas.append(data)
        return datas

    def get_prefix_dbname(self,dbname):
        return f"{self.__db_prefix}{dbname}"

    def create_collection(self,dbname):
        self.connect()
        dbname = self.get_prefix_dbname(dbname)
        return self.__db[dbname]



    # 保存数据到到sqlite3
    def save_data_to_sqlite(self,tabname=None,data={}):
        if tabname is None:
            tabname = "default1"
        con = self.__sqlite3
        print('successfu lconnection')
        cur = con.cursor()
        keys=data.keys()
        values=data.values()
        # print(cur.execute(".tables").fetchall())
        if tabname not in cur.execute("select name from sqlite_master where type='table' order by name"):
            query_create_table = [f"{x} text," for x in keys]
            query_create_table = tuple(query_create_table)
            print(query_create_table)
            query = f"""CREATE TABLE {tabname}{query_create_table} """
            # query = query % query_create_table
            cur.execute(query)
        else:
            cur.execute(f"use {tabname}")

        query_into_key = '("'
        query_into_key += '","'.join(keys)
        query_into_key1 = query_into_key + '")'

        print(query_into_key1)
        query_into_value = '("'
        query_into_value += '","'.join(values)
        query_into_value1 = query_into_value + '")'
        print(query_into_value1)
        query = f'''INSERT INTO {tabname} VALUES {query_into_key1},{query_into_value1}'''
        result = cur.execute(query)
        print('successfu insert into')
        con.commit()
        con.close()
        return result


    # 数据库获取数据
    def get_data_from_sqlite(self,tabname=None, conditions= {}):
        # TODO condition = 数字
        # TODO condition = {“limit”：100}，{“name”：100}

        if tabname is None:
            tabname = "default1"
        con = self.__sqlite3
        print('successfu lconnection')
        cur = con.cursor()
        # cur.execute("SELECT * FROM default1")
        print('查询数据：', cur.execute(f'SELECT * FROM {tabname}').fetchall())
        print('successfu select')
        if type(conditions) is int:
            where = f"limit:{conditions}"
            print(where)
        if type(conditions) is dict:
            for key, value in conditions.items():
                where1=key
                where2=value
                print('"{}"'.format(where1)+':'+where2)

