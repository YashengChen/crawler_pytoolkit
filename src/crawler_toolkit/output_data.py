import re
import os
import json
import pickle
import pysolr
import traceback
import pandas as pd
from tqdm import tqdm
from datetime import datetime
from pymongo import errors, MongoClient

from sqlalchemy.engine import URL
from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError
from sqlalchemy import create_engine, select, inspect, text
from sqlalchemy_utils import database_exists, create_database

from crawler_toolkit.share_module import LoggingSet, Message


class MongoDB_Actions:
    log = LoggingSet.get_logger(__name__)

    def __init__(self, connect_info: dict) -> None:
        '''
        passing mongodb connection dictionary:

        connect_info = {
            'database_name': 'YOUR_DATABASE_NAME',  str
            'host'         : 'IP_ADDRESS',          str
            'port'         : 'PORT',                int
            'username'     : 'YOUR_DB_USERNAME',    str
            'password'     : 'YOUR_DB_PASSWORD',    str
            'auth_source'  : 'AUTH_SOURCE_DB'       str
        }
        '''
        self.connect_info = connect_info
        self.mondb = self.init_database_client()

    def check_connection(self):
        '''Check Connection

        get server information
        return `True` or `False`.
        '''
        try:
            server_info = self.mongoDB_client.server_info()
            print(server_info)

        except Exception as e:
            err_mssg = traceback.format_exc()
            print(err_mssg)
            return False
        else:
            print('connection successful!')
            return True
    
    def init_database_client(self, database_name: str=None, microsecond_timeout: int=10000)-> object:
        '''Init DataBase Client
        
        create MongoClient Object mondb
        
        :param - `database_name` <str>: passing database name to init mongo client
        :param - `microsecond_timeout` <int>: settings time out time with microseconds
        '''
        # conn info
        if not database_name:
            database_name = self.connect_info.get('database_name')
        self.mongoDB_client   = MongoClient( 
                                        host      = self.connect_info.get('host'),
                                        port      = self.connect_info.get('port'),
                                        username  = self.connect_info.get('username'),
                                        password  = self.connect_info.get('password'),
                                        authSource= self.connect_info.get('auth_source'),
                                        serverSelectionTimeoutMS=microsecond_timeout
                                    )
        return self.mongoDB_client[database_name]

    def __check_create_data(self, create_data : list[dict]| pd.DataFrame| dict)-> list[dict]:
        '''check create_data instance,
        
        check datatype is datagrame or dict if is dataframe or dict to list[dict] else raise TypeError
        
        :param - `create_data` <list[dict]| dataframe| dict>: passing data to check type 
            if is dataframe or dict transfer to list[dict]
        '''
        if not isinstance(create_data, (pd.DataFrame, dict, list)):
            raise TypeError(f'create_data passing wrong <{type(create_data)}> type, only can accept (dataframe | list[dict] | dict)')
        if isinstance(create_data, pd.DataFrame):
            create_data = create_data.to_dict(orient="records")
        if isinstance(create_data, dict):
            create_data = [create_data]
        return create_data

    def create(self, create_data: list[dict], collection_name: str)-> None:
        ''' create data

        create data into collection pass if duplicate key
        :param - `create_data` <dict>: passing list dictionary to insert data
        :param - `collection_name` <str>: which collection to insert data
        '''
        create_data = self.__check_create_data(create_data=create_data)
        Message.splitline(f'[Mongodb Actions] write to Mongodb', 
            f'start write data to \n\tmongodb: {self.connect_info.get("database_name")} \n\tcollection: {collection_name}')

        collections = self.mondb[collection_name]
        sucess_num   = 0
        error_nums   = 0
        duplicate_data = 0
        total_create_data = tqdm(create_data, leave=True)
        for i in total_create_data:
            try:
                collections.insert_one(i)
                sucess_num += 1
                total_create_data.set_description(f"[Create Data] \"Sucess\" Insert data id:{i['_id']}")

            except errors.BulkWriteError as e:
                errmsg = e.details['writeErrors'][0]['errmsg']
                if re.findall('duplicate key', errmsg):
                    duplicate_data+=1
                    total_create_data.set_description(f"[Create Data] \"Fail\" Data already exist !")
                    print('Data already exist !')
                    
                else:
                    error_nums += 1
                    total_create_data.set_description(f"[Create Data] \"Error\" Error data: {sucess_num}")
                MongoDB_Actions.log.error(errmsg)

            except errors.DuplicateKeyError as dpke:
                duplicate_data+=1
                total_create_data.set_description(f"[Create Data] \"Fail\" Duplicate Key {i['_id']}!")
                errmsg = traceback.format_exc()
                MongoDB_Actions.log.error(errmsg)

            except Exception as e:
                errmsg = traceback.format_exc()
                MongoDB_Actions.log.error(errmsg)

            else:
                total_create_data.refresh()
        
        Message.splitline('Create Data to Mongodb', f'Sucess: {sucess_num}\nError: {error_nums}\nDuplicate: {duplicate_data}')

    def update(self, update_data: dict, collection_name: str, query_syntax: dict, upsert: bool=True):
        '''update data

        filter by dict to update data.
        
        :param - `update_data` <dict>: update key:value which match filter documents
        :param - `collection_name` <str>: which collection to insert data
        :param - `query_syntax` <dict>: passing dictionary key:value to filter documents
        :param - `upsert` <bool>: creates a new document if no documents match the filter
        '''
        Message.splitline(f'[Mongodb Actions] update Mongodb', 
            f'start update data to \n\tmongodb: {self.connect_info.get("database_name")} \n\tcollection: {collection_name}')

        collections = self.mondb[collection_name]
        
        newvalues = {"$set": update_data}
        update_result = collections.update_many(query_syntax, newvalues, upsert=upsert)
        update_stastic = update_result.raw_result

        Message.splitline(f'[Mongodb Actions] Update to Mongodb', 
            f'total: {update_stastic.get("n")}\nupdate: {update_stastic.get("nModified")}\nsuccess: {update_stastic.get("ok")}')

        return update_stastic

    def upsert(self, create_data: list[dict], collection_name: str, filter_key: str='_id', upsert: bool=True)-> None:
        ''' update or insert data

        InsertData to collection update if document match filter by "filter_key"

        :param - `create_data` <dict>: passing list dictionary to insert data
        :param - `collection_name` <str>: which collection to insert data
        :param - `filter_key` <str>: custom filter by create_data key, default="_id"
        :param - `upsert` <bool>: creates a new document if no documents match the filter
        '''
        
        create_data = self.__check_create_data(create_data=create_data)
        sucess_num   = 0
        error_nums   = 0
        duplicate_data = 0
        total_create_data = tqdm(create_data, leave=True)
        
        Message.splitline(f'[Mongodb Actions] write to Mongodb', 
            f'start write data to \n\tmongodb: {self.connect_info.get("database_name")} \n\tcollection: {collection_name}')

        collections = self.mondb[collection_name]
        for i in total_create_data:
            query = {filter_key: i[filter_key]}
            newvalues = {"$set": i}
            try:
                collections.update_many(query, newvalues, upsert=upsert)
                sucess_num += 1
                total_create_data.set_description(f"[Create Data] \"Sucess\" Insert data id:{i['_id']}")
    
            except errors.BulkWriteError as e:
                errmsg = e.details['writeErrors'][0]['errmsg']
                if re.findall('duplicate key', errmsg):
                    duplicate_data+=1
                    total_create_data.set_description(f"[Create Data] \"Fail\" Data already exist !")
                else:
                    error_nums += 1
                    total_create_data.set_description(f"[Create Data] \"Error\" Error data: {sucess_num}")
                MongoDB_Actions.log.error(errmsg)
            
            except errors.DuplicateKeyError as dpke:
                duplicate_data+=1
                total_create_data.set_description(f"[Create Data] \"Fail\" Duplicate Key {i['_id']}!")
                errmsg = traceback.format_exc()
                MongoDB_Actions.log.error(errmsg)

            else:
                total_create_data.refresh()
                
        Message.splitline('Write to Mongodb', f'Sucess: {sucess_num}\nError: {error_nums}\nDuplicate: {duplicate_data}')

    def retrieve(self, collection_name: str, query_syntax: dict={}, how: str='finds')-> list[dict]:
        '''retrieve data 
        
        Retrieve data from collection by pymongo syntax query.
        
        :param - `collection_name` <str>: which collection to insert data
        :param - `query_syntax` <dict>: pymongo query to filter document
        '''
        collections = self.mondb[collection_name]
        if how == 'finds':
            result = [doc for doc in collections.find(query_syntax)]
        elif how == 'find':
            result = [collections.find_one(query_syntax)]
        else:
            raise ValueError('args "how" only accept ["find"|"finds"]')
        Message.splitline('fetch data', f'total document: {len(result)}')
        return result

    def delete(self, collection_name: str, query_syntax: dict)-> None:
        '''delete data 
        
        delete data from collection by pymongo syntax query.
        
        :param - `collection_name` <str>: which collection to insert data
        :param - `query_syntax` <dict>: pymongo query to filter document
        '''
        collections = self.mondb[collection_name]
        delete_action = collections.delete_one(query_syntax)
        delete_statistic = delete_action.raw_result
        return delete_statistic

    def drop_collection(self, collection_name: str)-> bool:
        '''drop collection
        
        passing collection name to drop database collection.
        
        :param - `collection_name` <str>: which collection to insert data
        '''
        if collection_name in self.mondb.list_collection_names():
            collections = self.mondb[collection_name]
            collections.drop()
            if collection_name in self.mondb.list_collection_names():
                print(f'Drop Collection {collection_name} Fail, collection still exist')
                return False
            
            Message.splitline('[MongoDB Actions] drop collection', f'Drop Collection <"{collection_name}"> successful!')
            return True
        else:
            print(f'collection: "{collection_name}" not exist')
            return False

    def __repr__(self) -> str:
        rep = f'MongoDB_Actions(connect_info={self.connect_info!r}, db_engine={self.mondb!r})'
        return rep

    def __str__(self) -> str:
        string_format = f'connect_info={self.connect_info!r}, db_engine={self.mondb!r}'
        return string_format


