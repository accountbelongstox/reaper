import string
from queue import Queue

import json
import operator
# import shutil
from kernel.base.base import *
import os
import re
import time
import urllib
import http.cookiejar
# import lxml.html
# from lxml import etree
# from lxml.cssselect import CSSSelector
# from selenium import webdriver
# from selenium.webdriver.common.by import By
# from urllib.parse import urlparse
# from multiprocessing import Pool
import threading
import random
import pprint
from kernel.base.load_module import LoadModuleClass
# 为保证 driver 能正常打开
loadModules = LoadModuleClass()

from urllib.parse import urlparse

class ThreadCommon(BaseClass):
    __threads = {}
    __thread_name_max = 32

    def __init__(self, args):
        pass

    def create_thread(self,thread_type, target=None, args=(), thread_name=None, daemon=False):
        if thread_name is None:
            thread_name = self.get_thread_name(args)
        if thread_name in self.__threads:
            print(f"the ThreadCommon existed with name {thread_name}.")
            return self.__threads[thread_name]
        if thread_type == "selenium":
            thread = SeleniumThread(target=target, args=args, thread_name=thread_name,daemon=daemon)
            self.attach_modules(thread)
            self.attach_module(thread,"selenium_common")
            selenium_common = loadModules.get_module("selenium_common")
            selenium_common.main(
                {
                    "module":thread,
                    "driver_name":thread_name
                }
            )
            thread.setargs(args)
        elif thread_type == "downs":
            thread = DownThread(target=target, args=args, thread_name=thread_name,daemon=daemon)
            self.attach_module(thread,"http_common")
            thread.setargs(args)

        elif thread_type == "common":
            thread = CommonThread(target=target, args=args, thread_name=thread_name, daemon=daemon)
            self.attach_modules(thread)
            thread.setargs(args)


        elif thread_type == "translate":
            thread = TranslateThread(words=args)
            self.attach_module(thread,"translate_common")
        elif thread_type == "down_web":
            thread = WebDownThread(target=target,args=args,thread_name=thread_name, daemon=daemon)
            self.attach_module(thread,"selenium_common")
            self.attach_module(thread,"file_common")
            self.attach_module(thread,"http_common")
            self.attach_module(thread,"config_common")
            thread.setargs(args)
        elif thread_type == "down_web_open_url":
            #该线程是网页下载的子线程，只负责window浏览器tag页面的切换
            #并不需要显示加载selenium_common，该模块由主线程down_web在args中隐式传递。
            thread = WebDownOpenUrlThread(target=target,args=args,thread_name=thread_name, daemon=daemon)
        else:
            print(f"Not create thread Because of unknown thread type {thread_type}.")
            return None

        print(f"new thread : ")
        print(f"\tthread_type : {thread_type}")
        print(f"\tthread_name : {thread_name}")
        self.__threads[thread_name] = thread
        return thread

    def remove_thread(self, thread_name):
        self.__threads[thread_name] = None
        del self.__threads[thread_name]
        return True

    def get_thread_name(self,args=None):

        # if args is None:
        #     return None
        # if type(args) == str:
        #     thread_name = args
        # elif type(args) == tuple:
        #     try:
        #         thread_name = str(args[0])
        #     except:
        #         thread_name = self.gen_thread_name()
        # elif type(args) == dict:
        #     try:
        #         thread_name = str(args["thread_name"])
        #     except:
        #         thread_name = self.gen_thread_name()
        # else:
        #     thread_name = self.gen_thread_name()
        thread_name = self.gen_thread_name()

        return thread_name

    def gen_thread_name(self):
        # 生成线程名128个字符
        max = self.__thread_name_max
        m = random.randint(1, max)
        a = "".join([str(random.randint(0, 9)) for _ in range(m)])
        b = "".join([random.choice(string.ascii_letters) for _ in range(max - m)])
        thread_name = ''.join(random.sample(list(a + b), max))

        if thread_name in self.__threads:
            return self.gen_thread_name()
        else:
            return thread_name

    def attach_module(self,thread_ident,module_name):
        if type(thread_ident) == str:
            thread = self.__threads[thread_ident]
        else:
            thread = thread_ident
        loadModules.attach_module_from(thread,module_name)

    def attach_modules(self,thread_ident):
        if type(thread_ident) == str:
            thread = self.__threads[thread_ident]
        else:
            thread = thread_ident
        loadModules.attach_module(thread,"common")
        loadModules.attach_module(thread,"mode")

    def get_thread(self, thread_ident):
        if thread_ident in self.__threads:
            return self.__threads[thread_ident]
        else:
            print(f"Not Found thread: {thread_ident} in selenium_multi_process_mode.")
            return None

    def getDaemon(self, thread_ident):
        th = self.get_thread(thread_ident)
        daemon = th.getDaemon()
        return daemon

    def setDaemon(self, thread_ident, daemon):
        th = self.get_thread(thread_ident)
        th.setDaemon(daemon)

    def is_alive(self, thread_ident):
        th = self.get_thread(thread_ident)
        r = th.is_alive()
        return r

    def run(self, thread_ident):
        th = self.get_thread(thread_ident)
        return th.run()

    def join(self, thread_ident):
        th = self.get_thread(thread_ident)
        return th.join()

    def send(self, thread_ident, data):
        th = self.get_thread(thread_ident)
        th.send(data)

    def set(self, thread_ident, name, data):
        th = self.get_thread(thread_ident)
        th.set(name, data)

# 多线程下载模块
class DownThread(threading.Thread):  # 继承父类threading.Thread
    args = None

    def __init__(self, target, args, thread_name, daemon):
        threading.Thread.__init__(self, name=thread_name, daemon=daemon)
        self.target = target
        self.args = args
        self.thread_name = thread_name
        self.__send_args = Queue()

    def run(self):  # 把要执行的代码写到run函数里面 线程在创建后会直接运行run函数
        """
        @ 参数 url为 tuple 类型，则格式为 [
            ( url, file_name , override),
            ( url, file_name , override)
                                        ]  后面filename 及 override 不用传
        @ 参数为 list 类型,则格式为[url] filename 及 override 将会自动解析
        :param url:
        :param file_name:
        :param override:
        :return:
        """
        self.http_common.down_file(self.args)


    def set(self, name, data):
        self.__dict__[name] = data

    def send(self, send_args):
        self.__send_args.put(send_args)

    def setargs(self,args):
        self.args = args


