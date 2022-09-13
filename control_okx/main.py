#import os
import json
import os.path
import time

#import time
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.events import EventFiringWebDriver, AbstractEventListener
from selenium.webdriver.support.wait import WebDriverWait
#from multiprocessing import Pool
from concurrent.futures import ThreadPoolExecutor
#from queue import Queue
import re
from kernel.base.base import *


class Main(BaseClass):
    __startMain = "https://www.okx.com/markets/prices"
    __exchangeDataFile = "exchangeData.list"
    __premium_grasp_listtmp_ = []
    __change_list_tick = []
    __categories_trade_list = []
    __trade_historical_mongodb = "list_trade_historical"
    __redis_trade_item_dict_pre = "list_okx_"

    # 标准化
    # """
    #
    # categories_trade_list =
    # scan_trade_tick_list =
    # trade_item_dict =
    # trade_historical_list =
    # trade_historical_list =
    #
    # """

    def __init__(self,argv):
        pass

    def main(self,argv):
        #TODO 测试数据库函数每个单元
        # self.set_trade_categories --ok--
        # self.init_trade_historical_list
        # self.get_trade_historical_list_pop
        # self.set_trade_historical_list
        # self.set_grasp_listtmp
        # self.load_trade_historical
        # self.save_okx_exchange_rise
        # 另外需测试db_common函数中对于不存在的表返回类型是否为None

        #TODO
        # 首先从数据库中读取100条数据
        # 如果数据过旧，超过3天则没有参考价值，直接不作为对比，而直接添加
        # 如果数据在3天以前，则可以不以上一个tick为比较
        # 每个tick对比上一轮数据，有变化则加入缓存
        # 缓存中根据游标显示读到多少数据，小于1000则再从数据库中读1000条（旧的数据），大于1则读取最新数据填充（以读取的数量+上当前游标确定游标）
        # from urllib.parse import urlparse
        # up = urlparse("http://www.jqueryfuns.com/texiao/test")



        # ../resource/5733/0.jpg
        self.http_common.web_down("http://www.jqueryfuns.com")
        # self.selenium_common.down_website("http://www.jqueryfuns.com")
        # self.init_driver_local_test("index.html")
        # self.init_driver(self.__startMain)
        # self.start_thread_for_scan_trade_tick_list(click=False)
        # js_path = self.selenium_common.execute_js(self.__driver,"jquery-3.6.0.min.js")
        pass



    def init_driver_local_test(self,html_name="index.html"):
        self.__driver = self.selenium_common.open_local_html_to_beautifulsoup(html_name)

    def init_driver(self,url=None):
        self.__driver = self.selenium_common.get_empty_driver()
        # self.__driver = EventFiringWebDriver(self.__driver, PremiumChange())
        self.__driver = self.selenium_common.open_url(url,empty_driver=False)

    def start_thread_for_scan_trade_tick_list(self,click=True):
        #等待元素出现
        self.wait_and_find_data_token_names(click)
        #初始化历史数据列表，如果有的话。如果没有则等到开始抓取
        self.init_trade_historical_list()
        thread_pool = ThreadPoolExecutor(max_workers=1)
        thread_runIndes = 0
        change_task_test =[]
        thread_time = time.thread_time()
        while True:
            if len(change_task_test) == 0:
                thread_name=f"scratch-tread-{thread_runIndes}"
                save_to_mangodb = (thread_runIndes % 3  == 0)
                print( f" New tick {thread_name}/ thread_time:{thread_time}/ save to mangoDB:{save_to_mangodb} running.")
                change_task_test.append(
                    (
                        thread_name,
                        save_to_mangodb,
                        thread_time
                    )
                )
            task = thread_pool.submit(self.get_change_run, change_task_test.pop())
            thread_runIndes += 1
            task.result()

    def get_change_run(self,data):
        thread_name = data[0]
        is_serialize = data[1]
        thread_time = data[2]
        scan_trade_tick_list = self.scan_trade_tick_list()
        self.set_trade_categories(scan_trade_tick_list)
        for trade_item_dict in scan_trade_tick_list:
            short_name = trade_item_dict["short_name"]
            #获取一个历史数据，该历史数据包含一该类型项的一次完整的抓取
            grasp_historical_pop = self.get_trade_historical_list_pop(short_name)
            is_rise_changed = self.trade_rise_is_change(trade_item_dict,grasp_historical_pop)
            if is_rise_changed:
                self.set_trade_historical_list(short_name,trade_item_dict)
        if is_serialize : self.save_okx_exchange_rise()
        print(f"Count for change premium data are {len(self.__premium_grasp_listtmp_)} items." )
        return True

    def is_beautifulsoup(self):
        if self.__driver.__class__.__name__.__eq__("BeautifulSoup"):
            return True
        else:
            return False

    def wait_and_find_data_token_names(self,click=False):
        is_beautifulsoup = self.is_beautifulsoup()
        if  is_beautifulsoup is not True:
            WebDriverWait(self.__driver, 0).until(EC.presence_of_element_located( (By.CSS_SELECTOR, '''[data-token-name]''') ))
        if click:
            change_click = self.selenium_common.find_text_from(self.__driver, "//*[@data-clk]", "Change")
            change_click.click()
        if self.__allPremium == None:
            # self.__allPremium = self.__driver.find_elements(By.XPATH,'//*[@data-token-name|@data-id]')
            self.__allPremium = self.selenium_common.find_elements(self.__driver,'//*[@data-token-name|@data-id]')
        return self.__allPremium

    def trade_rise_is_change(self,tick_scratch_data,grasp_historical_pop):
        print(tick_scratch_data,grasp_historical_pop)
        tick_short_name = tick_scratch_data['short_name']
        historical_pop_short_name = grasp_historical_pop['short_name']
        tick_change = tick_scratch_data['change']
        historical_pop_change = grasp_historical_pop['change']
        is_likely_type = tick_short_name.__eq__(historical_pop_short_name)
        is_rise_changed = (tick_change != historical_pop_change)
        is_rise_changed = (is_likely_type and is_rise_changed)
        if is_rise_changed:
            primitive_price = tick_scratch_data["primitive_price"]
            last_num = tick_scratch_data["last_num"]
            print(f"Changing massage : {tick_short_name} is changed! price:({primitive_price}->{last_num}) {historical_pop_change}:( to {tick_change})")
        return is_rise_changed

    def scan_trade_tick_list(self):
        scan_trade_tick_list = []
        allPremium = self.__allPremium
        print( len(allPremium) )
        for ele in allPremium:
            print( ele.text)
            coin_infos = ele.text.split("\n")
            short_name = coin_infos[0]
            full_name = coin_infos[1]
            last_num = coin_infos[2]
            last_price_num = float(last_num[1:].replace(r",", ""))
            change_partial = coin_infos[3].split(" ")
            change = change_partial[0]
            change_sign = change[0]
            change_number = float(change[1:-1])
            if change_sign == "+":
                primitive_price = last_price_num / (1 + change_number / 100)
            elif change_sign == "-":
                primitive_price = last_price_num * (1 - change_number)
            market_cap = change_partial[1]
            c_time = time.strftime("%Y-%m-%d %H:%m:%S",time.gmtime())
            scan_trade_tick_list.append(
                {
                    "short_name": short_name,
                    "full_name": full_name,
                    "last_num": last_num,
                    "last_price_num": last_price_num,
                    "change_sign": change_sign,
                    "change": change,
                    "primitive_price": primitive_price,
                    "market_cap": market_cap,
                    "time": c_time,
                    "save_db": False
                }
            )
        return scan_trade_tick_list

    def tran_trade_categories(self,rise_tick_datas=None):
        categories = []
        if rise_tick_datas != None:
            rise_tick_datas = [str(x["short_name"]) for x in rise_tick_datas]
            for short_name in rise_tick_datas:
                categories.append(short_name)
        return categories


    def set_trade_categories(self,rise_tick_datas=None,sava_to_mongodb=False):
        daname = "list_trade_categories"
        mongodb_daname = "okx_list_trade_categories"
        categories = self.db_common.get_redis(daname)
        if rise_tick_datas == None:
            #如果redis没有缓存项目类的数据，则从mongodb读取
            if len(categories) == 0:
                categories = self.db_common.read_data_to(mongodb_daname,{})
                #从mongodb读取的数据并存入 redis.
                self.db_common.set_redis({
                    daname: categories
                })
        else:
            tick_categories = self.tran_trade_categories(rise_tick_datas)
            is_new_type_itme = False
            for short_name in tick_categories:
                if short_name not in categories:
                    is_new_type_itme = True
                    categories.append(short_name)
                    self.new_type_item(short_name,rise_tick_datas)
            if is_new_type_itme:
                self.db_common.set_redis({
                    daname: categories
                })
        self.__categories_trade_list = categories
        return categories

    def new_type_item(self,short_name,rise_tick_datas):
        for tick_data in rise_tick_datas:
            if short_name in tick_data:
                new_type_name = tick_data[short_name]
                print(f'new typeItem {new_type_name}')
                #TODO 发现新元素后的操作写在这里。
        pass


    def init_trade_historical_list(self):
        print("init trade historical list!")
        categories = self.set_trade_categories()
        if len(categories) == 0:
            scan_trade_tick_list = self.scan_trade_tick_list()
            categories = self.set_trade_categories(scan_trade_tick_list)
            print("categories",categories)
        for short_name in categories:
            if len(self.get_trade_historical_list(short_name)) == 0:
                all_premium_grasp_dict = self.load_trade_historical(max=1000)
                print(type(all_premium_grasp_dict))
                for trade_name,tick_scratch_list in all_premium_grasp_dict.items():
                    self.set_trade_historical_list(trade_name,tick_scratch_list)

    def get_trade_historical_list_pop(self,short_name): # trade_historical_list
        redis_name = self.get_redis_trade_historical_list_name(short_name)
        type_list = self.db_common.get_redis(redis_name,[0,0])
        print(f"get_trade_historical_list_pop {type(type_list)}{len(type_list)}")
        type_list = json.loads(type_list)
        print(f"get_trade_historical_list_pop {type(type_list)}{len(type_list)}")
        return type_list
    def get_trade_historical_list(self,short_name,pop=[0,-1]):
        redis_name = self.get_redis_trade_historical_list_name(short_name)
        type_list = self.db_common.get_redis(redis_name,pop)
        if type(type_list) == str:
            type_list = json.loads(type_list)
        return type_list
    def set_trade_historical_list(self,trade_name,tick_scratch_list):
        redis_name = self.get_redis_trade_historical_list_name(trade_name)
        self.db_common.set_redis({
            redis_name:json.dumps(tick_scratch_list)
        })
    def get_redis_trade_historical_list_name(self,short_name):
        return f"{self.__redis_trade_item_dict_pre}{short_name}"

    def load_trade_historical(self,max=1000,short_name=None):
        print( " load_okx_exchange_rise is exec .~")
        collection_name = self.__trade_historical_mongodb
        datas = []
        scan_trade_tick_list = self.scan_trade_tick_list()
        if self.__save_project_as_mongodb:
            if short_name != None:
                data = self.db_common.read_data_to(collection_name,{
                    "short_name":short_name,
                    "limit": max
                })
                datas = data
            else:
                #使用mongodb存储
                for trade_item_dict in scan_trade_tick_list:
                    short_name = trade_item_dict["short_name"]
                    data = self.db_common.read_data_to(collection_name,{
                        "short_name":short_name,
                        "limit": max
                    })
                    datas += data
        else:
            #使用本地文件序列化
            datas = self.db_common.unserialization(self.__exchangeDataFile)
            if datas == None:
                datas = []
        premium_grasp_list = {}
        for data in datas:
            short_name = data["short_name"]
            if premium_grasp_list.get(short_name) == None:
                premium_grasp_list[short_name] = []
            premium_grasp_list[short_name].append(data)
        return premium_grasp_list

    def categories_rise_sort(self,lg="%7"):
        """
        对可交易项目进行幅度排序。
        :param lg:
        :return:
        """
        lg = lg[1:]
        lg = float(lg)
        short_list = []
        trade_categories = self.__categories_trade_list
        for short_name in trade_categories:
            trade_info = self.get_trade_historical_list_pop(short_name)
            if trade_info["change"] >= lg : short_list.append(trade_info)
        short_list.sort(key = lambda x : x["change"], reverse = True)
        return short_list

    def monitor_trade_rises(self):
        categories_rise_sort = self.categories_rise_sort("%7")
        #调用多线程打开监控页面
        max_workers = len(categories_rise_sort)
        # categories_rise_sort = [(cate) for cate in categories_rise_sort]
        with ThreadPoolExecutor(max_workers=max_workers) as pool:
            pool.submit(self.oversee_trade_data,categories_rise_sort)



    def oversee_trade_data(self, category_rise):
        short_name = category_rise["short_name"]
        short_name = short_name.lower()
        trade_spot_url = f"https://www.okx.com/trade-spot/{short_name}-usdt"
        driver = self.selenium_common.open_url(trade_spot_url, empty_driver=True)

        while category_rise["change"] > 7:
            self.selenium_common.execute_js(driver,"monitor_trade_data.js")
        return True

    def save_okx_exchange_rise(self):
        #提取未保存数据
        grasp_listtmp = self.set_grasp_listtmp()
        #设置保存标志位
        for item in grasp_listtmp:
            item["save_db"] = True

        if self.__save_project_as_mongodb:
            #使用mongodb存储
            print( f"save_project_as_mongodb to {len(grasp_listtmp)} items.~")
            self.db_common.save_data_to("okx_exchange_rise",grasp_listtmp)
        else:
            #使用本地文件序列化
            print( f"db serialization to {len(grasp_listtmp)} items.~")
            obj = self.db_common.unserialization(self.__exchangeDataFile)
            if obj == None:
                obj = []
            obj = obj + grasp_listtmp
            self.db_common.serialization(obj, self.__exchangeDataFile)
        self.set_grasp_listtmp(clear=True)

    def rise_tick_data_pop(self,short_name):
        for c_tick in self.__change_list_tick:
            # 如果tick还没有添加,或者价格有变动,则压入tick并将上一次推入总数据列中.
            if c_tick["short_name"].__eq__(short_name):
                self.__change_list_tick.remove(c_tick)
                return c_tick
        return None

    def get_trade_link(self,item_name):
        return f"https://www.okx.com/trade-spot/{item_name}"