class MsSQL_Actions:
    log = LoggingSet.get_logger(__name__)

    def __init__(self, connect_info: dict|str=None, echo=False):
        '''Connection Information Passing

        :param - `connect_info` <dict|str>: passing dict connection object, or string connection url
            see more on: https://docs.sqlalchemy.org/en/20/core/engines.html
        :param - `echo` <bool>: passing bool True or False to show Query information
        '''

        self.connect_info = connect_info
        self.echo = echo
        self.db_engine = self.init_engine()
        
    @staticmethod
    def create_connection_uri(connect_info: dict)-> object:
        '''Create Connection URI
        
        Passing connection dictionary object to init connection url,

        :param - `connect_info`<dict> : passing dictionary connection information
            see more on: https://docs.sqlalchemy.org/en/20/core/engines.html
        
        see example below:
            connection_info = {
                'username'   : 'YOUR_USERNAME',
                'password'   : 'YOUR_PASSWORD',
                'host'       : 'IP_ADDRESS',
                'port'       : 'PORT',
                'database'   : 'DATABASE_NAME',
                'drivername' : 'mssql+pyodbc',
                'query': {
                            "driver": "ODBC Driver 18 for SQL Server",
                            "TrustServerCertificate":'yes',
                            "Encrypt": "yes",
                            "charset": "utf8"
                        }
            }
        '''
        return URL.create(**connect_info)

    def init_engine(self):
        '''Init Connection Engine Object
        
        Init Connection Engine for Database action.
        '''
        if not isinstance(self.connect_info, (dict, str)):
            raise TypeError('connect_info Type Error can\'t init engine')

        URI = self.connect_info
        if isinstance(self.connect_info, dict):
            URI = self.create_connection_uri(connect_info=self.connect_info)
        return create_engine(URI, echo=self.echo)

    def check_connection(self):
        '''Check Connection

        Query "SELECT 1" to Check Connection
        return `True` or `False`.
        '''
        with self.db_engine.connect() as conn:
            try:
                result = conn.execute(text('SELECT 1')).fetchall()
                print(result)
            except Exception as e:
                err_mssg = traceback.format_exc()
                print(err_mssg)
                return False
            else:
                print('connection sucessful.')
                return True

    def init_database(self, model_metadb: object)-> None:
        '''Init DataBase Which Not Exist
        
        Init Database which connection database if Not Exist and Create
        passing table model tables.

        :param - `model_metadb` <class>: declarative_base class object
        '''
        if not database_exists(self.db_engine.url):
            create_database(self.db_engine.url)
            print('create database sucess!')
        
        model_metadb.metadata.create_all(self.db_engine)
        print(f'init all table schema <{list(model_metadb.metadata.tables.keys())}>')
        Message.splitline('[DataBaseAction] init database', 'Sucess!')

    @staticmethod
    def row2dict(row: object):
        '''Row Object to dictionary
        
        Passing ORM Row retrieve Object to Convert to dictionary.

        :param - `row` <object>: sqlalchemy retrieve result
        '''
        result_data = dict()
        for c in inspect(row).mapper.column_attrs:
            result_data[c.key] = getattr(row, c.key)
        return result_data

    def create(self, datas: dict| list[dict], table_model: object)-> None:
        '''Create Data with ORM

        Passing dict or list[dict] and Table class, insert data to table.

        :param - `datas` <dict| list[dict]>: dict or list[dict] to insert data
        :param - `table_model` <object>: sqlalchemy table class object
        '''
        if not isinstance(datas, (list, dict)):
            raise TypeError('datas only support dict and list type')
        if isinstance(datas, dict):
            datas = [datas]

        with Session(self.db_engine) as session, session.begin():
            for datas in datas:
                modeldata_obj = table_model(**datas)
                session.add(modeldata_obj)
                session.flush()
                datas.update({'Id' : modeldata_obj.Id})
            session.commit()

    def retrieve(self, table_model: object, filter_by_dict: dict)-> list[dict]:
        '''### Retrieve Data With ORM
        Passing class table schema class, query by dictionary key:value.
        
        > ps. if value passing list[str], filter value in list[str] else 
        equal value

        :param - `table_model` <object>: sqlalchemy table class object
        :param - `filter_by_dict` <dict>: query by dictionary key:value
        '''
        if not isinstance(filter_by_dict, dict):
            raise TypeError('argument <filter_by_dict> only support "dict" type')

        sqry = select(table_model)
        for k, v in filter_by_dict.items():
            if isinstance(v, list):
                sqry = sqry.filter(table_model.__dict__[k].in_(v))
            else:
                sqry = sqry.where(table_model.__dict__[k] == v)

        with Session(self.db_engine) as session:
            query_result_data = session.execute(sqry).scalars().all()
            return  [self.row2dict(row) for row in query_result_data]
                
    def update(self, table_model: object, data_id: str, update_data: dict)-> None:
        '''Update Data with ORM
        
        Passing class table schema class and specific "data_id" to  update with dictionary key: value.
        
        :param - `table_model` <object>: sqlalchemy table class object
        :param - `data_id` <string>: data id  to filter which record to update
        :param - `update_data` <dict>: dictionary to update table columns: value
        '''
        with Session(self.db_engine) as session:
            try:
                data_qry = session.query(table_model)
                data_qry = data_qry.filter(table_model.Id==data_id)
                data_qry.update(update_data)

            except Exception as e:
                session.rollback()
                errmssg = traceback.format_exc()
                self.log.error(errmssg)
                raise
            else:
                session.commit()

    def delete(self, table_model: object, data_id: str)-> None:
        '''Delete Data with ORM
        
        Passing class table schema class and specific "data_id" to delete data from table.

        :param - `table_model` <object>: sqlalchemy table class object
        :param - `data_id` <string>: data id  to filter which record to delete 
        '''
        with Session(self.db_engine) as session:
            try:
                data_qry = session.query(table_model)
                data_qry = data_qry.filter(table_model.Id==data_id)
                data_qry.delete()
            except Exception as e:
                session.rollback()
                errmssg = traceback.format_exc()
                self.log.error(errmssg)
                raise
            else:
                session.commit()

    def syntax_query(self, query_syntax: str)-> list[dict]:
        '''Syntax query with string
        
        Passing SQL query string syntax for query data

        :param - `query_syntax` <string>: SQL query syntax to query data
        '''
        if not isinstance(query_syntax, str):
            raise TypeError('argument <query_syntax> only support "string" type')

        with Session(self.db_engine) as session:
            qry_result = session.execute(text(query_syntax)).fetchall()
            result = [row._asdict() for row in qry_result]
        return result

    def drop_table(self, table_model: object)-> None:
        '''Drop Table with table class
        
        Passing Table model to drop table, it will drop all table model 
        which in table model

        :param - `table_model` <object>: sqlalchemy table class object
        '''
        try:
            table_model.__table__.drop(self.db_engine)
        except Exception as e:
            err_mssg = traceback.format_exc()
            self.log.error(err_mssg)
        else:
            print(f'Drop Table <{table_model.__tablename__}> Successful')

    def __repr__(self):
        rep = f'MsSQL_Actions(connect_info={self.connect_info!r}, db_engine={self.db_engine!r}, echo={self.echo}'
        return rep

    def __str__(self):
        string_format = f'connect_info={self.connect_info}, db_engine={self.db_engine}, echo={self.echo}'
        return string_format


