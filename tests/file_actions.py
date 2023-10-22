import json
import unittest

import os
import sys
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.crawler_toolkit.output_data import Files_Actions

class FileActionTest(unittest.TestCase):
    filter_by = {
        'id': 99
    }

    single_data = {
        'id': 99,
        'name': 'test_solger'
    }

    multiple_data = [ {'id': i, 'name': f'test_{i}'} for i in range(4)]
    test_filefolder = './tests/fileaction_test'
    if not os.path.exists(test_filefolder):
        os.mkdir(test_filefolder)
    file_name = os.path.join(test_filefolder, 'test.json')
    pickle_name = os.path.join(test_filefolder, 'pickle.pkl')
    
    def test_1_check_filterkey(self):
        check_bool = Files_Actions.check_filter_key(
                        dict_data=self.single_data,
                        filter_by=self.filter_by
                    )
        self.assertTrue(check_bool, 'Fail check Filter key')
    
    def test_2_tojson_single(self):
        Files_Actions.toJson(output_data=self.single_data, output_path=self.file_name)
        result = Files_Actions.readJson(file_path=self.file_name)
        self.assertEqual(result, [self.single_data])

    def test_3_tojson_multiple(self):
        Files_Actions.toJson(output_data=self.multiple_data, output_path=self.file_name)
        result = Files_Actions.readJson(file_path=self.file_name)
        self.assertGreater(len(result), 4)

    def test_4_readjson(self):
        result = Files_Actions.readJson(file_path=self.file_name)
        self.assertGreater(len(result), 0)

    def test_5_updatejson_single(self):
        update_data = [{'filter_by': {'id': 99}, 'update_data': {'name': 'updateName'}}]
        Files_Actions.updateJson(update_data=update_data, file_path= self.file_name)
        result = Files_Actions.readJson(file_path=self.file_name)
        for r in result:
            if r.get('id') == 99:
                self.assertEqual(r.get('name'), 'updateName', 'Update Fail')
    
    def test_5_updatejson_multiple(self):
        mul_update_data = [
            {'filter_by': {'id': 99}, 'update_data': {'name': 'updateName_1'}},
            {'filter_by': {'id': 0}, 'update_data': {'name': 'updateName_1'}}
            ]
        Files_Actions.updateJson(update_data=mul_update_data, file_path= self.file_name)
        result = Files_Actions.readJson(file_path=self.file_name)
        for r in result:
            if r.get('id') in [99, 0]:
                self.assertEqual(r.get('name'), 'updateName_1', 'Update Fail')

    def test_6_loadPickle(self):
        Files_Actions.toPickle(output_data={'cookies': 'asflkasjdinb', 'header': 'google_chrome 111'}, filepath=self.pickle_name)
        self.assertTrue(os.path.exists(self.pickle_name), 'init pickle Fail')

    def test_7_toPickle(self):
        result = Files_Actions.loadPickle(filepath=self.pickle_name)
        self.assertEqual(result.get('cookies'), 'asflkasjdinb')

    def test_8_remove_folder(self):
        os.remove(self.file_name)
        os.remove(self.pickle_name)
        os.rmdir(self.test_filefolder)

if __name__ == '__main__':
    unittest.main()