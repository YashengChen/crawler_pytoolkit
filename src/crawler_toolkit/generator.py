import os
import re
import json
import string
import random
import requests
import pandas as pd
from scrapy import Selector
from datetime import date, datetime, timedelta

class FakeIdentity:
    ROOT_PATH = os.path.dirname(__file__)
    ZH_DATA_SOURCE = os.path.join(ROOT_PATH, 'source', 'zh_data')
    EN_DATA_SOURCE = os.path.join(ROOT_PATH, 'source', 'en_data')

    def en_name(gender: str):
        '''random init english name by gender
        
        :param - `gender` <str>: passing gender to init name, ["male", "female"]
        '''
        with open(os.path.join(FakeIdentity.EN_DATA_SOURCE, 'en_name.json'), 'r') as f:
            en_data_source = json.load(f)
        last_name = random.choice(en_data_source['lastname']).lower()
        first_name = random.choice(en_data_source[gender]).lower()
        return {
            'name': ', '.join([first_name , last_name]),
            'last_name' : last_name,
            'first_name' : first_name,
            'gender': gender
        }

    def cn_name()-> dict:
        '''random init chinese name
        '''
        result = dict()
        lastname_file = pd.read_json(os.path.join(FakeIdentity.ZH_DATA_SOURCE, 'lastname.json'))
        lastname_file = lastname_file.rename(columns={i:'LastName_'+i for i in lastname_file.columns})
        givename_file = pd.read_json(os.path.join(FakeIdentity.ZH_DATA_SOURCE, 'givename.json'))
        givename_file = givename_file.rename(columns={i:'GiveName_'+i for i in givename_file.columns})
        lastname = random.choice(lastname_file.to_dict('records'))
        givename = random.choice(givename_file.to_dict('records'))
        result.update(lastname)
        result.update(givename)
        return result

    def address()-> dict:
        '''random init taiwan address in zh & en
        '''
        city_info = pd.read_json(os.path.join(FakeIdentity.ZH_DATA_SOURCE, 'city.json'))
        street_name = pd.read_json(os.path.join(FakeIdentity.ZH_DATA_SOURCE, 'road.json'))
        street = {'zh_name': None, 'en_name': None}
        city = random.choice(city_info.to_dict('records'))
        road_of_city = street_name[street_name['site_id'] == (city['zh_city']+ city['zh_dist'])]
        if not road_of_city.empty:
            street = random.choice(road_of_city.to_dict('records'))
        nums = random.choice(range(1, 100))
        
        zh_address = ', '.join([city.get('zh_city',''), f"{city.get('zh_dist', '')} {street.get('zh_name','')} {nums}號"])
        en_address = ', '.join([f'No. {nums}', f"{street.get('en_name','')}, {city.get('en_dist','')}, {city.get('en_city','')}"])
        return {
            'address_zh' : re.sub('None', '', zh_address),
            'address_en' : re.sub('None', '', en_address),
        }

    def experience(age: int, birthdate: str, address: str=None)-> dict:
        '''random college & company experience
        '''
        result = {
            'CollegeName': None,
            'Department' : None,
            'CollegeTimeRange': None,
            'CompanyName' : None,
            'CompanyAddress': None,
            'WorkTimeRange': None,
        }
        cmpy = pd.DataFrame()
        college = pd.read_json(os.path.join(FakeIdentity.ZH_DATA_SOURCE, 'tw_college.json'))
        cmpy_json = pd.read_json(os.path.join(FakeIdentity.ZH_DATA_SOURCE, 'tw_company.json'))

        college =random.choice(college.to_dict('records')) if age >=18 else None
        if college:
            age18 = datetime.strptime(birthdate, '%Y-%m-%d') + timedelta(days=365*18)
            school_startyear = age18.year+1 if age18.month>9 else age18.year
            school_endyear = f'~{school_startyear+4}-06' if date.today().year - school_startyear >=4 else ''
            result.update({
                'CollegeName' : college.get('name_zh'),
                'Department'  : college.get('department_name'),
                'CollegeTimeRange': f'{school_startyear}-09{school_endyear}',
            })

            if address:
                cmpy = cmpy_json[cmpy_json['address'].str.match(f'{address}')]
            if cmpy.empty:
                cmpy = cmpy_json
            cmpy = random.choice(cmpy.to_dict('records')) if age > 22 else None

            if cmpy and school_endyear != '':
                cmp_startyear = school_startyear+5
                result.update({
                    'CompanyName' : cmpy.get('company_name'),
                    'CompanyAddress': cmpy.get('address'),
                    'WorkTimeRange': str(date.today().replace(year=cmp_startyear)),
                })

        return result

    def user(start_age: int=15, end_age: int=45):
        '''init user from range(`start_age` to `end_age`)
        return user with name age gender birthdate account name and address
        '''

        name_object = FakeIdentity.cn_name()
        age = random.choice(range(start_age, end_age))
        dateborn = random.choice(range(365))
        birthdate = date.today() - timedelta(days=age*365) - timedelta(days=dateborn)
        birthdate = str(birthdate)
        random_nums= birthdate.split('-')[-1] + str(random.choice(range(99)))

        zh_name = name_object.get(f'LastName_Character') + name_object.get(f'GiveName_Character')
        en_name = ','.join([name_object.get(f'LastName_English'),name_object.get(f'GiveName_English')])
        account_name = re.sub(',|-','',en_name) + random_nums

        address = FakeIdentity.address()
        adderss_dist = address.get('address_zh').split(',')[0]
        experience = FakeIdentity.experience(age=age, birthdate=birthdate, address=adderss_dist) 

        user = {
                'Name_zh': zh_name,
                'Name_en': en_name,
                'Age': age,
                'Gender'  : name_object.get(f'GiveName_Gender'),
                'BirthDate': birthdate,
                'AccountName' : account_name.lower(),
                'Address_zh': address.get('address_zh'),
                'Address_en': address.get('address_en')
            }

        if experience:
            user.update(experience)
        return user

    def account(nickname: str,  with_nums=True)-> str:
        '''random init account by nickname
        
        :param - nickname <str>: passing english nick name to init account
        :param - with_nums <bool>: account with number, default=True
        '''
        ran_nums_char = random.choice(range(4)) or 2
        ran_char = ''.join(random.choices(string.ascii_lowercase, k=ran_nums_char))
        create_list = [nickname, ran_char]
        if with_nums:
            ran_nums = ''.join(random.choices(string.digits, k=ran_nums_char))
            create_list = [nickname, ran_char, ran_nums]
        return ''.join(create_list)

    def password()-> str:
        '''random init password
        '''
        password_length = len(string.ascii_lowercase)
        half_length = password_length //3
        lower = string.ascii_lowercase
        upper = string.ascii_uppercase
        num = string.digits
        charater = ''.join([lower , upper])
        charater = random.sample(lower , half_length + password_length % 3)
        charater += random.sample(upper , half_length )
        charater += random.sample(num , half_length)
        temp = random.sample(charater , password_length)
        return ''.join(temp)


class UserAgent:
    def get_latest(browser: str)-> dict:
        '''scrape select browser  list dictionary useragent object 
        
        :param - `browser` <str>: passing browser which want to scrape
        '''
        total_data = pd.DataFrame()
        target_url = f'https://www.whatismybrowser.com/guides/the-latest-user-agent/{browser}'

        r = requests.get(target_url)
        page_source = Selector(text=r.text)
        total_tag = page_source.xpath('.//section[contains(@class, "section-block-main-extra")]/div/div[@class="content-block-main"]/*')
        for idx, tag in enumerate(total_tag):
            if tag.xpath('self::table[contains(@class, "listing-of-useragents")]'):
                title = total_tag[idx-1].xpath('text()').get()
                table_df = pd.read_html(total_tag[idx].get())[0]
                table_df.columns = ['Platform', 'User_Agent']
                table_df['Browser'] = browser
                table_df['System'] = title

                total_data = pd.concat([total_data, table_df])
        return total_data.to_dict(orient='records')

    def browser_list()-> list[str]:
        '''return list browser scrape options
        
        '''
        return ['chrome', 'firefox', 'safari', 'internet-explorer', 'edge', 'opera', 'vivaldi', 'yandex-browser']