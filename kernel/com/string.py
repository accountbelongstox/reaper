import datetime
import json

from kernel.base.base import *
# import xml.dom.minidom
import random
import string
import re
import time
import hashlib
# -*- coding: utf-8-*-
# Author: Jack Cui
# import sys
# from turtle import width
import cv2
# from PIL import Image
import numpy as np


# import xml.etree.ElementTree as etree
class String(BaseClass):

    def __init__(self, args):
        pass

    def byte_to_str(self, astr):
        try:
            astr = astr.decode('utf-8')
            return astr
        except:
            astr = str(astr)

            is_byte = re.compile('^b\'{0,1}')
            if re.search(is_byte, astr) is not None:
                astr = re.sub(re.compile('^b\'{0,1}'), '', astr)
                astr = re.sub(re.compile('\'{0,1}$'), '', astr)
            return astr

    def isnull(self, obj):
        try:
            if len(obj) == 0:
                return True
        except:
            pass
        if obj == None:
            return True
        elif obj == False:
            return True
        elif type(obj) == dict and len(obj.keys()) == 0:
            return True
        elif obj == 0:
            return True
        elif obj == 0.0:
            return True
        return False

    def is_notnull(self, obj):
        not_null = not self.isnull(obj)
        return not_null

    def to_unicode(self, a):
        sum = b''
        for x in a:
            if x == 'u':
                sum += b'\u'
            else:
                sum += x.encode()
        return sum

    def create_string_id(self, s_):
        symbol = '-'
        s_ = s_.split(symbol)
        ids = []
        for s in s_:
            tmp_s = self.random_string(s, str.isupper(s))
            ids.append(tmp_s)
        return symbol.join(ids)

    def random_num(self, a=0, b=100):
        number = random.randint(a, b)
        return number

    def random_string(self, n=64, upper=False):

        """生成一串指定位数的字符+数组混合的字符串"""
        if type(n) == str:
            n = len(n)
        m = random.randint(1, n)
        a = "".join([str(random.randint(0, 9)) for _ in range(m)])
        b = "".join([random.choice(string.ascii_letters) for _ in range(n - m)])
        s = ''.join(random.sample(list(a + b), n))
        if upper == True:
            s = s.upper()
        else:
            s = s.lower()
        return s

    def separate(self,string):
        pattern = re.compile(r"(\B|\b)+")
        sa = re.split(pattern,string)
        sa = [s for s in sa if s != ""]
        return sa

    def create_time(self, format="%Y-%m-%d %H:%M:%S"):
        t = time.strftime(format, time.localtime())
        return t

    def is_time_string(self, string):
        if type(string) != str:
            return False
        colons = re.findall(":", string)
        try:
            if len(colons) >= 2:
                time.strptime(string, "%Y-%m-%d %H:%M:%S")
                # time.strptime(check_date[ck_field], "Y年%m-%d %H:%M:%S")
            elif 0 < len(colons) < 2:
                time.strptime(string, "%Y-%m-%d %H:%M")
            else:
                time.strptime(string, "%Y-%m-%d")
            return True
        except:
            return False

    def md5(self, string=""):
        if string == "":
            string = self.create_time()
        md5 = hashlib.md5(string.encode('utf8')).hexdigest()
        return md5

    def create_time_no_space(self, format="%Y-%m-%d-%H:%M:%S"):
        return self.create_time(format=format)

    def dir_normal(self, filename, linux=False):
        filename = re.sub(re.compile(r"[\\\/]+"), "/", filename)
        if self.load_module.is_windows() and linux == False:
            # pattern = re.compile(r"[\/]+")
            filename = filename.replace("//", "/")
            filename = filename.replace("/", "\\")
        return filename

    def float(self, _str):
        try:
            _float = float(_str)
        except:
            str_reg = re.compile(r"[^0-9\.\+\-]")
            _str = re.sub(str_reg, "", _str)
            _float = float(_str)
        return _float

    def clear_string(self, string):
        space_pattern = re.compile(r"\s+")
        string = re.sub(space_pattern, "", string)
        return string

    def to_array(self, string,separatist=None):
        if separatist == None:
            separatist = [",",";"]
        space_pattern = re.compile(r"\s+")
        string = re.sub(space_pattern, "", string)
        return string

    def img_to_text(self, img_fname, save_fname=None):
        img = cv2.imread(img_fname)
        height, width, _ = img.shape
        text_list = []
        for h in range(height):
            for w in range(width):
                R, G, B = img[h, w]
                if R | G | B == 0:
                    break
                idx = (G << 8) + B
                text_list.append(chr(idx))
        content = "".join(text_list)
        print(content)
        if save_fname == None:
            save_fname = self.file_suffix(img_fname, "txt")
            self.com_util.print_info(f"text to image at {save_fname}")
        # self.com_file.save(content,save_fname)

    def json_load(self, string):
        try:
            json_loaded = json.loads(string)
        except Exception as e:
            self.com_util.print_error(f'json_load {e}')
            json_loaded = string
        return json_loaded

    def text_to_img(self, txt_fname, save_fname=None):
        content = self.com_file.read(txt_fname)
        text_len = len(content)
        img_w = 1000
        img_h = 1680
        img = np.zeros((img_h, img_w, 3))
        x = 0
        y = 0
        for each_text in content:
            idx = ord(each_text)
            rgb = (0, (idx & 0xFF00) >> 8, idx & 0xFF)
            img[y, x] = rgb
            if x == img_w - 1:
                x = 0
                y += 1
            else:
                x += 1
        if save_fname == None:
            save_fname = self.file_suffix(txt_fname, "jpg")
            self.com_util.print_info(f"text to image at {save_fname}")
        cv2.imwrite(save_fname, img)

    def file_suffix(self, file_path, suffix):
        file_path = file_path.split('.')[0:-1]
        suffix = suffix.replace('.', "")
        file_path.append(suffix)
        file_path = ".".join(file_path)
        return file_path