# selenium
class SeleniumThread(threading.Thread):  # 继承父类threading.Thread
    __driver = None
    __init_driver_open = True
    args = None

    def __init__(self, target, args, thread_name,daemon):
        threading.Thread.__init__(self,name=thread_name,daemon=daemon)
        user = args
        # config = user.config
        json_file = open('./control_douyin/config.json',encoding="utf-8")
        config = json.load(json_file)
        self.target = target
        self.args = config
        self.name = thread_name
        self.__send_args = Queue()
        self.__config = config

    def run(self):  # 把要执行的代码写到run函数里面 线程在创建后会直接运行run函数
        if self.target != None:
            self.target(self.args)
        else:
            try:
                if self.__config["must_login"] == True:
                    self.login()

                if self.__config["login"]["active_check"] == True:
                    self.logined_acitve()
            except:
                pass
            # self.url_open_active()

    def set(self,name,data):
        self.__dict__[name] = data

    def setargs(self,args):
        self.args = args

    def send(self,send_args):
        self.__send_args.put(send_args)

    def url_open_active(self):
        return
        # while True:
        #     self.__driver = self.selenium_common.get_driver()
        #     print(f"self.__driver {self.name } -> {self.__driver}")
        #     time.sleep(1)
        # return
        active_period = self.__config["login"]["login_active"]["active_period"]
        while True:
            #开始活动检查标志
            self.__config["login"]["active_check"] = True
            print("processing active checking.")
            if self.__config["login"]["mustLogin"]:
                isLogin = self.login_check()
                self.__config["login"]["isLogin"] = isLogin
                # if not isLogin:
                #     self.__config["login"]["isLogin"] = self.login_and_verify()
            if self.__config["login"]["isLogin"]:
                self.logined_acitve()
            #关闭活动检查标志
            self.__config["login"]["active_check"] = False
            #开始睡眠
            time.sleep(active_period)

    def login_check(self,init_check=False):
        if self.__driver is None:
            self.__driver = self.selenium_common.get_driver()
        #如果有验证页，则说明已经登陆过可能已过期，则刷新
        time.sleep(1)
        loginVerifyURL = self.__config["login"]["loginVerifyURL"]
        url_exists = self.selenium_common.find_url_from_driver_handles(loginVerifyURL)
        # print(f"login_check {loginVerifyURL} exists as {url_exists}")
        if url_exists == None:
            return False
        if init_check:
            return True
        self.__driver.refresh()
        #如果刷新过后页面依然存在，则说明未过期
        url_exists = self.selenium_common.find_url_from_driver_handles(loginVerifyURL)
        # print(f"login_check {loginVerifyURL} exists as {url_exists}")
        if url_exists == None:
            return False
        return True


    def login_and_verify(self):
        self.login()
        is_login = self.login_verify_continue()
        self.login_pre()
        return is_login

    def login_pre(self):
        login_pre = self.__config["login"]["login_pre"]
        if "clicks" in login_pre:
            clicks = login_pre["clicks"]
            for click_selector in clicks:
                time.sleep(3)
                click_element = self.selenium_common.find_element_wait( click_selector)
                if click_element is not None:
                    try:
                        click_element.click()
                    except:
                        pass

    def verification_from_login(self,x_offset=None,y_offset=None,code_verify=None):
        if x_offset is not None and y_offset is not None:
            self.verification_of_swipe(x_offset,y_offset)
        if code_verify is not None:
            self.verification_of_code(code_verify)

    def verification_of_swipe(self,x_offset=None,y_offset=None):
        if x_offset is not None and y_offset is not None:
            move_to_element = self.selenium_common.find_elements('.vcode-spin-button',is_beautifulsoup=True)
            move_to_element = move_to_element[0][0]
            id = move_to_element["id"]
            id = f"#{id}"
            self.selenium_common.move_to_element(id,x_offset,y_offset)

    def verification_of_code(self,code_verify=None):
            uc_common_token = self.selenium_common.find_element('#uc-common-token',is_beautifulsoup=False)
            uc_common_token.send_keys(code_verify)
            time.sleep(1)
            uc_common_token = self.selenium_common.find_element('.uc-token-confirm-btn',is_beautifulsoup=False)
            uc_common_token.click()

    def login_submit(self):
        submit_css = self.__config["login"]["submit"]
        submit = self.selenium_common.find_element_wait(submit_css)
        if self.selenium_common.is_element(submit):
            submit.click()
        if self.login_check():
            return True
        else:
            return False

    def login(self):
        userInput = self.__config["login"]["userInput"]
        pwdInput = self.__config["login"]["pwdInput"]
        submit = self.__config["login"]["submit"]
        loginURL = self.__config["login"]["loginURL"]
        loginUser = self.__config["login"]["loginUser"]
        loginPwd = self.__config["login"]["loginPwd"]
        html = self.selenium_common.get_html()
        current_url = self.selenium_common.get_current_url()
        self.selenium_common.open_url_as_new_window(loginURL)
        userInputElement = self.selenium_common.find_element_wait(userInput)
        pwdInputElement = self.selenium_common.find_element_wait(pwdInput)
        submitElement = self.selenium_common.find_element_wait(submit)
        send_keys_user = False
        send_keys_pwd = False
        click_login = False
        if userInputElement.__class__.__name__ == "WebElement":
            userInputElement.send_keys("")
            time.sleep(0.5)
            userInputElement.send_keys(loginUser)
            send_keys_user = True
        if pwdInputElement.__class__.__name__ == "WebElement":
            pwdInputElement.send_keys("")
            time.sleep(0.5)
            pwdInputElement.send_keys(loginPwd)
            send_keys_pwd = True
        if submitElement.__class__.__name__ == "WebElement":
            try:
                submitElement.click()
                click_login = True
            except:
                pass
        result = {}
        if send_keys_user and send_keys_pwd and click_login:
            if self.login_check(init_check=True):
                result["type"] = "success-init-check"
                result["status"] = True
                return result

            elif self.selenium_common.exists_element(".vcode-spin-img"):
                vcode_close = self.selenium_common.find_element(".vcode-close", is_beautifulsoup=False)
                vcode_close.click()
                submitElement.click()
                time.sleep(1)
                if self.login_check(init_check=True):
                    result["type"] = "success-vcode-close"
                    result["status"] = True
                else:
                    result["type"] = "fail-at-vcode-close"
                    result["status"] = False
                return result
            elif self.selenium_common.exists_element("#token-img"):
                screenshot_save_file = self.selenium_common.screenshot_of_selector("#token-img")
                ocr = self.file_common.image_to_str_from_paddleorc(screenshot_save_file)
                ocr_text = ocr["text"]
                code_verify = ocr_text
                print(f"ocr text {code_verify}")
                self.login_click(code_verify=code_verify)
                time.sleep(2)
                if self.login_check():
                    result["type"] = "success-code-verify"
                    result["status"] = True
                else:
                    result["type"] = "fail-to-code_verify"
                    result["status"] = False
                return result
            result = self.get_login_verify_html()
            return result
        else:
            log = "\n---------------------------------------------------------------------------------------------------------------------\n"
            log = log + f"userInputElement{type(userInputElement)}\n"
            log = log + f"pwdInputElement{type(pwdInputElement)}\n"
            log = log + f"submitElement{type(submitElement)}\n"
            log = log + html
            file_time = time.strftime("%Y%m%d%H%M%S", time.localtime())
            self.file_common.save_file(f"{file_time}{current_url}-{file_time}.log.html".replace("/","").replace(":",""), log)
            result["type"] = "fail-to-send_keys_user-and send_keys_pwd-click_login"
            result["status"] = False
            return result

    def login_verify_continue(self,check_deep=0):
        if check_deep == 0:
            return False
        loginVerifyURL = self.__config["login"]["loginVerifyURL"]
        loginVerifyURL = loginVerifyURL.split("?")[0]
        current_url = self.__driver.current_url
        current_url = current_url.split("?")[0]
        if operator.__eq__(current_url, loginVerifyURL):
            return True
        else:
            print(f"login_verify_continue check is :{self.__driver.current_url} to {loginVerifyURL} ")
            time.sleep(1)
            check_deep += 1
            return self.login_verify_continue(check_deep)
    #
    # def init_driver(self,url,cb=None):
    #     if self.__init_driver_open == True:
    #         self.selenium_common.open_url(url=url)
    #         print('load_JQuery loading..')
    #         self.selenium_common.load_JQuery_wait()
    #         self.__init_driver_open = False
    #     else:
    #         len_drivers = len(self.__driver.window_handles)
    #         url_exists = False
    #         for index in range(len_drivers):
    #             self.__driver.switch_to.window(self.__driver.window_handles[index])
    #             if self.__driver.current_url.find(url) == 0:
    #                 url_exists = True
    #                 print(f"init_driver found url is {self.__driver.current_url}")
    #                 break
    #         if not url_exists:
    #             js = "window.open('{}','_blank');"
    #             self.__driver.execute_script(js.format(url))
    #             print(f"init_driver open url by new window for page {url}")
    #             self.selenium_common.load_JQuery_wait()
    #     if cb != None: cb()

    def logined_acitve(self):
        active_url = self.__config["login"]["login_active"]["active_url"]
        buttons = self.__config["login"]["login_active"]["buttons"]
        self.selenium_common.open_url_as_new_window(active_url)
        for button_selector in buttons:
            button_selector = self.selenium_common.find_element_wait(button_selector)
            button_selector.click()
            time.sleep(3)

    def get_html_resource(self):
        #vcode-spin-img
        html = self.__driver.page_source
        html += "取得滑动登陆验证距离的javascript代码"
        return html

    def get_login_verify_html(self):
        result = {}
        if self.login_check():
            result["type"] = "success"
            result["src"] = "初始化成功,该接口可以正常请求但请不要随意重启服务器"
            return result
        else:
            self.__driver.refresh()
            self.login()
        time.sleep(3)

        selector_css = self.selenium_common.find_element(".vcode-spin-img", is_beautifulsoup=False)
        if self.selenium_common.is_element(selector_css):
            vcode_close = self.selenium_common.find_element(".vcode-close", is_beautifulsoup=False)
            vcode_close.click()
            result["type"] = "success"
            result["src"] = "初始化成功,该接口可以正常请求但请不要随意重启服务器"
            result["status"] = self.login_submit()
            return result
        else:
            try:
                result["type"] = "token_code"
                screenshot_save_file = self.selenium_common.screenshot_of_selector("#token-img")
                ocr = self.file_common.image_to_str_from_paddleorc(screenshot_save_file)
                ocr_text = ocr["text"]
                token_img_content = self.file_common.b64encode(screenshot_save_file)
                os.remove(screenshot_save_file)
                result["src"] = token_img_content

                return result
            except:
                result["type"] = "html"
                result["src"] = self.selenium_common.find_html_wait()
                return result
        # try:
        #     selector_css = self.selenium_common.find_element(".vcode-spin-img", is_beautifulsoup=True)
        #     vcode_spin_img = selector_css[0]
        #     # vcode_spin_img = insert_html_link_as_style + str(vcode_spin_img)
        #     vcode_spin_img = vcode_spin_img["src"]
        #     result["type"] = "rotate"
        #     result["src"] = vcode_spin_img
        #     return result
        # except:
        #     pass



    def get_data(self,args):
        while self.__config["login"]["active_check"] is True:
            time.sleep(1)
        getdata_result = {}
        try:
            datatypes_str = args["datatypes"]
            datatypes = datatypes_str.split(',')
            getdata_result["type"] = 0
            getdata_result["message"] = "successfully get data"
        except:
            # 如果不是当前token name请求，则跳过
            getdata_result["type"] = 0
            getdata_result["message"] = "no request name is datatype"
            getdata_result["error"] = f"no request name is datatype,datatype is {datatypes_str}"
            return getdata_result
        #
        # password = None
        # if "password" in args:
        #     password = args["password"]
        # method = None
        # if "method" in args:
        #     method = args["method"]

        graspFields = self.__config["data_fields"]
        fields_data = []
        pprint.pprint(graspFields)
        for grasp_unit in graspFields:
            datatype = grasp_unit["datatype"]
            if datatype not in datatypes:
                continue
            page = grasp_unit["page"]
            self.selenium_common.open_url_as_new_window( page)
            datas_by_class = grasp_unit["datas_by_class"]
            sentinel_selector = datas_by_class["sentinel_selector"]
            self.selenium_common.find_elements_value_wait(sentinel_selector,url=page)
            datas = datas_by_class["datas"]
            for data in datas:
                selectors = data["selectors"]
                datatype = data["datatype"]
                description = data["description"]
                for selector_value in selectors:
                    selectors = selector_value["selectors"]
                    #将selector转换成标准格式
                    # [
                    #     attr:"val,attr" ,
                    #     selector:".selector"
                    # ]
                    if type(selectors) == str:
                        selectors = selectors.split(",")
                        selector_dict = {}
                        selectors_temp = []
                        for selector in selectors:
                            selector_dict["selector"] = selector
                            selector_dict["attr"] = "val"
                            selectors_temp.append(selector_dict)
                        selectors = selectors_temp
                    elif type(selectors) == dict:
                        selectors = [selectors]

                    selector_names = selector_value["selector_names"]
                    if type(selector_names) == str:
                        selector_names = selector_names.split(",")

                    get_data_unit = {}
                    for selector_dict in selectors:
                        if "attr" in selector_dict:
                            attr = selector_dict["attr"]
                        else:
                            attr = "val"
                        selector = selector_dict["selector"]

                        if "callback" in selector_dict:
                            callback = selector_dict["callback"]
                        else:
                            callback = None


                        if attr == "val":
                            results = self.selenium_common.find_elements_value_by_js_wait( selector,page)
                        if attr == "attr":
                            attr_val = selector_dict["attr_val"]
                            results = self.selenium_common.find_elements_attr_by_js_wait( selector,attr_val,page)

                        for i in range(len(selector_names)):
                            selector_name = selector_names[i]
                            try:
                                result = results[i]
                            except:
                                result = None
                            if callback is not None:
                                result = callback(result)
                            if len( selectors ) > 1:
                                if selector_name not in get_data_unit:
                                    get_data_unit[selector_name] = [result]
                                else:
                                    get_data_unit[selector_name].append(result)
                            else:
                                get_data_unit[selector_name] = result

                    fields_data.append({
                        "datatype" : datatype,
                        "description" : description,
                        "data" : get_data_unit
                    })
                    print(f"get_data_unit {get_data_unit}")
        getdata_result["data"] = fields_data
        return getdata_result

    def quit(self):
        self.__driver.quit()

    def get_config(self,keys):
        pass


