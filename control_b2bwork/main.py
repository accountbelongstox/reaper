# import os
import datetime
import operator
import time
from kernel.base.base import *
import re
from flask import Flask, url_for, render_template
from flask import request as flask_request
import mimerender
import pprint

mimerender = mimerender.FlaskMimeRender()
flask_app = Flask(__name__)
app_self = None


class Main(BaseClass):
    __isRedis = True
    __exchangeDataFile = "exchangeData.list"
    __premium_grasp_listtmp_ = []
    __change_list_tick = []
    __categories_trade_list = []
    __trade_historical_mongodb = "list_trade_historical"
    __redis_trade_item_dict_pre = "list_okx_"
    __config = None
    __driver = None
    __admin_token = "wft6ZSbL2JY3w6fZe14OxDl3HTRZOAiE"

    # 标准化
    # categories_trade_list =
    # scan_trade_tick_list =
    # trade_item_dict =
    # trade_historical_list =
    # trade_historical_list =
    #
    # """

    def __init__(self, argv):
        global app_self
        app_self = self
        # self.com_selenium.create_single(self)
        pass

    def main(self, argv):
        network_th = self.com_thread.create_thread(thread_type="com",target=self.network_list)
        network_th.start()

    @flask_app.route('/add_account')
    def add_account():
        self = app_self
        user = flask_request.args.get('user')
        pwd = flask_request.args.get('pwd')
        if user is None or pwd is None:
            return {
                "type":"000",
                "message":"要添加的账号或密码不能为空。"
            }
        loginUser = self.get_account(user)
        if loginUser != None:
            return {
                "type":"00",
                "message":"账号已经存在，不能再添加。请修改。"
            }
        id_name = self.com_string.random_string(32,upper=False)
        self.add_account_to_account((
            id_name,user,pwd
        ))
        return {
                "type":"0",
                "message":"账号添加成功，请刷新网页。"
            }

    @flask_app.route('/delete_account')
    def delete_account():
        self = app_self
        user = flask_request.args.get('user')
        token = flask_request.args.get('token')
        if operator.__eq__(token,self.__admin_token):
            return {
                "type":None,
                "message":f"token error,the token is {token}"
            }
        if user is None:
            return {
                "type":"000",
                "message":"not parameter of user!"
            }
        loginUser = self.get_account(user)
        if loginUser == None:
            return {
                "type":"00",
                "message":"not exist the username."
            }
        self.delete_account_to_account(user)
        return {
                "type":"0",
                "message":"账号删除成功，请刷新网页。"
            }

    @flask_app.route('/api_manager')
    # @mimerender(
    #     default = 'html',
    #     xml=lambda message: '<message>%s</message>' % message,
    #     json = lambda message: json.dumps(message),
    #     html = lambda message: message,
    #     txt = lambda message: message
    # )
    def login_manager():
        url_for("static", filename="css/style.css", )
        self = app_self
        accounts = self.com_db.unserialization(self.get_account_serialization_file())
        if accounts == None:
            accounts = []
        manager_data = {}
        manager_data["accounts_list"] = []
        not_login = 0

        for account in accounts:
            id_name = account["login"]["id_name"]
            loginUser = account["login"]["loginUser"]
            th = self.com_thread.get_thread(id_name)
            if th == None:
                is_login = False
            else:
                is_login = th.login_check()
            if not is_login:
                not_login += 1
            manager_data["accounts_list"].append({
                "username": loginUser,
                "islogin": is_login,
            })
        manager_data["not_login"] = not_login
        return render_template("manager.html", manager_data=manager_data)

    @flask_app.route('/get_login_verify')
    def get_login_verify():
        return None
        self = app_self
        x_offset = flask_request.args.get('x_offset')
        username = flask_request.args.get('username')
        result = {}
        print(f"username is {username}")
        id_name = self.get_account_id_name(username)
        th = self.com_thread.get_thread(id_name)
        # 线程未启动，启动线程并开始登陆验证
        if th == None:
            th = self.account_browser_thread_create(username)
            time.sleep(5)
            vcode_close = self.com_selenium.is_element(".vcode-close", is_beautifulsoup=False)
            print(vcode_close)
            return None
        if th.login_check(init_check=True):
            result["type"] = "success"
            result["src"] = "初始化成功,该接口可以正常请求但请不要随意重启服务器"
            return result

        vcode_spin_img = self.com_selenium.find_element(".vcode-spin-img", is_beautifulsoup=False)
        if self.com_selenium.is_element(vcode_spin_img):
            vcode_close = self.com_selenium.find_element(".vcode-close", is_beautifulsoup=False)
            vcode_close.click()
            if th.login_check():
                result["type"] = "success"
                result["src"] = "初始化成功,该接口可以正常请求但请不要随意重启服务器"
                # result["status"] = self.login_submit()
            else:
                result["type"] = "null"
                result["src"] = "请重试."
            return result
        try:
            token_img = self.com_selenium.find_element("#token-img", is_beautifulsoup=False)
        except:
            token_img = None
        if self.com_selenium.is_element(token_img):
            result["type"] = "token_code"
            screenshot_save_file = self.com_selenium.screenshot_of_selector("#token-img")
            ocr = self.com_file.image_to_str_from_paddleorc(screenshot_save_file)
            ocr_text = ocr["text"]
            code_verify = ocr_text
            th.login_click(code_verify = code_verify)
            time.sleep(2)
            if th.login_check():
                result["type"] = "success"
                result["src"] = "初始化成功,该接口可以正常请求但请不要随意重启服务器"
            else:
                result["type"] = "null"
                result["src"] = "请重试."
            return result
        result = th.get_login_verify_html()
        return result
    #
    # @flask_app.route('/get_login_verify')
    # def get_login_verify():
    #     self = app_self
    #     x_offset = flask_request.args.get('x_offset')
    #     username = flask_request.args.get('username')
    #     result = {}
    #     print(f"username is {username}")
    #     code_verify = flask_request.args.get('code_verify')
    #     id_name = self.get_account_id_name(username)
    #     th = self.com_thread.get_thread(id_name)
    #     # 线程未启动，启动线程并开始登陆验证
    #     if th == None:
    #         th = self.account_browser_thread_create(username)
    #         time.sleep(5)
    #     if th.login_check(init_check=True):
    #         result["type"] = "success"
    #         result["src"] = "初始化成功,该接口可以正常请求但请不要随意重启服务器"
    #     elif x_offset is not None:
    #         y_offset = flask_request.args.get('y_offset')
    #         x_offset = int(x_offset)
    #         y_offset = int(y_offset)
    #         print(f" x_offset {x_offset} y_offset {y_offset}")
    #         th.login_click(x_offset, y_offset)
    #         time.sleep(2)
    #         if th.login_check():
    #             result["type"] = "success"
    #             result["src"] = "初始化成功,该接口可以正常请求但请不要随意重启服务器"
    #         else:
    #             result["type"] = "null"
    #             result["src"] = "请重试."
    #     elif code_verify is not None:
    #         th.login_click(code_verify = code_verify)
    #         time.sleep(2)
    #         if th.login_check():
    #             result["type"] = "success"
    #             result["src"] = "初始化成功,该接口可以正常请求但请不要随意重启服务器"
    #         else:
    #             result["type"] = "null"
    #             result["src"] = "请重试."
    #     else:
    #         result = th.get_login_verify_html()
    #     return result

    @flask_app.route('/api')
    def api():
        # 使用类加载器对类附加新类
        # 用于第三方调用接口时没有附加方法的问题
        self = app_self
        # method = flask_request.args.get('method')
        # password = flask_request.args.get('password')
        username = flask_request.args.get('username')
        if username == None:
            data = {
                "message": "no parameter as username",
                "type": None
            }
            return data

        datatypes = flask_request.args.get('datatypes')
        if datatypes == None:
            data = {
                "message": "no datatypes",
                "type": None
            }
            return data
        token = flask_request.args.get('token')
        if token == None:
            data = {
                "message": "no token",
                "type": None
            }
            return data
        if not operator.__eq__(token,self.__admin_token):
            data = {
                "message": f"token error,the token is {token}",
                "type": None
            }
            return data

        if operator.__eq__(datatypes,"add_account"):
            user = flask_request.args.get('user')
            pwd = flask_request.args.get('pwd')
            if user is None or pwd is None:
                return {
                    "type": "000",
                    "message": "no user or pwd"
                }
            loginUser = self.get_account(user)
            if loginUser != None:
                return {
                    "type": "00",
                    "message": "username exists."
                }
            id_name = self.com_string.random_string(32, upper=False)
            self.add_account_to_account((
                id_name, user, pwd
            ))
            return {
                "type": "0",
                "message": "add success"
            }
        elif operator.__eq__(datatypes, "delete_account"):
            user = flask_request.args.get('user')
            # pwd = flask_request.args.get('pwd')
            if user is None:
                return {
                    "type":"000",
                    "message":"not parameter of user!"
                }
            loginUser = self.get_account(user)
            if loginUser == None:
                return {
                    "type":"00",
                    "message":"not exist the username."
                }
            self.delete_account_to_account(user)
            return {
                    "type":"0",
                    "message":"delete success."
                }
        else:
            id_name = self.get_account_id_name(username)
            if id_name is None:
                data = {
                    "message": "no username",
                    "type": None
                }
                return data
            data_time = time.strftime("%Y%m%d", time.localtime())
            data_time_tempfile = f"time-{data_time}_id_name-{id_name}.datatemp"
            data_temp = self.com_db.unserialization(data_time_tempfile)
            if data_temp is not None:
                return data_temp
            th = self.com_thread.get_thread(id_name)
            print(f"username: {username} id_name: {id_name} th：{th}")
            if th is None:
                th = self.account_browser_thread_create(username)
                th.login()
            retry = 0
            while not th.login_check(init_check=True) and retry < 50:
                print(f"retry to login.")
                th.login()
                retry += 1
            if th.login_check(init_check=True):
                data = th.get_data({
                    "datatypes": datatypes
                })
                th.quit()
                self.com_db.serialization(data,data_time_tempfile)
                self.com_thread.remove_thread(thread_name=id_name)
                print(f"data{data}")
                return data
            else:
                data = {
                    "message": f"login error",
                    "type": None
                }
                return data

    def get_account_config(self, account_name, keys):
        if type(keys) == str:
            keys = [keys]
        if self.__config["multiaccount_support"] == True:
            multiaccount_datas = self.__config["multiaccount_datas"]
            # 有多账号的时候从多账号中读配置
            # 如果多账号没有配置则读总配置
            # 账号单独配置覆盖主配置
            account_config = None
            print(f"account_name {account_name}")
            for account in multiaccount_datas:
                print(f"account {account}")
                login = account["login"]
                if account_name == login["loginUser"]:
                    account_config = account
            if account_config == None:
                print(f"Not found account:{account_name} in multiaccount_datas in get_account_set.")
                return None
            value_as_multiaccounts = None
            value_as_config = None
            value = None
            for key in keys:
                exist_multiaccounts = True
                if value_as_multiaccounts == None:
                    try:
                        value_as_multiaccounts = account_config[key]
                    except:
                        exist_multiaccounts = False
                elif key in value_as_multiaccounts:
                    value_as_multiaccounts = value_as_multiaccounts[key]
                else:
                    exist_multiaccounts = False

                exist_config = True
                if value_as_config == None:
                    value_as_config = self.__config[key]
                elif key in value_as_config:
                    value_as_config = value_as_config[key]
                else:
                    exist_config = False

                if exist_multiaccounts:
                    value = value_as_multiaccounts
                elif exist_config:
                    value = value_as_config
                else:
                    print(f"key {key}")
                    print(f"value_as_config {value_as_config}")
                    value = None
                    break
            return value
        else:
            # 没有多账号直接从配置中读配置
            if account_name == self.__config["loginUser"]:
                value = None
                for key in keys:
                    if value == None:
                        value = self.__config[key]
                    else:
                        value = value[key]
                return value
            else:
                print(f"Not found account:{account_name} in self.__config['loginUser'] in get_account_set.")
                return None

    def init_config(self):
        config = {
            # 多账号支持,会启动多线程多个浏览器, 设置在下面
            # "multiaccount_support": True,
            "login": {
                "mustLogin": True,  # 是否需要预登陆
                "isLogin": False,  # 是否已经登陆
                "active_check": False,  # 活动检查
                "loginURL": "https://b2bwork.baidu.com/login",
                "loginVerifyURL": "https://b2bwork.baidu.com/dashboard",

                # "loginUser": "zsw100023649",
                # "loginPwd": "Mts77066.",
                "userInput": """//*[@id="uc-com-account"]""",
                "pwdInput": """//*[@id="ucsl-password-edit"]""",
                "submit": "#submit-form",
                "login_active": {
                    "active_url": "https://b2bwork.baidu.com/dashboard",
                    "active_period": 60,
                    "buttons": [
                        """/html/body/div[1]/div/div[2]/div[1]/div[1]/div/ul/div[8]/li/ul/div[1]/a""",
                        """//*[@id="app"]/div/div[1]/div/div[1]/div/img"""
                    ]
                },
                "login_pre": {
                    "clicks": [".primary"]
                }
            },
            "data_fields": [
                {
                    "datatype": "shop_score",
                    "description": "店铺评分",
                    "page": "https://b2bwork.baidu.com/dashboard",
                    "datas_by_class": {
                        "sentinel_selector": """//div[@class="shop-diagnose"]/p""",
                        "datas": [
                            {
                                "datatype": "shop_score",
                                "description": "店铺评分",
                                "selectors": [
                                    {
                                        "selector_names": "店铺评分",
                                        "selectors": {
                                            "selector":".shop-diagnose p",
                                            "attr": "val",
                                        }
                                    }
                                ],
                                "attr": "value"
                            }, {
                                "datatype": "commodity_management",
                                "description": "商品管理",
                                "selectors": [
                                    {
                                        "selector_names": "商品总数,交易商品,在售中,已下架,已驳回",
                                        "selectors": {
                                            "selector":".pm-data .item-data",
                                            "attr": "val",
                                        }
                                    }
                                ],
                                "attr": "value"
                            }
                        ]
                    }
                },
                {
                    "datatype": "smart_business_opportunity",
                    "description": "智慧商机",
                    "page": "https://b2bwork.baidu.com/service/business/index?scrollTop=0",
                    "datas_by_class": {
                        "sentinel_selector": '//*[@class="el-tooltip"]',
                        "datas": [
                            {
                                "datatype": "core_data",
                                "description": "核心数据",
                                "selectors": [
                                    {
                                        "selector_names": "曝光量,点击量,访客数,电话量,表单量,IM数",
                                        "selectors": {
                                            "selector":".el-tooltip",
                                            "attr": "val",
                                        }
                                    },

                                    {
                                        "selector_names": "曝光量百分比,点击量百分比,访客数增减,电话量增减,表单量增减,IM数增减",
                                        "selectors": [
                                            {
                                                "selector":".num span",
                                                "attr": "val",
                                            },
                                            {
                                                "selector": ".el-popover__reference span[class=icon]",
                                                "attr": "attr",
                                                "attr_val": "innerHTML",
                                                "callback": self.callback_core_data
                                            }
                                        ]
                                    }
                                ]
                            }
                        ]
                    }
                },

            ],
            "multiaccount_support": True,  # 多账号支持,会启动多线程多个浏览器
            "multiaccount_datas":
            # [  # 多账号的数据列表，设置会覆盖父一级的设置
            # {
            #     "login": {
            #         "loginUser": "zsw100023649",
            #         "loginPwd": "Mts77066."
            #     },
            #     "data_fields": []
            # }
            # ],
                self.com_db.unserialization(self.get_account_serialization_file()),
            # {
            #     "login": {
            #         "loginUser": "zsw100023649",
            #         "loginPwd": "Mts77066."
            #     },
            #     "data_fields": []
            # }
        }
        self.__config = config
        return self.__config

    def callback_core_data(self, data):
        data = str(data)
        try:
            if data.find("#bms-arrow-simple-top") != -1 or data.find(">+<") != -1:
                return "up"
            elif data.find("#bms-arrow-simple-bottom") != -1 or data.find(">-<") != -1:
                return "down"
            return None
        except:
            return None

    def get_account(self,username):
        multiaccount_datas = self.get_config("multiaccount_datas")
        if multiaccount_datas == None:
            return None
        for account in multiaccount_datas:
            login = account["login"]
            loginUser = login["loginUser"]
            if username == loginUser :
                return login
        return None

    def get_account_id_name(self,username):
        login = self.get_account(username)
        if login == None:
            return None
        return login["id_name"]

    def get_account_serialization_file(self):
        return "b2bwork_baidu_account_data.config"

    def get_accounts(self):
        accounts = self.com_db.unserialization(self.get_account_serialization_file())
        return accounts

    def delete_account_to_account(self, user):
        accounts = self.get_accounts()
        # accounts.remove(user)
        for i in range(len(accounts)):
            account = accounts[i]
            login = account["login"]
            loginUser = login["loginUser"]
            print(f"loginUser {loginUser} eq {user} {operator.eq(loginUser,user)}")
            if user == loginUser:
                del accounts[i]
                break
        print(f"accounts {accounts}")
        filename = self.get_account_serialization_file()
        self.com_db.serialization(accounts, filename,override=True)
        return self.init_config()

    def add_account_to_account(self, args):
        if type(args) == tuple:
            args = [args]
        account_data = []
        for account in args:
            try:
                id_name = account[0]
                loginUser = account[1]
                loginPwd = account[2]
            except:
                return None
            try:
                data_fields = account[3]
            except:
                data_fields = None
            account_item = {
                "login": {
                    "id_name": id_name,
                    "loginUser": loginUser,
                    "loginPwd": loginPwd
                }
            }
            if data_fields != None:
                account_item["data_fields"] = data_fields
            account_data.append(
                account_item
            )
        print(f"add_account_to_account {account_data}")
        filename = self.get_account_serialization_file()
        self.com_db.serialization(account_data, filename)
        return self.init_config()

    def get_config(self, account_name=None, keys=None):
        if self.__config == None:
            self.init_config()
        # 只有account_name一项，用account_name代替key
        if (account_name != None and keys == None) \
                or \
                (account_name == None and keys != None):
            if account_name in self.__config:
                return self.__config[account_name]
            else:
                print(f"Not found {account_name} in self.__config")
                return None
        if account_name != None and keys != None:
            return self.get_account_set(account_name, keys)
        else:
            return self.init_config()

    def network_list(self,args=None):
        if args is not None:
            print(args)
        port = self.com_config.get_global( 'flask_port')
        print(f'startup Flask app server. Listing port is {port}')
        flask_app.run(port=port, host="0.0.0.0")


    def multi_account_broser_create(self):
        self.account_browser_thread_create(allUsers=True)

    def account_browser_thread_create(self,allUsers=True):
        if type(allUsers) == str:
            notAllLoginUser = allUsers
        else:
            notAllLoginUser = None
        multiaccount_support = self.get_config("multiaccount_support")
        multiaccount_datas = self.get_config("multiaccount_datas")  # 本线程总支持的账号数
        config = {}
        for config_k, config_v in self.__config.items():
            config[config_k] = config_v
        # print(f"multiaccount_datas",multiaccount_datas)
        account_max_thread = 1
        if multiaccount_support == True:
            account_max_thread = len(multiaccount_datas)  # 最大支持的打开浏览器线程数为账号数
        # account_max_thread += 1 #预留一个线程给网络监听使用

        for id in range(account_max_thread):
            account = multiaccount_datas[id]
            # print(account)
            login = account["login"]
            loginUser = login["loginUser"]
            id_name = login["id_name"]
            if notAllLoginUser is not None and notAllLoginUser != loginUser:
                continue
            # deep_key = []
            for login_k, login_v in account.items():
                if type(login_v) == dict:
                    for login_k_, login_v_ in login_v.items():
                        if type(login_v_) == dict:
                            for login_k__, login_v__ in login_v_.items():
                                if type(login_v__) == dict:
                                    for login_k___, login_v___ in login_v__.items():
                                        if type(login_v___) == dict:
                                            for login_k____, login_v____ in login_v___.items():
                                                # deep_key.append(login_k____)
                                                config[login_k][login_k_][login_k__][login_k___][
                                                    login_k____] = login_v____
                                        else:
                                            config[login_k][login_k_][login_k__][login_k___] = login_v___
                                        # deep_key.append(login_k___)
                                else:
                                    config[login_k][login_k_][login_k__] = login_v__
                                # deep_key.append(login_k__)
                        else:
                            config[login_k][login_k_] = login_v_
                        # deep_key.append(login_k_)
                else:
                    config[login_k] = login_v
                # deep_key.append(login_k)
            # print(config)
            #     # config[login_k] = login_v
            # args = (config)
            th = self.com_thread.create_thread(thread_type="selenium",thread_name=id_name, args=config )
            # th.set("__config",self.get_config())
            th.start()
        # th = self.selenium_multi_process_mode.create_thread(target=self.network_list, args=config,thread_name="network_list",)
        # # th.set("__config",self.get_config())
        # th.start()
        return th
