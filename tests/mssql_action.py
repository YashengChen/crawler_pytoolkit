import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.crawler_toolkit.output_data import MsSQL_Actions

import unittest
from datetime import datetime

from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from sqlalchemy import Column, ForeignKey
from sqlalchemy.dialects.mssql import INTEGER, BIT, DATETIME, VARCHAR, TEXT, NVARCHAR
from sqlalchemy.ext.declarative import declarative_base

db = declarative_base()

class TestTable(db):
    """ TestTable """
    __tablename__ = "TestTable"
    Id   = Column(INTEGER, primary_key=True, autoincrement=True)
    AccountType = Column(VARCHAR(32), nullable=False)
    Created_Time = Column(DATETIME, default=func.now())


class MssqlActionTest(unittest.TestCase):
    TEST_CONNECTION = {
            'username': None,
            'password': None,
            'host': None,
            'port': None,
            'database': 'develop/sqlite.db',
            'drivername': 'sqlite',
            'query': None
        }
    ROOT_PATH = os.path.dirname(os.path.dirname(__file__))
    sql_action = MsSQL_Actions(connect_info=TEST_CONNECTION)
    create_time = datetime.strptime('2023-04-12 15:00:00','%Y-%m-%d %H:%M:%S')
    
    def test_1_connection(self):
        self.assertTrue(self.sql_action.check_connection(), 'Connection Fail')

    def test_2_init_database_table(self):
        self.sql_action.init_database(TestTable)
        db_path = os.path.join(self.ROOT_PATH, self.TEST_CONNECTION.get('database'))
        self.assertTrue(os.path.exists(db_path), 'Database Init Fail, DB not found')

    def test_3_table_exist(self):
        table_schema = self.sql_action.syntax_query('SELECT name FROM sqlite_schema')
        self.assertEqual(table_schema, [{'name': 'TestTable'}], 'Table Schema Not Exist')

    def test_4_create_single_data(self):
        insert_data = {'AccountType': 'Test1', 'Created_Time': self.create_time}
        self.sql_action.create(datas=insert_data, table_model=TestTable)
        sqry = 'SELECT * FROM TestTable WHERE AccountType = "Test1"'
        result = self.sql_action.syntax_query(sqry)
        self.assertGreater(len(result), 0, 'create_data fail')

    def test_5_create_multiple_data(self):
        # init fake data
        insert_data = list()
        for i in range(10):
            insert_data.append({'AccountType': f'type_{i}', 'Created_Time': self.create_time})
        self.sql_action.create(datas=insert_data, table_model=TestTable)

        # get account_type values
        type_list = [i['AccountType'] for i in insert_data]
        
        # retrieve from db to check create data len equal
        query_dict = {'AccountType': type_list}
        result = self.sql_action.retrieve(table_model=TestTable, filter_by_dict=query_dict)
        self.assertEqual(len(result), len(insert_data), 'create_data multiple fail')

    def test_6_update(self):
        self.sql_action.update(table_model=TestTable, data_id=1, update_data={'AccountType': 'Test_Modify'})
        result = self.sql_action.retrieve(table_model=TestTable, filter_by_dict={'Id': 1})
        if result:
            self.assertEqual(result[0]['AccountType'], 'Test_Modify', 'update value Fail')
        else:
            raise ValueError('empty result')
        
    def test_7_delete(self):
        self.sql_action.delete(table_model=TestTable, data_id=1)

        result = self.sql_action.retrieve(table_model=TestTable, filter_by_dict={'Id': 1})
        self.assertEqual(result, [], 'delete record Fail')

    def test_8_drop_table(self):
        # drop table
        self.sql_action.drop_table(table_model=TestTable)

        # select table exist or not
        table_schema = self.sql_action.syntax_query('SELECT name FROM sqlite_schema WHERE name = "TestTable"')
        self.assertEqual(table_schema, [], 'Table Schema Exist, Drop Fail')

if __name__ == '__main__':
    unittest.main()