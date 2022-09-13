from kernel.base.base import *
import os
import zipfile
import shutil
import pickle
import base64
import time
# import pytesseract
from paddleocr import PaddleOCR, draw_ocr
from PIL import Image

class FileCommon(BaseClass):

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
        data = self.string_common.byte_to_str(data)
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

    def load_file(self,file_name,encoding="utf-8"):

        file_name = self.get_path(file_name)
        if encoding == "b":
            f = open(file_name, f"rb+")
        else:
            f = open(file_name, f"r+",encoding=encoding)
        content = f.read()
        f.close()
        return content

    def open(self,file_name,encoding="utf-8"):
        content = self.load_file(file_name,encoding=encoding)
        return content

    def load_js(self,file_name,encoding="utf-8"):
        template_dir = self.config_common.get_js_dir()
        file_path = os.path.join(template_dir,file_name)
        content = self.load_file(file_path,encoding)
        return content

    def load_html(self,file_name,encoding="utf-8"):
        template_dir = self.config_common.get_template_dir()
        file_path = os.path.join(template_dir,file_name)
        content = self.load_file(file_path,encoding)
        return content

    def get_default_save_dir(self):
        save_dir = self.config_common.get_public("save_dir")
        return save_dir

    def save(self,file_name=None,content=None,encoding=None,override=False):
        return self.save_file(file_name, content, encoding=encoding, override=override)

    def create_file_name(self):
        filename = self.string_common.random_string(16)
        save_time = self.save_time()
        filename = f"{save_time}_filename_{filename}"
        filedir = self.config_common.get_public("save_dir")
        filesavedir = os.path.join(filedir,filename)
        return filesavedir

    def save_time(self,):
        t = time.strftime("%Y_%m_%d_%H_%M_%S", time.localtime())
        return t

    def save_file(self,file_name=None,content=None,encoding=None,override=False):
        if content is None:
            content = file_name
            file_name = None
        if content is None:
            print("the save not Found content.")
            return None
        if file_name is None:
            file_name = self.create_file_name()

        basename = os.path.dirname(file_name)
        if basename == "":
            basename = self.get_default_save_dir()
            file_name = os.path.join(basename,file_name)
        print(f"basename ：{basename}")
        print(f"file_name ：{file_name}")
        if os.path.exists(basename) is not True and os.path.isdir(basename) is not True:
            self.mkdir(basename)
        if not self.isfile(file_name):
            override = True

        if encoding == None and type(content) == str:
            encoding = "utf-8"
        if override ==True:
            m = "w"
        else:
            m = "a"
        if encoding == None:
            f = open(file_name, f"{m}b+")
        else:
            f = open(file_name, f"{m}+",encoding=encoding)
        try:
            f.write(content)
        except:
            f.close()
            content = self.string_common.byte_to_str(content)
            f = open(file_name, f"{m}+",encoding="utf-8")
            f.write(content)
        f.close()
        return file_name

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

            # shutil.rmtree(top_path)

    def isfile(self, path):
        if type(path) is not str:
            return False
        path = self.get_path(path)
        if os.path.exists(path) and os.path.isfile(path):
            return True
        else:
            return False

    def get_path(self,path):
        basedir = os.path.dirname(path)
        if os.path.exists(basedir) and os.path.isdir(basedir) :
            isdir = True
        else:
            isdir = False
        if not isdir:
            path = os.path.join(self.getcwd(),path)
        return path

    def isdir(self, path):
        if type(path) is not str:
            return False
        if os.path.exists(path) and os.path.isdir(path) :
            return True
        else:
            return False

    def filename_normal(self,filename):
        return filename.replace("\\","/")