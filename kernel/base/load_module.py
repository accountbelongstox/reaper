# from queue import Queue
from kernel.base.base import BaseClass

import importlib,importlib.util
import os
import json
import sys
import threading
# import traceback
import platform

class LoadModule(BaseClass):
    __kernel_name = "kernel"
    __com_dir = "com"
    __mode_dir = "mode"
    __control_name = ""
    __control_module = None
    __args = None
    __window_x = -20
    __window_y = -20
    com_global = {}
    mode_global = {}

    def init(self):
        argv = sys.argv
        self.argv = argv
        self.args = argv
        try:
            module_name = argv[1]
        except KeyError:
            print(KeyError, f"NoKey: need parameter;")
            module_name = "okx"
        sys.setrecursionlimit(300000)
        control_module_name = "control"
        # 首先是加载核心组件
        self.load_kernel_class()
        self.inter_attach_module()
        self.__control_name = module_name
        control = self.load_control_class(control_module_name, module_name, argv)
        self.__control_module = control
        self.execute_com_main()
        self.prerun_mode_class()
        # 加载qt UI模块
        self.load_qt(argv)
        # 数据库初始化
        self.db_initial_from_config(control)
        control.main(argv)


    def load_qt(self,args):
        if self.is_windows():
            from kernel.qt.qt_class import QtClass
            qt = QtClass(args)
            self.attach_module(qt)
            self.create_thread(target=qt.main,argv=args)

    def load_control_class(self,control_module_name,module_name=None,args=()):
        control = self.load_class(control_module_name,module_name,args)
        self.add_config(control)
        self.attach_module(control)
        return control

    def execute_com_main(self):
        # Mode 里的主方法放到单独的线程运行以免阻塞其他线程执行，其中qt_mode是用来执行界面的
        modes = self.com_global
        self.execute_main(modes,thread_execute=False)

    def prerun_mode_class(self):
        # Mode 里的主方法放到单独的线程运行以免阻塞其他线程执行，其中qt_mode是用来执行界面的
        modes = self.mode_global
        self.execute_main(modes,thread_execute=True)

    def set_args(self,key=None,value=None):
        args = {
            "file":self.argv[0],
            "control_name":self.args[1],
            "control_module": self.control_module
        }
        if key != None:
            args[key] = value
        return args


    def execute_main(self,modules,thread_execute=False):
        args = self.set_args()
        for name,mode in modules.items():
            if "main" in dir(mode):
                if thread_execute:
                    self.create_thread(mode.main,argv=args)
                else:
                    mode.main(args=args)

    # 由主线程创建
    def create_thread(self,target,argv):
        mode_thread = ThreadBase(target=target, argv=argv)
        mode_thread.start()

    def add_config(self,control):
        config_json = self.get_control_dir("config.json")
        if self.file_exists(config_json):
            f = open(config_json, f"r+", encoding="utf-8")
            content = f.read()
            f.close()
            config = json.loads(content)
            control.__setattr__("config",config)
            return config
        return None

    def db_initial_from_config(self,control):
        config = control.config
        if type(config) != dict:
            return False
        databases = config.get('database')
        if databases == None:
            return False
        databases = config.get('database')
        if type(databases) != list:
            databases = [databases]
        for database in databases:
            tabname = database.get('tabname')
            fields = database.get('fields')
            # com_db = self.get_com('db')
            control.com_db.create_table_and_extend(tabname,fields)

    def load_kernel_class(self):
        kernel_module_group = [self.__com_dir,self.__mode_dir]
        for kernel_module_name in kernel_module_group:
            module_path = self.get_module_dir(kernel_module_name)
            modules = os.listdir(module_path)
            modules = [m for m in modules if not m.startswith("__")]
            for m in modules:
                module_name = m.replace('.py', "")
                module = self.load_class(kernel_module_name,module_name,self.args)
                if kernel_module_name == self.__com_dir:
                    self.set_com(module_name,module)
                elif kernel_module_name == self.__mode_dir:
                    self.set_mode(module_name,module)
    def set_property(self,module,property):
        default_name = "com"
        property_name = property.__class__.__name__.lower()
        self.attach_module_com(property)
        property_name = f"{default_name}_{property_name}"
        module.__setattr__(property_name,property)
        return module
    def set_com(self,name,module):
        self.com_global[name] = module
    def get_com(self,name):
        return self.com_global.get(name)
    def set_mode(self,name,module):
        self.mode_global[name] = module

    def get_module_dir(self,module):
        curdir = self.getcwd()
        module_dir = os.path.join(curdir, self.__kernel_name, module)
        return module_dir
    def get_kernel_dir(self,dir):
        curdir = self.getcwd()
        module_dir = os.path.join(curdir, self.__kernel_name, dir)
        return module_dir
    def get_kernel_module_name(self,module_type_name,module_name):
        if module_type_name == "control":
            control_module_name = f"{module_type_name}_{module_name}"
            module_name = f"{control_module_name}.main"
        else:
            module_name = f"{self.__kernel_name}.{module_type_name}.{module_name}"
        return module_name

    def get_control_name(self):
        return self.__control_name

    def get_control_dir(self,filename=None,suffix=None):
        curdir = self.getcwd()
        module_name = f"control_{self.__control_name}"
        module_dir = os.path.join(curdir, module_name)
        if filename is not None:
            module_dir = os.path.join(module_dir, filename)
        if suffix is not None:
            module_dir = os.path.join(module_dir, suffix)
        return module_dir

    def get_control(self):
        control = self.__control_module
        return control

    def get_control_config(self):
        control = self.__control_module
        config = control.config
        return config

    def get_control_core_dir(self,suffix=None):
        core_file = self.get_control_dir(suffix="core_file")
        if os.path.exists(core_file) != True:
            os.mkdir(core_file)
        if suffix is not None:
            core_file = os.path.join(core_file, suffix)
        return core_file
    def attach_module(self,origin_module):
        origin_module.__setattr__("load_module",self)
        com = self.com_global
        self.attach_module_to(origin_module = origin_module, components = com, parameter_name = self.__com_dir)
        # mode = self.get_mode()
        # self.attach_module_to(origin_module = origin_module, components = mode, parameter_name = self.__mode_dir)

    def attach_module_com(self,origin_module):
        if "load_module" not in dir(origin_module):
            origin_module.__setattr__("load_module",self)
        com = self.com_global
        self.attach_module_to(origin_module = origin_module, components = com, parameter_name = self.__com_dir)
    def attach_module_mode(self,origin_module):
        if "load_module" not in dir(origin_module):
            origin_module.__setattr__("load_module",self)
        mode = self.mode_global
        self.attach_module_to(origin_module = origin_module, components = mode, parameter_name = self.__mode_dir)
    def attach_module_to(self,origin_module,components,parameter_name):
        if parameter_name in dir(origin_module):
            return
        origin_module_name = origin_module.__class__.__name__
        # component = Component()
        for component_name,component_module in components.items():
            component_module_name = component_module.__class__.__name__
            if component_module_name != origin_module_name:
                # component.__setattr__(component_name,component_module)
                set_parameter_name = f"{parameter_name}_{component_name}"
                # 形式com_xxxx的属性
                origin_module.__setattr__(set_parameter_name,component_module)
        # origin_module.__setattr__(parameter_name, component)

    def inter_attach_module(self):
        origin_common = self.com_global.items()
        for origin_name,origin_module in origin_common:
            self.attach_module_com(origin_module)
        origin_mode = self.mode_global.items()
        for origin_name,origin_module in origin_mode:
            self.attach_module_com(origin_module)

    def load_module_fram_file(self,module_name,module_path):
        spec = importlib.util.spec_from_file_location(module_name, module_path)
        return spec

    def load_class(self,module_type_name,module_name, *args, **kwargs):
        module_load_name =  self.get_kernel_module_name( module_type_name, module_name)
        if module_type_name == "control":
            class_name = "Main"
        else:
            class_name = module_name.title()
            # 形式为 kernel.com_main
        module_meta = __import__(module_load_name, globals(), locals(), [class_name])
        class_meta = getattr(module_meta, class_name)
        module = class_meta(*args, **kwargs)
        return module
    def load_module(self,module_type_name,module_name, *args, **kwargs):
        module_load_name =  self.get_kernel_module_name( module_type_name, module_name)
        if module_type_name == "control":
            class_name = "Main"
        else:
            class_name = module_name[0].upper() + module_name[1:]
            # 形式为 kernel.com_main
        module_meta = __import__(module_load_name, globals(), locals(), [class_name])
        class_meta = getattr(module_meta, class_name)
        # module = class_meta(*args, **kwargs)
        return class_meta

    def get_window_position(self,addnum=0):
        self.__window_x += addnum
        self.__window_y += addnum
        window_position = {
            "x": self.__window_x,
            "y": self.__window_y,
        }
        return window_position
    def get_base_dir(self):
        return __file__.split('kernel')[0]

    def file_exists(self, filename):
        if os.path.exists(filename) and os.path.isfile(filename):
            return True
        else:
            return False

    def is_windows(self):
        sysstr = platform.system()
        windows = "windows"
        if (sysstr.lower() == windows):
            return True
        else:
            return False

class ThreadBase(threading.Thread):
    def __init__(self, target=None,argv=(),daemon=False):
        if target == None:
            raise "load_module ThreadBase target conn't None."
        thread_name = target.__class__.__name__
        threading.Thread.__init__(self,name=thread_name,daemon=daemon)
        self.target = target
        self.argv = argv

    def run(self):
        self.target(self.argv)

class Component():
    def __setattr__(self, key, value):
        self.__dict__[key] = value