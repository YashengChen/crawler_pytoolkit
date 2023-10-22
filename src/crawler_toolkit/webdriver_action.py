import os
import pyotp
import pickle
import random
import warnings
import traceback
from time import sleep
from datetime import datetime
from seleniumwire import webdriver
from seleniumwire.utils import decode
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

from crawler_toolkit.share_module import LoggingSet, Message
from crawler_toolkit.output_data import Files_Actions

import undetected_chromedriver as uc
from undetected_chromedriver import ChromeOptions as UC_ChromeOptions

class WebdriverAction:
    '''Webdriver action interface
    
    Extend on selenium webdriver, build some action process for webdriver
    '''
    log = LoggingSet.get_logger(__name__)

    select_by = {
            'id': By.ID,
            'xpath': By.XPATH,
            'link_text': By.LINK_TEXT,
            'partial_link_text': By.PARTIAL_LINK_TEXT,
            'name': By.NAME,
            'tag_name': By.TAG_NAME,
            'class_name': By.CLASS_NAME,
            'css': By.CSS_SELECTOR,
        }

    def init_driver(
            use_driver: str='firefox',
            driver_path: str=None,
            options: list=None,
            headless: bool=True,
            remote_driver: str=None,
            set_preference: dict={},
            seleniumwire_option: dict={}
        )-> object:
        '''init webdriver

        :param - `user_driver`<str>: passing string of driver name.
        :param - `driver_path` <str>: passing local webdriver filepath or remote host:port
        :param - `options` <list>: passing option for webdriver
        :param - `headless` <bool>: True False to turn on/off GUI of browser
        :param - `remote_driver` <str>: passing string of driver name, which will remote to browser server
            to action select driver, user_driver need to be "remote"
        :param - `set_preference` <dict>: passing webdriver set_preference object(only support firefox)
        :param - `seleniumwire_option` <dict>: passing seleniumwire options object, proxy settings.
        - return `webdriver <object>`
        '''

        driver_use = {
            'chrome': {
                        'driver': webdriver.Chrome,
                        'option': webdriver.ChromeOptions()
                    },
            'uc_chrome': {
                        'driver': uc.Chrome,
                        'option': UC_ChromeOptions()
                    },
            'firefox': {
                        'driver': webdriver.Firefox,
                        'option': webdriver.FirefoxOptions()
                    },
            'edge': {
                        'driver': webdriver.Edge,
                        'option': webdriver.EdgeOptions()
                    },
            'remote': {
                        'driver': webdriver.Remote,
                        'option': webdriver.FirefoxOptions()
                    }
        }

        user_use = driver_use[use_driver]
        if remote_driver and remote_driver != 'firefox':
            user_use['option'] = driver_use[remote_driver]['option']
        option_obj = user_use['option']
        option_obj.headless = headless

        if options:
            for opt in options:
                option_obj.add_argument(opt)
        
        if set_preference:
            if remote_driver == 'firefox':
                for k, v in set_preference.items():
                    option_obj.set_preference(k, v)
            else:
                warnings.warn('set_preference only support firefox browser, set_prefernce fail')
        
        if remote_driver:
            default_sw_option = {
                    'auto_config': False,
                    'addr': '127.0.0.1', # use self host ip addr
                    'port': 9090 # passing integer that none used port
                }
            for k, v in default_sw_option.items():
                if k not in seleniumwire_option:
                    seleniumwire_option.update({k: v})

        
        if remote_driver:
            driver = user_use['driver'](
                    command_executor=driver_path,
                    options=option_obj,
                    seleniumwire_options=seleniumwire_option
                )
        elif use_driver == 'uc_chrome':
            driver = user_use['driver'](options=option_obj)

        else:
            driver = user_use['driver'](
                    executable_path=driver_path,
                    options=option_obj,
                    seleniumwire_options=seleniumwire_option
                )
        return driver

    def show_by_option()-> None:
        '''show find_elem_by options
        return `list[key]`
        '''
        print(list(WebdriverAction.select_by.keys()))

    def scrolling_to(driver: webdriver, xpath: str, postition: int=-1, delay: int=random.choice([3,5,7]))-> None:
        '''scrolling to web element position
        
        :param - `driver` <webdriver>: action webdriver object
        :param - `xpath` <str>: target element xpath
        :param - `postition` <int>: list return elements scrolling to which position, default=-1
        :param - `delay` <int>: sleep seconds after scrolling finish
        '''
        new_element  = WebdriverAction.find_elem_by(web_element=driver, value_str=xpath, how='finds')[postition]
        driver.execute_script("arguments[0].scrollIntoView();", new_element)
        Message.sleep_time(delay, 'scrolling to element, wait for render')

    def find_elem_by(web_element: object, value_str: str, how: str='find', by='xpath')-> object:
        '''find element by tags

        :param - `web_element` <object>: webdriver element object to action find
        :param - `value_str` <str>: passing value string to find data following `by` args.
        :param - `how` <str>: to select find one or all in [find|finds], default='find'
        :param - `by` <str>: by tags in ["id", "xpath", "link_text", "partial_link_text", "name", "tag_name", "class_name", "css"]
        '''
        try:
            how_way = {
                    'find': web_element.find_element, 
                    'finds': web_element.find_elements
                }
            element = how_way[how](by=WebdriverAction.select_by[by], value=value_str)
        except Exception as e:
            if how=='find':
                return None
            else:
                return []
        else:
            return element

    def extract_switch_tabpage(driver: webdriver, switch_url: str, func: object)-> str:
        '''action function in new tabpage
        open new tag and switch to window to extract passing function & return result
        
        :param - `driver` <webdriver>: action webdriver object
        :param - `switch_url` <str>: target url to open in new tab page
        :param - `func` <object>: action function and return result after open new tab page
        '''
        result = None

        try:
            # open new tab
            driver.execute_script('window.open()')

            # switch tab
            driver.switch_to.window(driver.window_handles[-1])
            
            # get page
            driver.get(switch_url)

            # wait for render page
            Message.sleep_time(5, 'switch page wait for render')

            # extarct data
            result = func(driver=driver)

        except Exception as e:
            err_mssg = traceback.format_exc()
            print(err_mssg)
            WebdriverAction.log.error(err_mssg)
            return result
        else:
            return result
            
        finally:
            # close tab
            driver.close()

            # back to main tab
            driver.switch_to.window(driver.window_handles[-1])

    def click_element(driver: webdriver, web_element: object, delay_seconds: int=1, js_click: bool=False)-> None:
        '''click element
        
        :param - `driver` <webdriver>: action webdriver object
        :param - `web_element` <object>: webdriver element object to action click
        :param - `delay_seconds` <int>: wait for seconds after click
        :param - `js_click` <book>: use javascript script to click or web_element
        '''
        if js_click:
            driver.execute_script('arguments[0].click();', web_element)
        else:
            web_element.click()
        sleep(delay_seconds)

    def window_height(driver: webdriver)-> int:
        '''show window height
        return `height`

        :param - `driver` <webdriver>: action webdriver object
        '''
        return driver.execute_script("return document.body.scrollHeight")

    def wait_element_show_by(driver: webdriver, delay_seconds: int, value_str: str, by: str='xpath')-> None:
        '''wait_element_show_by
        wait for `delay_seconds` element show
        
        :param - `driver` <webdriver>: action webdriver object
        :param - `value_str` <str>: passing value string to find data following `by` args.
        :param - `by` <str>: by tags in ["id", "xpath", "link_text", "partial_link_text", "name", "tag_name", "class_name", "css"]
        '''
        WebDriverWait(driver, delay_seconds).until(
                    EC.presence_of_element_located((WebdriverAction.select_by[by], value_str))
                )

    def scroll_to_end(driver: webdriver)-> None:
        '''scroll_to_end
        infinity loop to window size not increase
        
        :param - `driver` <webdriver>: action webdriver object
        '''
        scrolling_times = 0
        scrolling_next = True
        delay_time  = 7
        delay_limit = 15
        while scrolling_next:
            last_height = WebdriverAction.window_height(driver=driver)
            driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
            scrolling_times+=1

            if (scrolling_times % 10) == 0:
                Message.sleep_time(delay_time+15, custom_message='reach 10 times start sleep')

            if (scrolling_times% 30) == 0 and delay_time< delay_limit:
                delay_time += 5
            
            Message.sleep_time(delay_time, custom_message='scroll down, wait for render')
            new_height = WebdriverAction.window_height(driver=driver)
            if last_height == new_height:
                Message.splitline('[DriverAction]scroll_to_end', 'end of page , no more new data')
                scrolling_next = False

    def loading_cookies(driver: webdriver, cookies: list)-> bool:
        '''loading cookies into driver

        :param - `driver` <webdriver>: action webdriver object
        :param - `cookies` <list[dict]>: passing list[dict] cookies data
        '''
        Message.splitline('[WebdrvierAction] Loading Cookies', 'Start Loading Cookies')
        for cookie in cookies:
            driver.add_cookie(cookie)
        print('Finish Loading cookies into driver')

    def update_cookies(driver: webdriver, filepath: str):
        '''`driver.cookies` saving to filepath cookies file

        :param - `driver` <webdriver>: action webdriver object
        :param - `filepath` <str>: saving driver cookies to filepath
        '''
        Message.splitline('[WebdrvierAction] Update Cookies', 'Start Update Cookies')
        Files_Actions.toPickle(output_data=driver.get_cookies(), filepath=filepath)
        print(f'Finish Update Cookie Files: {filepath}')

    def send_keys(web_element: object, input_data: str, delay: float|int=.3):
        '''send key into web_element
        
        :param - `web_element` <object>: webdriver element object to action click
        :param - `input_data` <str>: input string data to web_element
        :param - `delay` <float| int>: sleep second after actions
        '''
        web_element.clear()
        web_element.send_keys(input_data)
        sleep(delay)

    def get_element_properties(driver: webdriver, web_element: object)-> object:
        '''get all properties data from web_elemnt
        
        :param - `driver` <webdriver>: action webdriver object
        :param - `web_element` <object>: webdriver element object to get properties
        '''
        java_script_code = 'var items = {}; for (index = 0; index < arguments[0].attributes.length; ++index)\
            { items[arguments[0].attributes[index].name] = arguments[0].attributes[index].value }; return items;'
        return driver.execute_script(java_script_code, web_element)

class ResponseProcess:
    def decode_body(response_body: object) ->str:
        '''decode selenium wire response body
        
        :param - `response_body` <object>: passing seleniumwire response object
        '''
        return decode(response_body.body, response_body.headers.get('Content-Encoding', 'identity')).decode('utf-8')


class Authentication:
    def fetch_auth_key(auth_key: str)-> str:
        '''auth key get passcode
        
        :param - `auth_key` <str>: passing two-factor access token key to get passcode
        - return `passcode`
        '''
        Message.splitline('[Authentication] Fetch key', 'Start Fetch Authenticator key')
        auth_client = pyotp.TOTP(auth_key)
        time_remaining = auth_client.interval - datetime.now().timestamp() % auth_client.interval
        if time_remaining< 7:
            Message.sleep_time(
                seconds=time_remaining, 
                custom_message=f'auth_key expire in: {time_remaining}, wait for next key'
            )            
        return auth_client.now()