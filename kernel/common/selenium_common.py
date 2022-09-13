import json
import operator
import shutil
from kernel.base.base import *
import os
import re
import time
import requests
from selenium.webdriver.common.desired_capabilities import DesiredCapabilities
#import lxml.html
from lxml import etree
from bs4 import BeautifulSoup
from lxml.cssselect import CSSSelector
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
# from queue import Queue
# from multiprocessing import Pool
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
# from selenium.webdriver.support.events import EventFiringWebDriver, AbstractEventListener
from selenium.common.exceptions import NoSuchElementException
from selenium.webdriver.common.action_chains import ActionChains
# import sched
import platform
from PIL import Image
# 为保证 driver 能正常打开
from kernel.base.load_module import LoadModuleClass

drivers_dict = {}
modules_dict = {}
webdriver_as = webdriver

class SeleniumCommon(BaseClass):
    __driver = None
    __driver_name = None
    __driver_version = None
    __googledriver_versions_from_down_url = []
    __chrome_down_url = 'http://registry.npmmirror.com/-/binary/chromedriver/'
    __wait_open_url = None

    def __init__(self,args):
        global drivers_dict
        global modules_dict

        if type(args) == dict:
            args = [args]
        configs = None
        for arg in args:
            if type(arg) is dict and "module" in arg:
                configs = arg
                break
            else:
                continue
        if configs is None \
                or \
        ("module" not in configs):
            return
        module = configs["module"]
        driver_name = configs["driver_name"]
        self.__driver_name = driver_name
        drivers_dict[self.__driver_name] = None
        modules_dict[self.__driver_name] = module
        LoadModuleClass().add_common_modules(self)

    # 创建一个浏览器，并可直接使用类的功能无须传递driver对象
    def main(self,args):
        opts = {}

        if "module" not in args:
            return

        module = args["module"]
        opts["module"] = module

        try:
            opts["driver_name"] = args["driver_name"]
        except:
            opts["driver_name"] = module.__class__.__name__

        selenium_common = SeleniumCommon(opts)
        module.__setattr__("selenium_common",selenium_common)


    def get_driver(self,not_wait=False):
        self.__driver = self.get_empty_driver(not_wait=not_wait)
        return self.__driver

    def open(self,url,load_jquery=False,callback=None,wait=None,not_wait=False):
        self.open_url_as_new_window(url,callback=callback,load_jquery=load_jquery,wait=wait,not_wait=not_wait)

    def open_url(self,url,load_jquery=False,callback=None,wait=None,not_wait=False):
        self.open_url_as_new_window(url,callback=callback,load_jquery=load_jquery,wait=wait,not_wait=not_wait)


    def open_url_as_new_window(self, url, load_jquery=False,callback=None,wait=None,not_wait=False):
        global drivers_dict
        if wait is None:
            wait = -1

        if wait == 0 or not_wait is True:
            not_wait = True
            time.sleep(0.1)
        else:
            not_wait = False
        driver = self.get_driver(not_wait=not_wait)

        if wait > 0:
            driver.set_page_load_timeout(wait)
            driver.set_script_timeout(wait)  # 这两种设置都进行才有效

        current_url = driver.current_url

        if current_url == 'data:,':
            try:
                driver.get(url=url)
            except:
                print(f"Timed out receiving message from renderer:{wait}")
        else:
            print(f"switch_to \"{url}\"")
            self.switch_to(url,load_jquery)
        if callback != None:
            callback(driver)
        else:
            return driver

    def is_ready(self):
        time.sleep(0.1)
        if self.get_current_url() is "data:,":
            return False
        js = "return document.readyState"
        ready = self.execute_js(js)

        print(f"open_ready {ready}")

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

    def switch_to(self,url_or_index,loadJQuery=False):
        driver = self.get_driver()
        len_drivers = len(driver.window_handles)
        if type(url_or_index) is int:
            index = url_or_index
            print(f"switch ot index {index}")
            if index > len_drivers:
                index = len_drivers-1
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
                if loadJQuery:self.load_jquery_wait()
            else:
                driver.refresh()
                print(f"init_driver url is existed of {url},url as refresh.")
                time.sleep(0.5)

    def open_local_html_to_beautifulsoup(self,html_name="index.html"):
        content = self.file_common.load_html(html_name)
        beautifulsoup = self.http_common.find_text_from_beautifulsoup(content)
        return beautifulsoup

    def screenshot_of_webpage(self,selector=None,file_path=None):  # screenshot
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
            filename = self.string_common.random_string(32,upper=False) + ".png"
        temp_dir = self.config_common.get_public("temp")
        self.file_common.mkdir(temp_dir)
        file_path = self.string_common.filename_normal(
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

    def screenshot_of_element(self,selector=None,file_path=None):  # 对目标网页进行截屏。这里截的是全屏
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
        shutil.copyfile(temp_img,file_path)
        os.remove(temp_img)
        return file_path

    def get_empty_driver(self,not_wait=False):
        global webdriver_as
        global drivers_dict
        global modules_dict
        #
        # print(f"self.__driver_name {self.__driver_name} from get_empty_driver")
        # print(f"self.__driver {self.__driver} from get_empty_driver")
        # print(f"drivers_dict {drivers_dict} from get_empty_driver")
        # print(f"modules_dict {modules_dict} from get_empty_driver")
        if drivers_dict[self.__driver_name] != None and self.__driver != None and operator.__eq__(drivers_dict[self.__driver_name],self.__driver):
            return self.__driver
        options = Options()
        # options = webdriver_as.ChromeOptions()
        # 处理SSL证书错误问题
        # prefs = {'profile.managed_default_content_settings.images': 2}
        # options.add_experimental_option('prefs', prefs)
        options.add_argument('--ignore-certificate-errors')
        options.add_argument('--ignore-ssl-errors')
        options.add_argument('--disable-infobars')# 禁用浏览器正在被自动化程序控制的提示
        options.add_argument("no-sandbox")
        options.add_argument('-–ignore-certificate-errors')
        if not_wait:
            options.page_load_strategy = "none"  # 'normal', 'eager', 'none' 页面加载模式
            chrome_dir = self.config_common.get_public("libs/chrome/chrome.exe")
            if self.file_common.is_file(chrome_dir):
                options.binary_location = self.config_common.get_public("libs/chrome/chrome.exe")
            desired_capabilities = DesiredCapabilities.CHROME
            desired_capabilities["pageLoadStrategy"] = "none"

        headless = self.config_common.get_global('headless')
        if headless:
            options.add_argument('--headless')
            options.add_argument('--disable-gpu')
            # options.add_argument('--blink-settings=imagesEnabled=false') # 不加载图片, 提升速度
        options.add_experimental_option('excludeSwitches', ['enable-automation'])
        options.add_experimental_option('excludeSwitches', ['enable-logging'])
        options.add_experimental_option("excludeSwitches", ['enable-automation', 'enable-logging'])

        driver_path = self.get_driver_path()
        service = Service(driver_path)

        driver = webdriver_as.Chrome(service=service,options=options)
        # driver.set_page_load_timeout(1)
        # driver.set_script_timeout(1)

        if not headless:
            driver.set_window_rect(x=200, y=20, width=1950, height=980)
        else:
            driver.set_window_rect(x=0, y=0, width=1950, height=980)
        self.set_driver(driver)
        return driver

    #设置driver驱动器，用于在不同线程间共享driver
    def set_driver(self,driver):
        drivers_dict[self.__driver_name] = None
        drivers_dict[self.__driver_name] = driver
        self.__driver = drivers_dict[self.__driver_name]
        modules_dict[self.__driver_name].__setattr__("__driver",driver)
        return self.__driver

    def find_url_from_driver_handles(self,url):
        driver = self.get_driver()
        try:
            handle_l = len(driver.window_handles)
        except:
            return None
        for index in range(handle_l):
            driver.switch_to.window(driver.window_handles[index])
            time.sleep(0.5)
            current_url = driver.current_url
            current_url = current_url.split("?")[0]
            if operator.__eq__(current_url, url):
                url_index = index
                return url_index
        return None

    def get_current_window_handle_index(self,driver):
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
        driver = self.get_driver()
        outerHTML = driver.execute_script("return document.documentElement.outerHTML")
        return outerHTML

    def close(self,handle=None):
        self.close_window(handle)
    def close_window(self,handle=None):
        if type(handle) is str:
            #TODO
            pass
        driver = self.get_driver()
        driver.close()

    def get_current_url(self):
        driver = self.get_driver()
        current_url = driver.current_url
        current_url = current_url.split("?")[0]
        return current_url

    def is_element(self,element):
        if element.__class__.__name__ == "WebElement":
            return True
        elif type(element) == str:

            elements = self.execute_js_wait(f"return document.querySelectorAll('{element}')")

            if len(elements) == 0:
                return False
            else:
                return True
        else:
            return False

    def element_exist(self,element):
        return self.is_element(element)

    def find_element(self,selector,is_beautifulsoup=False):
        eles = self.find_elements(selector,is_beautifulsoup)
        ele = None
        if len(eles) > 0:
            ele = eles[0]
        return ele

    def find_element_wait(self,selector,deep=0):
        if deep == 3:
            print(f"find_element_wait deep {deep}")
            return None
        print(f"find_element_wait {selector}")
        try:
            ele = self.find_element(selector)
            if ele != None:
                return ele
            raise NoSuchElementException
        except:
            deep += 1
            time.sleep(1)
            return self.find_element_wait(selector,deep)

    def find_content(self,selector):
        ele = self.find_element_wait(selector)
        try:
            text = ele.text
            text = text.replace("0","")
            if len(text) > 0:
                return ele.text
        except:
            return None

    def find_content_wait(self,selector,deep=0,url=None):
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
            return self.find_content_wait(selector,deep)


    def find_elements(self,selector,is_beautifulsoup=False):
        st = self.selector_parse(selector)
        if st == "css":
            ele = self.find_elements_by_css(selector,is_beautifulsoup)
        elif st == "xpath":
            ele = self.find_elements_by_xpath(selector,is_beautifulsoup)

        elif st == "id":
            ele = self.find_elements_by_id(selector,is_beautifulsoup)
        elif st == "tag":
            ele = self.find_elements_by_tagname(selector,is_beautifulsoup)
        else:
            ele = None

        if type(ele) != list:
            eles = [ele]
        else:
            eles = ele
        return eles

    def find_element_value_by_js_wait(self,selector):
        if selector[0] == '/':
            js = f"return document.evaluate('{selector}',document,null,XPathResult.FIRST_ORDERED_NODE_TYPE,null,).singleNodeValue.innerHTML"
        else:
            js = f"return document.querySelector('{selector}').textContent"

        return self.execute_js_wait(js)


    def find_elements_value_by_js_wait(self,selector,url=None):
        cont = self.statistical_elements_wait(selector,url=url)
        cont = int(cont)
        texts = []
        for el in range(cont):
            js = f"return document.querySelectorAll('{selector}')[{el}].textContent"

            text = self.execute_js_wait(js)

            texts.append(text)
        return texts

    def find_property(self,selector,attr_val,url=None):
        print(f"find_elements_attr_by_js_wait {selector} Get {attr_val}")
        cont = self.statistical_elements(selector,url=url)
        cont = int(cont)
        texts = []
        for el in range(cont):
            js = f"return document.querySelectorAll('{selector}')[{el}]['{attr_val}']"
            text = self.execute_javascript(js)
            texts.append(text)
        return texts

    def find_property_wait(self,selector,attr_val,url=None):
        print(f"find_elements_attr_by_js_wait {selector} Get {attr_val}")
        cont = self.statistical_elements_wait(selector,url=url)
        cont = int(cont)
        texts = []
        for el in range(cont):
            js = f"return document.querySelectorAll('{selector}')[{el}]['{attr_val}']"

            text = self.execute_js_wait(js)

            texts.append(text)
        return texts

    def statistical_elements(self,selector):
        js = f"return document.querySelectorAll('{selector}').length.toString()"

        cont = self.execute_js_wait(js)

        cont = int(cont)
        return cont

    def statistical_elements_wait(self,selector,num=0,url=None):
        cont = self.statistical_elements(selector)
        if num == 2 and url is not None:
            #如果连续查找不到元素,有可能浏览器被操作,查找当前url是否还存在,不存在则打开
            self.open_url_as_new_window(url)
            time.sleep(2)
        if cont > 0 or num == 3:
            print(f"find_elements_count_wait cont:{cont}")
            return cont
        else:
            time.sleep(1)
            driver = self.get_driver()
            # print(driver.page_source)
            num+=1
            current_url = driver.current_url
            print(f"find_elements_count_wait url {current_url} as cont:{cont}")

            return self.statistical_elements_wait(selector,num)


    def second_find_elements(self,ele,selector):
        st = self.selector_parse(selector)
        print(f"second_find_elements {selector}")
        eles = None
        if st == "css":
            eles = ele.find_elements(By.CSS_SELECTOR,selector)
        if st == "xpath":
            eles = ele.find_element(By.XPATH,selector)
        if st == "id":
            selector = selector[1:]
            eles = ele.find_element(By.ID,selector)
        if st == "tag":
            eles = ele.find_elements(By.TAG_NAME, selector.replace("<","").replace(">",""))
        if st == "text":
            eles = ele.find_elements_by_link_text(selector)
        return eles

    def selector_parse(self, selector):

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

        if selector[0] == "." or selector[0] == "[" :

            return "css"
        elif selector[0] == "/":
            return "xpath"
        if selector[0] == "#":
            return "id"
        if f"<{selector.strip()}>".lower() in HTML_TABS:
            return "tag"
        if selector.strip().lower() in HTML_TABS:
            return "tag"
        return "text"

    def find_elements_by_tagname(self,selector,is_beautifulsoup):
        driver = self.get_driver()
        selector = selector.replace("<","").replace(">","")
        if is_beautifulsoup:
            html = self.find_html_wait()
            soup = BeautifulSoup(html, "html.parser")
            eles = soup.find_all(selector)
        else:
            eles = driver.find_elements(By.TAG_NAME,selector)
        return eles


    def find_elements_by_id(self,selector,is_beautifulsoup):
        driver = self.get_driver()
        selector = selector[1:]
        if is_beautifulsoup:
            html = self.find_html_wait()
            soup = BeautifulSoup(html, "html.parser")
            ele = [ soup.find(id=selector) ]
        else:
            ele = [ driver.find_element(By.ID, selector) ]
        return ele

    def find_elements_by_css(self,selector,is_beautifulsoup):
        driver = self.get_driver()
        if is_beautifulsoup:
            html = self.find_html_wait()
            soup = BeautifulSoup(html,"html.parser")
            eles = soup.select(selector)
            # print(eles)
            # tree = etree.HTML(html)
            # selector = CSSSelector(selector)
            # for ele in selector(tree):
            #     eles.append(ele)
        else:
            eles = driver.find_elements(By.CSS_SELECTOR,selector)
        return eles


    def find_elements_by_xpath(self,selector,is_beautifulsoup):
        driver = self.get_driver()
        if is_beautifulsoup:
            html = self.find_html_wait()
            tree = etree.HTML(html)
            ele = tree.xpath("//*")
        else:
            print(f"find_elements_by_xpath ",selector)
            ele = driver.find_element(By.XPATH, selector)
        return ele

    def find_text_from(self, selector, s_text):
        menus = self.find_elements( selector)
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

    def action_element(self,selector,action,value=None):
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

    def search_content(self,search_content,search_selector,submit_selector):
        search = self.find_element(search_selector)
        search.send_keys(search_content)
        submit = self.find_element(submit_selector)
        submit.click()
        return self.get_current_url()

    def verification_text_click_code(self,args,screenshot=False):
        hint_selector = args.get('hint')
        identification_zone_selector = args.get('identification_zone')
        if screenshot:
            hint_img_path = self.screenshot_of_element(hint_selector)
            identification_zone_selector = self.screenshot_of_element(identification_zone_selector)
        else:
            hint_img = self.find_property_wait(hint_selector,"src")
            hint_img_path = self.http_common.down_file(hint_img)
            identification_zone_img = self.find_property_wait(identification_zone_selector,"src")
            identification_zone = self.http_common.down_file(identification_zone_img)
            print(f"hint_img_path {hint_img_path}")
            print(f"hint_img_path {identification_zone}")

        click_zone = args.get('click_zone')


    def wait_element(self,selector,timeout=None,deep=None):
        if timeout >= deep:
            return False
        element = self.find_element(selector)
        if element is None:
            time.sleep(1)
            deep += 1
            self.wait_element(selector,deep)
        else:
            return True

    def execute_js(self,js):

        js_path = self.config_common.get_static("js_dir")
        js_path = os.path.join(js_path,js)
        if os.path.isfile(js_path):
            return self.execute_js_file(js)
        else:

            return self.execute_js_code(js)


    def execute_js_file(self,js_file):
        driver = self.get_driver()
        js_path = self.config_common.get_static("js_dir")
        js_path = os.path.join(js_path,js_file)
        if os.path.isfile(js_path):
            js_string = self.file_common.load_file(js_path)
            print(f"execute_js from file {js_file}")
            print(f"execute_js from file {js_string[:100]}")
            return driver.execute_script(js_string)
        else:
            return None

    def execute_js_code(self, js_string):
        driver = self.get_driver()
        return driver.execute_script(js_string)


    def execute_js_wait(self,js,num=0):
        if num == 3:
            print(f"execute_js_wait execute to {num}")
            return None
        print(f"execute_js_wait of execute_js")
        try:
            return self.execute_js(js)
        except:
            time.sleep(1.5)

            num +=1
            return self.execute_js_wait(js,num)

    def load_jquery(self):
        print(f"load_JQuery")
        return self.execute_js("load_jquery.js")

    def load_jquery_wait(self,load_deep = 0):
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

    def sliding_element(self,selector,x_offset,y_offset):
        driver = self.get_driver()
        ele = self.find_element(selector)
        # ActionChains(driver).move_to_element_with_offset(ele, start, step).click().perform()
        # ActionChains(driver).click_and_hold(ele).move_by_offset(start, step).release().perform()
        # ActionChains(driver).drag_and_drop_by_offset(verify_img_element,start, step).perform()
        ActionChains(driver).click_and_hold(ele).move_by_offset(x_offset,y_offset ).release().perform()  # 5.与上一句相同，移动到指定坐标
        # ActionChains(driver).context_click(ele).perform()


    def move_element(self,selector,target=()):
        # TODO 调用本类中的find_element方法获得元素
        # TODO 利用ActionChains(driver). 方法移动元素到target 指定的坐标
        pass

    def js_find_attr(self, selector, attr):
        driver = self.get_driver()
        find_element_js = f"""return document.querySelector('{selector}')['{attr}']"""
        print(find_element_js)
        return driver.execute_script(find_element_js)

    def send_keys(self,selector,val):
        driver = self.get_driver()
        driver.execute_script(f"""
        $("{selector}").val("{val}")
        """)


    def get_googledriver_versions(self):
        if len(self.__googledriver_versions_from_down_url) != 0:
            return self.__googledriver_versions_from_down_url
        html = self.http_common.get(self.__chrome_down_url)
        json_string = self.string_common.byte_to_str(html)
        doc_as_json = json.loads(json_string)
        for item in doc_as_json:
            version = item['url'].split('chromedriver/')[1].replace('/','')
            #加添加chromedriver的标准地址，其他杂项地址不添加
            if re.search(re.compile('^\d'),version) != None:
                self.__googledriver_versions_from_down_url.append(version)
        return self.__googledriver_versions_from_down_url

    def get_googledriver_downloadurl(self,version=None):
        if version is None:
            version = self.__driver_version
        googledriver_down_name = self.get_chromedriver_name_from_down()
        googledriver_downloadurl = f"{self.__chrome_down_url}{version}/{googledriver_down_name}"
        print(f"current chromedriver version is {version}.")
        return googledriver_downloadurl


    def get_googledriver_from_down(self,version=None):
        versions = self.get_googledriver_versions()
        if version is not None and version not in versions:
            print("get_googledriver_from_down Not Found version: {}".format(version))
            return None
        url = self.get_googledriver_downloadurl(version)
        down_url = {
            "url": url,
            "extract": True
        }
        driver_path =  self.http_common.down_files(down_url,extract=True )
        return driver_path

    def get_googlechrome_version(self):
        if self.__driver_version == None:
            self.__driver_version = self.config_common.get_global("chromedriver_version")
        return self.__driver_version

    def get_chromedriver_name(self):
        if self.is_windows():
            return f"chromedriver.exe"
        else:
            return f"chromedriver"

    def is_windows(self):
        sysstr = platform.system()
        windows = "windows"
        if (sysstr.lower() == windows):
            return True
        else:
            return False

    def get_chromedriver_name_from_down(self):
        if self.is_windows():
            return f"chromedriver_win32.zip"
        else:
            return f"chromedriver_linux64.zip"

    def get_driver_path(self):  # get_chromedriverpath
        chromedriver_path = self.is_existing_driver_file()
        if chromedriver_path != None:
            return chromedriver_path
        else:
            self.get_googledriver_from_down(version=self.__driver_version)
            version = self.get_googlechrome_version()
            chromedriver_name = self.get_chromedriver_name()
            time.sleep(3)
            while self.is_existing_driver_file() == None:
                print(f"please wait {chromedriver_name} downing as {version} from {self.__chrome_down_url}.")
                time.sleep(3)
            return self.is_existing_driver_file()

    def is_existing_driver_file(self):
        chromedriver_name = self.get_chromedriver_name()
        driver_version = self.get_googlechrome_version()
        save_name_of_url = self.http_common.save_name_of_url(self.__chrome_down_url)
        chromedriver_path = os.path.join(save_name_of_url, driver_version)
        chromedriver_path = os.path.join(chromedriver_path, chromedriver_name)
        if os.path.exists(chromedriver_path) and os.path.isfile(chromedriver_path):
            chromedriver_path = self.string_common.filename_normal(chromedriver_path)
            print(f"selenium info:")
            print(f"\tdriver_name {self.__driver_name}")
            print(f"\tdriver_path {chromedriver_path}")
            return chromedriver_path
        else:
            return None
