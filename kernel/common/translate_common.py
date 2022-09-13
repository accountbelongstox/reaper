# from queue import Queue
# import operator
# import shutil
import ssl
from http.client import HTTPSConnection
from urllib.parse import urlparse
import time

import math


from kernel.base.base import *
import os
import re
import json
import requests
import pprint
from urllib import request,parse

import googletrans
from googletrans import Translator



# import time
# import lxml.html
# from lxml import etree
# from lxml.cssselect import CSSSelector
# import random
# import pprint
googletanslator = Translator(service_urls=[
      'translate.google.cn',
    ])

class TranslateCommon(BaseClass):
    __threads = {}

    MDX = None # 用来解析mdx文件的字段


    def __init__(self, args):
        pass

    def document_to_words(self,doc):
        splits_symbol = re.compile(r'[^\w]+')
        doc_words = re.split(splits_symbol,doc)
        contentAll = " ".join(doc_words)

        theBoardBeforeIsLowLetter = re.compile(r"(?<=\d)\B(?=\D)")
        theBoardBeforeIsUpLetter = re.compile(r"(?<=\D)\B(?=\d)")
        theBoardBeforeIsAcronym = re.compile(r"(?<=[A-Z])\B(?=[A-Z]{1}[a-z]{1})")
        theBoardBeforeIsWord = re.compile(r"(?<=[a-z])\B(?=[A-Z])")

        theBoardBeforeIsEnglish = re.compile(r"(?<=[a-zA-Z])\B(?=([\u4e00-\u9fa5]|[\ufe30-\uffa0]|[\u4e00-\uffa5]))")
        theBoardBeforeIsChnese = re.compile(r"(?<=([\u4e00-\u9fa5]|[\ufe30-\uffa0]|[\u4e00-\uffa5]))\B(?=[a-zA-Z])")

        theBoardSplitWord = re.compile(r"\b")

        contentAll = re.split(theBoardBeforeIsLowLetter,contentAll)
        contentAll = " ".join(contentAll)
        contentAll = re.split(theBoardBeforeIsUpLetter,contentAll)
        contentAll = " ".join(contentAll)
        contentAll = re.split(theBoardBeforeIsAcronym,contentAll)
        contentAll = " ".join(contentAll)
        contentAll = re.split(theBoardBeforeIsWord,contentAll)
        contentAll = " ".join(contentAll)
        contentAll = re.split(theBoardBeforeIsEnglish,contentAll)
        contentAll = " ".join(contentAll)
        contentAll = re.split(theBoardBeforeIsChnese,contentAll)
        contentAll = " ".join(contentAll)
        contentAll = contentAll.split("_")
        contentAll = " ".join(contentAll)
        contentAll = re.split(theBoardSplitWord,contentAll)

        contentAll = set(contentAll)
        words = {}
        words["en"] = []
        words["zh-cn"] = []
        words["bad"] = []
        for word in contentAll:
            if self.is_english(word):
                words["en"].append(word)
            elif self.is_chinese(word):
                words["zh-cn"].append(word)
            else:
                words["bad"].append(word)
        return words


    def is_true_word(self,word):
        isShortAlpha = re.compile(r'^\w$')
        # print(f"re.search(isShortAlpha,{word}) {re.search(isShortAlpha,word)}")
        if re.search(isShortAlpha,word) != None and len(word) > 1:
            return True
        isNumber = re.compile(r'^\d+$')
        if re.search(isNumber,word) != None:
            return False
        isLowLetterAndUpper = re.compile(r"^[a-z]{1}[A-Z]{1}$")
        if re.search(isLowLetterAndUpper,word) != None:
            return False
        isEmptyChar = ""
        if word == isEmptyChar:
            return False
        return True

    def is_chinese(self,word):
        pattern = re.compile(r"^([\u4e00-\u9fa5]|[\ufe30-\uffa0]|[\u4e00-\uffa5])+")
        if re.search(pattern,word) != None:
            return True
        return False

    def is_english(self,word):
        pattern = re.compile(r"^[a-z]+",re.I)
        if re.search(pattern,word) != None and len(word) > 1:
            return True
        return False

    def language(self):
        language = googletrans.LANGUAGES
        print(language)
        return language

    def translate_to_html(self, word,from_is="en",to="zh-cn",engine="google_cn",callback=None):
        result = self.translate(word,from_is=from_is,to=to,engine=engine,callback=callback)
        return result


    def translate(self, word,from_is="en",to="zh-cn",engine="google_cn",callback=None):
        is_file = self.file_common.isfile(word)
        if is_file:
            word = self.file_common.open(word)
        if type(word) is list:
            words = word
        else:
            if type(word) is not str:
                word = self.string_common.byte_to_str(word)
            words = self.document_to_words(word)
        if from_is in words:
            words = words[from_is]

        per_thread_solve_word_num = 30
        words_len = len(words)
        words_split = words_len/per_thread_solve_word_num
        max_thread = math.ceil(words_split)
        #最大调用线程数
        if max_thread > 60:
            max_thread = 60

        threads = []
        index = 0
        for i in range(max_thread):
            start_point = i * per_thread_solve_word_num
            end_point = i * per_thread_solve_word_num + per_thread_solve_word_num
            split_words = words[start_point:end_point]
            word_list = []
            for word in split_words:
                word_list.append(
                    {
                        "word":word,
                        "from_is" : from_is,
                        "to" : to,
                        "engine" : engine,
                        "index" : index,
                        "callback" : callback
                    }
                )
                index += 1
            th = self.thread_common.create_thread("translate",args=word_list)
            th.start()
            threads.append(th)
        result = []
        for th in threads:
            result_of_th = th.result()
            while result_of_th.qsize() > 0:
                result.append(result_of_th.get())
        result.sort(key = lambda item : item["index"])
        if callback is not None:
            return callback(result)
        else:
            return result

    def translate_from_google(self,word,dest="en",src="zh-CN",):
        out = googletanslator.translate(word,dest,src)

        result = {
            "text": out.text,
            "src": out.src,
            "dest": out.dest,
            "pronunciation": out.pronunciation,
        }
        return result


    def translate_from_mdx(self,word,from_is=None,to=None):
        if self.MDX is not None:
            from readmdict import MDX, MDD
            from pyquery import PyQuery as pq
            self.MDX = MDX
            self.MDD = MDD
            self.pyquery = pyquery
        '''
        # 如果是windows环境，运行提示安装python-lzo，但
        > pip install python-lzo
        报错“please set LZO_DIR to where the lzo source lives” ，则直接从 https://www.lfd.uci.edu/~gohlke/pythonlibs/#_python-lzo 下载 "python_lzo‑1.12‑你的python版本.whl" 
        > pip install xxx.whl 
        装上就行了，免去编译的麻烦
        '''
        mdx_file = "mdx/oxford.mdx"
        # 加载mdx文件
        mdx_dir = self.config_common.get_public(mdx_file)
        filename = mdx_dir
        headwords = [*self.MDX(filename)]  # 单词名列表
        items = [*self.MDX(filename).items()]  # 释义html源码列表
        if len(headwords) == len(items):
            print(f'加载成功：共{len(headwords)}条')
        else:
            print(f'【ERROR】加载失败{len(headwords)}，{len(items)}')

        # 查词，返回单词和html文件
        wordIndex = headwords.index(word.encode())
        query_word, html = items[wordIndex]
        query_word, html = query_word.decode(), html.decode()
        # print(word, html)

        # 从html中提取需要的部分，这里以the litte dict字典为例。到这一步需要根据自己查询的字典html格式，自行调整了。
        doc = self.pyquery(html)
        self.file_common.save(doc)
        coca2 = doc('div[class="coca2"]').text().replace('\n', '')
        print(coca2)
        meaning = doc("""div[class="dcb"]""").text()




    def translate_from_baidu(self,content):
        """
        作废的翻译连接
        :param content:
        :return:
        """
        url = "http://fanyi.baidu.com/sug"
        data = parse.urlencode({"kw": content})  # 将参数进行转码
        headers = {
            'User-Agent': 'Opera/9.80 (Android 2.3.4; Linux; Opera Mobi/build-1107180945; U; en-GB) Presto/2.8.149 Version/11.10'
        }
        req = request.Request(url, data=bytes(data, encoding="utf-8"), headers=headers)
        r = request.urlopen(req)
        # print(r.code) 查看返回的状态码
        html = r.read().decode('utf-8')
        # json格式化
        html = json.loads(html)
        print(html)
        for k in html["data"]:
            print(k["k"], k["v"])
        return html["data"]

    def translate_from_google_cn(self,word,from_is="en",to="zh-cn",callback=None):
        # 返回形式
        # auxiliary verb 助动词
        # prefix 前缀
        # pronounce 发音
        # pronounce_to 译文发音
        # phonetic_symbol 音标
        # phonetic_symbol_to 译文音标
        # adverb 副词
        # preposition 介词
        # conjunction 连词
        # adverb 副词
        request_time = time.strftime("%Y-%m-%d", time.localtime())
        url = f'https://translate.google.cn/_/TranslateWebserverUi/data/batchexecute'
        data = {
            "rpcids":"MkEWBc",
            "source-path":"/",
            "f.sid":"3528615277044966264",
            "bl":f"boq_translate-webserver_{request_time}.17_p0",
            "hl":to,
            "soc-app":"1",
            "soc-platform":"1",
            "soc-device":"1",
            "_reqid":"5445720",
            "rt":"c",
            'f.req': f'[[["MkEWBc","[[\\"{word}\\",\\"{from_is}\\",\\"{to}\\",true],[null]]",null,"generic"]]]'
        }
        res = self.http_common.post(url,data=data)
        res = res.decode('utf-8')
        # Google翻译是以数字+换行作为响应分隔符的，故以以下正则分割。
        res = re.split(re.compile(r"\d+\n"),res)
        res = res[1]
        # 去除google干扰字符
        res = res.replace('"[','[')
        res = res.replace(']"',']')
        res = res.replace('\\"','"')
        # 替换空值，以便于eval转码
        res = res.replace('true','True')
        res = res.replace('false','False')
        res = res.replace('null','None')
        # 将字符串里的unicode码查出
        unicode_code = re.findall(re.compile(r"\\\\u.{4}"),res)
        while len(unicode_code) > 0:
            # 并将unicode码转码后替换成字符串
            unicode = unicode_code.pop()
            trans_code = unicode[1:].encode().decode('unicode_escape')
            res = res.replace(unicode,trans_code)
        # 解析成一个对象
        rough = eval(res)
        rough_machining  = rough[0]
        shelled = []
        for item in rough_machining:
            if type(item) is list:
                shelled = item
                break
        result = {}
        result["word"] = word
        result["phonetic_symbol"] = shelled[0][0]
        result["from_is"] = shelled[2]
        result["pronounce"] = None
        result["pronounce_to"] = None
        main_mean = self.util_common.extract_list(shelled[1][0])
        main_mean = self.util_common.split_list(main_mean)
        main_mean = self.util_common.extract_list(main_mean[1])
        main_mean = self.util_common.split_list(main_mean)
        example_key = f"example"
        synonym_key = f"synonym"
        generic_key = f"generic"
        mean_key = "mean"

        for item in main_mean:
            if mean_key not in result:
                result[mean_key] = []
            result[mean_key].append(item[2])
        result[example_key] = []
        main_trans_result = shelled[1]
        result["to"] = main_trans_result[1]
        trans_to = main_trans_result[0]
        for trans_item in trans_to:
            if "phonetic_symbol_to" not in result:
                result["phonetic_symbol_to"] = trans_item[1]
        # print("-------------------------------")
        # print(main_trans_result)
        main_trans_result = self.util_common.extract_list(main_trans_result[0])
        # print(main_trans_result)
        main_trans_result = self.util_common.split_list(main_trans_result,start=1,split_symbol=[None,False,True])
        # print(main_trans_result)
        main_trans_result = self.util_common.extract_list(main_trans_result)
        #主要意思
        mean = main_trans_result[0]
        self.util_common.add_to_dict(result, mean_key, mean)
        try:
            main_info = shelled[3]
        except:
            if callback is not None:
                return callback(result)
            else:
                return result
        for trans_item in main_info:
            if type(trans_item) is list:
                info_of_trans = trans_item[0]
                for info in info_of_trans:
                    info_type = info[0]
                    # print("-------------------------------")
                    # print(f"{info_type}")
                    # print(f"\t{info}")
                    try:
                        info_detail = info[1]
                    except:
                        print(f"info----------------")
                        pprint.pprint(info)
                        return
                    #这是例句
                    if info_type is None:
                        # is generic 类型
                        if type(info_detail) is list:
                            if generic_key in result:
                                info_label = f"{generic_key}_mothertongue"
                                print(f"result[generic_key] {result[generic_key]}")
                                result[info_label] = result[generic_key]

                            result[generic_key] = {}
                            info_detail = self.util_common.extract_list(info_detail)
                            info_detail = self.util_common.split_list(info_detail,split_symbol=[None,False,True])
                            means = info_detail[0]
                            result[generic_key][mean_key] = means
                            if len(info_detail) > 1:
                                synonym = info_detail[1]
                            else:
                                synonym = []
                            print(f"means {means}")
                            print(f"synonym {synonym}")
                            result[generic_key][synonym_key] = synonym

                        else:
                            # print(f"\tinfo_detail {self.__query_example_and_synonym(info_detail)}")
                            result[example_key].append(info_detail)
                    else:
                        for detail_item in info_detail:

                            if info_type is "abbreviation":
                                self.util_common.add_to_dict(result, info_type, detail_item[0])
                            elif info_type in ["adverb","noun","adjective","exclamation","article","pronoun","pronoun","pronoun","pronoun","pronoun","pronoun"]:

                                # 如果项目已经存在,而说明需要将前一个替换为母语翻译
                                if info_type in result:
                                    info_label = f"{info_type}_mothertongue"
                                    result[info_label] = result[info_type]
                                result[info_type] = {}
                                result[info_type][example_key] = []
                                result[info_type][synonym_key] = []
                                # info_type => noun ,verb
                                # print(f"\t detail_item {detail_item}")
                                # 需要进行例句判断
                                mean = detail_item[0]
                                self.util_common.add_to_dict(result[info_type],mean_key,mean)
                                add_to_example = True
                                query_synonym = False
                                synonym = []
                                for i in range(len(detail_item)):
                                    item = detail_item[i]
                                    if item in [None,False,True]:
                                        add_to_example = False
                                        query_synonym = True
                                    if i > 0 and type(item) is str and add_to_example:
                                        #例句添加
                                        result[info_type][example_key].append(item)
                                    if i > 0 and query_synonym and type(item) is list:
                                        synonym = item
                                # print(f"\t mean {mean}")
                                # print(f"\t synonym {synonym}")
                                while len(synonym) > 0 and type(synonym[0][0]) == list:
                                    synonym = synonym[0]
                                # print(f"\t result[info_type][mean_key] {result[info_type][mean_key]}")
                                for item in synonym:
                                    # print(f"\t synonym_item {item}")
                                    if type(item) == list:
                                        item = item[0]
                                    self.util_common.add_to_dict(result[info_type], synonym_key, item)
                            else: # 其他未识别
                                result[info_type] = {}
                                for detail in detail_item:
                                    if type(detail) is str:  # 例句
                                        # self.util_common.add_to_dict(result[info_type], example_key, detail)
                                        self.util_common.add_to_dict(result[info_type], mean_key, detail)
                                    if type(detail) is list:  # 同义词
                                        detail_list = detail
                                        while type(detail_list[0][0]) is list:
                                            detail_list = detail_list[0]
                                        # print(f"\t\t\t\tdetail_list {detail_list}")
                                        for item in detail_list:
                                            while type(item[0][0]) is list:
                                                item = item[0]
                                            if type(item[0]) is list:
                                                verb = item[0][0]
                                            else:
                                                verb = item
                                            if type(verb) is list:
                                                verb = verb[0]
                                            self.util_common.add_to_dict(result[info_type], synonym_key, verb)
        if callback is not None:
            return callback(result)
        else:
            return result

    def __query_example_and_synonym(self,detail_item):
        add_to_example = True
        query_synonym = False
        synonym = []
        example = []
        if type(detail_item) is not list:
            return {
            "synonym":synonym,
            "example":[detail_item],
        }
        detail_item = self.util_common.extract_list(detail_item)
        for i in range(len(detail_item)):
            item = detail_item[i]
            if item in [None, False, True]:
                add_to_example = False
                query_synonym = True
            if i > 0 and type(item) is str and add_to_example:
                # 例句添加
                example.append(item)
            if i > 0 and query_synonym and type(item) is list:
                synonym = item
        synonym = self.util_common.extract_list(synonym)
        return {
            "synonym":synonym,
            "example":example,
        }

    def translate_from_youdao(self,word="", from_is='zh', to='en'):
        print('正在调用翻译接口:youdao')
        while True:
            # while Q.strip() == '' or len(Q.strip()) > 1000:
            # if Q.strip() == '':
            #    print('欲翻译文本不可以为空！')
            # if len(Q.strip()) > 1000:
            #    print('欲翻译文本长度不可以超过1000！')

            print('欲翻译文本 => %s' % (word))
            if word.strip() == '':
                return None
            data = {
                'q': word,
                'from': to,
                'to': from_is
            }
            print(f'translate_from_youdao : {from_is} to {to}')
            result = self.http_common.post_as_json('https://github.com/visionmedia/debug/issues/797', data)
            errorCode = result['errorCode']
            if errorCode != '0':
                print('出现错误！返回的状态码为：%s' % (errorCode))
                break
            else:
                print(result)
            # tSpeakUrl = json['tSpeakUrl']
            # speakUrl = json['speakUrl']
            # web = json['web']
            query = result['query']
            translation = result['translation']
            # for x in range(len(translation)):
            #     print('翻译结果' + str(x + 1) + " : " + translation[x])

            return translation

    def to_azure_voice(self,content_list,suffix = 'wav'):
        voiceDownloadDir = self.config_common.get_config("voiceDownloadDir")
        #支持的后缀格式

        speech_config  = speechsdk.SpeechConfig(subscription=getConfig("SubscriptionKey"), region=getConfig("ServiceRegion"))
        audio_config = speechsdk.audio.AudioOutputConfig(use_default_speaker=True)

        #根据GOOGLE翻译匹配的微软云语音
        speech_synthesis_language = getConfig("speech_synthesis_language")
        speech_synthesis_voice_name = getConfig("speech_synthesis_voice_name")

        # The language of the voice that speaks.
        speech_config.speech_synthesis_language = speech_synthesis_language
        speech_config.speech_synthesis_voice_name = speech_synthesis_voice_name
        speech_synthesizer = speechsdk.SpeechSynthesizer(speech_config=speech_config, audio_config=audio_config)

        # Get text from the console and synthesize to the default speaker.
        print("语音开始识别 识别引擎为： 微软云 -=- [Azure] \n")

        for k,text in content_list:
            filename = f'{text["id"]}_{text["start"]}_{text["duration"]}_{text["render_index"]}'
            voice = text["content"]
            voice_file_name = f'{filename}.{suffix}'
            aodioSavePath = os.path.join(f'{voiceDownloadDir}/', voice_file_name)
            content_list[k]['voice_file'] = formatDirectory(aodioSavePath)
            audioSaveConfig = speechsdk.audio.AudioOutputConfig(filename=aodioSavePath)
            synthesizer = speechsdk.SpeechSynthesizer(speech_config=speech_config, audio_config=audioSaveConfig)
            synthesizer.speak_text_async(voice)
            print(f" Azure 文字->语音识别成功({k}/{len(content_list)})*：")
            print(f"    当前台词为 ： {voice}")
            print(f"        ---> 文件名 ：{voice_file_name}")
        return content_list

    def to_voice(self,word):
        """
        # 目标语音下载
        :param url:
        :return:
        """
        r = requests.get(f'https://tts.youdao.com/fanyivoice?le=auto&word={voiceContent}')  # 发送请求
        # 保存
        voiceDownloadDir = self.config_common.get_public("down_file")
        savepath = os.path.join(f'{voiceDownloadDir}/{word}.wav')

        with open(f'{savepath}', 'wb+') as f:
            f.write(r.content)
            f.close()
            print(f"[语音]:{savepath}")
            return savepath


    def document_to_words_origin(self,doc):
        splits_symbol = re.compile(r'[^\、\·\{\}\_\s\r\n\!\=\"\:\*\s\]\[\(\)\@\#\$\%\^\&\*\-\+\《\》\<\>\,\.\，\。\；\：\‘\“\:\;\'\"\`\\\/\~]+')
        doc_words = re.split(splits_symbol,doc)
        print(doc_words)
        contentAll = " ".join(doc_words)
        theBoardBeforeIsLowLetter = re.compile(r"(?<=\d)\B(?=\D)")
        theBoardBeforeIsUpLetter = re.compile(r"(?<=\D)\B(?=\d)")
        theBoardBeforeIsAcronym = re.compile(r"(?<=[A-Z])\B(?=[A-Z]{1}[a-z]{1})")
        theBoardBeforeIsWord = re.compile(r"(?<=[a-z])\B(?=[A-Z])")
        theBoardSplitWord = re.compile(r"\b")

        contentAll = re.split(theBoardBeforeIsLowLetter,contentAll)
        contentAll = " ".join(contentAll)
        contentAll = re.split(theBoardBeforeIsUpLetter,contentAll)
        contentAll = " ".join(contentAll)
        contentAll = re.split(theBoardBeforeIsAcronym,contentAll)
        contentAll = " ".join(contentAll)
        contentAll = re.split(theBoardBeforeIsWord,contentAll)
        contentAll = " ".join(contentAll)
        contentAll = re.split(theBoardSplitWord,contentAll)
        contentAll = " ".join(contentAll)
        contentAll = set(contentAll)
        contentAll = list(contentAll)
        for i in range(len(contentAll)):
            word = contentAll[i]
            if self.purify_str(word):
                print(word, i, word)
                del contentAll[i]

        return contentAll