# 多线程下载模块
class CommonThread(threading.Thread):  # 继承父类threading.Thread
    args = None

    def __init__(self, target=None, args=(), thread_name=None, daemon=False):
        if thread_name is None:
            thread_name = str(random.random() * 100000)
        threading.Thread.__init__(self, name=thread_name, daemon=daemon)
        self.target = target
        self.args = args
        self.thread_name = thread_name
        self.__send_args = Queue()

    def run(self):  # 把要执行的代码写到run函数里面 线程在创建后会直接运行run函数
        if self.target != None:
            self.target(self.args)

    def set(self, name, data):
        self.__dict__[name] = data

    def send(self, send_args):
        self.__send_args.put(send_args)

    def setargs(self,args):
        self.args = args

class TranslateThread(threading.Thread):
    __result = Queue()
    __words = None
    __word_num = 0

    def __init__(self, words=Queue(), thread_name=None, daemon=False):
        threading.Thread.__init__(self, name=thread_name, daemon=daemon)
        self.__words = None
        self.__words = Queue()
        if type(words) is not list:
            words = [words]
        index = 0
        for word in words:
            if type(word) == str:
                word_dict = self.word_to_dict(word, index=index)
                self.__words.put(word_dict)
            elif word.__class__.__name__ == "Queue":
                while word.qsize() > 0:
                    trans_word = word.get()
                    word_dict = self.word_to_dict(trans_word, index=index)
                    self.words.put(word_dict)
            elif word.__class__.__name__ == "dict":
                word_dict = self.word_to_dict(word,index=index)
                self.__words.put(word_dict)
            else:
                self.__words.put(word)
            index +=1
        self.__word_num = self.__words.qsize()
        self.thread_name = thread_name


    def word_to_dict(self,word,default_engine="google_cn",from_is="en",to="zh-cn",callback=None,index=0):
        if type(word) == str:
            word_dict = {
                "word": word
            }
        else:
            word_dict = word

        if "from_is" not in word_dict:
            word_dict["from_is"] = from_is
        if "to" not in word_dict:
            word_dict["to"] = to
        if "engine" not in word_dict:
            word_dict["engine"] = default_engine
        if "callback" not in word_dict:
            word_dict["callback"] = callback
        if "index" not in word_dict:
            word_dict["index"] = index
        return word_dict

    def run(self):
        while self.__words.qsize() > 0:
            word_dict = self.__words.get()
            word = word_dict.get("word")
            to = word_dict.get("to")
            index = word_dict.get("index",0)
            from_is = word_dict.get("from_is")
            callback = word_dict.get("callback")
            engine = word_dict.get("engine")
            if engine == "google":
                result = self.translate_common.translate_from_google(word=word,from_is=from_is,to=to,callback=None)
            elif engine == "google_cn":
                result = self.translate_common.translate_from_google_cn(word=word,from_is=from_is,to=to,callback=None)
            elif engine == "baidu":
                result = self.translate_common.translate_from_baidu(word=word,from_is=from_is,to=to,callback=None)
            elif engine == "youdao":
                result = self.translate_common.translate_from_youdao(word=word,from_is=from_is,to=to,callback=None)
            else:
                print(f"not translate engine : {engine}")
                result = None
            if result is not None:
                result["index"] = index
                self.__result.put(result)
            else:
                print(result)
            if callback is not None:
                callback(result)
        return self.__result

    def done(self):
        if self.__words.qsize() ==0 and self.__result.qsize() == self.__word_num:
            return True
        else:
            return False

    def result(self):
        while self.done() is False:
            time.sleep(1)
        return self.__result

    def setargs(self,args):
        self.args = args

