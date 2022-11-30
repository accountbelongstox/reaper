from kernel.base.base import *
import os
import zipfile
import shutil
import pickle
import base64
import time
import pytesseract
import re
from paddleocr import PaddleOCR, draw_ocr
from urllib.parse import urlparse
from PIL import Image
import filetype
# from pysubs2 import SSAFile, SSAEvent, make_time
import pysubs2

class File(BaseClass):

    def __init__(self,args):
        pass

    def b64encode(self,data_file):
        if self.isfile(data_file):
            print(os.path.splitext(data_file))
            extent_file = os.path.splitext(data_file)[1]
            extent_file = extent_file.replace(".","")
            suffix = "data:image/{};base64,".format(extent_file)
            data = self.open(data_file, 'b')
        else:
            suffix = ""
            data = data_file
        data = base64.b64encode(data)
        data = self.com_string.byte_to_str(data)
        data = suffix + data
        return data

    def image_to_str(self,image_url, lang):
        im = Image.open(image_url)
        im = im.convert('L')
        print(f"im {im}")
        im_str = pytesseract.image_to_string(im, lang=lang)
        return im_str

    def image_to_str_from_paddleorc(self,img_path,lang="ch"):
        # ocr = PaddleOCR(use_angle_cls=True, )
        # # 输入待识别图片路径
        # img_path = r"d:\Desktop\4A34A16F-6B12-4ffc-88C6-FC86E4DF6912.png"
        # # 输出结果保存路径
        # result = ocr.ocr(img_path, cls=True)
        # for line in result:
        #     print(line)
        #
        ocr = PaddleOCR(use_angle_cls=True, lang="en")  # need to run only once to download and load model into memory
        result = ocr.ocr(img_path, cls=True)
        return {
            "text":result[0][1][0],
            "data":result
        }
    def rename_remove_space(self,filename):
        space_pattern  = re.compile(r"\s+")
        file_space = re.findall(space_pattern, filename)
        if (len(file_space) > 0):
            new_file_name = os.path.basename(filename)
            new_file_name = re.sub(space_pattern,"",new_file_name )
            file_basedir = os.path.dirname(filename)
            new_file = os.path.join(file_basedir, new_file_name)
            self.cut(filename, new_file)
            filename =new_file
        return filename
    def read_file(self,file_name,encoding="utf-8",info=False):
        return self.load_file(file_name,encoding,info=info)

    def load_file(self,file_name,encoding="utf-8",info=False):
        file_name = self.get_path(file_name)
        file_object = self.get_file_encode(file_name,encoding=encoding,info=info)
        content = None
        if file_object != None:
            content = file_object.get("content")
        return content

    def get_file_encode(self,file_name,encoding=None,info=False):
        codings = [
            "utf-8",
            "utf-16",
            "utf-16le",
            "utf-16BE",
            "gbk",
            "gb2312",
            "us-ascii",
            "ascii",
            "IBM037",
            "IBM437",
            "IBM500",
            "ASMO-708",
            "DOS-720",
            "ibm737",
            "ibm775",
            "ibm850",
            "ibm852",
            "IBM855",
            "ibm857",
            "IBM00858",
            "IBM860",
            "ibm861",
            "DOS-862",
            "IBM863",
            "IBM864",
            "IBM865",
            "cp866",
            "ibm869",
            "IBM870",
            "windows-874",
            "cp875",
            "shift_jis",
            "ks_c_5601-1987",
            "big5",
            "IBM1026",
            "IBM01047",
            "IBM01140",
            "IBM01141",
            "IBM01142",
            "IBM01143",
            "IBM01144",
            "IBM01145",
            "IBM01146",
            "IBM01147",
            "IBM01148",
            "IBM01149",
            "windows-1250",
            "windows-1251",
            "Windows-1252",
            "windows-1253",
            "windows-1254",
            "windows-1255",
            "windows-1256",
            "windows-1257",
            "windows-1258",
            "Johab",
            "macintosh",
            "x-mac-japanese",
            "x-mac-chinesetrad",
            "x-mac-korean",
            "x-mac-arabic",
            "x-mac-hebrew",
            "x-mac-greek",
            "x-mac-cyrillic",
            "x-mac-chinesesimp",
            "x-mac-romanian",
            "x-mac-ukrainian",
            "x-mac-thai",
            "x-mac-ce",
            "x-mac-icelandic",
            "x-mac-turkish",
            "x-mac-croatian",
            "utf-32",
            "utf-32BE",
            "x-Chinese-CNS",
            "x-cp20001",
            "x-Chinese-Eten",
            "x-cp20003",
            "x-cp20004",
            "x-cp20005",
            "x-IA5",
            "x-IA5-German",
            "x-IA5-Swedish",
            "x-IA5-Norwegian",
            "x-cp20261",
            "x-cp20269",
            "IBM273",
            "IBM277",
            "IBM278",
            "IBM280",
            "IBM284",
            "IBM285",
            "IBM290",
            "IBM297",
            "IBM420",
            "IBM423",
            "IBM424",
            "x-EBCDIC-KoreanExtended",
            "IBM-Thai",
            "koi8-r",
            "IBM871",
            "IBM880",
            "IBM905",
            "IBM00924",
            "EUC-JP",
            "x-cp20936",
            "x-cp20949",
            "cp1025",
            "koi8-u",
            "iso-8859-1",
            "iso-8859-2",
            "iso-8859-3",
            "iso-8859-4",
            "iso-8859-5",
            "iso-8859-6",
            "iso-8859-7",
            "iso-8859-8",
            "iso-8859-9",
            "iso-8859-13",
            "iso-8859-15",
            "x-Europa",
            "iso-8859-8-i",
            "iso-2022-jp",
            "csISO2022JP",
            "iso-2022-jp",
            "iso-2022-kr",
            "x-cp50227",
            "euc-jp",
            "EUC-CN",
            "euc-kr",
            "hz-gb-2312",
            "GB18030",
            "x-iscii-de",
            "x-iscii-be",
            "x-iscii-ta",
            "x-iscii-te",
            "x-iscii-as",
            "x-iscii-or",
            "x-iscii-ka",
            "x-iscii-ma",
            "x-iscii-gu",
            "x-iscii-pa",
            "utf-7",
       ]
        if encoding != None:
            codings = [encoding] + codings
        index = 0
        while index < len(codings):
            encoding = codings[index]
            try:
                f = open(file_name, f"r+",encoding=encoding)
                content = f.read()
                if info==True:
                    self.com_util.print_info(f"Successfully mode {encoding} to {file_name}")
                f.close()
                result = {
                    "encoding":encoding,
                    "content":content
                }
                return result
            except Exception as e:
                self.com_util.print_warn(f"file open error, {file_name}")
                self.com_util.print_warn(e)
                index+=1
        return None

    def open(self,file_name,encoding="utf-8"):
        content = self.load_file(file_name,encoding=encoding)
        return content

    def read(self,file_name,encoding="utf-8"):
        content = self.load_file(file_name,encoding=encoding)
        return content

    def load_js(self,file_name,encoding="utf-8"):
        template_dir = self.com_config.get_js_dir()
        file_path = os.path.join(template_dir,file_name)
        content = self.load_file(file_path,encoding)
        return content

    def load_html(self,file_name,encoding="utf-8"):
        template_dir = self.com_config.get_template_dir()
        file_path = os.path.join(template_dir,file_name)
        content = self.load_file(file_path,encoding)
        return content

    def get_default_save_dir(self):
        save_dir = self.com_config.get_public("save_dir")
        return save_dir

    def save(self,file_name=None,content=None,encoding=None,overwrite=False):
        return self.save_file(file_name, content, encoding=encoding, overwrite=overwrite)

    def create_file_name(self,prefix='',suffix=""):
        filename = self.com_string.random_string(16)
        save_time = self.save_time()
        if prefix != '':
            prefix = f"{prefix}_"
        filename = f"{prefix}{save_time}_{filename}{suffix}"
        filedir = self.com_config.get_public("save_dir")
        filesavedir = os.path.join(filedir,filename)
        return filesavedir

    def save_time(self,):
        t = time.strftime("%Y_%m_%d_%H_%M_%S", time.localtime())
        return t

    def save_file(self,file_name=None,content=None,encoding=None,overwrite=False):
        if file_name == None:
            print("the save Content not accessed.{file_name}%s}" % file_name)
            return None
        if content == None:
            content = file_name
            file_name = self.create_file_name()
        basename = os.path.dirname(file_name)
        if basename == "":
            basename = self.get_default_save_dir()
            file_name = os.path.join(basename,file_name)
        print(f"save_file ：{file_name}")
        if os.path.exists(basename) is not True and os.path.isdir(basename) is not True:
            self.mkdir(basename)
        if not self.isfile(file_name):
            overwrite = True

        if encoding == None and type(content) == str:
            encoding = "utf-8"
        if overwrite ==True:
            m = "w"
        else:
            m = "a"
        print(f"encoding {encoding}")
        if encoding == None or encoding == "binary":
            f = open(file_name, f"{m}b+")
            content = content.encode(encoding)
        else:
            f = open(file_name, f"{m}+",encoding=encoding)
        try:
            # self.com_util.print_warn(f"savefile_encoding {encoding}")
            f.write(content)
        except:
            f.close()
            content = self.com_string.byte_to_str(content)
            f = open(file_name, f"{m}+",encoding="utf-8")
            f.write(content)
        f.close()
        return file_name
    def read_file_bytes(self,file_name):
        file_name = self.get_path(file_name)
        if self.isfile(file_name):
            with open(file_name, "rb") as f:
                data = f.read()
            return data
        else:
            return None

    def zip_extract(self,file,member,o=None):
        if o == None:
            o = os.path.dirname(file)
        with zipfile(file) as f:
            f.extract(member,o)

    def zip_extractall(self,file,odir=None,member=None):
        if odir == None:
            odir = os.path.dirname(file)
        with zipfile.ZipFile(file) as f:
            f.extractall(odir,member)
        return odir
    def file_extract(self, filename):
        """
        #输助函数,将最后下载的文件解压和删除。
        :param filename:
        :return:
        """
        extract_dir = os.path.dirname(filename)
        print(f"extract file {filename} to {extract_dir}")
        return self.zip_extractall(filename,extract_dir)

    def remove(self,top_path):
        print("delete : " ,top_path)
        for root, dirs, files in os.walk(top_path, topdown=False):
            for name in files:
                os.remove(os.path.join(root, name))
            for name in dirs:
                os.rmdir(os.path.join(root, name))
        if os.path.isdir(top_path):
            os.rmdir(top_path)
        elif os.path.isfile(top_path):
            os.remove(top_path)

    def mkdir(self, dir):
        if os.path.exists(dir) and os.path.isdir(dir):
            return False
        else:
            os.makedirs(dir,exist_ok=True)
            return True

    def isFile(self, path):
        return self.isfile(path)
    def isfile(self, path):
        if type(path) is not str:
            return False
        path = self.get_path(path)
        if os.path.exists(path) and os.path.isfile(path) and os.path.getsize(path) > 0:
            return True
        else:
            return False

    def get_path(self,path):
        if os.path.exists(path) and os.path.isfile(path):
            return path
        public_dir = self.com_config.get_public(path)
        if os.path.exists(public_dir) and os.path.isfile(public_dir):
            return public_dir
        path = os.path.join(self.getcwd(),path)
        if os.path.exists(path) and os.path.isfile(path):
            return path
        else:
            return path

    def isdir(self, path):
        if type(path) is not str:
            return False
        if os.path.exists(path) and os.path.isdir(path) :
            return True
        else:
            return False

    def copy(self, src, dst):
        return shutil.copyfile(src, dst)
    def cut(self, src, dst):
        dst_basedir = os.path.dirname(dst)
        self.mkdir(dst_basedir)
        shutil.copyfile(src, dst)
        os.remove(src)
    def rmtree(self, dir):
        shutil.rmtree(dir)

    def dir_to_localurl(self, filename):
        control_name = self.load_module.get_control_name()
        filename = filename.split(control_name)[-1]
        filename = self.dir_normal(filename,linux=True)
        filename = filename.lstrip('/')
        return filename

    def file_type(self, filename):
        if self.isfile(filename) == False:
            return None
        kind = filetype.guess(filename)
        if kind is None:
            return ""
        else:
            if kind.extension == None:
                return ""
            return kind.extension
    def file_to(self,filename,encoding="utf-8"):
        file_object = self.get_file_encode(filename)
        if file_object == None:
            return False
        file_encode = file_object.get('encoding')
        if file_encode != encoding:
            content = self.read_file(filename)
            # content = content.encode(encoding)
            os.remove(filename)
            self.save(filename,content,encoding=encoding)
        return True

    def dir_to(self,filedir,encoding="utf-8"):
        files = os.listdir(filedir)
        for file in files:
            file = os.path.join(filedir, file)
            self.file_to(file,encoding)

    # def srt_to_doc(self,filename):
    #

    def srt(self, filename,language="en"):
        pattern = re.compile(r'^.+}')
        english_pattern = re.compile(r'^[a-zA-Z\-0-9\"]')
        chinese_pattern = re.compile(r"^([\u4e00-\u9fa5]|[\ufe30-\uffa0]|[\u4e00-\uffa5])+")
        encoding = self.get_file_encode(filename)
        encoding = encoding.get('encoding')
        subs = pysubs2.load(filename, encoding=encoding)
        subs.shift(s=2.5)
        strs = []
        for line in subs:
            if language == "en":
                text = line.text
                text = re.sub(pattern,"",text)
                if re.search(chinese_pattern,text) == None:
                    strs.append(text)
                else:
                    try:
                        origin_text = text
                        trans = self.com_translate.translate_from_google(origin_text,dest="en",src="zh-CN",)
                        text = trans.get('text')
                        print(f"be translated {origin_text} to {text}")
                        strs.append(text)
                    except Exception as e:
                        self.com_util.print_warn(e)
            else:
                text = line.text
        return strs

    def file_suffix(self,file_path,suffix):
        file_path = file_path.split('.')[0:-1]
        suffix = suffix.replace('.',"")
        file_path.append(suffix)
        file_path = ".".join(file_path)
        return file_path

    def get_template_dir(self,filename=None,fulllink=False):
        control_dir = self.load_module.get_control_dir()
        if filename == None:
            filename = ""
        elif filename and fulllink == True:
            top_symbol = re.compile(r'^\/')
            filename = re.sub(top_symbol, '', filename)
        template_folder = self.com_config.get_global("flask_template_folder")
        template_folder = os.path.join(control_dir,template_folder)
        filename = os.path.join(template_folder, filename)
        return filename

    def get_static_dir(self,filename=None,fulllink=False):
        control_dir = self.load_module.get_control_dir()
        print(control_dir)
        if filename == None:
            filename = ""
        elif filename and fulllink == True:
            top_symbol = re.compile(r'^\/')
            filename = re.sub(top_symbol, '', filename)
        template_folder = self.com_config.get_global("flask_static_folder")
        template_folder = os.path.join(control_dir,template_folder)
        filename = os.path.join(template_folder, filename)
        return filename