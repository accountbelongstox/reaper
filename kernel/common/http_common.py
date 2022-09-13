from kernel.base.base import *
import os
from lxml import etree
# import re
import requests
# import re
import urllib
from urllib.parse import urlparse
import http.cookiejar
import ssl
from http.client import HTTPSConnection
# import requests
from concurrent.futures import ThreadPoolExecutor,as_completed
# from multiprocessing import Pool,Process
from selenium import webdriver
import time
from selenium.webdriver.common.by import By

class HttpCommon(BaseClass):
    __header = {
            "accept-language": "zh-CN,zh,en;q=0.9",
            "sec-ch-ua": "Not A;Brand\";v=\"99\", \"Chromium\";v=\"102\", \"Google Chrome\";v=\"102",
            "sec-ch-ua-mobile": "?0",
            "sec-ch-ua-platform": "Windows",
            "sec-fetch-dest": "empty",
            "Connection": "close",
            "sec-fetch-mode": "cors",
            "sec-fetch-site": "same-origin",
            "user-agent":"Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/102.0.5005.63 Safari/537.36"
        }

    def __init__(self,args):
        pass

    def open_url(self,url,decode="utf-8"):
        cookie = http.cookiejar.CookieJar()
        handler = urllib.request.HTTPCookieProcessor(cookie)
        header = [
            ("accept-language", "zh-CN,zh,en;q=0.9"),
            ("sec-ch-ua", "Not A;Brand\";v=\"99\", \"Chromium\";v=\"102\", \"Google Chrome\";v=\"102"),
            ("sec-ch-ua-mobile", "?0"),
            ("sec-ch-ua-platform", "Windows"),
            ("sec-fetch-dest", "empty"),
            ("sec-fetch-mode", "cors"),
            ("sec-fetch-site", "same-origin"),
            ("user-agent", "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/102.0.5005.63 Safari/537.36")
        ]
        opener = urllib.request.build_opener(handler)
        opener.addheaders = header
        text = opener.open(url,verify=False)
        content = text.read()
        if type(decode) == str:
            content = content.decode(decode)
        return content

    def get(self,url):
        proxy = { "http": None, "https": None}
        session = requests.Session()
        session.trust_env = False
        response = session.get(url, verify=False,proxies=proxy,headers=self.__header)
        content = None
        if response.status_code == 200:
            content = response.content
        content = self.string_common.byte_to_str(content)
        return content

    def post(self,url,data={},json=False):
        proxy = { "http": None, "https": None}
        session = requests.Session()
        session.trust_env = False
        information = session.post(url,data, verify=False,proxies=proxy,headers=self.__header)
        content = None
        if information.status_code == 200:
            if json:
                content = information.json()
            else:
                content = information.content
        return content

    def post_as_json(self,url,data={}):
        return self.post(url,data,json=True)

    def down_web(self,url):
        #创建主线程，专用于打开页面，以及分析页面并调用多线程下载
        th_main = self.thread_common.create_thread(
            thread_type="down_web",
            args=url
        )
        th_main.start()

    def down_files(self,tupes_or_list,extract=False):
        # down_files 由多线程模块传给file_down处理,参数使用down_file的参数
        if type(tupes_or_list) != list:
            tupes_or_list = [tupes_or_list]

        for urlli in tupes_or_list:
            if type(urlli) == str:
                urlli = {
                    "url": urlli,
                    "extract": extract
                }
            th = self.thread_common.create_thread(
                thread_type="downs",
                args=urlli
            )
            try:
                th.start()
            except:
                print(f"threads can only be started once, thread name '{th.getName()}'")

    def down_file(self,args,overwrite=False,callback=None,extract=False):
        param = """
                多线程版
                :param tupes_or_list:
                @ 参数为 tuple 类型，则格式为 [
                    ( url, file_name , override , callback,extract),
                    ( url, file_name , override , callback,extract)
                                            ]
                @ 参数 extract 自动解压下载的zip文件
                @ 参数 url 下载url
                @ 参数 file_name 保存的文件
                @ 参数 override 自动覆盖
                @ 参数 callback 回调
                :return:
                """
        if type(args) == tuple:
            urlistuple = args
            url = urlistuple[0]
            try:
                save_filename = urlistuple[1]
            except:
                save_filename = os.path.basename(url)

            try:
                overwrite = urlistuple[2]
            except:
                pass

            try:
                extract = urlistuple[3]
            except:
                pass

            try:
                callback = urlistuple[4]
            except:
                pass
        elif type(args) == str:
            url = args
            save_filename = self.save_name_of_url(url)
            print(f"save_filename {save_filename} ")
        elif type(args) == dict:
            url = args["url"]
            try:
                save_filename = args["save_filename"]
            except:
                save_filename = self.save_name_of_url(url)

            try:
                overwrite = args["overwrite"]
            except:
                overwrite = False

            try:
                extract = args["extract"]
            except:
                extract = False

            try:
                callback = args["callback"]
            except:
                callback = None
        else:
            print(param)
            print(f"args {args}")
            return None

        if overwrite == False and os.path.exists(save_filename) is True and os.path.isfile(save_filename) is True:
            print(f"down filename exists of {save_filename}")
            if extract:self.down_file_extract(save_filename)
            if callback != None: return callback((save_filename,None))
            return None
        print(f"wget start url:{url} to save_filename:{save_filename}")
        content = self.get(url)
        if content == None:
            print(f"content is None.")
            if callback != None: return callback(content)
            return content
        basename = os.path.dirname(save_filename)
        if os.path.exists(basename) is not True and os.path.isdir(basename) is not True:
            self.mkdir(basename)
        if os.path.exists(save_filename) is not True or os.path.isfile(save_filename) is not True or overwrite == True:
            m = "w"
        else:
            m = "r"
        openmode = f"{m}b+"
        f = open(save_filename, openmode)
        f.write(content)
        f.close()
        if extract:self.down_file_extract(save_filename)
        if callback != None: return callback((save_filename,content))
        return (save_filename,content)

    def down_file_extract(self, filename):
        """
        #输助函数,将最后下载的文件解压和删除。
        :param filename:
        :return:
        """
        extract_dir = os.path.dirname(filename)
        print(f"extract file {filename} to {extract_dir}")
        self.file_common.zip_extractall(filename,extract_dir)



    def save_name_of_url(self,url):
        base_save_dir = self.get_base_down_dir()
        url_parse = urlparse(url)
        url_netloc = url_parse.netloc
        url_path = url_parse.path
        save_filename = os.path.join(base_save_dir, url_netloc + url_path)
        return save_filename

    def get_base_down_dir(self):
        downfile = self.config_common.get_public("downfile")
        return downfile

    def mkdir(self, dir):
        if os.path.exists(dir) and os.path.isdir(dir):
            return False
        else:
            os.makedirs(dir, exist_ok=True)
            return True


    def push_url_user(self,url):
        self.selenium_common.open_url_as_new_window(url)
        self.selenium_common.get_html()
        # page_text = self.selenium_common.find_elements_by_tagname('input',is_beautifulsoup=True)
        page_text1 = self.selenium_common.find_element('input',is_beautifulsoup=True)
        # print(page_text)
        for input_tagname1 in page_text1:
            input_tagname2 = str(input_tagname1)
            input_tagname3 = input_tagname2.split('type=')[-1].split(' ')[0].split('/')[0]
            print('{0}是:'.format(input_tagname3),input_tagname1)


    def push_url_text(self, url):
        self.selenium_common.open_url_as_new_window(url)
        self.selenium_common.get_html()
        page_text = self.selenium_common.find_element('input',is_beautifulsoup=True)
        for input_tagname1 in page_text:
            input_tagname2 = str(input_tagname1)
            input_tagname3 = input_tagname2.split('type=')[-1].split(' ')[0].split('/')[0]
            print('{0}是:'.format(input_tagname3), input_tagname1)
            if input_tagname3 == "text":
                input_tagname3.click()
                self.selenium_common.send_keys(input_tagname3,'demo1')
            elif input_tagname3 == "password":
                input_tagname3.click()
                self.selenium_common.send_keys(input_tagname3, 'diyuncms888')
        page_button = self.selenium_common.find_element('button', is_beautifulsoup=True)
        for button_tagname in page_button:
            button_tagname1 = str(button_tagname)
            button_tagname2 = button_tagname1.split('type=')[-1].split(' ')[0].split('>')[0]
            print('{0}是:'.format(button_tagname2), button_tagname1)
            if button_tagname2 == "button":
                button_tagname2.click()
        page_title = self.selenium_common.find_element('textarea', is_beautifulsoup=True)
        page_content = self.selenium_common.find_elements('textbox', is_beautifulsoup=True)
        print('描述', page_title)
        print('内容', page_content)