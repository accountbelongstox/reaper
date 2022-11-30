import json
import pprint
import re
import shutil
import time
# import socket
from queue import Queue


from kernel.base.base import *
import datetime
from time import strftime
from time import gmtime
# import xml.etree.ElementTree as etree
from urllib.parse import *
import inspect
import operator
import win32api
import win32con
from pymouse import PyMouse  # 模拟鼠标
from pykeyboard import PyKeyboard  # 模拟键盘

pyMouse = PyMouse()
pyKeyboard = PyKeyboard()

class Util(BaseClass):
    RED = '\033[31;1m'
    GREEN = '\033[32;1m'
    YELLOW = '\033[33;1m'
    BLUE = '\033[34;1m'
    MAGENTA = '\033[35;1m'
    CYAN = '\033[36;1m'
    BOLD = '\033[1m'
    UNDERLINE = '\033[4m'
    ENDC = '\033[0m'

    def __init__(self, args):
        pass

    # 将一个结果添加到list，如果没有key则创建
    def add_to_dict(self, result, key, value):
        if key not in result:
            result[key] = []
        if value not in result[key]:
            result[key].append(value)
        return result[key]

    # 将数组中的二维数组提取出来
    def extract_list(self, result):
        while len(result) == 1 and type(result[0]) is list:
            result = result[0]
        is_two_dimensional_list = None
        for item in result:
            if type(item) is list:
                is_two_dimensional_list = True
            else:
                is_two_dimensional_list = False
                break
        if is_two_dimensional_list:
            extract_list = []
            for item in result:
                extract_list.append(item[0])
            result = extract_list
        return result

    # 通过一个字符串分割数组
    def split_list(self, result, split_symbol=[None, False, True], start=0):
        if type(split_symbol) is not list:
            split_symbol = [split_symbol]
        split_list = []
        index = 0
        step = 0
        for i in range(len(result)):
            item = result[i]
            if item in split_symbol:
                if i == 0:
                    split_list.append([])
                elif i - index > 1:
                    step += 1
                    split_list.append([])
                index = i
            else:
                if i == 0:
                    split_list.append([])
                if type(item) is not list:
                    split_list[step].append(item)
                else:
                    item = self.extract_list(item)
                    for strip in item:
                        split_list[step].append(strip)
        return split_list

    def print_success(self, message, time=False):
        if time: message = f"{message} : {self.com_string.create_time()}"
        print(f"\033[0;37;42m{message}\033[0m")
        return self.print_result(message, -1)

    def print_danger(self, message, time=False):
        if time: message = f"{message} : {self.com_string.create_time()}"
        print(f"{self.RED}{message}\033[0m")
        return self.print_result(message, -1)

    def print_warn(self, message, time=False):
        if time: message = f"{message} : {self.com_string.create_time()}"
        print(f"{self.MAGENTA}{message}\033[0m")
        return self.print_result(message, -1)

    def print_info(self, message, time=False):
        if time: message = f"{message} : {self.com_string.create_time()}"
        print(f"\033[0;32;40m{message}\033[0m")
        return self.print_result(message, -1)

    def print_data(self, data):
        return self.result(data)

    def print_result(self, data, code=0):
        if data or data == None:
            if data == None:
                message = self.print_message("Sql request execute succeeded.", data)
            else:
                message = self.print_message("Data acquisition succeeded.", code)
            if type(data) == str:
                message = self.print_message(data, code)
            if type(data) != list:
                data = [data]
            length = len(data)
        else:
            message = self.print_message("Data acquisition failed.", -1)
            length = 0
        message["length"] = length
        message["data"] = data
        return message

    def print_message(self, msg, code=0):
        message = {
            "message": msg,
            "code": code
        }
        return message

    def pprint(self, data):
        pprint.pprint(data)

    def deduplication(self, data):
        try:
            data = list(
                set(data)
            )
        except Exception as e:
            print("deduplication_info", e)
            try:
                data = [list(t) for t in set([tuple(d) for d in data])]
            except Exception as e:
                print("deduplication_info", e)
                try:
                    data = set([str(item) for item in data])
                    data = [eval(i) for i in data]
                except Exception as e:
                    print("deduplication_info", e)
        return data

    def unique_list(self, list_arr):
        result = []
        for item in list_arr:
            if item not in result:
                result.append(item)
        return result

    def get_list_value(self, list_arr, arr_len, default=None):
        if not list_arr:
            return default
        if len(list_arr) >= arr_len + 1:
            return list_arr[arr_len]
        else:
            return default

    def get_dict_value(self, dict_object, key, default=None):
        if not dict_object:
            return default
        if key in dict_object:
            return dict_object[key]
        else:
            return default

    def array_to_queue(self, array, unique=True):
        queue = Queue()
        if unique == True:
            tmp_array = []
            for item in array:
                if item not in tmp_array:
                    tmp_array.append(item)
            array = tmp_array
        for item in array:
            queue.put(item)
        return queue

    def clear_value(self, arr, values=None):
        default_clear = [" ", ""]
        if type(arr) != list:
            return arr
        if values == None:
            values = default_clear
        if type(values) == str:
            values = [values]
        for item in default_clear:
            if item not in values:
                values.append(item)
        index = 0
        while index < len(arr):
            if arr[index] in values or str(arr[index]).strip() in values:
                del arr[index]
                index = index - 1
            index += 1
        return arr

    def rtrim(self, arr, value):
        index = 0
        while index < len(arr):
            if arr[index] == value:
                del arr[index]
                index = index - 1
            else:
                break
            index += 1
        return arr

    def ltrim(self, arr, value):
        index = len(arr) - 1
        while index >= 0:
            if arr[index] == value:
                del arr[index]
            else:
                break
            index -= 1
        return arr

    def trim(self, arr, value):
        arr = self.ltrim(arr, value)
        arr = self.rtrim(arr, value)
        return arr

    def get_parameter(self, method, info=True):
        parameter_names = inspect.getfullargspec(method)
        parameter_names = parameter_names.args
        if info: self.print_info(parameter_names)
        return parameter_names

    def create_time(self, format="%Y-%m-%d %H:%M:%S"):
        t = time.strftime(format, time.localtime())
        return t

    def timestamp_todate(self, timestamp):
        ctime = datetime.datetime.fromtimestamp(timestamp)
        ctime = str(ctime)
        return ctime

    def timer(self, starttime, format="%Y-%m-%d %H:%M:%S"):
        if type(starttime) == str:
            starttime = datetime.datetime.strptime(starttime, format)
        endtime = datetime.datetime.now()
        time_difference = (endtime - starttime).seconds
        time_statistics = strftime("%H:%M:%S", gmtime(time_difference))
        return time_statistics

    def equal_time(self, starttime, endtime, format="%Y-%m-%d %H:%M:%S"):
        if type(starttime) == str:
            starttime = datetime.datetime.strptime(starttime, format)
        if type(endtime) == str:
            endtime = datetime.datetime.strptime(endtime, format)
        time_difference = endtime > starttime
        # time_statistics = strftime("%H:%M:%S", gmtime(time_difference))
        return time_difference

    def create_time_now(self):
        now = datetime.datetime.now()
        return now

    def create_timestamp(self, length=10):
        now = int(round(time.time()))
        if length == 13:
            now = now * 1000
        return now
    def date_totimestamp(self, length=10):
        now = int(round(time.time()))
        if length == 13:
            now = now * 1000
        return now

    def proportion(self, x, rate=0):
        if rate == 0:
            return x
        rate_value = rate / 100
        if rate > 0:
            x = x + (x * rate_value)
        else:
            x = x - (x * rate_value)
        return x
    def to_json(self,data):
        try:
            data_json = json.loads(data)
        except Exception as e:
            data_json = data
            self.print_warn(e)
        return data_json

    def urljoin(self, url, sub_url):
        url = urljoin(url, sub_url)
        return url

    def get_module_name(self, module):
        name = module.__class__.__name__
        return name

    def eq(self, initial, compare):
        if (len(initial) != len(compare)):
            return False
        initial.sort(key=lambda x: str(x))
        compare.sort(key=lambda x: str(x))
        for index in range(len(initial)):
            initial_item = initial[index]
            compare_item = compare[index]
            if initial_item != compare_item:
                return False
        return True

    def to_english_array(self, s):
        if type(s) == list:
            s = " ".join(s)
        s = s.strip()
        pattern = re.compile(r'[^a-zA-Z]+')
        s = re.split(pattern, s)
        return s

    def cmd(self, demand, info=False):
        outs = os.popen(demand, 'r')
        out = outs.read()
        if info == True:
            print("info:", info)
        return out

    def ping_ips(self, ips):
        queue = self.array_to_queue(ips, unique=True)
        results = []
        while queue.qsize() > 0:
            ip = queue.get()
            result = self.ping_ip(ip)
            results.append(result)
        results.sort(key=lambda x: x['timeout'])
        return results

    def ping_ip(self, ip):
        cmd = f"ping {ip}"
        self.print_info(cmd)
        outs = os.popen(cmd, 'r')
        out = outs.read()
        get_time = re.compile(r"time\=(\d+)")
        time_group = re.findall(get_time, out)
        time_outs = re.compile(r"request\s+timed\s+out", re.I)
        time_outs_group = re.findall(time_outs, out)
        time_group = [int(t) for t in time_group]
        # 如果有 Request time out
        time_outs_group = [1000 for t in time_outs_group]
        # 合并所有延迟,并计算最终值.
        time_group = time_group + time_outs_group
        timeout = 0
        for t in time_group:
            timeout += t
        divint = len(time_group)
        is_NotFound_mianhost = False
        if divint == 0:
            is_NotFound_mianhost = True
            divint = 1
        timeout = timeout // divint
        if is_NotFound_mianhost:
            print("Error:", outs)

        self.print_info(f"ip: {ip} \n\ttimeout: {timeout}ms\n")
        result = {
            "ip": ip,
            "timeout": timeout
        }
        return result

    def set_hosts_file(self, domain, ipAddress):
        file = "C:/Windows/System32/drivers/etc/HOSTS"
        # file = self.load_module.get_control_dir('HOSTS')
        # format hosts_file
        print(f"\n update hosts:({domain} with {ipAddress} in {file}")
        local_text = self.com_file.open(file)
        local_text = local_text.strip()
        local_text = re.split('[\n\r]+', local_text)

        exists_domain = f' {domain}'
        update_ip = f"{ipAddress} {domain}"
        is_add = None
        for index in range(0, len(local_text)):
            item = local_text[index].strip()
            if item.endswith(exists_domain):
                if is_add == True:
                    local_text[index] = ""
                else:
                    is_add = True
                    local_text[index] = update_ip

        # 未添加过
        if is_add == None:
            local_text.append(update_ip)

        local_text = [t.strip() for t in local_text if t != ""]
        local_text = '\n'.join(local_text) + '\n'
        self.com_file.save(file, local_text, overwrite=True)

        # flush_dns
        self.flushdns()

    def flushdns(self):
        cmd = "ipconfig /flushdns"
        self.print_info(f'flushdns')
        self.cmd(cmd)

    def equal(self, origin, other):
        result = operator.eq(origin, other)
        return result

    def default_value(self, value, default=None):
        if value != None:
            return value
        else:
            return default

    def rmtree(self, dir):
        shutil.rmtree(dir, ignore_errors=False, onerror=None)

    def get_keycode(self,keycode):
        GetKeyboardLayoutName = win32api.GetKeyboardLayoutList()
        print("GetKeyboardLayoutName",GetKeyboardLayoutName)
        if isinstance(keycode,int):
            return keycode
        keymap = {
            "0": 49, "1": 50, "2": 51, "3": 52, "4": 53, "5": 54, "6": 55, "7": 56, "8": 57, "9": 58,
            'F1': 112, 'F2': 113, 'F3': 114, 'F4': 115, 'F5': 116, 'F6': 117, 'F7': 118, 'F8': 119,
            'F9': 120, 'F10': 121, 'F11': 122, 'F12': 123, 'F13': 124, 'F14': 125, 'F15': 126, 'F16': 127,
            "A": 65, "B": 66, "C": 67, "D": 68, "E": 69, "F": 70, "G": 71, "H": 72, "I": 73, "J": 74,
            "K": 75, "L": 76, "M": 77, "N": 78, "O": 79, "P": 80, "Q": 81, "R": 82, "S": 83, "T": 84,
            "U": 85, "V": 86, "W": 87, "X": 88, "Y": 89, "Z": 90,
            'BACKSPACE': 8, 'TAB': 9, 'TABLE': 9, 'CLEAR': 12,
            'ENTER': 13, 'SHIFT': 16, 'CTRL': 17,
            'CONTROL': 17, 'ALT': 18, 'ALTER': 18, 'PAUSE': 19, 'BREAK': 19, 'CAPSLK': 20, 'CAPSLOCK': 20, 'ESC': 27,
            'SPACE': 32, 'SPACEBAR': 32, 'PGUP': 33, 'PAGEUP': 33, 'PGDN': 34, 'PAGEDOWN': 34, 'END': 35, 'HOME': 36,
            'LEFT': 37, 'UP': 38, 'RIGHT': 39, 'DOWN': 40, 'SELECT': 41, 'PRTSC': 42, 'PRINTSCREEN': 42, 'SYSRQ': 42,
            'SYSTEMREQUEST': 42, 'EXECUTE': 43, 'SNAPSHOT': 44, 'INSERT': 45, 'DELETE': 46, 'HELP': 47, 'WIN': 91,
            'WINDOWS': 91, 'NMLK': 144,
            'NUMLK': 144, 'NUMLOCK': 144, 'SCRLK': 145}
        key_upper = keycode.upper()
        if key_upper in keymap:
            return keymap[key_upper]
        return keycode

    def is_special_key(self,key):
        if key in ["@","!","~"]:
            return True
        return False

    def combine_key(self,key_code):
        if key_code == "@":
            self.down_key("SHIFT")
            self.press_key("2")
            self.release_key("SHIFT")
    def type_string(self,string):
        pyKeyboard.type_string(string)

    def release_key(self,key_code):
        key_code = self.get_keycode(key_code)
        win32api.keybd_event(key_code, win32api.MapVirtualKey(key_code, 0), win32con.KEYEVENTF_KEYUP, 0)

    def down_key(self,key_code):
        key_code = self.get_keycode(key_code)
        win32api.keybd_event(key_code, win32api.MapVirtualKey(key_code, 0), 0, 0)

    def press_and_release_key(self,key_code):
        self.down_key(key_code)
        self.release_key(key_code)

    def press_key(self,key):
        key = self.get_keycode(key)
        if self.is_special_key(key) == True:
            self.combine_key(key)
        else:
            self.press_and_release_key(key)

    def get_system_metrics(self):
        result = {}
        result["x"] = win32api.GetSystemMetrics(win32con.SM_CXSCREEN)
        result["y"] = win32api.GetSystemMetrics(win32con.SM_CYSCREEN)
        return result