class Files_Actions:
    log = LoggingSet.get_logger(__name__)
    
    @staticmethod
    def check_filter_key(dict_data: dict, filter_by: dict)-> bool:
        '''Check Filter Key

        use for check that filter_by key equal in dict_data key: value,
        return True if all filter_by condition equal to dict_data else False
        
        :param - `dict_data` <dict>: target dictionary to compare with `filter_by`
        :param - `filter_by` <dict>: filter dictionary to check `filter_by` equal to `dict_data`
        '''
        result = list()
        for k, v in filter_by.items():
            key_exist = k in dict_data.keys()
            filter_key_equal = dict_data.get(k) == v
            if key_exist and filter_key_equal:
                result.append(True)
            else:
                result.append(False)
        return all(result)

    @staticmethod
    def check_exist_and_isfile(file_path :str):
        '''Check filepath exist and isfile
        
        if any condition not True, raise ValueError
        '''
        if not os.path.exists(file_path):
            raise ValueError(f'can\'t find filepath: {file_path}')
        if not os.path.isfile(file_path):
            raise ValueError(f'filepath is not an file: {file_path}')

    @staticmethod
    def toJson(
            output_data: dict| list[dict], 
            output_path: str, 
            append: bool=True,
            indent: int=4,
            ensure_ascii: bool=False,
            encoding: str='utf-8'
        )-> None:
        '''Write dictionary to Json file

        `output_data` to `output_path` json file, it can append data if file exist 
        by passing boolean append args.

        :param - `output_data` <dict| list[dict]>: output_data a dict or list dict
        :param - `output_path` <str>: the path where file store
        :param - `append` <bool>: passing `True` or `False` to append data into jsonfile, default is True
        '''
        if isinstance(output_data, dict):
            output_data = [output_data]
        result = output_data

        if os.path.isfile(output_path) and append:
            tmp_json = Files_Actions.readJson(file_path=output_path, encoding=encoding)
            if isinstance(tmp_json, dict):
                result.append(tmp_json)
            elif isinstance(tmp_json, list):
                result = (tmp_json + output_data)

        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(result, f, indent=indent, ensure_ascii=ensure_ascii)

    @staticmethod
    def readJson(file_path: str, encoding: str='utf-8')-> list[dict]:
        '''Read Json From Filepath
        
        Passing Filepath to load json data from json file.

        :param - `file_path` <str>: load file from filepath
        :param - `encoding` <str>: read with encoding code. default=`utf-8`
        '''
        Files_Actions.check_exist_and_isfile(file_path=file_path)
        with open(file_path, 'r', encoding=encoding) as f:
            auth_dicts = json.load(f)
        return auth_dicts
    
    @staticmethod
    def updateJson(update_data: list[dict], file_path: str)-> None:
        '''Update Json Files

        Only update which passing filter_by dict condition data, and saving back to json file.

        :param - `update_data` list[dict]: update 
            see example:
                update_data = [{
                                'filter_by': {id: 1}, 
                                'update_data': {'name': 'rock'}
                    }, {...}]
        :param - `file_path` <str>: load file from path and update dict object
        '''
        Files_Actions.check_exist_and_isfile(file_path=file_path)

        update_data = [update_data] if isinstance(update_data, dict) else update_data
        file_data = Files_Actions.readJson(file_path=file_path)
        for uda in update_data:
            # if not found data add to list
            for dic in file_data:
                if Files_Actions.check_filter_key(dict_data=dic, filter_by=uda['filter_by']):
                    dic.update(uda['update_data'])
                    Message.splitline('[updateJson] update sucess', dic)
        # output result
        Files_Actions.toJson(output_data=file_data, output_path=file_path, append=False)

    @staticmethod
    def loadPickle(filepath: str)-> object:
        '''LoadPickle
        Load pickle file From Path
        
        :param - `file_path` <str>: load file from filepath
        '''
        with open(filepath, "rb") as f:
            result = pickle.load(f)
        print(f'Finish loading pickles: {filepath}')
        return result

    @staticmethod
    def toPickle(output_data: object, filepath: str)-> None:
        '''ToPickle
        
        :param - `output_data` <object>: data which wanna output
        :param - `file_path` <str>: write file to filepath
        '''
        with open(filepath, 'wb') as f:
            pickle.dump(output_data, f)
        print(f'Finish saving pickles: {filepath}')


