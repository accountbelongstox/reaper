import threading
from datetime import timedelta
from kernel.base.base import *
import re
from flask import Flask as FlaskApp, url_for,request as flask_request, render_template
import mimerender
from flask_cors import CORS
# from  geventwebsocket.websocket import WebSocket,WebSocketError
# from  geventwebsocket.handler import WebSocketHandler
# from  gevent.pywsgi import WSGIServer
# import json
mimerender = mimerender.FlaskMimeRender()
import logging
from gevent import pywsgi
# from livereload import Server
user_socket_dict = {}

class FlaskThread(threading.Thread, BaseClass):
    """
    # 需要执行的函数需要有flask参数修饰,否则无法执行.
    # flask 的根目录在 control_xxx的目录,静态文件默认为 control_xxx/static
    # 参考文档: https://cloud.tencent.com/developer/article/2111798
    # 参考文档: http://docs.jinkan.org/docs/flask/
    # 参考文档: https://flask.palletsprojects.com/en/2.2.x/api/
    """
    _app = None
    _app_run = False
    __module = None
    __execute_function_key = None #验证是否可以执行函数
    __flask = None
    __static_folder = None
    __template_folder = None

    def __init__(self, args, target=None, thread_name=None, daemon=False):
        threading.Thread.__init__(self, name=thread_name, daemon=daemon)
        self.task = args.get('task')
        self.__module = args.get('module')
        self.target = target
        self.args = args
        self.thread_name = thread_name
        self.resultQueue = []
        self.is_alive = True

    def run(self):  # 把要执行的代码写到run函数里面 线程在创建后会直接运行run函数
        self.bind(self.__module,run=False)
        self.flask_run()
        pass

    def flask_run(self):
        if self._app_run == True:
            print(f"flask is already running.")
            return
        network_th = self.com_thread.create_thread(thread_type="com",target=self.flask_init)
        network_th.start()

    def bind(self,module,run=True):
        self.__module = module
        main_name = str(module).strip("<")
        split_text = re.compile(r"\s+")
        main_name = re.split(split_text,main_name)[0]
        main_name_split = main_name.split(".")[0:-1]
        main_name = ".".join(main_name_split)
        # Flask设置项
        # Flask(import_name,
        # static_url_path=None,
        # static_folder='static',
        # static_host=None,
        # host_matching=False,
        # subdomain_matching=False,
        # template_folder='templates',
        # instance_path=None,
        # instance_relative_config=False,
        # root_path=None)
        static_folder = self.com_config.get_global("flask_static_folder")
        self.__static_folder = static_folder
        template_folder = self.com_config.get_global("flask_template_folder")
        self.__template_folder = template_folder
        self._app = FlaskApp(main_name,static_folder=static_folder,template_folder=template_folder)

        # 禁用Flask 缓存
        self._app.config['SEND_FILE_MAX_AGE_DEFAULT'] = timedelta(seconds=1)
        self._app.config['PERMANENT_SESSION_LIFETIME'] = timedelta(seconds=1)
        self._app.send_file_max_age_default = timedelta(seconds=1)
        self._app.permanent_session_lifetime = timedelta(seconds=1)
        # self._app.config['DEBUG'] = True


        CORS(self._app)
        self.close_log()
        if run:
            self.flask_run()
            self._app_run = True

        @self._app.route('/<path:path>', methods=['GET', 'POST','PROPFIND','MKCOL'])
        def flask_route(path):
            route_url = path.split('/')[0]
            remote_addr = flask_request.remote_addr
            if route_url == "api":
                method_name = flask_request.args.get("method")
                self.set_flask_parameter("path",path)
                # 如果允许执行函数,则执行control类里边的方法
                if method_name == None:
                    return self.com_util.print_warn("method parameter is missing")

                execute_function_key = flask_request.args.get("key")
                if execute_function_key == None:
                    return self.com_util.print_warn("The function cannot be executed, a key is required.")

                allow_execute_function = self.compare_execution_function_keys(execute_function_key)
                if allow_execute_function == False:
                    return self.com_util.print_warn("The execute method permission is incorrect.")

                module = flask_request.args.get("module")
                self.com_util.print_info(f"address {remote_addr} visit api for method:{method_name} of module:{module}.")

                if module == "control" or not module:
                    main_module = self.__module
                else:
                    main_module = self.__dict__.get(module)

                method = self.get(main_module,method_name,remind=True)
                if method == None:
                    return self.com_util.print_result(f"method {method_name} does not exist")
                # 对于没有修饰flask参数的方法将无法执行
                parameter_names = self.com_util.get_parameter(method,info=False)
                if ("flask" in parameter_names):
                    return method(flask=self.__flask)
                else:
                    function_not_parameter_modified_not_executed = f"The function {method_name} cannot be executed without being modified by the flask parameter."
                    return self.com_util.print_warn(function_not_parameter_modified_not_executed)
                # try:
                #
                # except Exception as e:
                #     return self.warn(str(e))
            else:
                suffix = route_url.split(".")[-1]
                if suffix in ["html","htm"]:
                    route_html = self.get_template_dir(route_url)
                    if self.com_file.isfile(route_html):
                        return render_template(route_url)
                return route_url
        @self._app.route('/')
        def index():
            remote_addr = flask_request.remote_addr
            self.com_util.print_info(f"address {remote_addr} visit to /.")
            return render_template("index.html") #manager_data={}

        # @self._app.route('/ws/<username>')
        # def ws(username):
        #     global user_socket_dict
        #     user_socket = request.environ.get("wsgi.websocket")
        #     if not user_socket:
        #         return "请以WEBSOCKET方式连接"
        #
        #     user_socket_dict[username] = user_socket
        #     print(user_socket_dict)
        #
        #     while True:
        #         try:
        #             user_msg = user_socket.receive()
        #             for user_name, u_socket in user_socket_dict.items():
        #
        #                 who_send_msg = {
        #                     "send_user": username,
        #                     "send_msg": user_msg
        #                 }
        #
        #                 if user_socket == u_socket:
        #                     continue
        #                 u_socket.send(json.dumps(who_send_msg))
        #
        #         except WebSocketError as e:
        #             user_socket_dict.pop(username)
        #             print(user_socket_dict)
        #             print(e)

    def initialization(self):
        if self.__initialization == True:
            return
        self.__flask = FlaskContainer()
        self.__flask.__setattr__("url_for", url_for)
        self.__flask.__setattr__("render_template", render_template)
        self.__flask.__setattr__("flask_request", flask_request)
        self.__flask.__setattr__("request", flask_request)
        self.__flask.__setattr__("mimerender", mimerender)
        self.__flask.__setattr__("self", self)
        self.__execute_function_key = self.com_config.get_global('execute_function_key')
        # 初始化完毕
        self.__initialization = True

    def close_log(self):
        log = logging.getLogger('werkzeug')
        log.setLevel(logging.ERROR)
    #
    # def info(self,msg):
    #     return self.message(msg,0)
    # def data(self,data):
    #     return self.result(data)
    #
    # def result(self,data):
    #     if data:
    #         message = self.message("Data acquisition succeeded.",0)
    #         if type(data) != list:
    #             data = [data]
    #         length = len(data)
    #     else:
    #         message = self.message("Data acquisition failed.",-1)
    #         length = 0
    #     message["length"] = length
    #     message["data"] = data
    #     return message
    #
    #
    # def message(self,msg,code=0):
    #     message = {
    #         "message":msg,
    #         "code":code
    #     }
    #     return message
    #
    # def warn(self,msg):
    #     return self.message(msg,-1)

    def get_template_dir(self,filename=None):
        control_dir = self.load_module.get_control_dir()
        if filename == None:
            filename = ""
        template_folder = os.path.join(control_dir,self.__template_folder)
        filename = os.path.join(template_folder, filename)
        return filename

    def set_flask_parameter(self,key,value):
        self.__flask.__setattr__(key, url_for)

    def flask_init(self,args=None):
        self.initialization()
        port = self.com_config.get_global('flask_port')
        self.com_util.print_info(f'Flask-successfully:\nstartup Flask app server. Listing port is {port}')
        # server  = Server(self._app.wsgi_app)
        # server.watch('0.0.0.0')
        # server.serve()
        # # server.watch('**/*.*')
        # # server.serve()
        # #
        self.com_util.get_parameter(self._app.run)
        print(f'\n')
        # self._app.run(port=port, host="0.0.0.0")
        server = pywsgi.WSGIServer(('0.0.0.0', port), self._app)
        server.serve_forever()

    def get(self, module, key, remind=False):
        if key in dir(module):
            tool = getattr(module,key)
            return tool
        else:
            if remind:
                self.com_util.print_warn(f"class does not have this method")
            return None

    def compare_execution_function_keys(self,execute_function_key):
        if execute_function_key == self.__execute_function_key:
            return True
        else:
            return False

    def set(self, name, data):
        self.__dict__[name] = data

    def setargs(self, args):
        self.args = args

    def done(self):
        if self.is_alive == False:
            return True
        return False

    def result(self):
        while self.done() == False:
            self.com_util.print_warn(f"waiting for ComThread return.")
        resultQueue = self.resultQueue
        self.resultQueue = []
        return resultQueue


class FlaskContainer:
    pass