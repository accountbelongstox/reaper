from kernel.base.base import BaseClass
from kernel.qt.qt_class import QtClass

import importlib,importlib.util
import os
import json
import sys
import threading

class LoadModuleClass(BaseClass):
    __kernel_name = "kernel"
    __common_dir = "common"
    __mode_dir = "mode"
    __control_name = ""
    __args = None
    __load_modes = False

    def init(self):
        try:
            module_name = sys.argv[1]
        except KeyError:
            print(KeyError, f" need parameter;")
            return

        sys.setrecursionlimit(300000)
        control_module_name = "control"
        control = self.init_for_modules(control_module_name, module_name, sys.argv)
        control.main(sys.argv)

    def load_qt(self,args):
        qt = QtClass(args)
        self.create_thread(target=qt.main,args=args)

    def init_for_modules(self,control_module_name,module_name=None,args=()):
        if type(control_module_name) == str:
            control = self.load_class(control_module_name,module_name,args)
        else:
            control = control_module_name
        if control_module_name == "control":
            if self.__control_name == "":
                self.__control_name = module_name
                self.__args = args
            self.add_config(control,module_name)
        # self.load_kernel_common_class(args)
        self.load_kernel_common_class(args)
        self.load_kernel_mode_class(args)
        self.load_qt(args)
        return control

    # 将common类赋值给module
    def add_common_modules(self,module_or_modules):
        self.attach_module(module_or_modules,self.__common_dir)
    # 将mode类赋值给module
    def add_mode_modules(self,module_or_modules):
        self.attach_module(module_or_modules,self.__mode_dir)

    def load_kernel_common_class(self,args=()):
        module_init = len(self.common.keys()) == 0
        #如果是初化加载，则叠加属性。
        if module_init:
            self.load_kernel_class(module_type_name=self.__common_dir,args=args)
            self.add_common_modules(self.common)
    def load_kernel_mode_class(self,args=()):
        # Mode 里的主方法放到单独的线程运行以免阻塞其他线程执行，其中qt_mode是用来执行界面的
        if not self.__load_modes:
            self.__load_modes = True
            self.load_kernel_class(module_type_name=self.__mode_dir,args=args)
            self.add_common_modules(self.mode)
            # #mode类的主方法main会自动执行,并传入args参数
            for name,mode in self.mode.items():
                if "main" in dir(mode):
                    self.create_thread(mode.main,args=args)
    # 由主线程创建
    def create_thread(self,target,args):
        mode_thread = ThreadBase(target=target, args=args)
        mode_thread.start()

    def add_config(self,control,control_module_name):
        config_json = self.get_control_dir(control_module_name,"config.json")
        if self.file_exists(config_json):
            f = open(config_json, f"r+", encoding="utf-8")
            content = f.read()
            f.close()
            config = json.loads(content)
            control.__setattr__("config",config)

    def load_kernel_class(self,module_type_name="common",args=()):
        #如果已经加载过，则类的列表里有类的指针就不需要加载直接返回了
        if len(self.common.keys()) > 0 and module_type_name == self.__common_dir:
            return self.common
        elif len(self.mode.keys()) > 0 and module_type_name == self.__mode_dir:
            return self.mode

        module_path = self.get_module_dir(module_type_name)
        modules = os.listdir(module_path)
        modules = [m for m in modules if not m.startswith("__")]
        for m in modules:
            module_name = m.replace('.py', "")
            module = self.load_class(module_type_name,module_name,args)
            if module_type_name == self.__common_dir:
                self.common[module_name] = module
            elif module_type_name == self.__mode_dir:
                self.mode[module_name] = module

        if module_type_name == self.__common_dir:
            return self.common
        else:
            return self.mode

    #该方法在子线程类中有调用
    def attach_module_from(self,module,module_name):
        module_type = self.get_module_type(module_name)
        if module_type == "common":
            attach_module = self.common[module_name]
        else:
            attach_module = self.mode[module_name]
        is_module_attr = module.__dict__.get(module_name)
        if is_module_attr == None:
            module.__setattr__(module_name, attach_module)
            if "main" in dir(attach_module):
                args = {
                    "args": self.__args,
                    "module": module,
                    "module_name": module_name,
                    "control_name": self.__control_name
                }
                attach_module.main(args)


    def get_module(self,module_name):
        module_type = self.get_module_type(module_name)
        if module_type == "common":
            return self.common[module_name]
        else:
            return self.mode[module_name]

    def get_module_type(self,module_name):
        attach_module_name_parse = module_name.split('_')
        attach_module_name_len = len(attach_module_name_parse)
        module_type = attach_module_name_parse[attach_module_name_len - 1]
        return module_type

    def get_module_dir(self,module):
        curdir = self.getcwd()
        module_dir = os.path.join(curdir, self.__kernel_name, module)
        return module_dir

    def get_kernel_module_name(self,module_type_name,module_name):
        if module_type_name == "control":
            control_module_name = f"{module_type_name}_{module_name}"
            module_name = f"{control_module_name}.main"
        else:
            module_name = f"{self.__kernel_name}.{module_type_name}.{module_name}"
        return module_name

    def get_control_dir(self,module_type_name,filename=None):
        curdir = self.getcwd()
        module_name_parse = module_type_name.split("_")
        module_name = module_name_parse[len(module_name_parse) - 1]
        module_name = "control_"+module_name
        module_dir = os.path.join(curdir, module_name)
        if filename is not None:
            module_dir = os.path.join(module_dir, filename)
        return module_dir

    def attach_all_mode_to(self,control):
        self.attach_module(control,module_type_name="mode")

    def attach_module(self,module_or_modules,module_type_name="common"):
        if type(module_or_modules) != dict:
            module_or_modules = {
                module_or_modules.__class__.__name__: module_or_modules
            }
        if module_type_name == "common":
            kernermodules = self.common
        else:
            kernermodules = self.mode

        for module_name,module in module_or_modules.items():
            for simple_name,attach_module in kernermodules.items():
                attach_module_name = attach_module.__class__.__name__
                is_module_attr = module.__dict__.get(simple_name)
                module_name = module.__class__.__name__
                if is_module_attr == None \
                        and \
                module_name != attach_module_name:
                    module.__setattr__(simple_name,attach_module)
                    if "main" in dir(attach_module):
                        args = {
                            "args": self.__args,
                            "module": module,
                            "module_name": module_name,
                            "control_name":self.__control_name
                        }
                        attach_module.main(args)

    def load_module_fram_file(self,module_name,module_path):
        spec = importlib.util.spec_from_file_location(module_name, module_path)
        return spec

    def load_class(self,module_type_name,module_name, *args, **kwargs):
        module_load_name =  self.get_kernel_module_name( module_type_name, module_name)
        if module_type_name != "control":
            class_name = "".join([n.title() for n in module_name.split('_')])
        else:
            class_name = "Main"
        module_meta = __import__(module_load_name, globals(), locals(), [class_name])
        class_meta = getattr(module_meta, class_name)
        module = class_meta(*args, **kwargs)
        return module

    def getcwd(self):
        return __file__.split('kernel')[0]

    def get_base_dir(self):
        return __file__.split('kernel')[0]

    def file_exists(self, filename):
        if os.path.exists(filename) and os.path.isfile(filename):
            return True
        else:
            return False


class ThreadBase(threading.Thread):
    def __init__(self, target=None,args=(),daemon=False):
        if target == None:
            raise "load_module ThreadBase target conn't None."
        thread_name = target.__class__.__name__
        threading.Thread.__init__(self,name=thread_name,daemon=daemon)
        self.target = target
        self.args = args

    def run(self):
        self.target(self.args)