class WebDownOpenUrlThread(threading.Thread):
    __urls = None #用来接收从主线程传过来的Queue
    selenium_common = None
    __urls_page_resource_wait_queue = None #取得的每个页面的URL及源码暂存，交由主线程处理
    threadLock= None
    __listing = True
    #最大打开页面数
    __max_open_url = 50
    # __already_open_urls = {}
    def __init__(self,target=None, args=(),max_open=50,timeout=10, thread_name=None, daemon=False):
        threading.Thread.__init__(self, name=thread_name, daemon=daemon)
        self.args = args
        self.target = target
        self.__max_open_url = max_open
        #如果在该时间段内加载出一定的代码将转至动态加载时间翻倍
        self.__timeout = timeout
        self.thread_name = thread_name
        self.selenium_common = args[0]
        driver = args[1]
        self.selenium_common.set_driver(driver)
        self.__urls = args[2]
        self.threadLock = args[3]

    def run(self):
        max = self.__max_open_url
        while True:
            # 初始化执行，先监听所有TAG而，并单独使用一个线程实时切换。
            url_formats = self.get_url_from_queue(max=max)
            print(f"need new open urls {url_formats}")
            for url_format in url_formats:
                url = url_format["url"]
                # dir = url_format["dir"]
                # filename = url_format["filename"]
                self.selenium_common.open(url,not_wait=True)
                # url_format["index"] = self.selenium_common.get_current_window_handle_index()
                # self.threadLock.acquire()
                # self.__already_open_urls[url] = url_format
                # self.threadLock.release()
            #分析由WebDownForeachTagThread在切换tag中获取到地网页源码。
            time.sleep(0.2)

    # def get_already_open_urls(self):
    #     self.threadLock.acquire()
    #     already_open_urls = self.__already_open_urls
    #     self.threadLock.release()
    #     return already_open_urls

    def get_url_from_queue(self,max=1):
        if max == 1 and self.__urls.qsize() > 0:
            url = self.__urls.get()
        elif max > 1:
            urls = []
            while max > 0 and self.__urls.qsize() > 0:
                url = self.__urls.get()
                urls.append(url)
                max -= 1
            url = urls
        else:
            url = None
        return url

