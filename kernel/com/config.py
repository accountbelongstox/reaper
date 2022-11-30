from kernel.base.base import *
import configparser
import os
import re


class Config(BaseClass):

    def __init__(self,args):
        # super.__init__()
        # self.com = self.get_common()
        # self.mode = self.get_mode()
        pass

    def get_static(self,sub_dir):
        sub_dir = self.config_cfg("static",sub_dir)
        sub_dir = self.abs_dir__(sub_dir)
        return sub_dir

    def get_public(self,dir=None):
        sub_dir = self.config_cfg("static","public_dir")
        if dir != None:
            sub_dir = sub_dir + "/" + dir
        sub_dir = self.abs_dir__(sub_dir)
        return sub_dir

    def get_bin_dir(self,dir=None):
        sub_dir = self.config_cfg("static","bin_dir")
        if dir != None:
            sub_dir = sub_dir + "/" + dir
        sub_dir = self.abs_dir__(sub_dir)
        return sub_dir

    def get_template_dir(self,dir=None):
        sub_dir = self.config_cfg("static","template_dir")
        if dir != None:
            sub_dir = sub_dir + "/" + dir
        sub_dir = self.abs_dir__(sub_dir)
        return sub_dir

    def is_mainserver(self):
        is_main_server = self.config_cfg("global","is_main_server")
        return is_main_server

    def get_webdownload_dir(self):
        sub_dir = self.config_cfg("static","webdownload_dir")
        sub_dir = self.abs_dir__(sub_dir)
        return sub_dir

    def abs_dir__(self,dir):
        cwd = self.getcwd()
        dir = f"{ os.path.join(cwd,dir)}".replace('\\','/')
        if os.path.exists(dir) and os.path.isdir(dir):
            dir = dir+"/"
        return dir

    def get(self,key):
        return self.get_global(key)

    def get_global(self,key):
        return self.config_cfg("global",key)

    def get_config(self,section,key):
        return self.config_cfg(section,key)

    def config_cfg(self,section,key):
        cfg = self.config(type="cfg",section=section,key=key)
        return cfg

    def config_ini(self,section,key):
        cfg = self.config(type="ini",section=section,key=key)
        return cfg

    def get_libs(self,dir=""):
        sub_dir = self.load_module.get_kernel_dir("libs")
        sub_dir = os.path.join(sub_dir,dir)
        sub_dir = self.abs_dir__(sub_dir)
        return sub_dir

    def config(self,type="cfg",section="",key=""):
        cwd = self.getcwd()
        cfg_path = os.path.join(cwd,"config/config.cfg")
        if type=="cfg":
            cfg_parser = configparser.RawConfigParser()
        else: #type=="ini":
            cfg_parser = configparser.ConfigParser()
        cfg_parser.read(cfg_path)
        cfg = cfg_parser[section][key]
        if cfg in ["True","true"]:
            cfg = True
        elif cfg in ["false","False"]:
            cfg = False
        elif re.search(re.compile("^\d+$") , cfg) != None:
            cfg = int(cfg)
        elif re.search( re.compile("^\d+\.\d+$"),cfg ) != None:
            cfg = float(cfg)
        return cfg

    def getcwd(self,):
        return os.path.abspath(__file__).split('kernel')[0]