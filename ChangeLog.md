# Change Log: crawker_toolkit
###### tags: `ChangeLog`, `python-package`

### `2023-05-02` **v0.0.8**: 
- **mailserver.GmailServer**
    - add:
        - `set_images()`
- **share_module.Message**
    - update:
        - `sleeptime()`: only accept int or float
- update Descriptions:
    - generator.py 
    - mailserver.py
    - share_module.py
    - tor_controller.py

### `2023-04-26` **v0.0.7a0** hotfix: output_data.mongodb_actions
- **`MongoDB_Actions`**
    - fixed: 
        - remove print(error) and write to log
        - mongodb_action.retrieve add args how to select find_all or find_one
- **`mailserver`**
     - add:
         - mailserver add function description
         - `GMailServer.mail_prepare`: accept str or list mails will prepare object that can send by mailserver
- **`TempDataSet`**
    - refactor
        - replace name from `DuplicateFilter` to `TempDataSet`
        - `self.is_duplicate`: rename passing argument `url`> `unique_val`


### `2023-04-18` **v0.0.7** feature: **refactor output_data**
- **`MssqlActions`**
    - add:
        - __repr__, __str__
        - functions: `syntax_query`, `drop_table`, `check_connection`
        - refactor: create for single and multiple data insert
        - all function description
        - unittest for mssql_actions : tests/mssql_action.py
    - fixed:
        - rename func retreive > retrieve
        - create_all merge with create
        - update remove update UpdatedTime
        - delete remove update DeteltedTime
        - rename _create_connection_url > create_connection_url
        - create_connection_url to classmethod > staticmethod
- **`SolrActions`**
    - add:
        - __repr__, __str__
        - function: `check_connection`
        - unittest for solr_actions : tests/solr_actions.py
    - update:
        - all function description
- **`FileActions`**
    - add:
        - unittest for file_acitons : tests/file-actions.py
        - all function description
    - fixed:
        - toPickle & LoadPicke not close
- **`MongoActions`**
    - add:
        - __repr__, __str__, check_connection, create, update, delelte, drop_colleciton
        - unittest for solr_actions : tests/mongodb_actions.py
    - update:
        - all function description
        - rename `retreive` > `retrieve`
        - rename `create_update_exist` > `upsert`

### `2023-01-31` **v0.0.6**
- add:
    - **webdriver_action.init_driver** args:
        - `use_driver`: str=add "remote" options
        - `remote_driver`: str=passing remote driver use name: "firefox", "chrome", "edge"
        - `set_preference`: dict=passing dictionary preference k,value, for this time passing tor socket information setup proxy
        - `seleniumwire_option` replace "proxy_dict": dict= proxy_dict passing into seleniumwire_option, and seleniumwire option more available args can use.
    - **tor_controller**:
        - `TorController.switch_ip`: passing tor ip:port and auth_password to control tor to change ip
    
### `2023-01-06` **v0.0.5**
- add:
    - **generator**
        - `FakeIdentity.user`: generator user `name_zh`, `name_en`, `age`, `birthdate`, `account_name`, `address_zh`, `address_en`
        - `FakeIdentity.password`: generator password with random charactor in `lower, upper, numbers`
        - `UserAgent.get_latest`: scrapy latest user agent in website
        - `UserAgent.browser_list`: show available browser.
    - **webdriver_action**
        - `WebdriverAction.send_keys`: webdriver input value into element
        - `WebdriverActions.get_element_properties`: return all property of tag element 
- update:
    - **output_data**
        - `Mssql_Actions.__row2dict` > `Mssql_Actions.row2dict`: open to use
- remove:
    - **webdriver_action**
        - `WebdriverActions.find_elem_xpath`: new version use `WebdriverActions.find_elem_by`
        

### `2022-12-27` **v0.0.4**
- add:
    - **output_data**
        - `Files_Actions.readPickle`: load pickle files from path
        - `Files_Actions.toPickle`: saving pickle files to path
- update:
    - **webdriver_action**
        - `WebdriverAction.loading_cookies`: split `pickle` loading function

### `2022-12-22` **v0.0.3~a2**
- add:
    - **mailserver**:
        - `GMailServer`: Send Mail By Gmailserver
    - **webdriver_action**: 
        - `WebdriverAction.load_cookies`: load pickle_files to webdriver
        - `WebdriverAction.update_cookies`: webdrvier update cookie to pickle_files
        - `WebdriverAction.fetch_auth_key`: fetch two-factor key
        - `WebdriverAction.find_element_by`: webdriver find element by multiple select option args.
        - `ResponseProcess.decode_body`: decode webdriver response
    - **share_module**:
        - `DataProcess.str2hash`
        - `ArgsTF_define`: `TF_define`, `cama_str2list`

### `2022-12-15` **v0.0.2.a**
- hotfix:
    - `output_data.MsSql_Action.create_all()`: IntegrityError loop stop
    - `webdriver_action.WebdriverAction.init_driver()`: headess and option not work
            
### `2022-11-14` **v0.0.2**
- add:
    - **share_module**:
        1. `DataProcess` dictionary nest_get function and chinese translate etc... funtion
        2. `ArgsDefine` to deal with cmd passing args
        3. `DuplicationFilter` put string value into tuple that check already use value return `T/F`
        4. `File_Action` add `readJson`, `updateJson`
        5. `File_Action.toJson` add args append to control data append or over write all files
- update:
    - **webdriver_action**:
        1. `WebdriverAction.init_driver` to init driver

### `2022-11-10` **v0.0.1**
init project
- add:
    1. **share_module**:
        - `LoggingSet` that setting logging for project
        - `Message` that provide to print an message with custom splitline & sleep time with message for webdriver waiting.
    2. **output_data**:
        - `File_Action` to output data to file
        - `MongoDB_Action` to output data to mongodb
        - `MsSQL_Actions` to output data to Sql server
        - `Solr_Action` to interact with wolr `Create(update if id exist), Retrieve, Delete`
    3. **webdriver_action**:
        - `WebdriverAction` to handle selenium webdriver 