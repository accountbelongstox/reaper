import os

class BaseClass:
    def __setattr__(self, key, value):
        #print("__setattr__")
        self.__dict__[key] = value
    def __set__(self, instance, value):
        #print("__set__")
        self.__dict__[instance] = value

    def __get__(self, item):
        # print("取得方法")
        return self.__dict__.get(item)

    def __getattr__(self, item):
        # print("取得方法")
        return self.__dict__.get(item)

    def getcwd(self,file=None,suffix=None):
        if file is None:
            cwd = __file__.split('kernel')[0]
        else:
            cwd = os.path.dirname(file)

        if suffix != None:
            cwd = os.path.join(cwd,suffix)
        return cwd
