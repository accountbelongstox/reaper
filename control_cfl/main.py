from kernel.base.base import *

class Main(BaseClass):
    def __init__(self, argv):
        pass

    def main(self, argv):
        self.translate_common.py("")
        #需要测试的代码
        result = self.translate_common.translate_from_google_cn("测试","en","zh-CN")
        print(result)
