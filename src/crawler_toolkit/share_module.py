import re
import os
import sys
import logging
from tqdm import tqdm
from time import sleep
from opencc import OpenCC
from hashlib import sha256
from datetime import datetime


class LoggingSet:
    def setup_applevel_logger(logger_name: str='logging', file_name=None, log_level: str='debug', log_path: str=None):
        '''setup applevel logger
        init log and settings error level path etc..

        :param - `logger_name` <str>: loggername
        :param - `filename` <str>: output log filename
        :param - `log_level` <str>: setting log level [info| debug| warning| error]
        :param - `log_path`: <str>: settings output log folder path
        '''
        log_path = log_path or os.path.dirname(os.path.abspath(__name__))
        log_dict = {
                'info'   : logging.INFO,
                'debug'  : logging.DEBUG,
                'warning': logging.WARNING,
                'error'  : logging.ERROR
            }
        logger = logging.getLogger(logger_name)
        logger.setLevel(log_dict[log_level])
        formatter = logging.Formatter("%(asctime)s - %(name)s - %(levelname)s - %(message)s")
        sh = logging.StreamHandler(sys.stdout)
        sh.setFormatter(formatter)
        logger.handlers.clear()
        logger.addHandler(sh)
        if file_name:
            fh = logging.FileHandler(os.path.join(log_path, file_name))
            fh.setFormatter(formatter)
            logger.addHandler(fh)
        return logger

    def get_logger(module_name: object, logger_name: str='logging'):
        '''
        set logger object for module

        :param- `module_name` <module object>: passing class or function object to init child logger to output log
        :param- `logger_name` <str>: passing same name as self.setup_applevel_logger settings "logger_name" args
        '''
        return logging.getLogger(logger_name).getChild(module_name)


class Message:
    @staticmethod
    def splitline(title: str , context: str, linesymbol: str = '#')-> str:
        '''splitline 
        init split line with passing line symbol and print message
        
        :param - `title` <str>: splitline title
        :param - `context` <str>: infomation which wanna print out
        :param - `linesymbol` <str>: splitline use passing symbol, default is #

        preview example: \n
            |####| title |####|\n
            context
        '''
        print()
        print(str(datetime.now()) + ('|{:' + linesymbol + '^75}|').format('| %s |'%title))
        print(context)

    @staticmethod
    def sleep_time(seconds: int, custom_message: str='sleep action start'):
        '''sleep_time
        splitline and wait for seconds.

        :param - `seconds` <int>: wait for seconds
        :param - `custom_message` <str>: settings print information, default= "sleep action start"
        '''
        Message.splitline(f'[Message] total sleep: {seconds}', custom_message)
        if not isinstance(seconds, (int, float)):
            raise TypeError('args "seconds" only accept type <int>')
        if isinstance(seconds, float):
            seconds = int(seconds)
        
        time_loop = tqdm(range(seconds))
        for i in time_loop:
            sleep(1)


class DataProcess:
    @staticmethod
    def word_translate(str_data: str, how: str='t2s')-> str:
        '''word_translate
        it is transfer chinese between traditional and simpleified 
        
        
        :param - `str_data` <str>: which data need to transfer
        :param - `how` <str>: from which chinese to others, default="t2s"
            :`how` more option in `openCC` pypi url: https://pypi.org/project/opencc-python-reimplemented/
        '''
        cc = OpenCC(how)
        if str_data :
            str_data  = cc.convert(str_data)
        return str_data

    @staticmethod
    def nested_get(input_dict: dict, nested_key: list):
        '''nested_get
        extract value with nested_key from input_dict

        :param - `input_dict` <dict>: nested dictionary data
        :param - `nested_key` <list>: list level key
        '''
        result = input_dict
        if isinstance(input_dict, list):
            return None
        for k in nested_key:
            result = result.get(k, None)
            if result is None:
                return None
        return result

    @staticmethod
    def str2hash256(data_byte: bytes):
        '''string data to hash256

        :param `data_byte` <bytes>: data which want to trans to hash256
        '''
        if isinstance(data_byte, str):
            data_byte = data_byte.encode()
        hash_str = sha256()
        hash_str.update(data_byte)
        return hash_str.hexdigest()


class TempDataSet:
    '''temp data set
    
    init data_set to store unique value
    '''
    def __init__(self) -> None:
        self.data_set = set()
    
    def is_duplicated(self, unique_val: str)-> bool:
        '''check data already in set return True
        False if not in set and append unique_val to set

        :param - `unique_val` <str>: duplicate detect by `unique_val`
        '''
        if unique_val in self.data_set:
            return True
        self.data_set.add(unique_val)
        return False


class ArgsDefine:
    def TF_define(passing_args: str)-> bool:
        '''define string true false
        
        :param - `passing_args`: str: string true false or 0 to bool
        '''
        if passing_args in ['True', 'true', '1']:
            return True
        elif passing_args in ['False', 'false', '0']:
            return False
        else:
            raise ValueError(' only accept [True|False]')

    def cama_str2list(args_str: str):
        '''split string with cama to list data

        :param - `args_str` <str>: string data which want to split
        '''
        args_str = re.sub(' ', '', args_str)
        return args_str.split(',')


class DefaultSet:
    def init_folder(folder_list: list[str])-> None:
        '''init filepath 
        
        :param - folder_list <list[str]>: list default path need to create
        '''        
        for folder in folder_list:
            if folder and not os.path.exists(folder):
                os.mkdir(folder)
                print(f'path create: {folder}')
