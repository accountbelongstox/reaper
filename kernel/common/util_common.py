from kernel.base.base import *
#import xml.etree.ElementTree as etree
class UtilCommon(BaseClass):

    def __init__(self,args):
        pass

    #将一个结果添加到list，如果没有key则创建
    def add_to_dict(self, result,key,value):
        if key not in result:
            result[key]=[]
        if value not in result[key]:
            result[key].append(value)
        return result[key]
    #将数组中的二维数组提取出来
    def extract_list(self,result):
        while len(result) == 1 and type(result[0]) is list:
            result = result[0]
        is_two_dimensional_list = None
        for item in result:
            if type(item) is list:
                is_two_dimensional_list = True
            else:
                is_two_dimensional_list = False
                break
        if is_two_dimensional_list:
            extract_list = []
            for item in result:
                extract_list.append(item[0])
            result = extract_list
        return result

    #通过一个字符串分割数组
    def split_list(self,result,split_symbol=[None,False,True],start=0):
        if type(split_symbol) is not list:
            split_symbol = [split_symbol]
        split_list = []
        index = 0
        step = 0
        for i in range(len(result)):
            item = result[i]
            if item in split_symbol:
                if i == 0:
                    split_list.append([])
                elif i - index > 1:
                    step += 1
                    split_list.append([])
                index = i
            else:
                if i == 0:
                    split_list.append([])
                if type(item) is not list:
                    split_list[step].append(item)
                else:
                    item = self.extract_list(item)
                    for strip in item:
                        split_list[step].append(strip)
        return split_list
