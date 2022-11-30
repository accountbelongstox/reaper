from kernel.base.base import *
# import os
import json
import os.path
import pprint
import time
import datetime
# import time
# from queue import Queue
import re

class Main(BaseClass):
    __main_url = "https://www.okx.com"
    __markets_price_url = "/markets/prices"
    __trade_url = "/trade-spot/{0}-usdt"
    __benchmark_dbname = "list_okx_for_price_benchmarks"
    __benchmark_cache_file = "cache_okx_for_price_benchmarks.txt"
    __exchangeDataFile = "exchangeData.list"
    __premium_grasp_listtmp_ = []
    __change_list_tick = []
    __investment_amount = 100000  # 模拟投资额
    __raise_the_standard = 7  # 7%的标准
    __drop = -7  # 跌的幅度
    __categories_trade_list = []
    __trade_historical_mongodb = "list_trade_historical"
    __redis_trade_item_dict_pre = "list_okx_"
    __debug = False
    __debug_headless = False
    __chrome_browser_width = 1290
    __chrome_browser_height = 900

    # 价格基准点,对比规则是当有新的价格时,就与该价格比较.如果出现价格差,则返回价格
    __price_benchmark = {}
    __collection_price_interval = 1
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

    #看涨分析
    # 58分 - 03分 上涨0.1864 上涨0608992601024474
    # 从0.1757上升 0.06089926010244744
    # 0.1757, 0.1767, 0.1784, 0.1802, 0.1815, 0.1802, 0.1864,

    # 是否上涨参考
    # 59分 - 13分(0.1763 至14分涨到0.1772 - 0.1692)上涨率 : 0.04196217494089848
    # (分析 pha-usdt数据)

    def __init__(self, argv):
        pass

    def main(self, argv):
        # 分十个线程获取数据,打开全部货币页面.
        """
        监测长期下跌忽然上涨
        监测在短期忽然上扬,一般在几分钟至不到一分钟
        同样也要监测涨幅超过但时间是多久,太长了就没意义相当于平滑线条.
        :是的,要监测
        :return:
        """
        if self.com_config.is_mainserver() == True:
            self.com_thread.create_thread("flask", {"module": self}, run=True)
            self.com_translate.thread_translate(headless=True)
            self.com_api.update_ip_towebsitelisten()
        else:
            self.com_api.update_ip_towebsitelisten()
            # words = self.com_translate.get_remote_notranslated()
            # self.com_translate.thread_translate(words,save_db=False,put_remote=True,headless=False)

    def scanning_markets_quote_change_price(self, args):
        if self.__debug is False:
            self.open_markets_price_url()
            self.open_wait()
        print("After the webpage is loaded, start to get all the currency information")
        # 通过js获取网页信息,防止网页卡
        cycles = 0
        starttime = self.com_util.create_time_now()
        while True:
            coins = self.get_all_coin_prices()
            coins = coins.items()
            # """
            # 提取的格式为:
            # 'ZRX': {'collection_time': '2022-09-21-23:39:28',
            # 'color_up': '+0.67%',
            # 'full_name': '0x',
            # 'last_num': '$0.27',
            # 'last_price': 0.27,
            # 'quote_change': 0.67,
            # 'short_name': 'ZRX'}
            # """
            for coin_name, coin in coins:
                price_difference = self.gain_compare(coin)
                # 首次对比时将没有价格差,而是直接设置为基准值
                if price_difference is None:
                    continue
                coin_name = coin["short_name"]
                if price_difference > self.__raise_the_standard:  # 涨了7%
                    self.print_up(f"\n{coin_name} coin up 7%")
                    self.print_up(f"investment money.", time=True)
                    # 跟随走势走
                    self.set_benchmark(coin, replace=True)
                elif price_difference < self.__drop:  # 跌了了7%
                    self.print_fell(f"\n{coin_name} coin fell 7%", time=True)
                    # 逆势走
                    self.set_benchmark(coin, replace=True)
                # elif price_difference != 0:
                #     self.print_info(f"\nQuote change {price_difference}",time=True)
            price_interval = self.__collection_price_interval
            self.serialize_for_benchmark()
            cycles += 1
            coins_len = len(coins)
            time_statistics = self.com_util.timer(starttime)
            print(
                f"\rCompletion Number of coins acquired round {coins_len} coins, Cycles {cycles}, Run time is {time_statistics} .",
                end="", flush=True)
            # 每次采集间隔时间
            time.sleep(price_interval)

    def embed_js_to_get_price_per_page(self):
        js = self.load_module.get_control_dir("static/get_to_page_price_loop.js")
        print(js)
        self.com_selenium.execute_js(js)

    def get_to_page_price_loop(self):
        self.get_page_per_price()
        pass

    def get_page_per_ticker_price(self, flask):
        ticker_price = flask.flask_request.args.get("ticker_price")
        print(ticker_price)
        # TODO 将价格添加到记录中对比.
        return ""

    def open_markets_price_url(self):
        markets_price_url = self.com_util.urljoin(self.__main_url, self.__markets_price_url)
        self.open_url(markets_price_url)

    def open_trade_url(self, coin_name):
        suffix_url = self.__trade_url.format(coin_name)
        print(suffix_url)
        url = self.com_util.urljoin(self.__main_url, suffix_url)
        self.open_url(url)

    def open_url(self, url):
        self.com_selenium.open_url(url, width=self.__chrome_browser_width, height=self.__chrome_browser_height,
                                   headless=self.__debug_headless)

    def open_wait(self):
        while (not self.com_selenium.is_ready()):
            markets_price_url = self.com_util.url_join(self.__main_url, self.__markets_price_url)
            print(f"Wait for the page to load from {markets_price_url}")
            time.sleep(1)
        time.sleep(2)

    def find_new_coin(self):
        pass

    def print_up(self, message, time=False):
        if time: message = f"{message} : {self.com_string.create_time()}"
        print(f"\033[0;37;41m{message}\033[0m")

    def print_fell(self, message, time=False):
        if time: message = f"{message} : {self.com_string.create_time()}"
        print(f"\033[0;37;42m{message}\033[0m")

    def print_info(self, message, time=False):
        if time: message = f"{message} : {self.com_string.create_time()}"
        print(f"\033[0;32;40m{message}\033[0m")

    def gain_compare(self, coin):
        coin_name = coin["short_name"]
        coin_benchmark = self.get_benchmark(coin_name)
        if coin_benchmark == None:
            self.set_benchmark(coin)
            return None
        else:
            benchmark = self.__price_benchmark[coin_name]
            coin_benchmark = benchmark["quote_change"]
            current_quote = coin["quote_change"]
            poor_increase = current_quote - coin_benchmark
        return poor_increase

    def set_current_price(self, coin_name):
        pass

    def get_benchmark(self, coin_name):
        if coin_name not in self.__price_benchmark:
            return None
        else:
            return self.__price_benchmark[coin_name]

    def set_benchmark(self, coin, replace=False):
        coin_name = coin["short_name"]
        if coin_name not in self.__price_benchmark or replace is True:
            last_price = coin["last_price"]
            quote_change = coin["quote_change"]
            collection_time = coin["collection_time"]
            print(f"Currency {coin_name} sets a new benchmark {last_price} price")
            print("                    quote_change: {0:+}%".format(quote_change))
            print("                    collection_time: ".format(collection_time))
            self.__price_benchmark[coin_name] = {
                "last_price": last_price,
                "short_name": coin_name,
                "quote_change": quote_change,
                "collection_time": collection_time,
            }

    def extract_coin_html(self, coins_html):
        """
        提取的格式为:
        'ZRX': {'collection_time': '2022-09-21-23:39:28',
        'color_up': '+0.67%',
        'full_name': '0x',
        'last_num': '$0.27',
        'last_price': 0.27,
        'quote_change': 0.67,
        'short_name': 'ZRX'}
        """

        # 去空格是为了正则
        space_reg = re.compile(r"\s+")
        coins_html = re.sub(space_reg, "", coins_html)

        # html格式的信息都是在html标签如>XXX<中,因此直接提取标签中的信息
        short_name_reg = r"(?<=\>)[^\<\>\b]+?(?=\<)"
        coins_information = re.findall(short_name_reg, coins_html)

        # 提取后的信息如 '$422,133.71', 'Trade', '|', 'Convert', 'PST', 清除数组中的Convert值
        character = "Convert"
        coins_information = self.com_util.clear_value(coins_information, character)

        split_symbol = "|"
        coins_information = self.com_util.trim(coins_information, split_symbol)
        # 提取后的信息如 '$422,133.71', 'Trade', '|', 'Convert', 'PST', 因此正好使用|将数据组分隔
        coins_information = self.com_util.split_list(coins_information, split_symbol)

        # 提取信息
        coins = {}
        for coin_info in coins_information:
            short_name = coin_info[0]
            full_name = coin_info[1]
            last_num = coin_info[2]
            okg_sm = coin_info[3]
            color_up = coin_info[4]

            coins[short_name] = {}
            coin = coins[short_name]
            coin["short_name"] = short_name
            coin["full_name"] = full_name
            coin["last_num"] = last_num
            coin["last_price"] = self.com_string.float(last_num)
            coin["quote_change"] = self.com_string.float(okg_sm)
            coin["color_up"] = color_up
            coin["short_name"] = short_name
            coin["collection_time"] = self.com_string.create_time_no_space()
        # pprint.pprint(coins)
        return coins

    def get_all_coin_prices(self):
        # 所执行的代码为 document.querySelector('.table-box.token-list-table tbody').innerHTML
        if self.__debug:
            # 测试代码
            coins_html = self.com_file.read_file("coins.html")
        else:
            coins_html = self.com_selenium.find_html_by_js_wait(".table-box.token-list-table tbody", deep=None)
        if coins_html == None:
            print(f"web page fetch error!")
            coins_html = ""
        coins = self.extract_coin_html(coins_html)
        # """
        # 提取的格式为:
        # 'ZRX': {'collection_time': '2022-09-21-23:39:28',
        # 'color_up': '+0.67%',
        # 'full_name': '0x',
        # 'last_num': '$0.27',
        # 'last_price': 0.27,
        # 'quote_change': 0.67,
        # 'short_name': 'ZRX'}
        # """
        return coins

    def set_coin_price_to_cache(self, coins):
        pass

    def set_coin_price_to_database(self):
        pass

    def start_thread_for_scan_trade_tick_list(self, click=True):
        # 等待元素出现
        self.wait_and_find_data_token_names(click)
        # 初始化历史数据列表，如果有的话。如果没有则等到开始抓取
        self.init_trade_historical_list()
        thread_pool = ThreadPoolExecutor(max_workers=1)
        thread_runIndes = 0
        change_task_test = []
        thread_time = time.thread_time()
        while True:
            if len(change_task_test) == 0:
                thread_name = f"scratch-tread-{thread_runIndes}"
                save_to_mangodb = (thread_runIndes % 3 == 0)
                print(f" New tick {thread_name}/ thread_time:{thread_time}/ save to mangoDB:{save_to_mangodb} running.")
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

    def serialize_for_benchmark(self):
        # print( f"Serialize and save the benchmark price to file {self.__benchmark_cache_file}")
        self.com_db.serialization(self.__price_benchmark, self.__benchmark_cache_file, override=True, notion=False)

    def store_database_for_benchmark(self):
        # print( f"Save benchmark price to database {self.__benchmark_dbname}")
        self.com_db.save_data_to(self.__benchmark_dbname, self.__price_benchmark)

    def get_change_run(self, data):
        thread_name = data[0]
        is_serialize = data[1]
        thread_time = data[2]
        scan_trade_tick_list = self.scan_trade_tick_list()
        self.set_trade_categories(scan_trade_tick_list)
        for trade_item_dict in scan_trade_tick_list:
            short_name = trade_item_dict["short_name"]
            # 获取一个历史数据，该历史数据包含一该类型项的一次完整的抓取
            grasp_historical_pop = self.get_trade_historical_list_pop(short_name)
            is_rise_changed = self.trade_rise_is_change(trade_item_dict, grasp_historical_pop)
            if is_rise_changed:
                self.set_trade_historical_list(short_name, trade_item_dict)
        if is_serialize: self.save_okx_exchange_rise()
        print(f"Count for change premium data are {len(self.__premium_grasp_listtmp_)} items.")
        return True

    def is_beautifulsoup(self):
        if self.__driver.__class__.__name__.__eq__("BeautifulSoup"):
            return True
        else:
            return False

    def wait_and_find_data_token_names(self, click=False):
        is_beautifulsoup = self.is_beautifulsoup()
        if is_beautifulsoup is not True:
            WebDriverWait(self.__driver, 0).until(
                EC.presence_of_element_located((By.CSS_SELECTOR, '''[data-token-name]''')))
        if click:
            change_click = self.selenium_common.find_text_from(self.__driver, "//*[@data-clk]", "Change")
            change_click.click()
        if self.__allPremium == None:
            # self.__allPremium = self.__driver.find_elements(By.XPATH,'//*[@data-token-name|@data-id]')
            self.__allPremium = self.selenium_common.find_elements(self.__driver, '//*[@data-token-name|@data-id]')
        return self.__allPremium

    def trade_rise_is_change(self, tick_scratch_data, grasp_historical_pop):
        print(tick_scratch_data, grasp_historical_pop)
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
            print(
                f"Changing massage : {tick_short_name} is changed! price:({primitive_price}->{last_num}) {historical_pop_change}:( to {tick_change})")
        return is_rise_changed

    def scan_trade_tick_list(self):
        scan_trade_tick_list = []
        allPremium = self.__allPremium
        print(len(allPremium))
        for ele in allPremium:
            print(ele.text)
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
            c_time = time.strftime("%Y-%m-%d %H:%m:%S", time.gmtime())
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

    def tran_trade_categories(self, rise_tick_datas=None):
        categories = []
        if rise_tick_datas != None:
            rise_tick_datas = [str(x["short_name"]) for x in rise_tick_datas]
            for short_name in rise_tick_datas:
                categories.append(short_name)
        return categories

    def set_trade_categories(self, rise_tick_datas=None, sava_to_mongodb=False):
        daname = "list_trade_categories"
        mongodb_daname = "okx_list_trade_categories"
        categories = self.com_db.get_redis(daname)
        if rise_tick_datas == None:
            # 如果redis没有缓存项目类的数据，则从mongodb读取
            if len(categories) == 0:
                categories = self.com_db.read_data_to(mongodb_daname, {})
                # 从mongodb读取的数据并存入 redis.
                self.com_db.set_redis({
                    daname: categories
                })
        else:
            tick_categories = self.tran_trade_categories(rise_tick_datas)
            is_new_type_itme = False
            for short_name in tick_categories:
                if short_name not in categories:
                    is_new_type_itme = True
                    categories.append(short_name)
                    self.new_type_item(short_name, rise_tick_datas)
            if is_new_type_itme:
                self.com_db.set_redis({
                    daname: categories
                })
        self.__categories_trade_list = categories
        return categories

    def new_type_item(self, short_name, rise_tick_datas):
        for tick_data in rise_tick_datas:
            if short_name in tick_data:
                new_type_name = tick_data[short_name]
                print(f'new typeItem {new_type_name}')
                # TODO 发现新元素后的操作写在这里。
        pass

    def init_trade_historical_list(self):
        print("init trade historical list!")
        categories = self.set_trade_categories()
        if len(categories) == 0:
            scan_trade_tick_list = self.scan_trade_tick_list()
            categories = self.set_trade_categories(scan_trade_tick_list)
            print("categories", categories)
        for short_name in categories:
            if len(self.get_trade_historical_list(short_name)) == 0:
                all_premium_grasp_dict = self.load_trade_historical(max=1000)
                print(type(all_premium_grasp_dict))
                for trade_name, tick_scratch_list in all_premium_grasp_dict.items():
                    self.set_trade_historical_list(trade_name, tick_scratch_list)

    def get_trade_historical_list_pop(self, short_name):  # trade_historical_list
        redis_name = self.get_redis_trade_historical_list_name(short_name)
        type_list = self.com_db.get_redis(redis_name, [0, 0])
        print(f"get_trade_historical_list_pop {type(type_list)}{len(type_list)}")
        type_list = json.loads(type_list)
        print(f"get_trade_historical_list_pop {type(type_list)}{len(type_list)}")
        return type_list

    def get_trade_historical_list(self, short_name, pop=[0, -1]):
        redis_name = self.get_redis_trade_historical_list_name(short_name)
        type_list = self.com_db.get_redis(redis_name, pop)
        if type(type_list) == str:
            type_list = json.loads(type_list)
        return type_list

    def set_trade_historical_list(self, trade_name, tick_scratch_list):
        redis_name = self.get_redis_trade_historical_list_name(trade_name)
        self.com_db.set_redis({
            redis_name: json.dumps(tick_scratch_list)
        })

    def get_redis_trade_historical_list_name(self, short_name):
        return f"{self.__redis_trade_item_dict_pre}{short_name}"

    def load_trade_historical(self, max=1000, short_name=None):
        print(" load_okx_exchange_rise is exec .~")
        collection_name = self.__trade_historical_mongodb
        datas = []
        scan_trade_tick_list = self.scan_trade_tick_list()
        if self.__save_project_as_mongodb:
            if short_name != None:
                data = self.com_db.read_data_to(collection_name, {
                    "short_name": short_name,
                    "limit": max
                })
                datas = data
            else:
                # 使用mongodb存储
                for trade_item_dict in scan_trade_tick_list:
                    short_name = trade_item_dict["short_name"]
                    data = self.com_db.read_data_to(collection_name, {
                        "short_name": short_name,
                        "limit": max
                    })
                    datas += data
        else:
            # 使用本地文件序列化
            datas = self.com_db.unserialization(self.__exchangeDataFile)
            if datas == None:
                datas = []
        premium_grasp_list = {}
        for data in datas:
            short_name = data["short_name"]
            if premium_grasp_list.get(short_name) == None:
                premium_grasp_list[short_name] = []
            premium_grasp_list[short_name].append(data)
        return premium_grasp_list

    def categories_rise_sort(self, lg="%7"):
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
            if trade_info["change"] >= lg: short_list.append(trade_info)
        short_list.sort(key=lambda x: x["change"], reverse=True)
        return short_list

    def monitor_trade_rises(self):
        categories_rise_sort = self.categories_rise_sort("%7")
        # 调用多线程打开监控页面
        max_workers = len(categories_rise_sort)
        # categories_rise_sort = [(cate) for cate in categories_rise_sort]
        with  ThreadPoolExecutor(max_workers=max_workers) as pool:
            pool.submit(self.oversee_trade_data, categories_rise_sort)

    def oversee_trade_data(self, category_rise):
        short_name = category_rise["short_name"]
        short_name = short_name.lower()
        trade_spot_url = f"https://www.okx.com/trade-spot/{short_name}-usdt"
        driver = self.selenium_common.open_url(trade_spot_url, empty_driver=True)

        while category_rise["change"] > 7:
            self.selenium_common.execute_js(driver, "monitor_trade_data.js")
        return True

    def save_okx_exchange_rise(self):
        # 提取未保存数据
        grasp_listtmp = self.set_grasp_listtmp()
        # 设置保存标志位
        for item in grasp_listtmp:
            item["save_db"] = True

        if self.__save_project_as_mongodb:
            # 使用mongodb存储
            print(f"save_project_as_mongodb to {len(grasp_listtmp)} items.~")
            self.com_db.save_data_to("okx_exchange_rise", grasp_listtmp)
        else:
            # 使用本地文件序列化
            print(f"db serialization to {len(grasp_listtmp)} items.~")
            obj = self.com_db.unserialization(self.__exchangeDataFile)
            if obj == None:
                obj = []
            obj = obj + grasp_listtmp
            self.com_db.serialization(obj, self.__exchangeDataFile)
        self.set_grasp_listtmp(clear=True)

    def rise_tick_data_pop(self, short_name):
        for c_tick in self.__change_list_tick:
            # 如果tick还没有添加,或者价格有变动,则压入tick并将上一次推入总数据列中.
            if c_tick["short_name"].__eq__(short_name):
                self.__change_list_tick.remove(c_tick)
                return c_tick
        return None

    def get_trade_link(self, item_name):
        return f"https://www.okx.com/trade-spot/{item_name}"

    # ----------------------------------------------------------------------------------------
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
    # from selenium.webdriver.com_by import By
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
    #         network_th = self.thread_common.create_thread(thread_type="com",target=self.network_list)
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
    #         accounts = self.com_db.unserialization(self.get_account_serialization_file())
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
    #                 "userInput": """//*[@id="uc-com-account"]""",
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
    #                 self.com_db.unserialization(self.get_account_serialization_file()),
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
    #         self.com_db.serialization(account_data, filename)
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
    #         categories = self.com_db.get_redis(daname)
    #         if rise_tick_datas == None:
    #             #如果redis没有缓存项目类的数据，则从mongodb读取
    #             if len(categories) == 0:
    #                 categories = self.com_db.read_data_to(mongodb_daname,{})
    #                 #从mongodb读取的数据并存入 redis.
    #                 self.com_db.set_redis({
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
    #                 self.com_db.set_redis({
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
    #                   FOUND NEW ELEMENT..
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
    #         type_list = self.com_db.get_redis(redis_name,[0,0])
    #         print(f"get_trade_historical_list_pop {type(type_list)}{len(type_list)}")
    #         type_list = json.loads(type_list)
    #         print(f"get_trade_historical_list_pop {type(type_list)}{len(type_list)}")
    #         return type_list
    #     def get_trade_historical_list(self,short_name,pop=[0,-1]):
    #         redis_name = self.get_redis_trade_historical_list_name(short_name)
    #         type_list = self.com_db.get_redis(redis_name,pop)
    #         if type(type_list) == str:
    #             type_list = json.loads(type_list)
    #         return type_list
    #     def set_trade_historical_list(self,trade_name,tick_scratch_list):
    #         redis_name = self.get_redis_trade_historical_list_name(trade_name)
    #         self.com_db.set_redis({
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
    #                 data = self.com_db.read_data_to(collection_name,{
    #                     "short_name":short_name,
    #                     "limit": max
    #                 })
    #                 datas = data
    #             else:
    #                 #使用mongodb存储
    #                 for trade_item_dict in scan_trade_tick_list:
    #                     short_name = trade_item_dict["short_name"]
    #                     data = self.com_db.read_data_to(collection_name,{
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
    #             self.com_db.save_data_to("okx_exchange_rise",grasp_listtmp)
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

    def is_coin_name(self, coin_name, insert=None):
        table = self.com_db.get_dbfixedname('coin_digital')
        id = self.com_db.get_id(table, {
            "coin_name": coin_name
        })
        if id == 0:
            if insert != None:
                id = self.com_db.save(table, {
                    "coin_name": coin_name
                }, result_id=True)
                return id
            else:
                return None
        return id

    def put_transaction_data(self, flask):
        coin_name = flask.flask_request.form.get('coin_name')
        transaction = flask.flask_request.form.get('transaction')
        if coin_name == None or transaction == None:
            message = f"need a coin name or some transaction"
            self.com_util.print_warn(message)
            return self.com_util.print_result(data=message)
        transaction = self.com_string.json_load(transaction)
        id = self.is_coin_name(coin_name, insert={"coin_name": coin_name})
        transactions = []
        for tx in transaction:
            tx.append(id)
            transactions.append(tx)
        table = self.com_db.get_dbfixedname('coin_real_time_point')
        transactions = self.com_db.list_bind(table, transactions)
        message = self.com_db.save(table, data=transactions, insert_list=True)
        message = self.com_util.print_result(data=message)
        return message

    def get_transaction_data(self, flask):
        coin_name = flask.flask_request.args.get('coin_name')
        t = flask.flask_request.args.get('t')
        limit = flask.flask_request.args.get('limit')
        sort = flask.flask_request.args.get('sort')
        if coin_name == None:
            message = f"need a coin name or some transaction"
            self.com_util.print_warn(message)
            return self.com_util.print_result(data=message)
        t = self.com_util.default_value(t, self.com_util.create_timestamp(length=13))
        limit = self.com_util.default_value(limit, 100)
        sort = self.com_util.default_value(sort, 'DESC')
        id = self.is_coin_name(coin_name)
        if id == None:
            message = f"the {coin_name} not found"
            self.com_util.print_warn(message)
            return self.com_util.print_result(data=message)
        table = self.com_db.get_dbfixedname('coin_real_time_point')
        message = self.com_db.read(table, {
            "coin_name_id": id,
            "real_time": f"<{t}",
        }, sort=f"real_time {sort}", limit=limit, print_sql=True)
        message = self.com_util.print_result(data=message)
        return message

    def test_change_data(self, flask):
        coin_name = flask.flask_request.form.get('coin_name')
        investment_amount = flask.flask_request.form.get('investment_amount')
        balance = flask.flask_request.form.get('balance')
        message = flask.flask_request.form.get('message')
        profit = flask.flask_request.form.get('profit')
        buy_price = flask.flask_request.form.get('buy_price')
        buy_time = flask.flask_request.form.get('buy_time')
        sale_price = flask.flask_request.form.get('sale_price')
        sale_time = flask.flask_request.form.get('sale_time')
        message = flask.flask_request.form.get('message')
        url = flask.flask_request.form.get('url')

        if coin_name == None:
            info = f"need a coin name"
            self.com_util.print_warn(info)
            return self.com_util.print_result(data=info)
        file_path = self.com_config.get_public(f'data_analyze/exchange_website_{url}.txt')
        message = self.com_file.save(file_path, message)
        message = self.com_util.print_result(data=message)
        return message
