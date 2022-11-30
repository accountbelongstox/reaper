import json
import operator
import shutil
import pprint
from kernel.base.base import *
import os
import re
import time
# import requests
# from selenium.webdriver.common.desired_capabilities import DesiredCapabilities
# import lxml.html
from lxml import etree
from bs4 import BeautifulSoup
from lxml.cssselect import CSSSelector
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.select import Select
from browsermobproxy import Server
# from queue import Queue
# from multiprocessing import Pool
# from selenium.webdriver.support.ui import WebDriverWait
# from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.desired_capabilities import DesiredCapabilities
# from selenium.webdriver.support.events import EventFiringWebDriver, AbstractEventListener
from selenium.common.exceptions import NoSuchElementException
from selenium.webdriver.common.action_chains import ActionChains
# import sched
from PIL import Image

# from pykeyboard import PyKeyboard
# 为保证 driver 能正常打开
# import traceback

drivers_dict = {}
webdriver_as = webdriver


class Selenium(BaseClass):
    __driver = None
    __driver_name = None
    __googledriver_versions_from_down_url = []
    __driver_remote_url = {
        "chrome": 'http://registry.npmmirror.com/-/binary/chromedriver/',
        "edge": 'https://msedgedriver.azureedge.net/',
    }
    __wait_open_url = None
    __browsermob_proxy = False
    __driver_downing_fromremote = False
    __download_dir = None  # 默认下载目录

    def __init__(self, args):
        global drivers_dict
        driver_name = str(args)
        self.__driver_name = driver_name
        drivers_dict[self.__driver_name] = None

    # 创建一个浏览器，并可直接使用类的功能无须传递driver对象
    def bind(self, module):
        driver_name = id(module)
        selenium = Selenium(driver_name)
        module = self.load_module.set_property(module, selenium)
        return module

    def open(self, url, load_jquery=False, callback=None, wait=None, not_wait=False, width=None, height=None,
             headless=None, mobile=False, open_devtools=False, driver_type="chrome", disable_gpu=False):
        if self.is_exists_driver() != False:
            self.switch_to(url, load_jquery)
            return True

        if wait is None:
            wait = -1
        if wait == 0 or not_wait is True:
            not_wait = True
            time.sleep(0.1)
        else:
            not_wait = False
        driver = self.get_driver(not_wait=not_wait, width=width, height=height, headless=headless, mobile=mobile,
                                 open_devtools=open_devtools, driver_type=driver_type, disable_gpu=disable_gpu)
        if wait > 0:
            driver.set_page_load_timeout(wait)
            driver.set_script_timeout(wait)  # 这两种设置都进行才有效

        current_url = driver.current_url
        if self.__browsermob_proxy == True:
            self.proxy.new_har(url, options={'captureHeaders': True, 'captureContent': True})
        if current_url == 'data:,':
            try:
                driver.get(url=url)
            except:
                print(f"Timed out receiving message from renderer:{wait}")
        else:
            print(f"switch_to \"{url}\"")
            self.switch_to(url, load_jquery)
        if callback != None:
            callback(driver)
        else:
            return driver

    def is_ready(self):
        time.sleep(0.1)
        if self.get_current_url() == "data:,":
            return False
        js = "return document.readyState"
        ready = self.execute_js(js)
        if ready == "complete":
            return True
        else:
            return False

    def open_ready_wait(self):
        if self.is_ready() is not True:
            time.sleep(1)
            print("open_ready_wait")
            return self.open_ready_wait()
        else:
            return True

    def get_window_handles(self):
        driver = self.get_driver()
        return driver.window_handles

    def get_window_handles_length(self):
        driver = self.get_driver()
        len_drivers = len(driver.window_handles)
        return len_drivers

    def switch_to(self, url_or_index, loadJQuery=False):
        driver = self.get_driver()
        len_drivers = len(driver.window_handles)
        if type(url_or_index) is int:
            index = url_or_index
            # print(f"switch ot index {index}")
            if index >= len_drivers:
                index = len_drivers - 1
            driver.switch_to.window(driver.window_handles[index])
        else:
            url = url_or_index
            url_exists = False
            url_eq = url.split('?')[0]
            url_eq = url_eq.split('#')[0]
            for index in range(len_drivers):
                driver.switch_to.window(driver.window_handles[index])
                time.sleep(0.5)

                current_url = driver.current_url
                current_url = current_url.split("?")[0]
                current_url = current_url.split("#")[0]

                if operator.__eq__(current_url, url_eq):
                    url_exists = True
                    print(f"init_driver found url is {driver.current_url}")
                    break
            if not url_exists:
                js = "window.open('{}','_blank');"
                driver.execute_script(js.format(url))
                print(f"init_driver open url by new window for page {url}")
                len_drivers = len(driver.window_handles)
                index = len_drivers - 1
                driver.switch_to.window(driver.window_handles[index])
                if loadJQuery: self.load_jquery_wait()
            else:
                driver.refresh()
                print(f"init_driver url is existed of {url},url as refresh.")
                time.sleep(0.5)

    def open_local_html_to_beautifulsoup(self, html_name="index.html"):
        content = self.com_file.load_html(html_name)
        beautifulsoup = self.com_http.find_text_from_beautifulsoup(content)
        return beautifulsoup

    def screenshot_of_webpage(self, selector=None, file_path=None):  # screenshot
        driver = self.get_driver()
        file_path = self.get_screenshot_save_path(file_path)
        if selector is not None:
            return self.screenshot_of_element(selector, file_path)
        driver.save_screenshot(file_path)
        # page_snap_obj = Image.open(file_path)
        # print(f"page_snap_obj {page_snap_obj}")
        return file_path

    def get_screenshot_save_path(self, filename=None):
        if filename is None:
            filename = self.com_string.random_string(32, upper=False) + ".png"
        temp_dir = self.com_config.get_public("downfile/screenshot")
        self.com_file.mkdir(temp_dir)
        file_path = self.com_string.dir_normal(
            os.path.join(temp_dir, filename)
        )
        return file_path

    # def get_image(driver):  # 对验证码所在位置进行定位，然后截取验证码图片
    #     img = driver.find_element_by_class_name('code')
    #     time.sleep(2)
    #     location = img.location
    #     print(location)
    #     size = img.size
    #     left = location['x']
    #     top = location['y']
    #     right = left + size['width']
    #     bottom = top + size['height']
    #
    #     page_snap_obj = get_snap(driver)
    #     image_obj = page_snap_obj.crop((left, top, right, bottom))
    #     # image_obj.show()
    #     return image_obj  # 得到的就是验证码

    def screenshot_of_element(self, selector=None, file_path=None):  # 对目标网页进行截屏。这里截的是全屏
        file_path = self.get_screenshot_save_path(file_path)
        driver = self.get_driver()
        element = self.find_element(selector)
        location = element.location
        size = element.size
        driver.save_screenshot(file_path)
        x = location['x']
        y = location['y']
        width = location['x'] + size['width']
        height = location['y'] + size['height']
        im = Image.open(file_path)
        im = im.crop((int(x), int(y), int(width), int(height)))
        temp_img = self.get_screenshot_save_path()
        im.save(temp_img)
        im.close()
        os.remove(file_path)
        shutil.copyfile(temp_img, file_path)
        os.remove(temp_img)
        return file_path

    def is_exists_driver(self):
        global drivers_dict
        if drivers_dict[self.__driver_name] != None and self.__driver != None and operator.__eq__(
                drivers_dict[self.__driver_name], self.__driver):
            return self.__driver
        else:
            return False

    def get_driver(self, not_wait=False, width=None, height=None, headless=None, mobile=False, open_devtools=False,
                   proxy=False, driver_type="chrome", disable_gpu=False):
        is_exists_driver = self.is_exists_driver()
        if is_exists_driver is not False:
            return self.__driver

        if not headless:
            if width == None:
                width = 1950
            if height == None:
                height = 980
        else:
            if width is None:
                width = 800
            if height is None:
                height = 600

        driver_path = self.get_driver_path(driver_type)
        if driver_type == "chrome":
            driver = self.get_chrome_driver(driver_path=driver_path, proxy=proxy, open_devtools=open_devtools,
                                            mobile=mobile, width=width, height=height, not_wait=not_wait,
                                            headless=headless, disable_gpu=disable_gpu)
        else:
            driver = self.get_edge_driver(driver_path=driver_path, proxy=proxy, open_devtools=open_devtools,
                                          mobile=mobile, width=width, height=height, not_wait=not_wait,
                                          headless=headless, disable_gpu=disable_gpu)
        self.print_driver_parameters(driver_type)
        # 设置页面加载时间
        # driver.set_page_load_timeout(1)
        # 设置脚本超时时间
        # driver.set_script_timeout(1)

        stealth_min = self.com_config.get_libs('stealth.min.js')
        stealth_min = self.com_file.read_file(stealth_min)
        driver.execute_cdp_cmd("Page.addScriptToEvaluateOnNewDocument", {
            "source": stealth_min
        })
        base_js = self.com_config.get_libs('$$.js')
        base_js = self.com_file.read_file(base_js)
        driver.execute_cdp_cmd("Page.addScriptToEvaluateOnNewDocument", {
            "source": base_js
        })
        # driver.set_window_size(width, height)
        # windows_position = self.load_module.get_window_position(20)
        # window_x = windows_position.get("x")
        # window_y = windows_position.get("y")
        # driver.set_window_position(window_x, window_y)
        self.set_driver(driver)
        return driver

    def get_window_position(self):
        driver = self.get_driver()
        position = driver.get_window_position()
        return position

    def get_edge_driver(self, driver_path, width, height, proxy=None, open_devtools=None, mobile=None, not_wait=False,
                        headless=False, disable_gpu=False, driver_type="edge"):
        global webdriver_as
        from selenium.webdriver.edge.service import Service
        from selenium.webdriver.edge.options import Options
        options = Options()
        service = Service(driver_path)
        options = self.get_driver_public_options(options, headless=headless, width=width, height=height,
                                                 disable_gpu=disable_gpu)
        driver = webdriver_as.Edge(service=service, options=options)
        return driver

    def delete_olddownloaddir(self,download_prefix='downfile_'):
        down_dir = self.load_module.get_control_dir()
        down_dirlist = os.listdir(down_dir)
        c_time = self.com_util.create_timestamp()
        for down in down_dirlist:
            if down.find(download_prefix) != -1:
                old_download_dir = self.load_module.get_control_dir(down)
                st_ctime = os.stat(old_download_dir).st_ctime
                time_difference = c_time - st_ctime
                if time_difference > 60:
                    print(f"delete old download_dir before {time_difference} of {old_download_dir}")
                    self.com_util.rmtree(old_download_dir)

    def get_download_dir(self,filename=""):
        driver_hash = self.com_string.md5(self.__driver_name)
        if not self.__download_dir:
            download_prefix = 'downfile_'
            self.delete_olddownloaddir(download_prefix)
            down_dir = self.load_module.get_control_dir(f"{download_prefix}{driver_hash}")
            down_dir = self.com_string.dir_normal(down_dir)
            self.__download_dir = down_dir
        filename = os.path.join(self.__download_dir,filename)
        return filename

    def get_download_files(self, wait=10):
        return self.get_download_file(wait=wait)

    def get_download_filename(self, file_name):
        if self.com_http.is_url(file_name):
            file_name = os.path.basename(file_name)
        file_name = file_name.split("?")[0]
        return file_name

    def is_dynamic_url(self,url):
        url = url.split("?")[-1]
        if url.find('.') == -1:
            return True
        return False

    def get_download_file(self, file_name=None, wait=10):
        wait_second = 0.5
        index = 0
        download_dir = self.get_download_dir()
        listdir = os.listdir(download_dir)
        if file_name != None:
            file_name = self.get_download_filename(file_name)

        result = {
            "dynamic_url":False,
            "file_name":None,
        }
        # 代表是动态地址,即没有文件后缀名的
        def is_exists_file(file_name,listdir):
            if file_name in listdir:
                return file_name
            # 对于动态url
            if self.is_dynamic_url(file_name) == True:
                result["dynamic_url"] = True
                check_file = None
                for file in listdir:
                    # 优先查找带xxx.的文件名
                    if file.startswith(f"{file_name}.") and check_file == None:
                        check_file = file
                    if file.startswith(file_name) and check_file == None:
                        check_file = file
                if check_file != None:
                    return check_file
            return None

        find_filename = is_exists_file(file_name,listdir)
        while find_filename == None and (index / 2) < wait:
            if index % 2 == 0 and index > wait:
                self.com_util.print_info(f"wait downloading file {index / 2}s at {download_dir}")
            time.sleep(wait_second)
            listdir = os.listdir(download_dir)
            index += wait_second
            find_filename = is_exists_file(file_name,listdir)
        if find_filename != None:
            result["file_name"] = os.path.join(download_dir, find_filename)
        return result

    def set_download_dir(self, download_dir):
        self.__download_dir = download_dir
        return self.__download_dir

    def get_driver_public_options(self, options, width, height, headless=False, disable_gpu=False):
        options.add_argument('--ignore-certificate-errors')
        options.add_argument('--ignore-ssl-errors')
        options.add_argument('--disable-infobars')  # 禁用浏览器正在被自动化程序控制的提示
        options.add_argument("no-sandbox")
        options.add_argument(f'--window-size={width},{height}')
        options.add_argument("--incognito")
        options.add_argument("--mute-audio")  # 静音
        #解决跨域
        options.add_argument("--args --disable-web-security --user-data-dir")
        options.add_argument("--trusted-download-sources")

        options.add_experimental_option('excludeSwitches', ['enable-automation'])
        options.add_experimental_option('excludeSwitches', ['enable-logging'])
        # 禁止自动关闭浏览器
        options.add_experimental_option('detach', True)

        down_dir = self.get_download_dir()
        self.com_file.mkdir(down_dir)
        prefs = {
            # 'profile.managed_default_content_settings.images': 2,
            # # "profile.managed_default_content_settings.images": 1,
            'profile.default_content_settings.popups': 0,  # 防止保存弹窗
            'download.default_directory': down_dir,  # 设置默认下载路径
            "profile.default_content_setting_values.automatic_downloads": 1,  # 允许多文件下载
        }
        options.add_experimental_option('prefs', prefs)

        if headless:
            options.add_argument('--headless')
            options.add_argument('--disable-gpu')
        if disable_gpu:
            options.add_argument('--disable-gpu')
            options.add_argument('--blink-settings=imagesEnabled=false')  # 不加载图片, 提升速度
        return options

    def get_chrome_driver(self, driver_path, width, height, proxy=None, open_devtools=None, mobile=None, not_wait=False,
                          headless=False, disable_gpu=False, driver_type="chrome"):
        from selenium.webdriver.chrome.service import Service
        from selenium.webdriver.chrome.options import Options

        options = Options()
        service = Service(driver_path)

        if open_devtools:
            options.add_argument('--auto-open-devtools-for-tabs')

        if mobile:
            width = 375
            height = 812
            pixelRatio = 3.0
            mobile_emulation = {
                "deviceName": "iPhone SE",
            }
            mobile_emulation = {
                "deviceName": "iPhone SE",
                "deviceMetrics": {"width": width,
                                  "height": height,
                                  "pixelRatio": pixelRatio
                                  },
                "userAgent": "Mozilla/5.0 (Linux; Android 4.2.1; en-us; Nexus 5 Build/JOP40D) AppleWebKit/535.19 (KHTML, like Gecko) Chrome/18.0.1025.166 Mobile Safari/535.19"}
            # options.use_chromium = True
            # options.set_capability("platformName", "Android 6.0")
            # options.set_capability("mobileEmulation", mobile_emulation)
            options.add_experimental_option("mobileEmulation", mobile_emulation)
            # options.add_experimental_option("mobileEmulation", mobile_emulation_specs)

        options = self.get_driver_public_options(options, headless=headless, width=width, height=height,
                                                 disable_gpu=disable_gpu)

        # 处理SSL证书错误问题
        # prefs = {'profile.managed_default_content_settings.images': 2}
        # options.add_experimental_option('prefs', prefs)
        options.add_experimental_option("excludeSwitches", ['enable-automation', 'enable-logging'])
        options.add_argument(
            'user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/105.0.0.0 Safari/537.36')

        desired_capabilities = DesiredCapabilities.CHROME
        if not_wait:
            options.page_load_strategy = "none"  # 'normal', 'eager', 'none' 页面加载模式
            desired_capabilities["pageLoadStrategy"] = "none"
        if self.load_module.is_windows():
            chrome_filedir = "libs/chrome/chrome.exe"
            chrome_dir = self.com_config.get_public(chrome_filedir)
            if self.com_file.isfile(chrome_dir):
                options.binary_location = self.com_config.get_public(chrome_filedir)

        desired_capabilities['loggingPrefs'] = {
            'browser': 'ALL',
            # 'driver': 'ALL',
            'performance': 'ALL',
        }

        desired_capabilities['goog:chromeOptions'] = {
            'perfLoggingPrefs': {
                'enableNetwork': True,
            },
            'w3c': False,
        }
        if proxy:
            browsermob_proxy = self.com_config.get_public("libs/browsermob-proxy-2.1.4/bin/browsermob-proxy")
            self.__browsermob_proxy = True
            if self.load_module.is_windows():
                browsermob_proxy += ".bat"
            server = Server(browsermob_proxy)
            server.start()
            self.proxy = server.create_proxy()
            proxy_argument = '--proxy-server={0}'.format(self.proxy.proxy)
            options.add_argument(proxy_argument)

        driver = webdriver_as.Chrome(service=service, chrome_options=options, desired_capabilities=desired_capabilities)
        return driver

    def print_driver_parameters(self, driver_type):
        parameter_names = ""
        if driver_type == "chrome":
            parameter_names = self.com_util.get_parameter(webdriver_as.Chrome)
        elif driver_type == "edge":
            parameter_names = self.com_util.get_parameter(webdriver_as.Edge)
        print(f"\tdriver_parameter:{parameter_names}")

    # 设置driver驱动器，用于在不同线程间共享driver
    def set_driver(self, driver):
        global drivers_dict
        drivers_dict[self.__driver_name] = None
        drivers_dict[self.__driver_name] = driver
        self.__driver = drivers_dict[self.__driver_name]
        return self.__driver

    def test_bot(self, driver_type):
        self.open("https://bot.sannysoft.com/", driver_type=driver_type)

    def get_current_window_handle_index(self, driver):
        current_window_handle = driver.current_window_handle
        for i in range(len(driver.window_handles)):
            if current_window_handle == driver.window_handles[i]:
                return i
        return -1

    def document_initialised(self):
        driver = self.get_driver()
        outerHTML = driver.execute_script("return document.documentElement.outerHTML")
        if outerHTML != None or len(outerHTML) > 0:
            print(f"outerHTML{len(outerHTML)}")
        return driver

    def find_html_wait(self):
        driver = self.get_driver()
        outerHTML = driver.execute_script("return document.documentElement.outerHTML")
        if outerHTML != None or len(outerHTML) > 0:
            return outerHTML
        else:
            return self.find_html_wait()

    def get_html(self):
        outerHTML = self.execute_js_code("return document.documentElement.outerHTML")
        return outerHTML

    def get_document_links(self):
        js_code = """
        let hrefs = []
        let links = document.links
        for(let i=0;i<links.length;i++){
            let e = links[i];
            hrefs.push({
                index:i,
                href:e.href,
                base_url:e.baseURI,
                host:e.host,
                hostname:e.hostname,
                inner_text:e.innerText,
                origin:e.origin,
                pathname:e.pathname,
                protocol:e.protocol
            })
        }
        return hrefs
        """
        links = self.execute_js_and_return(js_code)
        return links

    def get_document_resource(self, tagname="img"):
        js_code = """
        let res = []
        let tags = document.querySelectorAll(`%s`)
        for(let i=0;i<tags.length;i++){
            let e = tags[i];
            let src = null;
            if(e.dataset){
                src = e.dataset.src
            }
            res.push({
                index:i,
                href:e.href,
                src:src,
                current_src:e.currentSrc,
                dataset:e.dataset,
                nodeName:e.nodeName,
                base_url:e.baseURI,
                host:e.host,
                hostname:e.hostname,
                inner_text:e.innerText,
                origin:e.origin,
                pathname:e.pathname,
                protocol:e.protocol,
                alt:e.alt
            })
        }
        return res
        """ % (tagname,)
        res = self.execute_js_and_return(js_code)
        return res

    def set_html(self, content, selector=None):
        driver = self.get_driver()
        content = self.com_db.encode(content)
        if not selector:
            js = f"document.documentElement.innerHTML = `{content}`"
        else:
            js = f"document.querySelector('{selector}').innerHTML = `{content}`"
        driver.execute_script(js)

    def close(self, handle=None):
        self.close_window(handle)

    def close_window(self, handle=None):
        if type(handle) is str:
            # TODO
            pass
        driver = self.get_driver()
        driver.close()

    def close_page(self, url=None, safe=True):
        if type(url) == str:
            self.switch_to(url)
        if safe == True:
            handlength = self.get_window_handles_length()
            # print(f"handlength {handlength}")
            if handlength <= 1:
                return True
        jscode = 'window.close()'
        self.execute_js_code(jscode)

    def quit(self):
        driver = self.get_driver()
        driver.quit()

    def get_current_url(self, full=False):
        driver = self.get_driver()
        try:
            current_url = driver.current_url
        except Exception  as e:
            self.com_util.print_warn(e)
            current_url = ''
        if full == False:
            current_url = current_url.split("?")[0]
        return current_url

    def is_element(self, element):
        if element.__class__.__name__ == "WebElement":
            return True
        elif type(element) == str:
            elements = self.execute_js_wait(f"return document.querySelectorAll(`{element}`)")
            if len(elements) == 0:
                return False
            else:
                return True
        else:
            return False

    def element_exist(self, element):
        return self.is_element(element)

    def find_element(self, selector, is_beautifulsoup=False, driver=None):
        eles = self.find_elements(selector, is_beautifulsoup, driver)
        ele = None
        if len(eles) > 0:
            ele = eles[0]
        return ele

    def find_element_by_js(self, selector):
        js = f"return document.querySelector(`{selector}`)"
        return self.execute_js_code(js)

    def find_element_by_js_wait(self, selector, deep=30):
        js = f"return document.querySelector(`{selector}`)"
        ele = self.execute_js_code(js)
        setpin = 2
        index = 0
        while ele == None and (setpin * index) < deep:
            wait_second = index / setpin
            if wait_second > 5:
                print(f"Waiting {selector} {index / setpin} seconds js:{js}")
            time.sleep(0.5)
            ele = self.execute_js_code(js)
            index += 1
        return ele

    def find_elements_wait(self, selector, deep=0, driver=None):
        if deep == 3 and deep is not False:
            return None
        try:
            ele = self.find_elements(selector, driver=driver)
            if ele != None:
                return ele
            raise NoSuchElementException
        except:
            deep += 1
            time.sleep(0.5)
            return self.find_elements_wait(selector, deep, driver)

    def find_element_wait(self, selector, deep=0):
        if deep == 3 * 3 and deep is not False:
            return None
        try:
            ele = self.find_element(selector)
            if ele != None:
                return ele
            raise NoSuchElementException
        except:
            deep += 1
            time.sleep(1)
            return self.find_element_wait(selector, deep)

    def find_content(self, selector):
        ele = self.find_element_wait(selector)
        try:
            text = ele.text
            text = text.replace("0", "")
            if len(text) > 0:
                return ele.text
        except:
            return None

    def find_content_wait(self, selector, deep=0, url=None):
        if deep == 3:
            print(f"find_elements_value_wait deep {deep}")
            return None
        print(f"find_elements_value_wait {selector}")
        text = self.find_content(selector)
        if text is not None:
            return text
        else:
            deep += 1
            time.sleep(1)
            return self.find_content_wait(selector, deep)

    def find_elements(self, selector, is_beautifulsoup=False, driver=None):
        st = self.selector_parse(selector)
        if st == "css":
            ele = self.find_elements_by_css(selector, is_beautifulsoup, driver)
        elif st == "xpath":
            ele = self.find_elements_by_xpath(selector, is_beautifulsoup, driver)
        elif st == "id":
            ele = self.find_elements_by_id(selector, is_beautifulsoup, driver)
        elif st == "tag":
            ele = self.find_elements_by_tagname(selector, is_beautifulsoup, driver)
        else:
            ele = None

        if type(ele) != list:
            eles = [ele]
        else:
            eles = ele
        return eles

    def find_html_by_js_wait(self, selector, deep=None, no_wait=False):
        if selector[0] == '/':
            js = f"return document.evaluate('{selector}',document,null,XPathResult.FIRST_ORDERED_NODE_TYPE,null,) ? document.evaluate('{selector}',document,null,XPathResult.FIRST_ORDERED_NODE_TYPE,null,).singleNodeValue.outerHTML : null"
        else:
            js = f"""return document.querySelector('{selector}') ? document.querySelector('{selector}').outerHTML : null"""

        if no_wait:
            return self.execute_js(js)
        return self.execute_js_wait(js, deep)

    def find_html_by_js(self, selector):
        return self.find_html_by_js_wait(selector, no_wait=True)

    def find_element_value_by_js_wait(self, selector, no_wait=False, deep=30, text_not=None, info=False):
        if selector[0] == '/':
            js = f"return document.evaluate(`{selector}`,document,null,XPathResult.FIRST_ORDERED_NODE_TYPE,null,) ? document.evaluate(`{selector}`,document,null,XPathResult.FIRST_ORDERED_NODE_TYPE,null,).singleNodeValue.innerHTML : null"
        else:
            js = f"return document.querySelector(`{selector}`) ? document.querySelector(`{selector}`).textContent : null"
        if no_wait:
            return self.execute_js(js)
        if deep == False:
            deep = 99999
        self.find_element_by_js_wait(selector, deep=deep)

        setpin = 2
        val = self.execute_js_code(js)
        val = val.strip()
        index = 0
        while val == text_not and (index / setpin) < deep:
            if info == True:
                print(
                    f"Waiting-selector[fun:find_element_value_by_js_wait]: ({selector}) \n\tvalue:{val}, (value-not: {text_not})\n\twaited: {index / setpin} second, deep: {deep}")
            time.sleep(0.5)
            val = self.execute_js_code(js)
            index += 1

        return val

    def find_value_by_js(self, selector):
        return self.find_element_value_by_js_wait(selector, no_wait=True)

    def find_value_by_js_wait(self, selector, text_not=None, deep=10, info=False):
        return self.find_element_value_by_js_wait(selector, text_not=text_not, deep=deep, info=info)

    def find_attr_by_js(self, selector, attr):
        js = f"return document.querySelector(`{selector}`) ? document.querySelector(`{selector}`).{attr} : null"
        return self.execute_js_code(js)

    def find_text_content_by_js_wait(self, selector, text_not=None, deep=10, info=False):
        return self.find_element_value_by_js_wait(selector, text_not=text_not, deep=deep, info=info)

    def find_text_content_by_js(self, selector):
        return self.find_element_value_by_js_wait(selector, no_wait=True)

    def find_text_content_list(self, selector, child_selector="", next_sibling="", html_split=False,
                               deduplication=False, attribute="innerHTML", wait=False):
        # 第一个选择器 selector就要形成组,第二个选择选择器只是选择里边的细节元素.
        clear_element = ["", " ", "|", ", ", ",", '"']
        if child_selector != "" and child_selector:
            child_selector = f".querySelector(`{child_selector}`)"
        if next_sibling != "":
            selector_sentence = f"document.querySelector(`{selector}`){next_sibling};"
        else:
            selector_sentence = f"document.querySelectorAll(`{selector}`);"
        if html_split == True:
            html_split = ".split(/<.+?>/)"
        else:
            html_split = ""
        wait_while = ""
        if wait == True:
            wait_while = """let index = 0;
            while(df_div == null || df_div.length == 0){
                console.log(index)
                df_div = get_df_div()
                index++
            }"""
        js = """
        function get_find_text_content_list() { 
            let content_list = []
            let df_div;
            let get_df_div = ()=>{
                try{
                    df_div = %s
                    return df_div
                }catch(e) {
                    console.log(e)
                    return []
                }
            }
            df_div = get_df_div()
            %s
            if(!df_div){
                return []
            }
            for(let i = 0; i < df_div.length; i++){
                let e
                try{
                    e = df_div[i]%s.%s%s
                    content_list.push(e)
                }catch(e) {
                    return []
                }
            }
            return content_list
        }
        return get_find_text_content_list();
        """ % (selector_sentence, wait_while, child_selector, attribute, html_split)

        text_content_list = self.execute_js_and_return(js)
        text_content_list = self.com_util.clear_value(text_content_list, clear_element)
        for content in text_content_list:
            self.com_util.clear_value(content, clear_element)
        if deduplication:
            text_content_list = self.com_util.deduplication(text_content_list)
        return text_content_list

    def find_elements_value_by_js_wait(self, selector, url=None):
        cont = self.statistical_elements_wait(selector, url=url)
        cont = int(cont)
        texts = []
        for el in range(cont):
            js = f"return document.querySelectorAll('{selector}') ? document.querySelectorAll('{selector}')[{el}].textContent : null"

            text = self.execute_js_wait(js)

            texts.append(text)
        return texts

    def find_property(self, selector, attr_val, url=None):
        print(f"find_elements_attr_by_js_wait {selector} Get {attr_val}")
        cont = self.statistical_elements(selector, url=url)
        cont = int(cont)
        texts = []
        for el in range(cont):
            js = f"return document.querySelectorAll('{selector}') ? document.querySelectorAll('{selector}')[{el}]['{attr_val}'] : null"
            text = self.execute_javascript(js)
            texts.append(text)
        return texts

    def find_property_wait(self, selector, attr_val, url=None):
        print(f"find_elements_attr_by_js_wait {selector} Get {attr_val}")
        cont = self.statistical_elements_wait(selector, url=url)
        cont = int(cont)
        texts = []
        for el in range(cont):
            js = f"return document.querySelectorAll('{selector}') ? document.querySelectorAll('{selector}')[{el}]['{attr_val}'] : null"

            text = self.execute_js_wait(js)

            texts.append(text)
        return texts

    def statistical_elements(self, selector):
        js = f"return document.querySelectorAll('{selector}') ? document.querySelectorAll('{selector}').length.toString() : 0"

        cont = self.execute_js_wait(js)

        cont = int(cont)
        return cont

    def statistical_elements_wait(self, selector, num=0, url=None):
        cont = self.statistical_elements(selector)
        if num == 2 and url is not None:
            # 如果连续查找不到元素,有可能浏览器被操作,查找当前url是否还存在,不存在则打开
            self.open_url_as_new_window(url)
            time.sleep(2)
        if cont > 0 or num == 3:
            print(f"find_elements_count_wait cont:{cont}")
            return cont
        else:
            time.sleep(1)
            driver = self.get_driver()
            # print(driver.page_source)
            num += 1
            current_url = driver.current_url
            print(f"find_elements_count_wait url {current_url} as cont:{cont}")
            return self.statistical_elements_wait(selector, num)

    def second_find_elements(self, ele, selector):
        st = self.selector_parse(selector)
        print(f"second_find_elements {selector}")
        eles = None
        if st == "css":
            eles = ele.find_elements(By.CSS_SELECTOR, selector)
        if st == "xpath":
            eles = ele.find_element(By.XPATH, selector)
        if st == "id":
            selector = selector[1:]
            eles = ele.find_element(By.ID, selector)
        if st == "tag":
            eles = ele.find_elements(By.TAG_NAME, selector.replace("<", "").replace(">", ""))
        if st == "text":
            eles = ele.find_elements_by_link_text(selector)
        return eles

    def selector_parse(self, selector):
        selector = selector.strip().lower()
        HTML_TABS = ["<a>", "<abbr>", "<acronym>", "<abbr>", "<address>", "<applet>", "<embed>", "<object>", "<area>",
                     "<article>", "<aside>", "<audio>", "<b>", "<base>", "<basefont>", "<bdi>", "<bdo>", "<big>",
                     "<blockquote>", "<body>", "<br>", "<button>", "<canvas>", "<caption>", "<center>", "<cite>",
                     "<code>", "<col>", "<colgroup>", "<command>", "<data>", "<datalist>", "<dd>", "<del>", "<details>",
                     "<dir>", "<div>", "<dfn>", "<dialog>", "<dl>", "<dt>", "<em>", "<embed>", "<fieldset>",
                     "<figcaption>", "<figure>", "<font>", "<footer>", "<form>", "<frame>", "<frameset>", "<h1>",
                     "<h2>", "<h3>", "<h4>", "<h5>", "<h6>", "<head>", "<header>", "<hr>", "<html>", "<i>", "<iframe>",
                     "<img>", "<input>", "<ins>", "<isindex>", "<kbd>", "<keygen>", "<label>", "<legend>", "<li>",
                     "<link>", "<main>", "<map>", "<mark>", "<menu>", "<menuitem>", "<meta>", "<meter>", "<nav>",
                     "<noframes>", "<noscript>", "<object>", "<ol>", "<optgroup>", "<option>", "<output>", "<p>",
                     "<param>", "<pre>", "<progress>", "<q>", "<rp>", "<rt>", "<ruby>", "<s>", "<samp>", "<script>",
                     "<section>", "<select>", "<small>", "<source>", "<span>", "<strike>", "<del>", "<s>", "<strong>",
                     "<style>", "<sub>", "<summary>", "<details>", "<sup>", "<svg>", "<table>", "<tbody>", "<td>",
                     "<template>", "<textarea>", "<tfoot>", "<th>", "<thead>", "<time>", "<title>", "<tr>", "<track>",
                     "<tt>", "<u>", "<ul>", "<var>", "<video>", "<wbr>", "<xmp>"]
        first_alphabet = selector[0]
        if first_alphabet == "/":
            return "xpath"
        elif first_alphabet == "#":
            return "id"
        elif f"<{selector}>" in HTML_TABS or selector in HTML_TABS:
            return "tag"
        elif first_alphabet in [".","["] \
                or selector.find(" ") != -1\
                or selector.find(":") != -1\
                or selector.find("[") != -1\
                or selector.find(">") != -1\
                :
            return "css"
        else:
            return "text"

    def find_elements_by_tagname(self, selector, is_beautifulsoup, driver=None):
        if driver is None:
            driver = self.get_driver()
        selector = selector.replace("<", "").replace(">", "")
        if is_beautifulsoup:
            html = self.find_html_wait()
            soup = BeautifulSoup(html, "html.parser")
            eles = soup.find_all(selector)
        else:
            eles = driver.find_elements(By.TAG_NAME, selector)
        return eles

    def find_elements_by_id(self, selector, is_beautifulsoup, driver=None):
        if driver is None:
            driver = self.get_driver()
        selector = selector[1:]
        if is_beautifulsoup:
            html = self.find_html_wait()
            soup = BeautifulSoup(html, "html.parser")
            ele = [soup.find(id=selector)]
        else:
            ele = [driver.find_element(By.ID, selector)]
        return ele

    def find_elements_by_css(self, selector, is_beautifulsoup, driver=None):
        if driver is None:
            driver = self.get_driver()
        if is_beautifulsoup:
            html = self.find_html_wait()
            soup = BeautifulSoup(html, "html.parser")
            eles = soup.select(selector)
            # print(eles)
            # tree = etree.HTML(html)
            # selector = CSSSelector(selector)
            # for ele in selector(tree):
            #     eles.append(ele)
        else:
            eles = driver.find_elements(By.CSS_SELECTOR, selector)
        return eles

    def find_elements_by_xpath(self, selector, is_beautifulsoup, driver=None):
        if driver is None:
            driver = self.get_driver()
        if is_beautifulsoup:
            html = self.find_html_wait()
            tree = etree.HTML(html)
            ele = tree.xpath("//*")
        else:
            print(f"find_elements_by_xpath ", selector)
            ele = driver.find_element(By.XPATH, selector)
        return ele

    def find_text_from(self, selector, s_text):
        menus = self.find_elements(selector)
        index = 0
        eles = []
        for m in menus:
            text = m.text
            if text == None:
                text = ""
            text = text.strip()
            if text.__eq__(s_text):
                eles.append(menus[index])
            index += 1
        return eles[0]

    def action_element(self, selector, action, value=None):
        selector_parse = self.selector_parse(selector)
        if selector_parse == "xpath":
            js = f"document.evaluate('{selector}', document).iterateNext()"

            if action == "click":
                js += (".click()")
            elif action == "value":
                js = js % (".value = '%s'" % value)
        else:
            js = f"document.querySelectorAll('{selector}')"
            js += ".forEach(%s)"
            if action == "click":
                js = js % ("ele =>{ele.click()}")
            elif action == "value":
                js = js % "ele=>{console.log(ele.value);ele.value = '%s'}"
                js = js % value
            else:
                js = js % ("ele =>{ele.%s()}")
                js = js % (action)
        return self.execute_js(js)

    def search_content(self, search_content, search_selector, submit_selector):
        search = self.find_element(search_selector)
        search.send_keys(search_content)
        submit = self.find_element(submit_selector)
        submit.click()
        return self.get_current_url()

    def verification_text_click_code(self, args, screenshot=False):
        hint_selector = args.get('hint')
        identification_zone_selector = args.get('identification_zone')
        if screenshot:
            hint_img_path = self.screenshot_of_element(hint_selector)
            identification_zone_selector = self.screenshot_of_element(identification_zone_selector)
        else:
            hint_img = self.find_property_wait(hint_selector, "src")
            hint_img_path = self.com_http.down_file(hint_img)
            identification_zone_img = self.find_property_wait(identification_zone_selector, "src")
            identification_zone = self.com_http.down_file(identification_zone_img)
            print(f"hint_img_path {hint_img_path}")
            print(f"hint_img_path {identification_zone}")

        click_zone = args.get('click_zone')

    def wait_element(self, selector, timeout=None, deep=None):
        if timeout >= deep:
            return False
        element = self.find_element(selector)
        if element is None:
            time.sleep(1)
            deep += 1
            self.wait_element(selector, deep)
        else:
            return True

    def execute_js(self, js):
        js_path = self.com_config.get_static("js_dir")
        js_path = os.path.join(js_path, js)
        if os.path.isfile(js_path) or os.path.isfile(js):
            return self.execute_js_file(js)
        else:
            return self.execute_js_code(js)

    def execute_js_and_return(self, js_code, not_wait=False):
        temp_parameter = "__$temp_$parameter"
        js = """
        window.%s = (()=>{
            %s
        })()
        """ % (temp_parameter, js_code)
        self.execute_js_code(js)
        if not_wait == False:
            time.sleep(0.2)
            time.sleep(0.2)
        js = "return window.%s" % temp_parameter
        result = self.execute_js_code(js)
        index = 0
        while result == None and index < 75:  # 3秒内等待
            if not_wait == False:
                time.sleep(0.2)
            print(f"Waiting for execute_js_and_return element {index / 5}seconds return value")
            result = self.execute_js_code(js)
            index += 1
        return result

    def execute_js_file(self, js_file):
        driver = self.get_driver()
        js_path = self.com_config.get_static("js_dir")
        js_path = os.path.join(js_path, js_file)
        if os.path.isfile(js_path):
            js_string = self.com_file.load_file(js_path)
            print(f"execute_js from file {js_file}")
            print(f"execute_js from file {js_string[:100]}")
            return driver.execute_script(js_string)
        else:
            return None

    def execute_js_code(self, js_string):
        driver = self.get_driver()
        return driver.execute_script(js_string)

    def execute_js_wait(self, js, deep=0):
        if not deep:
            deep = 9
        result = self.execute_js(js)
        index = 0
        while result == None and index < deep:
            result = self.execute_js(js)
            print(f"execute_js_wait execute to {js[:50]}")
            time.sleep(1)
            index += 1
        return result

    def load_jquery(self):
        print(f"load_JQuery")
        return self.execute_js("load_jquery.js")

    def load_jquery_wait(self, load_deep=0):
        if load_deep == 3:
            print(f"load_JQuery_wait load_deep {load_deep}")
            return False
        driver = self.get_driver()
        print(f"load_JQuery_wait")
        try:
            jQueryString = driver.execute_script(f"return jQuery.toString()")
            print(jQueryString)
            return True
        except:

            time.sleep(1.5)

            load_deep += 1
            self.load_jquery()
            return self.load_jquery_wait(load_deep)

    def sliding_element(self, selector, x_offset, y_offset):
        driver = self.get_driver()
        ele = self.find_element(selector)
        # ActionChains(driver).move_to_element_with_offset(ele, start, step).click().perform()
        # ActionChains(driver).click_and_hold(ele).move_by_offset(start, step).release().perform()
        # ActionChains(driver).drag_and_drop_by_offset(verify_img_element,start, step).perform()
        ActionChains(driver).click_and_hold(ele).move_by_offset(x_offset,
                                                                y_offset).release().perform()  # 5.与上一句相同，移动到指定坐标
        # ActionChains(driver).context_click(ele).perform()

    def move_element(self, selector, target=()):
        # TODO 调用本类中的find_element方法获得元素
        # TODO 利用ActionChains(driver). 方法移动元素到target 指定的坐标
        pass

    def js_find_attr(self, selector, attr):
        driver = self.get_driver()
        find_element_js = f"""return document.querySelector('{selector}')['{attr}']"""
        print(find_element_js)
        return driver.execute_script(find_element_js)

    def send_keys(self, selector, val,simulation=False):
        if simulation == True:
            self.send_keys_simulation(selector, val)
        else:
            self.send_keys_js(selector, val)

    def send_keys_js(self,selector,val):
        self.focus(selector,)
        js_code = """document.querySelector(`%s`).value = `%s`""" % (selector, val)
        self.execute_safe_script(selector, js_code)

    def explicit_position_element(self, selector):
        browser_titlehigh = 80
        element = self.find_element(selector)
        location = element.location
        location_x = location["x"]
        location_y = location["y"]
        window_position = self.get_window_position()
        window_x = window_position["x"]
        window_y = window_position["y"]
        size = element.size
        size_height = size["height"] / 2
        if size_height < 1:size_height = size["height"]
        size_width = size["width"] / 2
        if size_width < 1:size_width = size["width"]
        x = window_x+location_x+size_width
        y = window_y+browser_titlehigh+location_y+size_height
        # metrics = self.com_util.get_system_metrics()
        print("x",x,"y",y)

    def send_keys_simulation(self,selector,val):
        self.focus(selector)
        self.com_util.type_string(val)
        time.sleep(1)

    def focus(self,selector):
        js = """document.querySelector(`%s`).focus()""" % (selector)
        self.execute_safe_script(selector, js)

    def click(self, selector):
        self.event(selector, "click")

    def remove(self, selector):
        self.event(selector, "remove")

    def event(self, selector, event):
        js = """if(document.querySelector(`%s`))document.querySelector(`%s`).%s()""" % (selector, selector, event)
        self.execute_safe_script(selector, js)

    def html(self, selector, html_text):
        html_text = html_text.replace('`', '\\`')
        js = self.create_selector_script(selector, '.innerHTML=`%s`' % html_text)
        self.execute_safe_script(selector, js)

    def before(self, selector, html):
        self.insert_html(selector, html, 'before')

    def after(self, selector, html):
        self.insert_html(selector, html, 'after')

    def insert_html(self, selector, html, insert_action):
        html = html.replace('`', '\\`')
        if insert_action == "before":
            js = """document.querySelector(`%s`).innerHTML = document.querySelector(`%s`).innerHTML +`%s`""" % (
            selector, selector, html)
        else:
            js = """document.querySelector(`%s`).innerHTML = `%s`+document.querySelector(`%s`).innerHTML""" % (
            selector, html, selector)
        self.execute_safe_script(selector, js)

    def create_selector_script(self, selector, script):
        js = """document.querySelector(`%s`)%s""" % (selector, script)
        return js

    def execute_safe_script(self, selector, script, alert=True):
        driver = self.get_driver()
        js = """if(document.querySelector(`%s`)){%s}""" % (selector, script)
        if alert:
            js += """else{console.debug(`Selenium failed to execute script, selector%s`)}""" % selector
        try:
            driver.execute_script(js)
        except Exception as e:
            self.com_util.print_warn(e)
            if str(e).find('closed') != -1:
                print('chrome was already close,restart.')

    def get_driver_remoteurl(self, driver_type):
        return self.__driver_remote_url[driver_type]

    def get_driver_downloadurl(self, driver_type, version):
        url = self.get_driver_remoteurl(driver_type)
        if driver_type == "chrome":
            url = f"{url}{version}/"
            if self.load_module.is_windows():
                return f"{url}chromedriver_win32.zip"
            else:
                return f"{url}chromedriver_linux64.zip"
        elif driver_type == "edge":
            url = f"{url}{version}/"
            if self.load_module.is_windows():
                edge_url = f"{url}edgedriver_win64.zip"
                self.com_util.print_warn(f"Edge Driver cannot download automatically, please download manually.")
                self.com_util.print_warn(edge_url)
                self.com_util.print_warn(edge_url)
                self.com_util.print_warn(edge_url)
                return edge_url
            else:
                return f"{url}edgedriver_linux64.zip"

    def get_driver_from_down(self, download_url):
        down_url = {
            "url": download_url,
            "extract": True
        }
        driver_path = self.com_http.downs(down_url, extract=True, overwrite=True)
        return driver_path

    def get_driver_version(self, driver_type):
        return self.com_config.get_global(f"{driver_type}_version")

    def get_driver_path_name(self, driver_type):
        if self.load_module.is_windows():
            if driver_type == "chrome":
                return f"chromedriver.exe"
            else:
                return f"msedgedriver.exe"
        else:
            if driver_type == "chrome":
                return f"chromedriver.exe"
            else:
                return f"msedgedriver"

    def get_driver_path(self, driver_type):
        version = self.get_driver_version(driver_type)
        driver_path = self.is_existing_driver_file(driver_type, version)
        while driver_path == False:
            if self.__driver_downing_fromremote == False:
                self.__driver_downing_fromremote = True
                download_url = self.get_driver_downloadurl(driver_type, version)
                print(f"Downloading driver remote files, please wait for {download_url}.")
                self.get_driver_from_down(download_url)
            time.sleep(2)
            driver_path = self.is_existing_driver_file(driver_type, version)

        print(f"selenium info:")
        print(f"\tdriver_type {driver_type}")
        print(f"\tdriver_name {self.__driver_namee}")
        print(f"\tdriver_path {driver_path}")
        return driver_path

    def is_existing_driver_file(self, driver_type, driver_version):
        driver_name = self.get_driver_path_name(driver_type)
        driver_remote_url = self.get_driver_remoteurl(driver_type)
        url_to_filename = self.com_http.url_to_savename(driver_remote_url)
        driver_path = os.path.join(url_to_filename, driver_version)
        driver_path = os.path.join(driver_path, driver_name)
        driver_path = self.com_string.dir_normal(driver_path)
        if os.path.exists(driver_path) and os.path.isfile(driver_path):
            return driver_path
        else:
            return False

    # """
    # selenium自带抓包的使用，desired_capabilities
    # ###
    # 做爬虫的时候，有时候遇到需要的数据在加载资源当中，通常做法是拼接url，然后获取数据，但首先需要进行分析，如果拼接中的参数有加密的情况时，如果不能模拟算法生成正确的参数，那就很头疼。而访问performance，可以获得加载网站时的资源请求信息，可以通过这一特点，获取url和数据。
    # ####
    # 复制代码
    # from selenium import webdriver
    #
    # driver.get('https://www.baidu.com')
    #
    # # print console log messages
    # for entry in driver.get_log('browser'):
    #     print(entry)
    # entry格式：
    # {'level': 'SEVERE',
    # 'message': 'https://open.ccod.com/WARTC/cphoneRTC/verto-min.js 2086:28 "INVALID METHOD OR NON-EXISTANT CALL REFERENCE IGNORED" "verto.clientReady"',
    # 'source': 'console-api',
    # 'timestamp': 1626147049481}
    # 其中source：
    # console-api 控制台日志
    # network 网络日志

    def set_browser(self):

        prefs = {
            "profile.managed_default_content_settings.images": 1,

        }
        if self.flash_urls is not None and len(self.flash_urls) != 0:
            prefs['profile.managed_plugins_allowed_for_urls'] = self.flash_urls
        self.options.add_experimental_option('prefs', prefs)
        self.options.add_experimental_option('w3c', False)

        # 方法1
        # capabilities = DesiredCapabilities.CHROME
        # capabilities['loggingPrefs'] = {"performance","all"}
        # self.driver = webdriver.Chrome(
        #     desired_capabilities=capabilities
        # )

        # 方法2
        # self.options.add_experimental_option("excludeSwitches", ['enable-automation'])  # window.navigator.webdriver设置为undefined，逃过网站的防爬检查,headless无效
        desired_capabilities = self.options.to_capabilities()  # 将功能添加到options中
        desired_capabilities['loggingPrefs'] = {
            "performance": "ALL"  # 添加日志
        }
        self.driver = webdriver.Chrome(
            desired_capabilities=desired_capabilities
        )

    def gethtml(self):
        url = 'http://www.baidu.com'
        self.driver.get(url)
        print(self.driver.get_log('performance'))
        print('-' * 60)
        print(self.driver.get_log('performance'))
        for entry in self.driver.get_log('performance'):
            params = json.loads(entry.get('message')).get('message')
            print(params.get('request'))  # 请求连接 包含错误连接
            print(params.get('response'))  # 响应连接 正确有返回值得连接

    def get_log(self):
        result = self.proxy.har
        for entry in result['log']['entries']:
            pprint.pprint(entry)
        return entry

    def wait_select(self, selector, deep=0):
        ele = self.find_element_wait(selector, deep=False)
        if not deep:
            deep_max = 9999
        else:
            deep_max = deep
        index = 0
        while len(Select(ele).all_selected_options) == 0 and index < deep_max:
            print(f"wait_select {selector} {deep}")
            index += 1
            time.sleep(1)
        return ele

    def select_wait(self, selector, value):
        self.select(selector, value)

    def select(self, selector, value):
        ele = self.wait_select(selector)
        Select(ele).select_by_value(value)

    def wait_select_by_js(self, selector, deep=30):
        js = f"return document.querySelector(`{selector}`)"
        result = self.execute_js(js)
        index = 0
        while result == None and index < deep:
            result = self.execute_js(js)
            index += 1
            print(f"wait:{js}")
            time.sleep(1)
        return result

    def screen_click(self, x, y):
        driver = self.get_driver()
        # xoffset 和 yoffset 分别为节点坐标的 x 和 y
        ActionChains(driver).move_by_offset(xoffset=x, yoffset=y).click().perform()
        # 执行这一步释放鼠标，（可选
        ActionChains(driver).release()

    def create_element(self, tagname, property=None, text="", action=None, insert="body"):
        element = ""
        if property == None:
            property = {}
        if property.get("id") == None:
            property["id"] = self.com_string.md5()
        for key, value in property.items():
            if value not in ["null", "undefined", "true", "false"]:
                value = f'"{value}"'
            element += f'''element.{key} = {value};'''
        if text != "":
            text = f"""let text = document.createTextNode("%s");
                element.appendChild(text);""" % text
        if action != None:
            action = f"""
                element.%s();
            """ % action
        # 'beforebegin': 在该元素本身的前面。
        # 'afterbegin': 只在该元素当中，在该元素第一个子孩子前面。
        # 'beforeend': 只在该元素当中，在该元素最后一个子孩子后面。
        # 'afterend': 在该元素本身的后面。
        insert = f"""document.querySelector(`%s`).insertAdjacentElement('beforebegin', element)""" % insert
        js = """(()=>{
                let element = document.createElement("%s");
                %s
                %s
                %s
                %s
             })()""" % (tagname, text, element, insert, action)
        self.execute_js(js)

    def offset_scrolltowindow(self, selector):
        js = """
        function getElementTop(el,targetEl) {
          const parent = el.offsetParent;
          const top = el.offsetTop;
          return parent && parent !== targetEl
            ? getElementTop(parent, targetEl) + top
            : top;
        }
        return getElementTop(document.querySelector(`%s`),document.querySelector(`body`))
        """ % selector
        result = self.execute_js_and_return(js)
        return result

    def offset_towindow(self, selector):
        js = """
        function getElementTop(el,targetEl) {
          const parent = el.offsetParent;
          const top = el.offsetTop;
          return parent && parent !== targetEl
            ? getElementTop(parent, targetEl) + top
            : top;
        }
        return getElementTop(document.querySelector(`%s`),document.querySelector(`body`)) - (document.body.scrollTop + document.documentElement.scrollTop)
        """ % selector
        result = self.execute_js_and_return(js)
        return result

    def offset_top(self, selector):
        return self.find_attr_by_js(selector, 'offsetTop')

    def offset_left(self, selector):
        return self.find_attr_by_js(selector, 'offsetLeft')

    def element_height(self, selector):
        return self.find_attr_by_js(selector, 'getBoundingClientRect().height')

    def element_width(self, selector):
        return self.find_attr_by_js(selector, 'getBoundingClientRect().width')

    def is_show(self, selector):
        parent = self.find_attr_by_js(selector, 'offsetParent')
        if not parent:
            return True
        return False

    def scroll_into_view(self, selector):
        self.event(selector, "scrollIntoView")

    def scroll_to_bottom(self):
        self.scroll_to(0, 'window.scrollTo(document.body.scrollHeight')

    def scroll_to_top(self):
        self.scroll_to('window.scrollTo(document.body.scrollHeight', 0)

    def scroll_to(self, start, height):
        is_show = f"window.scrollTo({start}, {height})"
        self.execute_js_code(is_show)

    def down_file(self, url,save=True):
        file_name = self.get_download_filename(url)
        is_dynamic_url = self.is_dynamic_url(file_name)
        download = {
            "url": url,
            "dynamic_url": is_dynamic_url,
        }
        if is_dynamic_url == True:
            hint_img_path = self.com_http.down_file(url)
            download["save_filename"] = hint_img_path["save_filename"]
        else:
            property = {
                "href": url,
                "download": url,
            }
            self.create_element("a", property=property, text="down", action="click", insert="body")

            save_filename = self.get_download_file(url)
            handle_len = self.get_window_handles_length()
            self.switch_to(handle_len - 1)
            time.sleep(0.5)
            download["save_filename"] = save_filename["file_name"]
        print(f"down_file {url}")
        return download



    # 基于$$插件
    def down_file_ajax(self, url, save=True):
        result = 'selenium-NotDownloaded'
        js = """
        (()=>{
            let url = `%s`;
            if(!document.$download_temp){
                document.$download_temp = {};
            }
            document.$download_temp[url] = `%s`;
            $$.get_datastream(url,(data)=>{
                document.$download_temp[url] = data
            });
        })()
        """ % (url,result)
        self.execute_js_code(js)
        return_js = f'return document.$download_temp[`{url}`]'
        result = self.execute_js_code(return_js)
        while result == 'selenium-NotDownloaded':
            time.sleep(3)
            result = self.execute_js_code(return_js)
        file_name = os.path.basename(url)
        if save == True:
            print(result)
            file_name = self.get_download_dir(file_name)
            self.com_file.save(file_name,result,encoding="binary")
            result = {
                "url":url,
                "save_filename": file_name
            }
            print(result)
        return True

    def get_html_ips(self, wait_element=None, text_not=None, info=False, html=None):
        is_seleniumscratchhtml = False
        if html == None:
            is_seleniumscratchhtml = True
            html = self.get_html()

        if html.find("page can’t be found") != -1 and html.find('No webpage was found for the web address') != -1:
            return []
        if wait_element != None and is_seleniumscratchhtml == True:
            self.find_text_content_by_js_wait(wait_element, text_not=text_not, deep=False, info=info)
        ip_pattern = re.compile(r'[0-9]{1,}\.[0-9]{1,}\.[0-9]{1,}\.[0-9]{1,}')
        if is_seleniumscratchhtml == True:
            html = self.get_html()
        ips = re.findall(ip_pattern, html)
        return ips
