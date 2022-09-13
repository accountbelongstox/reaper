from kernel.base.base import *
import xml.dom.minidom
import random
import string
import re
import time
#import xml.etree.ElementTree as etree
class StringCommon(BaseClass):

    def __init__(self,args):
        pass

    def byte_to_str(self,astr):
        astr = str(astr)

        is_byte = re.compile('^b\'{0,1}')
        if re.search(is_byte,astr) is not None:
            astr = re.sub(re.compile('^b\'{0,1}'),'',astr)
            astr = re.sub(re.compile('\'{0,1}$'),'',astr)


        return astr

    def isnull(self,obj):
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

    def is_notnull(self,obj):
        not_null = not self.isnull(obj)
        return not_null

    def to_unicode(self,a):
        sum = b''
        for x in a:
            if x == 'u':
                sum += b'\u'
            else:
                sum += x.encode()
        return sum

    def create_string_id(self,s_):
        symbol = '-'
        s_ = s_.split(symbol)
        ids = []
        for s in s_:
            tmp_s = self.random_string(s, str.isupper(s))
            ids.append(tmp_s)
        return symbol.join(ids)


    def random_string(self,n=64,upper = False):

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


    def create_time(self,format= "%Y-%m-%d %H:%M:%S"):
        t = time.strftime(format, time.localtime())
        return t


    def filename_normal(self,filename):
        return filename.replace("\\","/")