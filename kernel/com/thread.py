import string
from queue import Queue
from kernel.base.base import *
import time
import threading
import random

thread_lock = threading.Lock()
global_thread = {}


class Thread(BaseClass):
    __threads = None
    __thread_name_max = 32

    def __init__(self, args):
        global global_thread
        self.__threads = global_thread
        pass

    def create_thread(self, thread_type, args=None, thread_name=None, daemon=False, run=False, target=None, wait=False):
        # """
        # a thread must be translated into some task as Queue
        # and output a resultQueue by thread-self
        # """
        if args == None:
            args = {}
        if thread_name is None:
            thread_name = self.get_thread_name()
        if thread_name in self.__threads:
            print(f"the ThreadCommon existed with name {thread_name}.")
            return self.__threads[thread_name]
        self.set_threads(thread_name, "thread_type", thread_type)
        self.set_threads(thread_name, "thread_name", thread_name)

        module_name = f'{thread_type}Thread'
        thread = self.load_module.load_module('thread', module_name)
        args = self.args_setqueueandlock(args, thread_name)
        parameter = self.com_util.get_parameter(thread, info=False)
        if "target" in parameter:
            thread = thread(args=args, target=target, thread_name=thread_name, daemon=daemon)
        else:
            thread = thread(args=args, thread_name=thread_name, daemon=daemon)

        self.load_module.attach_module(thread)
        self.com_selenium.bind(thread)
        print(f"new thread : \n\tthread_type : {thread_type}\n\tthread_name : {thread_name}\n")

        self.set_threads(thread_name, "thread", thread)

        if run:
            return thread.start()
        return thread

    def create_thread_pool(self, thread_type, args=None, max_thread=30, tasks_per_thread=50, wait=False, info=True,
                           target=None, callback=None):
        thread_pool_name = self.get_thread_name()
        if args == None:
            args = {}
        if type(args) == Queue:
            task = args
            args = {
                "task": task,
            }
        else:
            max_thread = self.get_args(args, "max_thread", default=max_thread)
            wait = self.get_args(args, "wait", default=wait)
            info = self.get_args(args, "info", default=info)
            callback = self.get_args(args, "callback", default=callback)
            tasks_per_thread = self.get_args(args, "tasks_per_thread", default=tasks_per_thread)

            task = args.get('task')
            if task == None:
                self.com_util.print_warn(f"thread_pool not transition a task Queue: {task}")
                return None
        task_qsize = task.qsize()
        thread_num = int(task_qsize / tasks_per_thread)  # 每线程处理敘数
        if thread_num < 1:
            thread_num = 1
        thread_list = []
        # 如果已经有存在的线程,则不用添加新线程
        thread_count = self.thread_type_count(thread_type)
        need_threads = thread_num - thread_count
        if need_threads > max_thread:
            need_threads = max_thread
        if need_threads > 0:
            message = f"""threadPool start with {need_threads} thread\n""" + \
                      f"""\ttype : {thread_type}\n""" + \
                      f"""\tname : {thread_pool_name}\n""" + \
                      f"""\talready_threads : {thread_count}\n""" + \
                      f"""\tstart_thread : {need_threads}\n""" + \
                      f"""\twait : {wait}\n""" + \
                      f"""\tcallback : {callback}\n""" + \
                      f"""\tinformation : total queue {task_qsize} to be, start {need_threads} thread\n""" + \
                      f"""\targs : {args}\n""" + \
                      f"""\ttask_qsize : {task_qsize}\n"""
            print(message)
            for thread_id in range(need_threads):
                th = self.create_thread(
                    thread_type=thread_type,
                    args=args,
                    target=target,
                )
                thread_list.append(th)
                th.start()
        else:
            self.restart_threads(thread_type, thread_num)

        if wait:
            result_queue = self.join(thread_type, info=info)
            return result_queue

    def restart_threads(self, thread_type, thread_num):
        threads = self.get_thread_from_type(thread_type)
        index = 0
        for th in threads:
            if index == thread_num:
                print(f"The startup thread is enough")
                break
            # 代表当前线程的任务还未完成.
            if th.is_alive() == False:
                th.run()
            index += 1

    def args_setqueueandlock(self, args, thread_ident):
        task = "task"
        if task not in args:
            args[task] = self.get_thread_queue(thread_ident, task)
        result = "result"
        if result not in args:
            args[result] = self.get_thread_queue(thread_ident, result)
        threadlockname = "thread_lock"
        if threadlockname not in args:
            args[threadlockname] = thread_lock
        return args

    def set_args(self, args, key, value):
        if key not in args:
            args[key] = value
        return args

    def get_args(self, args, key, default=None):
        if key in args:
            return args[key]
        return default

    def set_threads(self, thread_name, key, value, safe=False):
        if thread_name not in self.__threads:
            self.__threads[thread_name] = {}
        if safe == True and key in self.__threads[thread_name]:
            return True
        self.__threads[thread_name][key] = value
        return self.__threads[thread_name][key]

    def thread_done(self, thread_type):
        threads = self.get_thread_from_type(thread_type)
        for thread in threads:
            if thread.done() == False:
                return False
        return True

    def update_queue(self, thread_queue, update_list):
        if update_list == None:
            return thread_queue
        elif type(update_list) == str:
            update_list = [update_list]
        elif type(update_list) != list:
            return thread_queue
        elif len(update_list) == 0:
            return thread_queue
        queue_list = []
        thread_lock.acquire()
        while thread_queue.qsize() > 0:
            queue_list.append(thread_queue.get())
        for item in update_list:
            if item not in queue_list:
                queue_list.append(item)
        for item in queue_list:
            thread_queue.put(item)
        thread_lock.release()
        return thread_queue

    def join(self, thread_type, info=True):
        index = 1
        wait_interval = 2
        while (self.thread_done(thread_type)) != True:
            time.sleep(wait_interval)
            if info: print(f"Waiting for the thread group to download, it takes {index * wait_interval} seconds.")
            index += 1
        result_queue = self.thread_result(thread_type)
        return result_queue

    def thread_result(self, thread_type):
        threads = self.get_thread_from_type(thread_type)
        result_list = []
        for thread in threads:
            thread_result = thread.result()
            result_list += thread_result
        return result_list

    def remove_thread(self, thread_name):
        self.__threads[thread_name] = None
        del self.__threads[thread_name]
        return True

    def get_thread_name(self):
        thread_name = self.gen_thread_name()
        return thread_name

    def gen_thread_name(self):
        # 生成线程名128个字符
        max = self.__thread_name_max
        m = random.randint(1, max)
        a = "".join([str(random.randint(0, 9)) for _ in range(m)])
        b = "".join([random.choice(string.ascii_letters) for _ in range(max - m)])
        thread_name = ''.join(random.sample(list(a + b), max))

        if thread_name in self.__threads:
            return self.gen_thread_name()
        else:
            return thread_name

    def get_thread(self, thread_ident):
        if thread_ident in self.__threads:
            return self.__threads[thread_ident]["thread"]
        else:
            print(f"Not Found thread: {thread_ident} in selenium_multi_process_mode.")
            return None

    def get_thread_queue(self, thread_ident, queue_type):
        q = self.set_threads(thread_ident, queue_type, Queue(), safe=True)
        return q

    def get_thread_from_type(self, thread_type):
        threads = self.__threads.items()
        thread_list = []
        for thread_name, thread_item in threads:
            if thread_type == thread_item["thread_type"]:
                # thread = thread_item["thread"]
                thread_list.append(thread_item["thread"])
        return thread_list

    def thread_type_count(self, thread_type):
        threads = self.get_thread_from_type(thread_type)
        thread_len = len(threads)
        return thread_len

    def getDaemon(self, thread_ident):
        th = self.get_thread(thread_ident)
        daemon = th.getDaemon()
        return daemon

    def setDaemon(self, thread_ident, daemon):
        th = self.get_thread(thread_ident)
        th.setDaemon(daemon)

    def is_alive(self, thread_ident):
        th = self.get_thread(thread_ident)
        r = th.is_alive()
        return r

    def restart(self, thread_ident):
        if type(thread_ident) == str:
            thread = self.get_thread(thread_ident)
        else:
            thread = thread_ident
        if thread.is_alive() == False:
            thread.run()
        return thread

    def run(self, thread_ident):
        th = self.get_thread(thread_ident)
        return th.run()

    def send(self, thread_ident, data):
        th = self.get_thread(thread_ident)
        th.send(data)

    def set(self, thread_ident, name, data):
        th = self.get_thread(thread_ident)
        th.set(name, data)