class WebDownThread(threading.Thread):
    #资源锁
    threadLock = threading.Lock()
    __down_web_page_queue = Queue()

    #待打开分析的url地址
    #存储方式为元组(load_dir , url)
    __urls = Queue()

    #待下载的资源url
    #存储方式为元组(load_dir , url)
    __resource_urls = Queue()

    #是否一直监听并循环检测window tag
    __listing = True

    #用于暂存每一个临时取得的页面
    __temp_html = None

    __base_url = None
    __historical_url = []

    __already_downloaded_urls = Queue()
    __already_downloaded_resource_urls = Queue()

    __down_web_thread_pool = None
    __down_web_charset = None
    __down_web_tab_threads = []
    __down_web_driver = None
    __down_web_downing = True
    __down_web_listen_tag_init = True
    __down_web_listen_tag_flag = True
    __website_url = None

    def __init__(self, target=None, args=(), thread_name=None, daemon=False):
        threading.Thread.__init__(self, name=thread_name, daemon=daemon)
        self.target = target
        self.args = args
        self.thread_name = thread_name
        if type(args) is str:
            self.__website_url = args
        else:
            self.__website_url = args[0]

    #获得该值用于在线程外启动子线程并赋值给子线程
    #子线程要使用主线程的selenium_common属性
    def get_selenium_common(self):
        return self.selenium_common
    def get_selenium_driver(self):
        return self.selenium_common.get_driver()
    #获得该值用于在线程外启动子线程并赋值给子线程
    def get_urls_page_resource_wait_queue(self):
        return self.__urls_page_resource_wait_queue
    def get_thread_lock(self):
        return self.threadLock
    def get_urls(self):
        return self.__urls

    def init_base_url(self):
        url = self.__website_url
        self.set_base_url()
        # 首次提交的网页也先加入队列，该方便对比重复
        self.add_url_to_queue(url)

    def start_sub_thread_open_url(self):
        #共享给子线程的 selenium_common 模块
        selenium_common = self.get_selenium_common()
        #共享给子线程的 selenium_driver 模块
        selenium_driver = self.get_selenium_driver()
        #共享给子线程的用于存放网页源码的队列
        urls = self.get_urls()
        #共享给子线程的线程锁
        thread_lock = self.get_thread_lock()
        #需要传给子线程的参数
        args = (
            selenium_common,
            selenium_driver,
            urls,
            thread_lock
        )
        self.thread_common = ThreadCommon(())
        #创建辅助子线程，专用于浏览器tag切换，并取得已经加载完毕的网页并存入 urls_page_resource_wait_queue 暂存，交由主线程处理。
        self.open_url_thread = self.thread_common.create_thread(
            thread_type="down_web_open_url",
            args=args
        )
        self.open_url_thread.start()
        return self.open_url_thread

    # 专门负责切换网页url
    def run(self):
        index = 0
        empty_url = "data:,"
        #将初始url添加到队列。
        self.init_base_url()
        #创建并启动专用于打开网页的子线程
        self.start_sub_thread_open_url()

        while self.__listing == True:
            handles_len = self.selenium_common.get_window_handles_length()
            if index == handles_len:
                index = 0
            self.selenium_common.switch_to(index)
            is_ready = self.selenium_common.is_ready()
            url = self.selenium_common.get_current_url()
            if is_ready is True and url is not empty_url:
                html = self.selenium_common.get_html()
                print(f"url is_ready,the result add to <urls_page_resource_wait_queue>:")
                print(f"\turl:{url}")
                print(f"\thtml:{len(html)}")
                print(f"\thtml_text:{html[0:60]}")
                self.find_all_from_tag_a()

                self.find_all_tab_and_replace_html( [
                    #返回值dict类型key为每个键的名称html直接在函数里保存了
                    ["<script>",
                     ["src"]
                     ],
                    ["<img>",
                     ["src"]
                     ],
                    ["<link>",
                     ["href"]
                     ],
                    ["<a>",
                     ["href"]
                     ],
                ])
                # already_open_urls = self.open_url_thread.get_already_open_urls()
                #TODO
                #在此分析和提取出网页源码的url和src
                #提取出所有 a 标签并添加到urls
                #提取出所有资源
                #保存及路径分析交由主线程负责
                # self.__urls_page_resource_wait_queue.put({
                #     "url":url,
                #     "html":html,
                # })
                if handles_len > 1:
                    self.selenium_common.close()
                else:
                    self.selenium_common.open(empty_url,not_wait=True)
                    self.selenium_common.switch_to(0)
                    self.selenium_common.close()
                    print(f"browser window tag is empty.")
                    print(f"website downloaded.")
                    print(f"done.")
                    # TODO
                    # 全站结束采集在于这里开启break予以打断
                    # break
            else:
                index += 1
    def stop(self):
        self.__listing = False
    def set_temp_html(self,html):
        self.__temp_html = html
    def get_temp_html(self):
        return self.__temp_html
    def load_url_from_queue(self):
        url = self.get_url_from_queue()
        if url != None:
            self.selenium_common.open(url, not_wait=True)
    def add_url_to_queue(self,url):
        #经过处理后的url_format格式为
        #url
        #dir
        #filename
        if type(url) is str:
            url_format = self.url_to_filename(url, "<a>", ele=None)
            urls = [url_format]
        else:
            urls = url

        for url_format in urls:
            url = url_format["url"]
            # 对于已经存在的历史url跳过
            if url not in self.__historical_url and url is not "data:,":
                self.__historical_url.append(url_format)
                self.__urls.put(url_format)
            else:
                print(f"already downloaded : {url}")
    def get_url_from_queue(self,max=1):
        if max == 1 and self.__urls.qsize() > 0:
            url = self.__urls.get()
        elif max > 1:
            urls = []
            while max > 0 and self.__urls.qsize() > 0:
                url = self.__urls.get()
                urls.append(url)
                max -= 1
            url = urls
        else:
            url = None
        return url
    def set_base_url(self):
        web_url = self.__website_url
        web_url_parse = urlparse(web_url)
        down_web_base_url = web_url_parse.scheme + "://" + web_url_parse.netloc
        self.__base_url = down_web_base_url

    #url补全
    def url_completion_by_baseurl(self,link_url):
        url_urlparse = urlparse(link_url)
        base_url_urlparse = urlparse(self.__base_url)
        url_path = str(url_urlparse.path)
        url_offset = url_path
        if self.down_website_equal_url_strict(self.__base_url, link_url) == False:
            # 对于用二级域名的图片,则直接将二级域名移到当前文件夹做为目录
            url_offset = f"/{url_urlparse.netloc}{url_path}"
        if self.down_website_equal_url(self.__base_url, link_url) is not True:
            return None
        return link_url

    def url_to_filename(self,link_url,tag_type, ele):
    # old function name is down_website_url_to_file_format
        base_url = self.__base_url
        url_urlparse = urlparse(link_url)
        base_url_urlparse = urlparse(self.__base_url)
        url_path = str(url_urlparse.path)
        url_query = url_urlparse.query
        url_offset = url_path
        if self.down_website_equal_url_strict(self.__base_url, link_url) == False:
            # 对于用二级域名的图片,则直接将二级域名移到当前文件夹做为目录
            url_offset = f"/{url_urlparse.netloc}{url_path}"
        if tag_type.__eq__("<script>"):
            # 对于没有js地址的动态获取数据,则直接强行在最后加上.cs结尾
            if url_offset.endswith(f".js") is not True:
                url_offset = f"{url_path}{url_query}.js"
        # link文件命名规则
        elif tag_type.__eq__("<link>"):
            url_offset_link = self.down_website_source_link_suffix(ele, url_offset, url_path, url_query,"rel")
            if url_offset_link != None:
                url_offset = url_offset_link
            elif self.down_website_source_link_suffix(ele, url_offset, url_path, url_query,"type") != None:
                url_offset = url_offset_link
        # a连接文件命名规则
        elif tag_type.__eq__("<a>"):
            if self.down_website_equal_url(self.__base_url, link_url) is not True:
                return None
            filename_split = os.path.splitext(url_offset)
            if filename_split[1].__eq__(""):
                url_offset = f"{url_offset}/index.html"
        url_offset = re.sub(r"[\=\|\?\^\*\`\;\,\，\&]", "_", url_offset)
        # filename Format
        filename_url = self.url_format(
            f"{base_url_urlparse.netloc}/{url_offset}"
        )
        url_local = self.url_format(
            self.url_to_localdir(filename_url)
        )
        link_url = self.url_format(link_url)
        url_offset = self.down_website_join_path(base_url, url_offset)
        # return {
        #     "dir":url_local,
        #     "filename":url_offset,
        #     "url":link_url
        # }

        return {
            # 经转换后的可以直接下载的url连接
            "full_url": url_local,
            # 本地
            "local_url": url_offset,
            "source_url": link_url,
            "filename": url_offset
        }

    def foreach_browser_tag(self):
        handles_len = self.selenium_common.get_window_handles_length()
        index = 0
        while handles_len > 0:
            if index == handles_len:
                index = 0
            self.selenium_common.switch_to(index)
            is_ready = self.selenium_common.is_ready()
            if is_ready is True:
                alinks = self.find_all_from_tag_a()
                self.add_url_to_queue(alinks)
                if handles_len > 1:
                    self.selenium_common.close()
                else:
                    break
            else:
                index += 1
            handles_len = self.selenium_common.get_window_handles_length()

    def website_down_is_done(self):
        handles_len = self.selenium_common.get_window_handles_length()
        if handles_len == 0 and self.selenium_common.get_current_url() == "data:,":
            handles_len = 0
        #以下条件都不具备关闭结束网站拷贝的条件
        #
        #如果当前页面还有未关闭的打开窗口
        #则说明还有页面没有读取源码（因为读取源码的页面会在foreach_tag专门线程里被关闭）
        #则表示还未下载完
        #或者
        #__urls 里还有未打开完的网页，则表示网页还未下载完毕。
        #或者
        #从foreach_tag线程里读取到的源码还暂存在<__urls_page_resource_wait_queue>队列里未进行分析，里边可能分析出新的url
        if handles_len > 0 or self.__urls.qsize() > 0 or self.__urls_page_resource_wait_queue.qsize() > 0 :
            return True
        else:
            return False

    def down_website_source_thread(self):
        th = []
        while len(self.__resource_urls) > 0:
            th.append(self.__resource_urls.pop())
        if len(th) == 0:
            return
        return self.http_common.down_files(th)

    def down_website_run(self):
        while self.down_website_continue():
            while self.__down_web_page_queue.qsize() > 0:
                web_page = self.__down_web_page_queue.get()
                url_web = web_page[0]
                url_local = web_page[1]
                if len(self.__down_web_tab_threads) < 1:
                    driver = self.open_url(url_web)
                else:
                    js = "window.open('{}','_blank');"
                    driver.execute_script(js.format(url_web))
                self.__down_web_tab_threads.append(url_web)
                HTML_Content = driver.page_source
                _bdriver = self.http_common.find_text_from_beautifulsoup(HTML_Content)
                self.down_website_set_chatset(_bdriver)
                HTML_Content = self.down_website_find_source_add_toQueue(_bdriver, url_web, HTML_Content, "<script>","src")
                
                HTML_Content = self.down_website_find_source_add_toQueue(_bdriver, url_web, HTML_Content, "<img>","src")
                
                HTML_Content = self.down_website_find_source_add_toQueue(_bdriver, url_web, HTML_Content, "<link>","href")
                
                HTML_Content = self.down_website_find_a_add_toQueue(_bdriver, url_web, HTML_Content, "<a>", "href")

                self.file_common.save_file(url_local, HTML_Content, override=True, encoding=self.__down_web_charset)
                print(f"tick done-{url_web}:historical:{len(self.__down_web_historical)}")

                th = []
                while len(self.__resource_urls) > 0:
                    th.append(self.__resource_urls.pop())
                if len(th) != 0:
                    self.http_common.down_files(th)

    def find_all_from_tag_a(self):
        tagname = "<a>"
        eles = self.selenium_common.find_elements(tagname)
        alinks = []
        for ele in eles:
            url = ele.get_attribute("href")
            dom_attribute = ele.get_dom_attribute("href")
            if url == None:
                continue
                # javascript 空标签跳过
            if url.startswith("javascript:"):
                continue
            if dom_attribute == None:
                continue
            if dom_attribute.startswith("javascript:"):
                continue
            url = str(url)
            url = url.strip()
            dom_attribute = str(dom_attribute)
            dom_attribute = dom_attribute.strip()
            if url.__eq__(""):
                continue
            if dom_attribute.__eq__(""):
                continue
                # 空字符串及当前而跳过
            if url.__eq__("/"):
                continue
            if dom_attribute.__eq__("/"):
                continue
            url = self.url_format(url)
            print(f"url : {url}")
            url_format = self.url_to_filename(url, tagname, ele)
            if url_format == None:
                continue
            else:
                alinks.append(url_format)
        return alinks

    def down_website_run_backup(self):
        while self.__down_web_page_queue.qsize() > 0 or self.__down_web_page_queue.qsize() > 0:
            while self.__down_web_page_queue.qsize() > 0:
                web_page = self.__down_web_page_queue.get()
                url_web = web_page[0]
                url_local = web_page[1]
                driver = self.open_url(url_web)

                HTML_Content = driver.page_source
                self.down_website_set_chatset(driver)
                HTML_Content = self.find_all_tab_and_replace_html( url_web, [
                    ["<script>",["src"]],
                    ["<img>",["src"]],
                    ["<link>",["href"]],
                    ["<a>",["href"]],
                ])

                HTML_Content = self.down_website_find_source_add_toQueue(driver, url_web, HTML_Content, "<script>","src")
                HTML_Content = self.down_website_find_source_add_toQueue(driver, url_web, HTML_Content, "<img>", "src")
                HTML_Content = self.down_website_find_source_add_toQueue(driver, url_web, HTML_Content, "<link>","href")
                HTML_Content = self.down_website_find_a_add_toQueue(driver, url_web, HTML_Content, "<a>", "href")

                self.file_common.save_file(url_local, HTML_Content, override=True, encoding=self.__down_web_charset)
                print(f"tick done-{url_web}:historical:{len(self.__down_web_historical)}")

                th = []
                while len(self.__resource_urls) > 0:
                    th.append(self.__resource_urls.pop())
                if len(th) != 0:
                    self.http_common.down_files(th)

    def down_website_join_path(self, base_url, current_dir):
        base_url_parse = urlparse(base_url)
        base_url_path = base_url_parse.path
        current_url_parse = urlparse(current_dir)
        current_url_path = current_url_parse.path
        base_url_path = self.url_format(base_url_path)
        current_url_path = self.url_format(current_url_path)
        if current_url_path.startswith("/"):
            current_url_path_dirname = os.path.dirname(current_url_path)
            base_url_paths = self.down_website_url_split(base_url_path)
            current_url_paths = self.down_website_url_split(current_url_path)
            # 先将相同的路径深度依次递归向上抵消相同路径
            while True:
                if len(base_url_paths) < 1 or len(current_url_paths) < 1:
                    break
                if base_url_paths[0].__eq__(current_url_paths[0]):
                    base_url_paths = base_url_paths[1:]
                    current_url_paths = current_url_paths[1:]
                else:
                    break
            if len(current_url_paths) > 0:
                current_url_path = "/".join(current_url_paths)
            else:
                current_url_path = ""
            # 先检查两个路径是否相等
            if base_url_path.__eq__(current_url_path_dirname):
                # 如果路径相等则先把路径替换为相对路径,直接抵消可以不用替换为相对路径，直接返回即可。
                current_url_path = re.sub(re.compile(r"^\/"), "", current_url_path)
            # 对于不相等的路径，则要由当前页面的深度依次递归向上返回主路径再找到相对路径
            else:
                current_url_path = "../" * len(base_url_paths) + "/".join(current_url_paths)
        return current_url_path

    def down_website_set_chatset(self):
        if self.__down_web_charset == None:
            metas = self.find_elements("<meta>")
            for meta in metas:
                charset = meta.get_attribute("charset")
                if charset != None:
                    self.__down_web_charset = charset
                    break
        if self.__down_web_charset == None:
            self.__down_web_charset = "utf-8"

    def down_website_is_historical_url(self, url):
        threadLock.acquire()
        if url in self.__down_web_historical:
            threadLock.release()
            return True
        else:
            self.__down_web_historical.update(url)
            threadLock.release()
            return False

    def url_to_localdir(self, web_url):
        url_parse = urlparse(web_url)
        webdownload_dir = self.config_common.get_webdownload_dir()
        baseDir = os.path.join(webdownload_dir, url_parse.netloc)
        url_parse_path = re.sub(re.compile(r"^\/"), "", url_parse.path)
        fod_dir = os.path.join(baseDir, url_parse_path)
        return fod_dir

    def down_website_find_a_add_toQueue(self, tagname, atr):
        HTML_Content = self.find_all_tab_and_replace_html( tagname, atr)
        return HTML_Content

    def down_website_find_source_add_toQueue(self, tagname, atr):
        HTML_Content = self.find_all_tab_and_replace_html( tagname, atr)
        return HTML_Content

    def find_all_tab_and_replace_html(self, tagnames):
        # tagnames 参数形式为 [
        # ["<a>",["href"]]
        # ]的二维数组
        # 其中的第二项表示 attr可以为一个数组。
        # 返回类型为
        # {
        #     "a" : {
        #          "href":[
        #               "xxxx/xxxx"
        #          ]
        #     },
        #     "img" : {
        #          "href":[
        #               "xxxx/xxxx"
        #          ]
        #     }
        # }

        if tagnames[0] is not list:
            #如果查找格式为["<tab>","href"]的一维数组，转为二维数组方便查询
            tagnames = [tagnames]

        url_web = self.get_temp_current_url()
        html = self.selenium_common.get_temp_html()

        for tagname_and_attr in tagnames:
            tagname = tagname_and_attr[0]
            attrs = tagname_and_attr[0]
            for atr in attrs:
                #tagnames 格式为["<tab>","src"]
                eles = self.selenium_common.find_elements(tagname)
                if tagname == "<a>":
                    is_a_link = True
                else:
                    is_a_link = False
                alinks = []
                for ele in eles:
                    source_url = ele.get_attribute(atr)
                    dom_attribute = ele.get_dom_attribute(atr)
                    if source_url == None:
                        continue
                        # javascript 空标签跳过
                    if source_url.startswith("javascript:"):
                        continue
                    if dom_attribute == None:
                        continue
                    if dom_attribute.startswith("javascript:"):
                        continue
                    source_url = str(source_url)
                    source_url = source_url.strip()
                    dom_attribute = str(dom_attribute)
                    dom_attribute = dom_attribute.strip()
                    if source_url.__eq__(""):
                        continue
                    if dom_attribute.__eq__(""):
                        continue
                        # 空字符串及当前而跳过
                    if source_url.__eq__("/"):
                        continue
                    if dom_attribute.__eq__("/"):
                        continue
                    source_url = self.url_format(source_url)
                    # # 对于已经存在的历史url跳过
                    # if self.down_website_is_historical_url(source_url) == True:
                    #     print(f"already down the url:<{source_url}>")
                    #     continue
                    # if self.down_website_is_historical_url(url_web) == True:
                    #     print(f"already down the url:<{url_web}>")
                    #     continue

                    urls_format_and_locat = self.url_to_file_format(source_url, tagname, ele, url_web)
                    if urls_format_and_locat == None:
                        continue

                    url_offset = urls_format_and_locat[1]
                    url_local = urls_format_and_locat[0]
                    html = self.down_website_replace_htmlcontent(html, dom_attribute, url_offset)
                    if is_a_link:

                        url_format = self.url_to_filename(url,"<a>",None)

                        self.down_website_add_webpageQueue(attribute, url_local)
                    else:
                        self.down_website_add_resourceList(attribute, url_local)

                    url_format = self.url_to_filename(source_url, tagname, ele)
                    if url_format == None:
                        continue
                    else:
                        alinks.append(url_format)

        url_web = self.url_to_filename(url_web,"<a>",None)
        url_filename = url_web["dir"]
        self.file_common.save_file(url_filename, html)

        return alinks

    def down_website_equal_url(self, url_main, url_other):
        url_main_parse = urlparse(url_main)
        url_main = url_main_parse.netloc
        url_main = re.sub(re.compile(r"^www\."), "", url_main)
        url_other_parse = urlparse(url_other)
        url_other = url_other_parse.netloc
        url_other = re.sub(re.compile(r"^www\."), "", url_other)
        if url_other.endswith(url_main) or url_main.endswith(url_other):
            return True
        else:
            return False

    def down_website_equal_url_strict(self, url_main, url_other):
        url_main_parse = urlparse(url_main)
        url_main = url_main_parse.netloc.lower()
        url_other_parse = urlparse(url_other)
        url_other = url_other_parse.netloc.lower()
        if url_main.__eq__(url_other):
            return True
        else:
            return False

    def down_website_replace_htmlcontent(self, HTML_Content, dom_attribute, url_to_file_format):
        dom_attribute_s = dom_attribute
        dom_attribute_t = url_to_file_format
        # dom_attribute_s = f'="{dom_attribute}'
        # dom_attribute_t = f'="{url_to_file_format}'
        # HTML_Content = HTML_Content.replace(dom_attribute_s, dom_attribute_t)
        # dom_attribute_s = f"='{dom_attribute}"
        # dom_attribute_t = f"='{url_to_file_format}"
        # HTML_Content = HTML_Content.replace(dom_attribute_s, dom_attribute_t)
        # dom_attribute_s = f"={dom_attribute}"
        # dom_attribute_t = f"={url_to_file_format}"
        HTML_Content = HTML_Content.replace(dom_attribute_s, dom_attribute_t)
        return HTML_Content

    def down_website_source_link_suffix(self, ele, url_offset, url_path, url_query, link_attr):
        # 根据link的类型查找对应后续名字。
        url_NewOffset = None
        taty = ele.get_attribute(link_attr)
        taty = str(taty).strip()
        taties = re.split(re.compile(r"\s+"), taty)
        taties = [tag.lower() for tag in taties]
        down_classic = {
            "rel": [
                ("icon", "icon"),
                ("preload", None),
                ("stylesheet", "css"),
                ("mask-icon", "icon"),
                ("fluid-icon", "icon"),
                ("search", None)
            ],
            "type": [
                ("text/css", "css"),
                ("text/javascript", "js"),
            ]
        }
        down_refs = down_classic[link_attr]
        fetch_property = [t[0] for t in down_refs]
        intersection = set(taties).intersection(fetch_property)
        if len(intersection) > 0:
            reftype = intersection.pop()
            for ref in down_refs:
                refname = ref[0]
                suffix = ref[1]
                if suffix != None and refname.__eq__(reftype) and url_offset.endswith(f".{suffix}") is not True:
                    url_NewOffset = f"{url_path}{url_query}.{suffix}"
                    break
        return url_NewOffset

    def url_format(self, url):
        url = re.sub(re.compile(r"[\/\\]+"), "/", url)
        url = re.sub(re.compile(r"[^0-9a-zA-Z\_\-\/]+$"),"", url)
        return url

    def down_website_url_split(self, url):
        urls = [p.strip() for p in re.split(re.compile(r"[\/]+"), url) if p != ""]
        return urls

    def down_website_add_webpageQueue(self, url_web, url_local):
        self.__down_web_page_queue.put(
            (url_web, url_local)
        )

    def down_website_add_resourceList(self, url_web, url_local):
        threadLock.acquire()
        self.__resource_urls.append(sov
            (url_web, url_local, True)
        )
        threadLock.release()

    def down_website_get_resourceList(self):
        self.threadLock.acquire()
        web_resource_item = self.__resource_urls.pop()
        self.threadLock.release()
        return web_resource_item

    def setargs(self,args):
        self.args = args