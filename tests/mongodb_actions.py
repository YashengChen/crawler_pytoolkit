import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.crawler_toolkit.output_data import MongoDB_Actions


import unittest

class MongoDBActionsTest(unittest.TestCase):
    MONGODB_CONN_INFO = {
        'database_name': 'TEST',
        'host': '127.0.0.1',
        'port': 27017,
        'username': 'admin',
        'password': 'asdf',
        'auth_source': 'admin'
    }

    mongo_actions = MongoDB_Actions(connect_info=MONGODB_CONN_INFO)
    fake_data = [{'_id': i,'name': f'test_{i}', 'age': i*10} for i in range(4)]
    collection_name = 'unittest'
    def test_1_check_connection(self):
        self.assertTrue(self.mongo_actions.check_connection(), 'Connection Fail')

    def test_2_create(self):
        self.mongo_actions.create(create_data=self.fake_data, collection_name=self.collection_name)
        result = self.mongo_actions.retrieve(collection_name=self.collection_name, query_syntax={})
        self.assertEqual(result, self.fake_data, 'Create Data Fail')
    
    def test_3_update(self):
        query_syntax = {'_id': 0}
        update_result = self.mongo_actions.update(update_data={'name': 'test_update'}, query_syntax=query_syntax, collection_name=self.collection_name)
        result = self.mongo_actions.retrieve(collection_name=self.collection_name, query_syntax=query_syntax)[0]
        self.assertEqual(result.get('name'), 'test_update', 'Update Data Fail')

    def test_4_upsert(self):
        upsert_data = [{'_id': 3, 'name': 'upsert_test', 'age': 30}, {'_id': 4, 'name': 'upsert_test', 'age': 40}]
        self.mongo_actions.upsert(create_data=upsert_data, collection_name=self.collection_name)
        result = self.mongo_actions.retrieve(collection_name=self.collection_name, query_syntax={'name': 'upsert_test'})
        self.assertEqual(result, upsert_data, 'Upsert=true, Fail')

    def test_5_delete(self):
        query_syntax = {'_id': 0}
        self.mongo_actions.delete(collection_name=self.collection_name, query_syntax=query_syntax)
        result = self.mongo_actions.retrieve(collection_name=self.collection_name, query_syntax=query_syntax)
        self.assertEqual(len(result), 0, 'Delete data Fail')

    def test_9_drop_collection(self):
        drop_success = self.mongo_actions.drop_collection(collection_name=self.collection_name)
        self.assertTrue(drop_success, 'Drop collection Fail')

        drop_success = self.mongo_actions.drop_collection(collection_name=self.collection_name)
        self.assertFalse(drop_success, 'collection not exist')

if __name__ == '__main__':
    unittest.main()