class Solr_Actions:
    def __init__(self, solr_url: str)-> None:
        '''Solr_Actions.init Object
        
        :param - `solr_url` <str>: passing solr url 
            example: http://localhost:8983/solr/
            
        see document on: https://pypi.org/project/pysolr/
        '''
        self.solr_url = solr_url
        self.solr_engine = pysolr.Solr(url=self.solr_url, timeout=10)

    def check_connection(self):
        '''Check Connection

        pysolr ping solr target from engine
        return `True` or `False`.
        '''
        try:
            response_data = self.solr_engine.ping()
            r_json = json.loads(response_data)
            if r_json.get('status') == 'OK':
                print('connection sucessful.')
        except Exception as e:
            err_mssg = traceback.format_exc()
            print(err_mssg)
            return False
        else:
            return True

    def create(self, create_data: dict| list[dict])-> None:
        '''Insert data to solr core
        
        :param - `create_data`<list[dict]>: passing list dictionary object to insert into solr
        '''
        if isinstance(create_data, dict):
            create_data = [create_data]
            
        # action
        self.solr_engine.add(docs=create_data)
        self.solr_engine.commit()
        # final
        Message.splitline('Write to Solr', f'Total Insert: {len(create_data)}')
        
    def retrieve(self, query_sytax: str)-> list:
        '''Query solr data

        passing query syntax text to retrieve data from solr core

        :param - query_sytax <str>: solr query syntax to query data
        '''
        retrieve_result = [doc for doc in self.solr_engine.search(q=query_sytax)]
        Message.splitline('read from Solr', f'Total Fetch: {len(retrieve_result)}')
        return retrieve_result
        
    def delete(self, id_code: list)-> None:
        '''Delete solr data by id_code
        
        Passing list id to delete from solr core

        :param `id_code` <list[str]>: list id_code for record which want to delete from solr
        '''
        self.solr_engine.delete(id=id_code)
        self.solr_engine.commit()
        Message.splitline('Delete data', f'delete data id: {id_code} success!')
    
    def __repr__(self) -> str:
        rep = f'Solr_Actions(solr_url={self.solr_url}, solr_engine={self.solr_engine})'
        return rep

    def __str__(self) -> str:
        string_format = f'solr_url={self.solr_url}, solr_engine={self.solr_engine}'
        return string_format