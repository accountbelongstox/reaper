import time

from kernel.base.base import *
from pymongo import MongoClient
import redis
import json
import os
import pickle
import operator
import sqlite3
from lxml import etree
import re
import threading

threadingLock = threading.Lock()


class Db(BaseClass):
    __mongodb = None
    __redis = None
    __db_list = []
    __db_name = None
    __db_type = None
    __db = None
    __db_prefix = "pr_"

    def __init__(self, args):
        pass

    # 自动创建数据库
    def main(self, args):
        database = self.com_config.get_global("database")
        if database != True:
            print("The database is not enabled in the configuration.")
            return
        self.set_data_type()
        database_name = self.create_db_name()
        self.com_util.print_info(f"Modules use database files {database_name} ")
        self.create_default_tab()
        self.create_base_table()
        self.com_util.print_info("The database is initializing.")

    def get_dbfixedname(self, fixed_name):
        databases = self.get_dbconfig()
        tabnames = [db.get('tabname') for db in databases if db.get('fixed_name') == fixed_name]
        tabname = tabnames[-1]
        return tabname

    def get_translation_dictionary(self):
        return "translation_dictionary"

    def get_translation_group(self):
        return "translation_group"

    def get_translation_voices(self):
        return "translation_voices"

    def get_translation_notebook(self):
        return "translation_notebook"

    # def get_translation_voices(self):
    #     return "translation_voices"
    def create_base_table(self, ):
        # 创建翻译基本表
        table_name = self.get_translation_dictionary()
        self.create_table_and_extend(table_name, {
            "word": "VARCHAR(100) UNIQUE",
            "language": "TEXT",
            "translate_bing": "TEXT",
            "last_time": "REAL",
            "read": "INTEGER",
            "word_sort": "VARCHAR(100)",
            "phonetic_us": "VARCHAR(50)",
            "phonetic_us_sort": "VARCHAR(50)",
            "phonetic_uk": "VARCHAR(50)",
            "phonetic_uk_sort": "VARCHAR(50)",
        })
        # 创建翻译组基本表
        table_name = self.get_translation_group()
        self.create_table_and_extend(table_name, {
            "group_n": "TEXT UNIQUE",
            "description": "TEXT",
            "group_token": "CHAR(100)",
            "language": "TEXT",
            "include_words": "TEXT",
            "count": "REAL",
            "link_words": "TEXT",
            "u_group": "TEXT",
            "group_type": "CHAR(100)",
            "last_time": "REAL",
            "read": "INTEGER",
            "word_read": "INTEGER",
            "origin_text": "TEXT",
        })
        # #创建文档语音
        table_name = self.get_translation_voices()
        self.create_table_and_extend(table_name, {
            "group_id": "INTEGER",
            "sentence": "TEXT",
            "voice": "TEXT",
            "link_words": "TEXT",
            "last_time": "REAL",
            "read": "INTEGER",
        })
        # #创建每日生词
        table_name = self.get_translation_notebook()
        self.create_table_and_extend(table_name, {
            "group_id": "INTEGER",
            "user_id": "INTEGER",
            "word_id": "INTEGER",
            "reference_url": "TEXT",
            "last_time": "REAL",
            "read": "INTEGER",
        })

    def get_database_dir(self, dbname=None):
        database_file = self.load_module.get_control_core_dir(f"db")
        if os.path.exists(database_file) != True:
            os.mkdir(database_file)
        if dbname != None:
            database_file = os.path.join(database_file, dbname)
        return database_file

    def get_database_file(self):
        if self.__db_name == None:
            database_name = self.create_db_name()
            database_name = self.get_database_dir(f"{database_name}.db")
            self.__db_name = database_name
        return self.__db_name

    def connect(self):
        database_name = self.get_database_file()
        if self.get_data_type("sqlite"):
            self.__con = sqlite3.connect(database_name, check_same_thread=False)
            self.__db = self.__con.cursor()
        elif self.get_data_type("mongodb"):
            self.__mongodb = MongoClient('mongodb://localhost:27017/')
            self.__db = self.__mongodb[self.__db_name]
        else:
            print("The database type is not supported.")
            return None
        return self.__db

    def set_data_type(self):
        database_type = self.com_config.get_global("database_type")
        database_type = database_type.lower()
        self.__db_type = database_type

    def get_data_type(self, type_compare):
        if self.__db_type == None:
            self.__db_type = self.com_config.get_global("database_type")
            db_type = self.__db_type
        else:
            db_type = self.__db_type
        if db_type.startswith("sqlite"):
            db_type = "sqlite"
        elif db_type.startswith("mongodb"):
            db_type = "mongodb"
        elif db_type.startswith("mysql"):
            db_type = "mysql"
        else:
            db_type = None
        if type_compare != None:
            return db_type == type_compare
        return db_type

    def get_db_name(self):
        return self.__db_name

    def is_db_file(self, db_name=None):
        if db_name == None:
            db_name = self.__db_name
        return os.path.isfile(db_name)

    def create_db_name(self):
        db_name = self.load_module.get_control_name()
        if self.__db_type != None:
            db_name = f"control_{db_name}_{self.__db_type}"
        return db_name

    def connect_redis(self):
        if self.__redis == None:
            # self.__redis = redis.StrictRedis(host='localhost', port=6379, db=0)
            pool = redis.ConnectionPool(host='localhost', port=6379, db=0)
            self.__redis = redis.Redis(connection_pool=pool)
        return self.__redis

    def serialization(self, obj, file_path=None, override=False, notion=True):
        if not (os.path.exists(file_path) and os.path.isfile(file_path)):
            file_path = self.get_serialization_default_dir(file_path)
        if os.path.exists(file_path) and os.path.isfile(file_path) and override == False:
            old_obj = self.unserialization(file_path)
            if type(old_obj) == dict and type(obj) == dict:
                for k, v in obj.items():
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
                        if notion:
                            print(f"serialization add list as {new_data_item} in {file_path}")
                        old_obj.append(new_data_item)
            else:
                if notion:
                    print(f"serialization Not supported data type: {type(obj)}")
                old_obj = obj
            obj = old_obj
        if notion:
            print(f"Serialize object to {file_path}")
        file = open(file_path, 'wb+')
        pickle.dump(obj, file, pickle.HIGHEST_PROTOCOL)

    def unserialization(self, file_path=None):
        print(f"unserialization data from {file_path}")
        if not (os.path.exists(file_path) and os.path.isfile(file_path)):
            file_path = self.get_serialization_default_dir(file_path)
        if os.path.exists(file_path) and os.path.isfile(file_path):
            file = open(file_path, 'rb')
            try:
                obj = pickle.load(file)
                return obj
            except:
                return None
        else:
            return None

    def get_serialization_default_dir(self, file_path=None):
        if file_path == None:
            file_path = "public_data_serialization.config"
        core_data_dir = self.load_module.get_control_dir("core_file/serialization_data")
        file_path = os.path.join(core_data_dir, file_path)
        return file_path

    def set_redis(self, dicts):
        redisdb = self.connect_redis()
        if type(dicts) != list:
            dicts = [dicts]
        for dic_itme in dicts:
            for k, v in dic_itme.items():

                if type(v) == list:
                    if len(v) > 0: redisdb.lpush(k, *v)
                elif type(v) == set:
                    if len(v) > 0: redisdb.sadd(k, *v)
                else:
                    if k.startswith('list'):
                        if len(v) > 0: redisdb.lpush(k, v)
                    elif k.startswith('set'):
                        if len(v) > 0: redisdb.sadd(k, v)
                    else:
                        redisdb.set(k, v)

    def remove_redis(self, key):
        redisdb = self.connect_redis()
        redisdb.delete(key)

    def get_redis_list(self, key, condition=[0, -1]):
        redisdb = self.connect_redis()
        datas = redisdb.lrange(key, *condition)
        if datas != None:
            datas = [t.decode("utf-8") for t in datas]
        return datas

    def get_redis_set(self, key):
        redisdb = self.connect_redis()
        datas = redisdb.smembers(key)
        return datas

    def get_redis(self, key, condition=[0, -1]):
        if key.startswith('list'):
            datas = self.get_redis_list(key, condition)
        elif key.startswith('set'):
            datas = self.get_redis_set(key)
        else:
            redisdb = self.connect_redis()
            datas = redisdb.get(key)
            if datas != None:
                datas = json.loads(datas)
        return datas

    def save_data_to(self, collection_name, data):
        print("save_data_to", type(data))
        collection = self.create_collection(collection_name)
        if type(data) == dict:
            x = collection.insert_one(data)
            print(f" save_data_toinsert {len(x.inserted_id)} item")
        elif type(data) == list and len(list) > 0:
            x = collection.insert_many(data)
            print(f" save_data_toinsert {len(x.inserted_ids)} item")
        else:
            print("save_data_to => not support format")

    def read_data_to(self, collection_name, condition):
        collection = self.create_collection(collection_name)
        if "limit" in condition:
            new_con = {}
            for k, v in condition.items():
                if k != "limit":
                    new_con[k] = v
            result = collection.find(new_con).limit(condition["limit"])
        else:
            result = collection.find(condition)
        datas = []
        for data in result:
            datas.append(data)
        return datas

    def get_prefix_dbname(self, dbname):
        return f"{self.__db_prefix}{dbname}"

    def create_collection(self, dbname):
        self.connect()
        dbname = self.get_prefix_dbname(dbname)
        return self.__db[dbname]

    def create_table_and_extend(self, tabneme, keys=None):
        if self.is_table(tabneme):
            # print(f"The datatable {tabneme} already exists, extend the column")
            columns = self.extended_column(tabneme, keys)
            return columns
        else:
            return self.create_table(tabneme, keys)

    def create_table(self, tabneme, keys=None):
        if type(keys) == list:
            keys = [f"{key} TEXT" for key in keys]
            sql_keys = ",".join(keys)
        elif type(keys) == dict:
            keys = keys.items()
            sql_keys = []
            for key, item in keys:
                column = self.column_type(item)
                sql_keys.append(f"{key} {column}")
            sql_keys = ",".join(sql_keys)
        else:
            if keys == None:
                keys = ""
            keys = str(keys)
            if keys != "":
                sql_keys = f"{keys} TEXT"
            else:
                sql_keys = ""
        if sql_keys != "":
            sql_keys = f",{sql_keys}"
        sql_keys += ",time REAL"
        sql = f"""
        CREATE TABLE {tabneme}(
           id INTEGER primary key AUTOINCREMENT
            {sql_keys}
        );
        """
        res = self.sqlite_exec(sql)
        result = type(res) != str
        if result:
            self.com_util.print_info(f"Successfully created data table {tabneme}")
        return result

    def is_table(self, dbname):
        sql = f"select count(*) from sqlite_master where type='table' and name='{dbname}'"
        res = self.sqlite_exec_fetchone(sql)
        is_exists = res[0] > 0
        return is_exists

    def query_table_info(self, tabname):
        sql = f"PRAGMA table_info([{tabname}])"
        res = self.sqlite_exec_fetchall(sql)
        return res

    def get_default_tabname(self):
        return "sundries_default_table"

    def create_default_tab(self):
        dbname = self.get_default_tabname()
        if self.is_table(dbname) != True:
            keys = {
                "text": "TEXT",
                "origin_type": "TEXT",
                "read": "REAL",
            }
            self.create_table(dbname, keys)

    def save_sundries(self, data):
        tabname = self.get_default_tabname()
        data = {
            "text": repr(data),
            "origin_type": str(type(data)),
        }
        data = self.set_time(data)
        sql = self.gen_insert_sql(tabname, data)
        print(f"Need to specify the table name and temporarily store the data in the {tabname} table")
        result = self.sqlite_exec(sql)
        return result

    def get_tables(self, full=False):
        if full:
            selector = "*"
        else:
            selector = "name"
        sql = f"SELECT {selector} FROM sqlite_master WHERE type='table'"
        res = self.sqlite_exec_fetchall(sql)
        if full:
            return res
        res = [tabname[0] for tabname in res]
        return res

    def extended_column(self, tabname, data):
        data_difference = []
        if type(data) == str:
            data_difference.append(data)
        elif type(data) == dict:
            data_difference = list(data.keys())
        elif type(data) == list:
            data_difference = data
        else:
            print(f"Unsupported extended column key{data}.")
            return
        columns = self.get_columns(tabname)
        # self.com_util.print_warn(columns)
        try:
            data_difference = list(
                set(data_difference).difference(
                    set(columns)
                )
            )
        except Exception as e:
            self.com_util.print_warn(data_difference)
            self.com_util.print_warn(columns)
            self.com_util.print_warn(e)

        for column_type in data_difference:
            if type(data) == dict:
                sql = f"{column_type} {self.column_type(data[column_type])}"
            else:
                sql = f"{column_type} {self.column_type(column_type)}"
            sql = f"ALTER TABLE {tabname} ADD {sql}"
            self.sqlite_exec(sql)
        return True

    def column_type(self, val):
        column_types = [
            "INT", "INTEGER", "TINYINT", "SMALLINT", "MEDIUMINT", "BIGINT", "UNSIGNED", "BIG", "INT", "INT2", "INT8",
            "INTEGER", "CHARACTER(20)", "VARCHAR(255)", "VARYING", "CHARACTER(255)", "NCHAR(55)", "NATIVE",
            "CHARACTER(70)", "NVARCHAR(100)", "TEXT", "CLOB", "TEXT", "BLOB", "no", "datatype", "specified", "NONE",
            "REAL", "DOUBLE", "DOUBLE", "PRECISION", "FLOAT", "REAL", "NUMERIC", "DECIMAL(10,5)", "BOOLEAN", "DATE",
            "DATETIME", "NUMERIC"
        ]
        val = val.strip()
        if val in column_types:
            return val
        pattern = re.compile(r"^[CHAR|CHARACTER|VARCHAR|CHARACTER|NCHAR|CHARACTER|NVARCHAR|DECIMAL|VARCHAR]+\(\d+\)",
                             re.I)
        if re.match(pattern, val):
            return val
        if type(val) == int:
            return "INTEGER"
        if type(val) == float or self.com_string.is_time_string(val):
            return "REAL"
        return "TEXT"

    def get_columns(self, tabname):
        info = self.query_table_info(tabname)
        columns = [name[1] for name in info]
        return columns

    def match_table(self, data):
        if type(data) != dict:
            return None
        keys = list(data.keys())
        tables = self.get_tables()
        for table in tables:
            columns = self.get_columns(table)
            if (columns[0].lower() == "id"):
                del columns[0]
            if (self.com_util.eq(keys, columns)):
                return table
        return None

    def sqlite_exec_fetchmany(self, sql):
        res = self.sqlite_exec(sql, fetch="fetchmany")
        return res

    def sqlite_exec_fetchall(self, sql):
        res = self.sqlite_exec(sql, fetch="fetchall")
        return res

    def sqlite_exec_fetchone(self, sql):
        res = self.sqlite_exec(sql, fetch="fetchone")
        return res

    def sqlite_only_exec(self, sql):
        self.connect()
        try:
            if type(sql) == list:
                # sql = ";\n".join(sql)
                # sql = sql + ";"
                # res = self.__db.executescript(sql)
                exec_success = 0
                exec_fail = 0
                err = None
                for row in sql:
                    try:
                        self.__db.execute(row)
                        exec_success += 1
                    except Exception as e:
                        if err == None:
                            err = str(e)
                        exec_fail += 1
                res = f"{err}, SQL executes {exec_success} successfully and failed {exec_fail}"
            else:
                res = self.__db.execute(sql)
        except Exception as e:
            self.com_util.print_warn(sql)
            self.com_util.print_danger(e)
            res = f"{str(e)}"
        return res

    def sqlite_exec(self, sql, fetch="fetchone"):
        threadingLock.acquire()
        res = self.sqlite_only_exec(sql)
        if type(res) != str:
            if fetch == "fetchone":
                res = res.fetchone()
            elif fetch == "fetchmany":
                res = res.fetchmany()
            elif fetch == "fetchall":
                res = res.fetchall()
        is_commit = self.db_commit()
        while is_commit == False:
            time.sleep(3)
            is_commit = self.db_commit()
        self.sqlite_close()
        threadingLock.release()
        return res

    def db_commit(self):
        try:
            self.__con.commit()
            return True
        except Exception as e:
            self.com_util.print_warn(e)
            return False

    def sqlite_close(self):
        self.__db.close()
        self.__con.close()

    def save(self, tabname=None, data=None, insert_list=False, result_id=False):
        if self.get_data_type("sqlite"):
            return self.save_data_to_sqlite(tabname=tabname, data=data, insert_list=insert_list, result_id=result_id)
        elif self.get_data_type("mongodb"):
            return self.save_data_to_mongodb(tabname=tabname, data=data)

    # 保存数据到到sqlite
    def save_data_to_sqlite(self, tabname=None, data=None, insert_list=False, result_id=False):
        origin_data = data
        if data == None:
            data = tabname
            tabname = None
        if data == None:
            print(f"The stored data is empty")
            return False

        if type(data) != list:
            data = [data]
        for i in range(len(data)):
            data_item = data[i]
            # 如何存入的是一个单独的字符串则存和通用数据库中.
            data[i] = self.set_default_val(data_item)
            self.set_time(data[i])

        if tabname == None:
            return self.save_sundries(data)

        if insert_list:
            sql = self.gen_insert_sql_list(tabname, data)
        else:
            sql = self.gen_insert_sql(tabname, data)
        result = self.sqlite_exec(sql)
        if self.is_no_table(result):
            self.create_table(tabname, data)
            return self.save_data_to_sqlite(tabname, data)
        if self.is_no_column(result):
            self.extended_column(tabname, origin_data)
            return self.save_data_to_sqlite(tabname, origin_data)
        if result_id == True:
            result = self.read(tabname, data, select="*")
            result = result[0][0]
        return result

    def gen_update_sql(self, tabname, data):
        return self.gen_general_sql(tabname, data, "update")

    def gen_insert_sql(self, tabname, data):
        return self.gen_general_sql(tabname, data, "insert")

    def gen_insert_sql_list(self, tabname, data):
        return self.gen_general_sql(tabname, data, "insert_list")

    def gen_general_sql(self, tabname, data, sql_type="insert"):
        if type(data) is not list:
            data = [data]

        columns = []
        insert_column = None
        values = []
        for data_item in data:
            value_item = []
            for key, value in data_item.items():
                if type(value) != str:
                    value = json.dumps(value)
                    value = self.encode_apostrophe(value)
                else:
                    value = self.encode(value)
                value = value.strip("'")
                # print(value)
                # exit()
                value = f"'{value}'"
                value_item.append(f"{value}")
                if insert_column == None:
                    columns.append(f"{key}")

            insert_column = ""
            values.append(value_item)

        if sql_type == "insert" or sql_type == "insert_list":
            insert_column = ",".join(columns)
            insert_column = f"({insert_column})"
            insert_values = []
            insert_sql_list = []
            for value in values:
                insert_value = ",".join(value)
                insert_value = f"({insert_value})"

                # 数组形式的单条插入
                insert_sql = f"insert into {tabname} {insert_column} values {insert_value}"
                insert_sql_list.append(insert_sql)

                insert_values.append(insert_value)
            if sql_type == "insert_list":
                return insert_sql_list
            else:
                # 单条语句式的插入
                insert_values = ",".join(insert_values)
                insert_sql = "insert into %s %s values %s" % (tabname, insert_column, insert_values)
                return insert_sql
        elif sql_type == "update":
            update_sql = []
            values = values[0]
            for i in range(len(values)):
                column = columns[i]
                value = values[i]
                value_strip = value.strip("'")
                if value_strip.startswith("+") or value_strip.startswith("-"):
                    value = f"{column}{value_strip}"
                update_sql.append(f"{column}={value}")
            update_sql = ",".join(update_sql)
            insert_sql = "update %s set %s" % (tabname, update_sql)
        else:
            insert_sql = None
        return insert_sql

    def list_bind(self, tabname, data):
        columns = self.get_columns(tabname)
        if columns[0] == "id":
            columns = columns[1:]
        insert_sql_lists = []
        for item in data:
            item_dict = {}
            for index in range(len(item)):
                key = columns[index]
                item_dict[key] = item[index]
            insert_sql_lists.append(item_dict)
        return insert_sql_lists

    def encode(self, value):
        if type(value) is not str:
            return value
        value = value.replace("'", "&apos;")
        value = value.replace('"', "&quot;")
        # value = value.replace('&', "&amp;")
        return value

    def encode_apostrophe(self, value):
        if type(value) is not str:
            return value
        value = value.replace("'", "&apos;")
        # value = value.replace('&', "&amp;")
        return value

    def decode(self, value):
        if type(value) is not str:
            return value
        value = value.replace("&apos;", "'")
        value = value.replace("&quot;", '"')
        value = value.replace("\\'", "'")
        # value = value.replace('&amp;', "&")
        return value

    def set_time(self, data):
        if "time" not in data:
            data["time"] = self.com_string.create_time()
        return data

    def set_default_val(self, val):
        if type(val) == dict:
            return val
        val = {
            "text": val
        }
        return val

    # 数据库获取数据
    def read(self, tabname=None, conditions=None, limit=(0, 1000), select="*", result_object=False, sort="",
             print_sql=False,select_as=None,):
        default_limit_length = 1000
        if tabname == None:
            tabname = self.get_default_tabname()
        conditions = self.query_conditions(conditions)
        if limit not in (None, False):
            if type(limit) == str:
                limit = limit.split(',')
            if type(limit) == int:
                limit_len = limit
                offset = 0
            elif type(limit) in [tuple, list]:
                if len(limit) > 1:
                    limit_len = limit[1]
                    offset = limit[0]
                else:
                    limit_len = limit[0]
                    offset = 0
            else:
                offset = 0
                limit_len = default_limit_length
            if str(limit_len) == "":
                limit_len = default_limit_length
            limit_sql = f"LIMIT {limit_len} OFFSET {offset}"
        else:
            limit_sql = ""
        sort = self.gen_sql_sort(sort)

        select_as_sql = self.gen_select_as_sql(select_as)

        sql = f"select {select}{select_as_sql} from {tabname} {conditions} {sort} {limit_sql}"
        if print_sql:
            print(sql)
        result = self.sqlite_exec_fetchall(sql)
        if type(result) == str:
            return result
        for i in range(len(result)):
            row = result[i]
            if type(row) == tuple:
                row = list(row)
                result[i] = list(row)
                if result_object:
                    for j in range(len(row)):
                        row_item = row[j]
                        if type(row_item) == str and re.search(re.compile(r"^[a-zA-Z0-9]"), row_item.strip()) == None:
                            try:
                                try:
                                    row_item = json.loads(row_item)
                                except:
                                    row_item = self.decode(row_item)
                                    row_item = json.loads(row_item)
                                result[i][j] = row_item
                            except Exception as e:
                                self.com_util.print_warn(f"Failed to fetch result to convert JSON, {row_item[:60]}")
                                self.com_util.print_warn(e)
        return result

    def gen_select_as_sql(self,select_as,prefix=True):
        select_as_sql = []
        if type(select_as) == dict:
            for key, value in select_as.items():
                select_as_sql.append(f"({value}) as '{key}'")
        if len(select_as_sql) > 0:
            select_as_sql = ",".join(select_as_sql)
            if prefix == True:
                select_as_sql = f",{select_as_sql}"
        else:
            select_as_sql = ''
        return select_as_sql

    def get_id(self, tabname, conditions):
        id = self.read(tabname, conditions, select="id")
        if len(id) == 0:
            id = 0
        else:
            id = id[0][0]
        return id

    def count(self, tabname=None, conditions=None, select="*", print_sql=False,return_sql=False,select_as=None,):
        conditions = self.query_conditions(conditions)
        if select_as != None:
            select = None
        if select == None:
            select_as_sql = self.gen_select_as_sql(select_as,prefix=False)
            select_sql = ""
        else:
            select_sql = f"COUNT({select})"
            select_as_sql = self.gen_select_as_sql(select_as)
        sql = f'SELECT {select_sql}{select_as_sql} FROM {tabname} {conditions}'
        if return_sql == True:
            return sql
        if print_sql == True:
            print(sql)

        if select_as != None:
            result = self.sqlite_exec_fetchall(sql)
        else:
            result = self.sqlite_exec_fetchone(sql)
        count = result[0]
        return count

    def gen_sql_sort(self, sort):
        if sort and sort != "":
            sort_string = []
            if type(sort) == dict:
                for key, value in sort.items():
                    sort_string.append(f"{key} {value}")
                sort_string = ",".join(sort_string)
            elif type(sort) == str:
                sort = sort.strip()
                sorts = re.split(re.compile(r"\s+"), sort)
                sort = sorts[0]
                if len(sorts) > 1:
                    order = sorts[1]
                else:
                    order = "ASC"
                sort_string = f"{sort} {order}"
            sort = f" ORDER BY {sort_string}"
            return sort
        else:
            return ""

    def read_data_from_mongo(self, tabname=None, conditions=None, limit=(0, 1000), select="*"):
        pass

    def decode_deep(self, result):
        if type(result) == list:
            for i in range(len(result)):
                row = result[i]
                result[i] = self.decode(str(row))
                try:
                    result[i] = eval(result[i])
                except:
                    pass
        elif type(result) == str:
            result = self.decode(str(result))
            try:
                result = eval(result)
            except:
                pass
        return result

    def delete(self, tabname, conditions):
        conditions = self.query_conditions(conditions)
        if conditions == "":
            print("Data delete-upgrades do not allow null conditions")
            return False
        sql = f"DELETE FROM {tabname} {conditions}"
        result = self.sqlite_exec(sql)
        return result

    def update(self, tabname, data, conditions):
        origin_data = data
        conditions = self.query_conditions(conditions)
        if conditions == "":
            print("Data upgrades do not allow null conditions")
            return False
        sql = self.gen_update_sql(tabname, data)
        sql = f"{sql} {conditions}"
        result = self.sqlite_exec(sql)
        # print(result)
        if self.is_no_column(result):
            self.extended_column(tabname, origin_data)
            return self.update(tabname, origin_data, conditions)
        return result

    def is_no_table(self, result):
        if type(result) == str:
            if result.find("no table") != -1 or result.find("no such table") != -1:
                return True
        return False

    def get_dbconfig(self):
        config = self.load_module.get_control_config()
        dbconfig = config.get('database')
        return dbconfig

    def get_tables_from_config(self):
        databases = self.get_dbconfig()
        databases = [tabname.get('tabname') for tabname in databases]
        return databases

    def is_no_column(self, result):
        if type(result) == str:
            if result.find("no column") != -1 or result.find("no such column") != -1:
                return True
        return False

    def query_conditions(self, conditions):
        if type(conditions) == str:
            condition_list = conditions.split(',')
            condition_dict = {}
            for requirement in condition_list:
                requirements = requirement.split("=")
                requirement_item = requirements[0].strip()
                requirement_value = requirements[1].strip()
                condition_dict[requirement_item] = requirement_value
            conditions = condition_dict
        if type(conditions) == dict:
            condition = []
            for key, requirement in conditions.items():
                if requirement in ["", None, 'null']:
                    condition.append(
                        f"({key}='' or {key}='null' or {key} is null)"
                    )
                elif type(requirement) == list:
                    is_num = re.compile(r"^[0-9]+$")
                    requirements_list = []
                    for item in requirement:
                        if re.match(is_num, item) != None:
                            item = str(item)
                        else:
                            item = f"'{str(item)}'"
                        requirements_list.append(
                            item
                        )

                    requirement_list = ",".join(requirements_list)
                    condition.append(
                        f"{key} in ({requirement_list})"
                    )
                else:
                    requirement = str(requirement)
                    requirement = requirement.strip()
                    symbol = "="
                    greater_than_sign = ">"
                    less_than_sign = "<"
                    vague_sign = "%"
                    if requirement.startswith(less_than_sign):
                        symbol = less_than_sign
                        requirement = requirement.split(less_than_sign)[1].strip()
                    elif requirement.startswith(greater_than_sign):
                        symbol = greater_than_sign
                        requirement = requirement.split(greater_than_sign)[1].strip()
                    elif requirement.startswith(vague_sign):
                        symbol = ' like '
                    condition.append(
                        f"{key}{symbol}'{requirement}'"
                    )
            if len(condition) > 0:
                condition = " and ".join(condition)
            else:
                condition = ""

            if condition == "":
                conditions = ""
            else:
                conditions = f"where {condition}"
            return conditions
        else:
            return ""