#----------------------------------------------------------------------------------------

class PremiumChange(AbstractEventListener):
    def before_change_value_of(self,element, driver):
        print(element)
        print("price change!")


#
#
#
#
#
# # import os
# import json
# # import os.path
# import time
#
# from kernel.base.base import *
# # import time
# from selenium.webdriver.common.by import By
# from selenium.webdriver.support import expected_conditions as EC
# from selenium.webdriver.support.events import EventFiringWebDriver, AbstractEventListener
# from selenium.webdriver.support.wait import WebDriverWait
# # from multiprocessing import Pool
# from concurrent.futures import ThreadPoolExecutor
# # from queue import Queue
# import re
# # from multiprocessing import Process
# from flask import Flask, url_for, render_template
# from flask import request as flask_request
# from kernel.base.load_module_class import *
# import mimerender
# from multiprocessing import Process, Pipe
# import pprint
#
# #
# # from twisted.web import proxy, http
# # from twisted.internet import reactor
# # from twisted.python import log
# # import sys
# # #
# # # log.startLogging(sys.stdout)
# # #
#
# mimerender = mimerender.FlaskMimeRender()
# flask_app = Flask(__name__)
# app_self = None
#
#
# class B2Bworkbaidu(BaseClass):
#     __isRedis = True
#     __exchangeDataFile = "exchangeData.list"
#     __premium_grasp_listtmp_ = []
#     __change_list_tick = []
#     __categories_trade_list = []
#     __trade_historical_mongodb = "list_trade_historical"
#     __redis_trade_item_dict_pre = "list_okx_"
#     __config = None
#     __driver = None
#
#     # 标准化
#     # categories_trade_list =
#     # scan_trade_tick_list =
#     # trade_item_dict =
#     # trade_historical_list =
#     # trade_historical_list =
#     #
#     # """
#
#     def __init__(self, argv):
#         global app_self
#         app_self = self
#         # self.selenium_common.create_single(self)
#         pass
#
#     def main(self, argv):
#         # # test
#         # self.thread_common.create_thread(
#         #     target=self.down_file,
#         #     args=(),
#         #     thread_name="fdsafas"
#         # )
#         # return
#
#         #self.multi_account_broser_create()
#         # with ThreadPoolExecutor(max_workers=1) as pool:
#         #     pool.submit(self.network_list)
#         # pass
#         network_th = self.thread_common.create_thread(thread_type="common",target=self.network_list)
#         network_th.start()
#
#     @flask_app.route('/add_account')
#     def add_account():
#         self = app_self
#         user = flask_request.args.get('user')
#         pwd = flask_request.args.get('pwd')
#         if user is None or pwd is None:
#             return {
#                 "type":"000",
#                 "message":"要添加的账号或密码不能为空。"
#             }
#         loginUser = self.get_account(user)
#         if loginUser != None:
#             return {
#                 "type":"00",
#                 "message":"账号已经存在，不能再添加。请修改。"
#             }
#         self.add_account_to_account((
#             user,pwd
#         ))
#         return {
#                 "type":"0",
#                 "message":"账号添加成功，请刷新网页。"
#             }
#
#     @flask_app.route('/api_manager')
#     # @mimerender(
#     #     default = 'html',
#     #     xml=lambda message: '<message>%s</message>' % message,
#     #     json = lambda message: json.dumps(message),
#     #     html = lambda message: message,
#     #     txt = lambda message: message
#     # )
#     def login_manager():
#         url_for("static", filename="css/style.css", )
#         self = app_self
#         accounts = self.db_common.unserialization(self.get_account_serialization_file())
#         if accounts == None:
#             accounts = []
#         manager_data = {}
#         manager_data["accounts_list"] = []
#         not_login = 0
#         data_fields = self.get_config("data_fields")
#
#         for data in data_fields:
#             datatype = data["datatype"]
#             description = data["description"]
#             # {
#             #     "datatype":datatype,
#             #     "description":description
#             # }
#         # datatype
#         for account in accounts:
#             loginUser = account["login"]["loginUser"]
#             th = self.thread_common.get_thread(loginUser)
#             if th == None:
#                 th = self.account_browser_thread_create(loginUser)
#                 time.sleep(5)
#             is_login = th.login_check()
#             if not is_login:
#                 not_login += 1
#             manager_data["accounts_list"].append({
#                 "username": loginUser,
#                 "islogin": is_login,
#             })
#         manager_data["not_login"] = not_login
#         return render_template("manager.html", manager_data=manager_data)
#
#     @flask_app.route('/get_login_verify')
#     def get_login_verify():
#         self = app_self
#         x_offset = flask_request.args.get('x_offset')
#         username = flask_request.args.get('username')
#         print(f"username is {username}")
#         code_verify = flask_request.args.get('code_verify')
#         th = self.thread_common.get_thread(username)
#         resule = {}
#         if x_offset is not None:
#             y_offset = flask_request.args.get('y_offset')
#             x_offset = int(x_offset)
#             y_offset = int(y_offset)
#             print(f" x_offset {x_offset} y_offset {y_offset}")
#             th.login_click(x_offset, y_offset)
#             time.sleep(5)
#             is_login = th.login_check()
#             if is_login:
#                 resule["type"] = "success"
#                 resule["message"] = "初始化成功,该接口可以正常请求但请不要随意重启服务器"
#                 return resule
#             else:
#                 resule["type"] = "null"
#                 resule["message"] = "请重试."
#                 return resule
#         elif code_verify is not None:
#             th.login_click(code_verify = code_verify)
#             time.sleep(5)
#             result = th.get_login_verify_html()
#             return result
#         else:
#             result = th.get_login_verify_html()
#             return result
#
#     @flask_app.route('/api')
#     def api():
#         # 使用类加载器对类附加新类
#         # 用于第三方调用接口时没有附加方法的问题
#         self = app_self
#         method = flask_request.args.get('method')
#         datatypes = flask_request.args.get('datatypes')
#         username = flask_request.args.get('username')
#         password = flask_request.args.get('password')
#         th = self.thread_common.get_thread(username)
#         if username == None:
#             data = {
#                 "message": "no username",
#                 "type": None
#             }
#             return data
#         if datatypes == None:
#             data = {
#                 "message": "no datatypes",
#                 "type": None
#             }
#             return data
#         data = th.get_data({
#             "method": method,
#             "datatypes": datatypes
#         })
#         print(f"data{data}")
#         return data
#
#     def get_account_config(self, account_name, keys):
#         if type(keys) == str:
#             keys = [keys]
#         if self.__config["multiaccount_support"] == True:
#             multiaccount_datas = self.__config["multiaccount_datas"]
#             # 有多账号的时候从多账号中读配置
#             # 如果多账号没有配置则读总配置
#             # 账号单独配置覆盖主配置
#             account_config = None
#             print(f"account_name {account_name}")
#             for account in multiaccount_datas:
#                 print(f"account {account}")
#                 login = account["login"]
#                 if account_name == login["loginUser"]:
#                     account_config = account
#             if account_config == None:
#                 print(f"Not found account:{account_name} in multiaccount_datas in get_account_set.")
#                 return None
#             value_as_multiaccounts = None
#             value_as_config = None
#             value = None
#             for key in keys:
#                 exist_multiaccounts = True
#                 if value_as_multiaccounts == None:
#                     try:
#                         value_as_multiaccounts = account_config[key]
#                     except:
#                         exist_multiaccounts = False
#                 elif key in value_as_multiaccounts:
#                     value_as_multiaccounts = value_as_multiaccounts[key]
#                 else:
#                     exist_multiaccounts = False
#
#                 exist_config = True
#                 if value_as_config == None:
#                     value_as_config = self.__config[key]
#                 elif key in value_as_config:
#                     value_as_config = value_as_config[key]
#                 else:
#                     exist_config = False
#
#                 if exist_multiaccounts:
#                     value = value_as_multiaccounts
#                 elif exist_config:
#                     value = value_as_config
#                 else:
#                     print(f"key {key}")
#                     print(f"value_as_config {value_as_config}")
#                     value = None
#                     break
#             return value
#         else:
#             # 没有多账号直接从配置中读配置
#             if account_name == self.__config["loginUser"]:
#                 value = None
#                 for key in keys:
#                     if value == None:
#                         value = self.__config[key]
#                     else:
#                         value = value[key]
#                 return value
#             else:
#                 print(f"Not found account:{account_name} in self.__config['loginUser'] in get_account_set.")
#                 return None
#
#     def init_config(self):
#         config = {
#             # 多账号支持,会启动多线程多个浏览器, 设置在下面
#             # "multiaccount_support": True,
#             "login": {
#                 "mustLogin": True,  # 是否需要预登陆
#                 "isLogin": False,  # 是否已经登陆
#                 "active_check": False,  # 活动检查
#                 "loginURL": "https://b2bwork.baidu.com/login",
#                 "loginVerifyURL": "https://b2bwork.baidu.com/dashboard",
#
#                 # "loginUser": "zsw100023649",
#                 # "loginPwd": "Mts77066.",
#                 "userInput": """//*[@id="uc-common-account"]""",
#                 "pwdInput": """//*[@id="ucsl-password-edit"]""",
#                 "submit": "#submit-form",
#                 "login_active": {
#                     "active_url": "https://b2bwork.baidu.com/dashboard",
#                     "active_period": 60,
#                     "buttons": [
#                         """//*[@id="app"]/div/div[2]/div[1]/div[1]/div/ul/div[3]/li/ul/div[1]/a/li/span""",
#                         """//*[@id="app"]/div/div[2]/div[1]/div[1]/div/ul/div[1]/a/li/span"""
#                     ]
#                 },
#                 "login_pre": {
#                     "clicks": [".primary"]
#                 }
#             },
#             "data_fields": [
#                 {
#                     "datatype": "shop_score",
#                     "description": "店铺评分",
#                     "page": "https://b2bwork.baidu.com/dashboard",
#                     "datas_by_class": {
#                         "sentinel_selector": """//div[@class="shop-diagnose"]/p""",
#                         "datas": [
#                             {
#                                 "datatype": "shop_score",
#                                 "description": "店铺评分",
#                                 "selectors": [
#                                     {
#                                         "selector_names": "店铺评分",
#                                         "selector": ".shop-diagnose p"
#                                     }
#                                 ],
#                                 "attr": "value"
#                             }, {
#                                 "datatype": "commodity_management",
#                                 "description": "商品管理",
#                                 "selectors": [
#                                     {
#                                         "selector_names": "商品总数,交易商品,在售中,已下架,已驳回",
#                                         "selector": ".pm-data .item-data"
#                                     }
#                                 ],
#                                 "attr": "value"
#                             }
#                         ]
#                     }
#                 },
#                 {
#                     "datatype": "smart_business_opportunity",
#                     "description": "智慧商机",
#                     "page": "https://b2bwork.baidu.com/service/business/index?scrollTop=0",
#                     "datas_by_class": {
#                         "sentinel_selector": '//*[@class="el-tooltip"]',
#                         "datas": [
#                             {
#                                 "datatype": "core_data",
#                                 "description": "核心数据",
#                                 "selector": ".el-tooltip",
#                                 "selectors": [
#                                     {
#                                         "selector_names": "曝光量,点击量,访客数,电话量,表单量,IM数",
#                                         "selector": ".el-tooltip"
#                                     }
#                                 ],
#                                 "attr": "value"
#                             }
#                         ]
#                     }
#                 },
#
#             ],
#             "multiaccount_support": True,  # 多账号支持,会启动多线程多个浏览器
#             "multiaccount_datas":
#             # [  # 多账号的数据列表，设置会覆盖父一级的设置
#             # {
#             #     "login": {
#             #         "loginUser": "zsw100023649",
#             #         "loginPwd": "Mts77066."
#             #     },
#             #     "data_fields": []
#             # }
#             # ],
#                 self.db_common.unserialization(self.get_account_serialization_file()),
#             # {
#             #     "login": {
#             #         "loginUser": "zsw100023649",
#             #         "loginPwd": "Mts77066."
#             #     },
#             #     "data_fields": []
#             # }
#         }
#         self.__config = config
#         return self.__config
#
#     def get_account(self,username):
#         multiaccount_datas = self.get_config("multiaccount_datas")
#         if multiaccount_datas == None:
#             return None
#         for account in multiaccount_datas:
#             login = account["login"]
#             loginUser = login["loginUser"]
#             if username == loginUser :
#                 return login
#         return None
#
#     def get_account_serialization_file(self):
#         return "b2bwork_baidu_account_data.txt"
#
#     def add_account_to_account(self, args):
#         if type(args) == tuple:
#             args = [args]
#         account_data = []
#         for account in args:
#             try:
#                 loginUser = account[0]
#                 loginPwd = account[1]
#             except:
#                 return None
#             try:
#                 data_fields = account[2]
#             except:
#                 data_fields = None
#             account_item = {
#                 "login": {
#                     "loginUser": loginUser,
#                     "loginPwd": loginPwd
#                 }
#             }
#             if data_fields != None:
#                 account_item["data_fields"] = data_fields
#             account_data.append(
#                 account_item
#             )
#         print(f"add_account_to_account {account_data}")
#         filename = self.get_account_serialization_file()
#         self.db_common.serialization(account_data, filename)
#         return self.init_config()
#
#     def get_config(self, account_name=None, keys=None):
#         if self.__config == None:
#             self.init_config()
#         # 只有account_name一项，用account_name代替key
#         if (account_name != None and keys == None) \
#                 or \
#                 (account_name == None and keys != None):
#             if account_name in self.__config:
#                 return self.__config[account_name]
#             else:
#                 print(f"Not found {account_name} in self.__config")
#                 return None
#         if account_name != None and keys != None:
#             return self.get_account_set(account_name, keys)
#         else:
#             return self.init_config()
#
#     def network_list(self,args):
#         port = self.config_common.get_global( 'flask_port')
#
#         print(f'startup Flask app server. Listing port is {port}')
#         flask_app.run(port=port, host="0.0.0.0")
#
#
#     def multi_account_broser_create(self):
#         self.account_browser_thread_create(allUsers=True)
#
#     def account_browser_thread_create(self,allUsers=True):
#         if type(allUsers) == str:
#             notAllLoginUser = allUsers
#         else:
#             notAllLoginUser = None
#         # self.add_account_to_account(("zsw100023649","Mts77066."))
#         multiaccount_support = self.get_config("multiaccount_support")
#         multiaccount_datas = self.get_config("multiaccount_datas")  # 本线程总支持的账号数
#         print(f"multiaccount_datas {multiaccount_datas}")
#         print(f"get_config {self.get_config()}")
#         config = {}
#         for config_k, config_v in self.__config.items():
#             config[config_k] = config_v
#         # print(f"multiaccount_datas",multiaccount_datas)
#         account_max_thread = 1
#         if multiaccount_support == True:
#             account_max_thread = len(multiaccount_datas)  # 最大支持的打开浏览器线程数为账号数
#         # account_max_thread += 1 #预留一个线程给网络监听使用
#
#         for id in range(account_max_thread):
#             account = multiaccount_datas[id]
#             # print(account)
#             login = account["login"]
#             loginUser = login["loginUser"]
#             if notAllLoginUser is not None and notAllLoginUser != loginUser:
#                 continue
#             # deep_key = []
#             for login_k, login_v in account.items():
#                 if type(login_v) == dict:
#                     for login_k_, login_v_ in login_v.items():
#                         if type(login_v_) == dict:
#                             for login_k__, login_v__ in login_v_.items():
#                                 if type(login_v__) == dict:
#                                     for login_k___, login_v___ in login_v__.items():
#                                         if type(login_v___) == dict:
#                                             for login_k____, login_v____ in login_v___.items():
#                                                 # deep_key.append(login_k____)
#                                                 config[login_k][login_k_][login_k__][login_k___][
#                                                     login_k____] = login_v____
#                                         else:
#                                             config[login_k][login_k_][login_k__][login_k___] = login_v___
#                                         # deep_key.append(login_k___)
#                                 else:
#                                     config[login_k][login_k_][login_k__] = login_v__
#                                 # deep_key.append(login_k__)
#                         else:
#                             config[login_k][login_k_] = login_v_
#                         # deep_key.append(login_k_)
#                 else:
#                     config[login_k] = login_v
#                 # deep_key.append(login_k)
#             # print(config)
#             #     # config[login_k] = login_v
#             # args = (config)
#             th = self.thread_common.create_thread(thread_type="selenium",thread_name=loginUser, args=config )
#             # th.set("__config",self.get_config())
#             th.start()
#         # th = self.selenium_multi_process_mode.create_thread(target=self.network_list, args=config,thread_name="network_list",)
#         # # th.set("__config",self.get_config())
#         # th.start()
#         return
#
#     def init_driver_local_test(self,html_name="index.html"):
#         self.__driver = self.selenium_common.open_local_html_to_beautifulsoup(html_name)
#
#
#     def start_thread_for_scan_trade_tick_list(self,click=True):
#         #等待元素出现
#         self.wait_and_find_data_token_names(click)
#         #初始化历史数据列表，如果有的话。如果没有则等到开始抓取
#         self.init_trade_historical_list()
#         thread_pool = ThreadPoolExecutor(max_workers=1)
#         thread_runIndes = 0
#         change_task_test =[]
#         thread_time = time.thread_time()
#         while True:
#             if len(change_task_test) == 0:
#                 thread_name=f"scratch-tread-{thread_runIndes}"
#                 save_to_mangodb = (thread_runIndes % 3  == 0)
#                 print( f" New tick {thread_name}/ thread_time:{thread_time}/ save to mangoDB:{save_to_mangodb} running.")
#                 change_task_test.append(
#                     (
#                         thread_name,
#                         save_to_mangodb,
#                         thread_time
#                     )
#                 )
#             task = thread_pool.submit(self.get_change_run, change_task_test.pop())
#             thread_runIndes += 1
#             task.result()
#
#     def get_change_run(self,data):
#         thread_name = data[0]
#         is_serialize = data[1]
#         thread_time = data[2]
#         scan_trade_tick_list = self.scan_trade_tick_list()
#         self.set_trade_categories(scan_trade_tick_list)
#         for trade_item_dict in scan_trade_tick_list:
#             short_name = trade_item_dict["short_name"]
#             #获取一个历史数据，该历史数据包含一该类型项的一次完整的抓取
#             grasp_historical_pop = self.get_trade_historical_list_pop(short_name)
#             is_rise_changed = self.trade_rise_is_change(trade_item_dict,grasp_historical_pop)
#             if is_rise_changed:
#                 self.set_trade_historical_list(short_name,trade_item_dict)
#         if is_serialize : self.save_okx_exchange_rise()
#         print(f"Count for change premium data are {len(self.__premium_grasp_listtmp_)} items." )
#         return True
#
#     def is_beautifulsoup(self):
#         if self.__driver.__class__.__name__.__eq__("BeautifulSoup"):
#             return True
#         else:
#             return False
#
#     def wait_and_find_data_token_names(self,click=False):
#         is_beautifulsoup = self.is_beautifulsoup()
#         if  is_beautifulsoup is not True:
#             WebDriverWait( 0).until(EC.presence_of_element_located( (By.CSS_SELECTOR, '''[data-token-name]''') ))
#         if click:
#             change_click = self.selenium_common.find_text_from( "//*[@data-clk]", "Change")
#             change_click.click()
#         if self.__allPremium == None:
#             # self.__allPremium = self.__driver.find_elements(By.XPATH,'//*[@data-token-name|@data-id]')
#             self.__allPremium = self.selenium_common.find_elements('//*[@data-token-name|@data-id]')
#         return self.__allPremium
#
#     def trade_rise_is_change(self,tick_scratch_data,grasp_historical_pop):
#         print(tick_scratch_data,grasp_historical_pop)
#         tick_short_name = tick_scratch_data['short_name']
#         historical_pop_short_name = grasp_historical_pop['short_name']
#         tick_change = tick_scratch_data['change']
#         historical_pop_change = grasp_historical_pop['change']
#         is_likely_type = tick_short_name.__eq__(historical_pop_short_name)
#         is_rise_changed = (tick_change != historical_pop_change)
#         is_rise_changed = (is_likely_type and is_rise_changed)
#         if is_rise_changed:
#             primitive_price = tick_scratch_data["primitive_price"]
#             last_num = tick_scratch_data["last_num"]
#             print(f"Changing massage : {tick_short_name} is changed! price:({primitive_price}->{last_num}) {historical_pop_change}:( to {tick_change})")
#         return is_rise_changed
#
#
#     def scan_trade_tick_list(self):
#         scan_trade_tick_list = []
#         allPremium = self.__allPremium
#         print( len(allPremium) )
#         for ele in allPremium:
#             print( ele.text)
#             coin_infos = ele.text.split("\n")
#             short_name = coin_infos[0]
#             full_name = coin_infos[1]
#             last_num = coin_infos[2]
#             last_price_num = float(last_num[1:].replace(r",", ""))
#             change_partial = coin_infos[3].split(" ")
#             change = change_partial[0]
#             change_sign = change[0]
#             change_number = float(change[1:-1])
#             if change_sign == "+":
#                 primitive_price = last_price_num / (1 + change_number / 100)
#             elif change_sign == "-":
#                 primitive_price = last_price_num * (1 - change_number)
#             market_cap = change_partial[1]
#             c_time = time.strftime("%Y-%m-%d %H:%m:%S",time.gmtime())
#             scan_trade_tick_list.append(
#                 {
#                     "short_name": short_name,
#                     "full_name": full_name,
#                     "last_num": last_num,
#                     "last_price_num": last_price_num,
#                     "change_sign": change_sign,
#                     "change": change,
#                     "primitive_price": primitive_price,
#                     "market_cap": market_cap,
#                     "time": c_time,
#                     "save_db": False
#                 }
#             )
#         return scan_trade_tick_list
#
#     def tran_trade_categories(self,rise_tick_datas=None):
#         categories = []
#         if rise_tick_datas != None:
#             rise_tick_datas = [str(x["short_name"]) for x in rise_tick_datas]
#             for short_name in rise_tick_datas:
#                 categories.append(short_name)
#         return categories
#
#
#     def set_trade_categories(self,rise_tick_datas=None,sava_to_mongodb=False):
#         daname = "list_trade_categories"
#         mongodb_daname = "okx_list_trade_categories"
#         categories = self.db_common.get_redis(daname)
#         if rise_tick_datas == None:
#             #如果redis没有缓存项目类的数据，则从mongodb读取
#             if len(categories) == 0:
#                 categories = self.db_common.read_data_to(mongodb_daname,{})
#                 #从mongodb读取的数据并存入 redis.
#                 self.db_common.set_redis({
#                     daname: categories
#                 })
#         else:
#             tick_categories = self.tran_trade_categories(rise_tick_datas)
#             is_new_type_itme = False
#             for short_name in tick_categories:
#                 if short_name not in categories:
#                     is_new_type_itme = True
#                     categories.append(short_name)
#                     self.new_type_item(short_name,rise_tick_datas)
#             if is_new_type_itme:
#                 self.db_common.set_redis({
#                     daname: categories
#                 })
#         self.__categories_trade_list = categories
#         return categories
#
#     def new_type_item(self,short_name,rise_tick_datas):
#         for tick_data in rise_tick_datas:
#             if short_name in tick_data:
#                 new_type_name = tick_data[short_name]
#                 print(f'new typeItem {new_type_name}')
#                 #TODO 发现新元素后的操作写在这里。
#         pass
#
#
#     def init_trade_historical_list(self):
#         print("init trade historical list!")
#         categories = self.set_trade_categories()
#         if len(categories) == 0:
#             scan_trade_tick_list = self.scan_trade_tick_list()
#             categories = self.set_trade_categories(scan_trade_tick_list)
#             print("categories",categories)
#         for short_name in categories:
#             if len(self.get_trade_historical_list(short_name)) == 0:
#                 all_premium_grasp_dict = self.load_trade_historical(max=1000)
#                 print(type(all_premium_grasp_dict))
#                 for trade_name,tick_scratch_list in all_premium_grasp_dict.items():
#                     self.set_trade_historical_list(trade_name,tick_scratch_list)
#
#     def get_trade_historical_list_pop(self,short_name): # trade_historical_list
#         redis_name = self.get_redis_trade_historical_list_name(short_name)
#         type_list = self.db_common.get_redis(redis_name,[0,0])
#         print(f"get_trade_historical_list_pop {type(type_list)}{len(type_list)}")
#         type_list = json.loads(type_list)
#         print(f"get_trade_historical_list_pop {type(type_list)}{len(type_list)}")
#         return type_list
#     def get_trade_historical_list(self,short_name,pop=[0,-1]):
#         redis_name = self.get_redis_trade_historical_list_name(short_name)
#         type_list = self.db_common.get_redis(redis_name,pop)
#         if type(type_list) == str:
#             type_list = json.loads(type_list)
#         return type_list
#     def set_trade_historical_list(self,trade_name,tick_scratch_list):
#         redis_name = self.get_redis_trade_historical_list_name(trade_name)
#         self.db_common.set_redis({
#             redis_name:json.dumps(tick_scratch_list)
#         })
#     def get_redis_trade_historical_list_name(self,short_name):
#         return f"{self.__redis_trade_item_dict_pre}{short_name}"
#
#     def load_trade_historical(self,max=1000,short_name=None):
#         print( " load_okx_exchange_rise is exec .~")
#         collection_name = self.__trade_historical_mongodb
#         datas = []
#         scan_trade_tick_list = self.scan_trade_tick_list()
#         if self.__save_project_as_mongodb:
#             if short_name != None:
#                 data = self.db_common.read_data_to(collection_name,{
#                     "short_name":short_name,
#                     "limit": max
#                 })
#                 datas = data
#             else:
#                 #使用mongodb存储
#                 for trade_item_dict in scan_trade_tick_list:
#                     short_name = trade_item_dict["short_name"]
#                     data = self.db_common.read_data_to(collection_name,{
#                         "short_name":short_name,
#                         "limit": max
#                     })
#                     datas += data
#         else:
#             #使用本地文件序列化
#             datas = self.file_common.unserialization(self.__exchangeDataFile)
#             if datas == None:
#                 datas = []
#         premium_grasp_list = {}
#         for data in datas:
#             short_name = data["short_name"]
#             if premium_grasp_list.get(short_name) == None:
#                 premium_grasp_list[short_name] = []
#             premium_grasp_list[short_name].append(data)
#         return premium_grasp_list
#
#     def categories_rise_sort(self,lg="%7"):
#         """
#         对可交易项目进行幅度排序。
#         :param lg:
#         :return:
#         """
#         lg = lg[1:]
#         lg = float(lg)
#         short_list = []
#         trade_categories = self.__categories_trade_list
#         for short_name in trade_categories:
#             trade_info = self.get_trade_historical_list_pop(short_name)
#             if trade_info["change"] >= lg : short_list.append(trade_info)
#         short_list.sort(key = lambda x : x["change"], reverse = True)
#         return short_list
#
#     def monitor_trade_rises(self):
#         categories_rise_sort = self.categories_rise_sort("%7")
#         #调用多线程打开监控页面
#         max_workers = len(categories_rise_sort)
#         # categories_rise_sort = [(cate) for cate in categories_rise_sort]
#         with ThreadPoolExecutor(max_workers=max_workers) as pool:
#             pool.submit(self.oversee_trade_data,categories_rise_sort)
#
#
#
#     def oversee_trade_data(self, category_rise):
#         short_name = category_rise["short_name"]
#         short_name = short_name.lower()
#         trade_spot_url = f"https://www.okx.com/trade-spot/{short_name}-usdt"
#         driver = self.selenium_common.open_url(trade_spot_url, empty_driver=True)
#
#         while category_rise["change"] > 7:
#             self.selenium_common.execute_js(driver,"monitor_trade_data.js")
#         return True
#
#     def save_okx_exchange_rise(self):
#         #提取未保存数据
#         grasp_listtmp = self.set_grasp_listtmp()
#         #设置保存标志位
#         for item in grasp_listtmp:
#             item["save_db"] = True
#
#         if self.__save_project_as_mongodb:
#             #使用mongodb存储
#             print( f"save_project_as_mongodb to {len(grasp_listtmp)} items.~")
#             self.db_common.save_data_to("okx_exchange_rise",grasp_listtmp)
#         else:
#             #使用本地文件序列化
#             print( f"file serialization to {len(grasp_listtmp)} items.~")
#             obj = self.file_common.unserialization(self.__exchangeDataFile)
#             if obj == None:
#                 obj = []
#             obj = obj + grasp_listtmp
#             self.file_common.serialization(obj, self.__exchangeDataFile)
#         self.set_grasp_listtmp(clear=True)
#
#     def rise_tick_data_pop(self,short_name):
#         for c_tick in self.__change_list_tick:
#             # 如果tick还没有添加,或者价格有变动,则压入tick并将上一次推入总数据列中.
#             if c_tick["short_name"].__eq__(short_name):
#                 self.__change_list_tick.remove(c_tick)
#                 return c_tick
#         return None
#
#
#
#




