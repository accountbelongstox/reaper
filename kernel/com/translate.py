# from queue import Queue
# import operator
# import shutil
# import ssl
# from http.client import HTTPSConnection
# from urllib.parse import urlparse
import time

import math
from queue import Queue

from kernel.base.base import *
import os
import re
import json
import requests
from urllib import request, parse

import googletrans
from googletrans import Translator

threadQueue = None

googletanslator = Translator(service_urls=[
    'translate.12gm.com',
    # 'translate.google.com',
    # 'translate.google.com.hk',
    # 'translate.google.cn',
])


class Translate(BaseClass):
    __threads = {}
    MDX = None  # 用来解析mdx文件的字段

    def __init__(self, args):
        pass

    def get_googletranslate(self, ):
        ns = "nslookup translate.google.com"
        return ns

    def main(self, args):
        # 初始化数据表
        # self.create_databasename()
        self.load_local_transwords()
        pass

    def add_wordtodictinary(self, doc):
        if type(doc) == str:
            words = self.document_to_words(doc)
        else:
            words = doc
        save_words = []
        language = "en"
        en_words = self.get_wordfromtransobject(language, words)
        for word in en_words:
            save_words.append({
                "language": language,
                "word": word,
            })
        count = len(en_words)
        result = self.sava_to_db(save_words)
        if type(result) == str:
            return result
        else:
            return f"A total of {count} words are saved to the database."

    def get_wordfromtransobject(self, language, wordtransobject):
        words = []
        for language_type, wordtransobjectitem in wordtransobject.items():
            # 目前只支持英文
            if language_type == language:
                for word in wordtransobjectitem:
                    words.append(word)
        return words

    def update_translate_db(self, words):
        if type(words) is str:
            words = json.loads(words)
        word = words["word"]
        words["last_time"] = self.com_string.create_time()
        words["read_time"] = self.com_string.create_time("1970-01-01")
        res = self.com_db.update(self.com_db.get_translation_dictionary(), words, {
            "word": word,
        })
        return res

    def update_translate(self):
        words = self.com_db.read(self.com_db.get_translation_dictionary(), {
            "word": ["manner", "Aaronj", "Aaronj"]
        }, limit=None, select="word,translate_bing", result_object=True)
        for word in words:
            translate_bing = word[1]
            new_word = {}
            self.com_util.pprint(translate_bing)
            for key, word_item in translate_bing.items():
                if key != "phonetic_symbol":
                    if key in ["synonyms_type", "advanced_translate_type"]:
                        for i in range(len(word_item)):
                            item = word_item[i]
                            item = re.sub(re.compile(r"<.+?>"), "", item)
                            word_item[i] = item
                            new_word[key] = word_item
                    else:
                        new_word[key] = word_item
            word = {
                "word": word[0],
                "translate_bing": translate_bing,
            }
            self.update_translate_db(word)

    def sava_to_db(self, data, tabname="word", db_key="word"):
        if tabname == "word":
            tabname = self.com_db.get_translation_dictionary()
        elif tabname == "group":
            tabname = self.com_db.get_translation_group()
        if type(data) == str:
            data = {
                db_key: data,
            }
        data = self.set_default_val(data)
        result = self.com_db.save(tabname, data, insert_list=True)
        return result

    def set_default_val(self, data):
        if type(data) != list:
            data = [data]
        for word_item in data:
            self.set_addval(word_item, "last_time", self.com_string.create_time())
            self.set_addval(word_item, "read", 0)
        return data

    def read_not_translated(self, engine="bing", condition=None):
        if condition == None:
            condition = {
                f"translate_{engine}": "",
            }
        words = self.com_db.read(self.com_db.get_translation_dictionary(), condition, limit=None, select="word")
        words = [word[0] for word in words]
        return words

    def get_remote_notranslated(self):
        url = self.com_http.get_remote_url("get_not_translated")
        words = self.com_http.get(url)
        words = self.com_util.to_json(words)
        words = words.get('data')
        return words

    def get_words_db(self, limit=(0, 1000), group_n=None):
        words = self.com_db.read(self.com_db.get_translation_dictionary(), {

        }, limit=limit)
        return words

    def set_addval(self, word, key, value):
        if key not in word:
            word[key] = value
        return word

    def translate(self, word, from_is="en", to="zh-cn", engine="google_cn", callback=None, timeout=None):
        is_file = self.com_file.isfile(word)
        if is_file:
            word = self.com_file.open(word)
        if type(word) is list:
            words = word
        else:
            if type(word) is not str:
                word = self.com_string.byte_to_str(word)
            words = self.document_to_words(word)
        if from_is in words:
            words = words[from_is]
        if engine == "bing":
            return self.translate_from_bing(words)

        per_thread_solve_word_num = 30
        words_len = len(words)
        words_split = words_len / per_thread_solve_word_num
        max_thread = math.ceil(words_split)
        # 最大调用线程数
        if max_thread > 60:
            max_thread = 60

        threads = []
        for i in range(max_thread):
            start_point = i * per_thread_solve_word_num
            end_point = i * per_thread_solve_word_num + per_thread_solve_word_num
            fragment_translation = words[start_point:end_point]
            fragment_word_translateobject_list = []
            for index in range(len(fragment_translation)):
                word = fragment_translation[index]
                translateobject = self.word_to_translateobject(word, from_is=from_is, to=to, engine=engine,
                                                               callback=callback, index=index)
                fragment_word_translateobject_list.append(translateobject)
            th = self.com_thread.create_thread("translate", args=fragment_word_translateobject_list)
            th.start()
            threads.append(th)

        time_count = 0
        # 如果线程全部结束则返回结果
        while (self.thread_translation_has_ended(threads) != True):
            if self.is_timeout(time_count, timeout):
                print(f'translation timed out')
                break
            time.sleep(1)
            time_count += 1
        result = self.get_thread_result(threads)
        if callback is not None:
            return callback(result)
        else:
            return result

    def not_translatedtoqueue(self,words=None,condition=None):
        global threadQueue
        if threadQueue == None:
            threadQueue = Queue()
        if type(words) == str : words = [words]
        if words == None:
            words = self.read_not_translated(condition=condition)
        threadQueue = self.com_thread.update_queue(threadQueue, words)
        update_time = self.com_string.create_time()
        self.com_util.print_info(f'no-translated:{len(words)} words add to tasks and qsize:{threadQueue.qsize()},update_time {update_time}')
        return threadQueue

    def get_thread_translatemax(self,qsize):
        max_thread = 10
        min_thread = 4
        max_processing_per_thread = 1000
        thread_n = min_thread
        if self.load_module.is_windows():
            if qsize > max_processing_per_thread:
                thread_n = int(qsize / max_processing_per_thread)
                if thread_n > max_thread:
                    thread_n = max_thread
        return thread_n

    def thread_translate(self, words=None, wait=False, condition=None, debug=False, headless=True,save_db=True,callback=None,put_remote=False):
        global threadQueue
        # headless = False
        if threadQueue == None:
            threadQueue = Queue()
        if put_remote == True:
            callback = self.put_remoteword
        threadQueue = self.not_translatedtoqueue(words=words,condition=condition)
        qsize = threadQueue.qsize()
        max_thread = self.get_thread_translatemax(qsize)
        tasks_per_thread = int(qsize / max_thread)
        min_processing_per_thread = 10
        if tasks_per_thread < min_processing_per_thread:
            tasks_per_thread = min_processing_per_thread
        thread_args = {
            "task": threadQueue,
            "save_db": save_db,
            # "save_db":False,
            "info": False,
            "headless": headless,
            "debug": debug,
            "callback": callback,
            "tasks_per_thread": tasks_per_thread,
        }
        self.com_thread.create_thread_pool("translate", args=thread_args, wait=wait,max_thread=max_thread, )

    def put_remoteword(self,word,trans):
        put_word = {
            "word":word,
            "trans":trans,
        }
        if trans == None:
            # submit is.
            return
        voice_files = trans.get('voice_files')
        sample_images = trans.get('sample_images')
        put_word = self.get_trans_val(put_word,sample_images)
        put_word = self.get_trans_val(put_word,voice_files)
        url = self.com_http.get_remote_url('trans_word')
        self.com_http.post(url,put_word)

    def get_trans_val(self,put_word,file_val):
        if file_val == None:
            return put_word
        for key,val in file_val.items():
            save_filename = val.get('save_filename')
            full_filename = self.com_file.get_template_dir(save_filename,fulllink=True)
            put_word[save_filename] = self.com_file.read_file_bytes(full_filename)
        return put_word


    def document_extract_en(self, doc):
        splits_symbol = re.compile(r'[^a-zA-Z]+')
        doc_words = re.split(splits_symbol, doc)
        doc_words = list(
            set(doc_words)
        )
        return doc_words

    def count_document_words(self, doc):
        if type(doc) == list:
            return doc
        splits_symbol = re.compile(r'[^\w]+')
        doc_words = re.split(splits_symbol, doc)
        contentAll = " ".join(doc_words)
        theBoardBeforeIsLowLetter = re.compile(r"(?<=\d)\B(?=\D)")
        theBoardBeforeIsUpLetter = re.compile(r"(?<=\D)\B(?=\d)")
        theBoardBeforeIsAcronym = re.compile(r"(?<=[A-Z])\B(?=[A-Z]{1}[a-z]{1})")
        theBoardBeforeIsWord = re.compile(r"(?<=[a-z])\B(?=[A-Z])")
        theBoardBeforeIsEnglish = re.compile(r"(?<=[a-zA-Z])\B(?=([\u4e00-\u9fa5]|[\ufe30-\uffa0]|[\u4e00-\uffa5]))")
        theBoardBeforeIsChnese = re.compile(r"(?<=([\u4e00-\u9fa5]|[\ufe30-\uffa0]|[\u4e00-\uffa5]))\B(?=[a-zA-Z])")
        theBoardSplitWord = re.compile(r"\b")
        contentAll = re.split(theBoardBeforeIsLowLetter, contentAll)
        contentAll = " ".join(contentAll)
        contentAll = re.split(theBoardBeforeIsUpLetter, contentAll)
        contentAll = " ".join(contentAll)
        contentAll = re.split(theBoardBeforeIsAcronym, contentAll)
        contentAll = " ".join(contentAll)
        contentAll = re.split(theBoardBeforeIsWord, contentAll)
        contentAll = " ".join(contentAll)
        contentAll = re.split(theBoardBeforeIsEnglish, contentAll)
        contentAll = " ".join(contentAll)
        contentAll = re.split(theBoardBeforeIsChnese, contentAll)
        contentAll = " ".join(contentAll)
        contentAll = contentAll.split("_")
        contentAll = " ".join(contentAll)
        contentAll = re.split(theBoardSplitWord, contentAll)
        contentAll = " ".join(contentAll)
        contentAll = contentAll.split(" ")
        contentAll = set(contentAll)
        contentAll = list(contentAll)
        contentAll = [word.strip() for word in contentAll if word != ""]
        return contentAll

    def document_to_words(self, content_words):
        if type(content_words) == str:
            content_words = self.count_document_words(content_words)
        contentAll_words = self.words_to_standard_translate_list(content_words)
        return contentAll_words

    def words_to_standard_translate_list(self, contentAll):
        words = {}
        english_key = "en"
        chinese_key = "zh-cn"
        unsupported_key = "unsupported"
        words[english_key] = []
        words[chinese_key] = []
        words[unsupported_key] = []
        for word in contentAll:
            if self.is_english(word):
                words[english_key].append(word)
            elif self.is_chinese(word):
                words[chinese_key].append(word)
            else:
                words[unsupported_key].append(word)
        return words

    def is_true_word(self, word):
        isShortAlpha = re.compile(r'^\w$')
        # print(f"re.search(isShortAlpha,{word}) {re.search(isShortAlpha,word)}")
        if re.search(isShortAlpha, word) != None and len(word) > 1:
            return True
        isNumber = re.compile(r'^\d+$')
        if re.search(isNumber, word) != None:
            return False
        isLowLetterAndUpper = re.compile(r"^[a-z]{1}[A-Z]{1}$")
        if re.search(isLowLetterAndUpper, word) != None:
            return False
        isEmptyChar = ""
        if word == isEmptyChar:
            return False
        return True

    def is_chinese(self, word):
        pattern = re.compile(r"^([\u4e00-\u9fa5]|[\ufe30-\uffa0]|[\u4e00-\uffa5])+")
        if re.search(pattern, word) != None:
            return True
        return False

    def is_english(self, word):
        word = word.strip()
        pattern = re.compile(r"^[a-zA-Z]+$", re.I)
        if re.search(pattern, word) != None and len(word) > 1:
            return True
        return False

    def language(self, word):
        return self.determine_the_type_of_language(word)

    def determine_the_type_of_language(self, word):
        if self.is_english(word):
            return "en"
        elif self.is_chinese(word):
            return "zh-cn"
        else:
            return None

    def google_translate_language(self):
        language = googletrans.LANGUAGES
        return language

    def translate_to_html(self, word, from_is="en", to="zh-cn", engine="google_cn", callback=None):
        result = self.translate(word, from_is=from_is, to=to, engine=engine, callback=callback)
        return result

    def to_html(self, result):
        for item in result:
            print(item)

    def to_text(self, result):
        for item in result:
            print(item)

    def is_timeout(self, time_count, timeout):
        if timeout == None:
            return False
        if (time_count >= timeout):
            return True
        else:
            return False

    def get_thread_result(self, threads):
        result = []
        for th in threads:
            result_of_th = th.result()
            while result_of_th.qsize() > 0:
                result.append(result_of_th.get())
        result.sort(key=lambda item: item["index"])
        return result

    def thread_translation_has_ended(self, threads):
        for th in threads:
            if th.done() == False:
                return False
        return True

    def word_to_translateobject(self, word, engine="google_cn", from_is="en", to="zh-cn", callback=None, index=0):
        word_translateobject = {
            "word": word,
            "from_is": from_is,
            "to": to,
            "engine": engine,
            "index": index,
            "callback": callback
        }
        return word_translateobject

    def translate_from_google(self, word, dest="en", src="zh-CN", ):
        out = googletanslator.translate(word, dest, src)
        # voice = self.microsoft_azure_to_voice(out.text)
        voice = None
        result = {
            "origin": word,
            "text": out.text,
            "src": out.src,
            "dest": out.dest,
            "pronunciation": voice,
        }
        return result

    def bing_engine_get_static_file(self, word, language="", index="", file_suffix="", file_type="voice",dynamic_url=False):
        if language != "":
            language = f"_{language}"
        if index != "":
            index = f"_{index}"
        word = re.sub(re.compile(r"[^\w]+"), "", word)
        md5 = self.com_string.md5(word)
        static_file = f"{word}{language}{index}{md5}{file_suffix}"
        static_file = self.bing_engine_voice_static_dir(static_file, file_type=file_type)
        return static_file

    def bing_engine_voice_static_dir(self, filename=None, file_type=""):
        static_folder = self.get_static()
        down_dir = self.load_module.get_control_dir(f"{static_folder}/bing/{file_type}")
        if filename:
            down_dir = os.path.join(down_dir, filename)
        down_dir = self.com_string.dir_normal(down_dir)
        return down_dir

    def bing_engine_htmlshell(self, htmls):
        self.com_selenium.remove('.se_div')
        self.com_selenium.remove('.b_footer')
        self.com_selenium.remove('.sidebar')
        self.com_selenium.remove('#b_header')
        self.com_selenium.html('.lf_area', '')
        bing_engine_htmlshell = self.com_selenium.get_html()
        file_name = self.com_file.create_file_name(prefix='bing_html', suffix='.html')
        self.com_file.save(file_name, bing_engine_htmlshell, overwrite=True)
        while len(htmls) > 0:
            html = htmls.pop(0)
            self.com_selenium.before('.lf_area', html)
        result_html = self.com_selenium.get_html()
        file_name = self.com_file.create_file_name(prefix='bing', suffix='.html')
        file_name = self.com_file.save(file_name, result_html, overwrite=True)
        return file_name

    def get_static(self):
        static_folder = self.com_config.get_global("flask_static_folder")
        static_folder = os.path.join(static_folder, 'translate_wave')
        return static_folder

    def translate_from_mdx(self, word, from_is=None, to=None):
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
        mdx_dir = self.com_config.get_public(mdx_file)
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
        self.com_file.save(doc)
        coca2 = doc('div[class="coca2"]').text().replace('\n', '')
        print(coca2)
        meaning = doc("""div[class="dcb"]""").text()

    def translate_from_baidu(self, content):
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

    def translate_from_google_cn(self, word, from_is="en", to="zh-cn", callback=None):
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
            "rpcids": "MkEWBc",
            "source-path": "/",
            "f.sid": "3528615277044966264",
            "bl": f"boq_translate-webserver_{request_time}.17_p0",
            "hl": to,
            "soc-app": "1",
            "soc-platform": "1",
            "soc-device": "1",
            "_reqid": "5445720",
            "rt": "c",
            'f.req': f'[[["MkEWBc","[[\\"{word}\\",\\"{from_is}\\",\\"{to}\\",true],[null]]",null,"generic"]]]'
        }
        res = self.com_http.post(url, data=data)
        res = res.decode('utf-8')
        # Google翻译是以数字+换行作为响应分隔符的，故以以下正则分割。
        res = re.split(re.compile(r"\d+\n"), res)
        res = res[1]
        # 去除google干扰字符
        res = res.replace('"[', '[')
        res = res.replace(']"', ']')
        res = res.replace('\\"', '"')
        # 替换空值，以便于eval转码
        res = res.replace('true', 'True')
        res = res.replace('false', 'False')
        res = res.replace('null', 'None')
        # 将字符串里的unicode码查出
        unicode_code = re.findall(re.compile(r"\\\\u.{4}"), res)
        while len(unicode_code) > 0:
            # 并将unicode码转码后替换成字符串
            unicode = unicode_code.pop()
            trans_code = unicode[1:].encode().decode('unicode_escape')
            res = res.replace(unicode, trans_code)
        # 解析成一个对象
        rough = eval(res)
        rough_machining = rough[0]
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
        main_mean = self.com_util.extract_list(shelled[1][0])
        main_mean = self.com_util.split_list(main_mean)
        main_mean = self.com_util.extract_list(main_mean[1])
        main_mean = self.com_util.split_list(main_mean)
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
        main_trans_result = self.com_util.extract_list(main_trans_result[0])
        # print(main_trans_result)
        main_trans_result = self.com_util.split_list(main_trans_result, start=1, split_symbol=[None, False, True])
        # print(main_trans_result)
        main_trans_result = self.com_util.extract_list(main_trans_result)
        # 主要意思
        mean = main_trans_result[0]
        self.com_util.add_to_dict(result, mean_key, mean)
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
                        self.com_util.pprint(info)
                        return
                    # 这是例句
                    if info_type is None:
                        # is generic 类型
                        if type(info_detail) is list:
                            if generic_key in result:
                                info_label = f"{generic_key}_mothertongue"
                                print(f"result[generic_key] {result[generic_key]}")
                                result[info_label] = result[generic_key]

                            result[generic_key] = {}
                            info_detail = self.com_util.extract_list(info_detail)
                            info_detail = self.com_util.split_list(info_detail, split_symbol=[None, False, True])
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

                            if info_type == "abbreviation":
                                self.com_util.add_to_dict(result, info_type, detail_item[0])
                            elif info_type in ["adverb", "noun", "adjective", "exclamation", "article", "pronoun",
                                               "pronoun", "pronoun", "pronoun", "pronoun", "pronoun"]:

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
                                self.com_util.add_to_dict(result[info_type], mean_key, mean)
                                add_to_example = True
                                query_synonym = False
                                synonym = []
                                for i in range(len(detail_item)):
                                    item = detail_item[i]
                                    if item in [None, False, True]:
                                        add_to_example = False
                                        query_synonym = True
                                    if i > 0 and type(item) is str and add_to_example:
                                        # 例句添加
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
                                    self.com_util.add_to_dict(result[info_type], synonym_key, item)
                            else:  # 其他未识别
                                result[info_type] = {}
                                for detail in detail_item:
                                    if type(detail) is str:  # 例句
                                        # self.com_util.add_to_dict(result[info_type], example_key, detail)
                                        self.com_util.add_to_dict(result[info_type], mean_key, detail)
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
                                            self.com_util.add_to_dict(result[info_type], synonym_key, verb)
        if callback is not None:
            return callback(result)
        else:
            return result

    def __query_example_and_synonym(self, detail_item):
        add_to_example = True
        query_synonym = False
        synonym = []
        example = []
        if type(detail_item) is not list:
            return {
                "synonym": synonym,
                "example": [detail_item],
            }
        detail_item = self.com_util.extract_list(detail_item)
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
        synonym = self.com_util.extract_list(synonym)
        return {
            "synonym": synonym,
            "example": example,
        }

    def translate_from_youdao(self, word="", from_is='zh', to='en'):
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
            result = self.com_http.post_as_json('https://github.com/visionmedia/debug/issues/797', data)
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

    #
    # def to_azure_voice(self,content_list,suffix = 'wav'):
    #     voiceDownloadDir = self.com_config.get_config("voiceDownloadDir")
    #     #支持的后缀格式
    #
    #     speech_config  = speechsdk.SpeechConfig(subscription=getConfig("SubscriptionKey"), region=getConfig("ServiceRegion"))
    #     audio_config = speechsdk.audio.AudioOutputConfig(use_default_speaker=True)
    #
    #     #根据GOOGLE翻译匹配的微软云语音
    #     speech_synthesis_language = getConfig("speech_synthesis_language")
    #     speech_synthesis_voice_name = getConfig("speech_synthesis_voice_name")
    #
    #     # The language of the voice that speaks.
    #     speech_config.speech_synthesis_language = speech_synthesis_language
    #     speech_config.speech_synthesis_voice_name = speech_synthesis_voice_name
    #     speech_synthesizer = speechsdk.SpeechSynthesizer(speech_config=speech_config, audio_config=audio_config)
    #
    #     # Get text from the console and synthesize to the default speaker.
    #     print("语音开始识别 识别引擎为： 微软云 -=- [Azure] \n")
    #
    #     for k,text in content_list:
    #         filename = f'{text["id"]}_{text["start"]}_{text["duration"]}_{text["render_index"]}'
    #         voice = text["content"]
    #         voice_file_name = f'{filename}.{suffix}'
    #         aodioSavePath = os.path.join(f'{voiceDownloadDir}/', voice_file_name)
    #         content_list[k]['voice_file'] = formatDirectory(aodioSavePath)
    #         audioSaveConfig = speechsdk.audio.AudioOutputConfig(filename=aodioSavePath)
    #         synthesizer = speechsdk.SpeechSynthesizer(speech_config=speech_config, audio_config=audioSaveConfig)
    #         synthesizer.speak_text_async(voice)
    #         print(f" Azure 文字->语音识别成功({k}/{len(content_list)})*：")
    #         print(f"    当前台词为 ： {voice}")
    #         print(f"        ---> 文件名 ：{voice_file_name}")
    #     return content_list

    def to_voice(self, sentence, engin="azure"):
        if (engin == "azure"):
            return self.microsoft_azure_to_voice(sentence)
        elif (engin == "youdao"):
            return self.youdao_engine_get_voice_file(sentence)
        else:
            self.com_util.print_warn(f"engine not supported")
            return None

    def microsoft_azure_to_voice(self, sentence="", speed=0.3, voice="en-US-JennyNeural", language="en-US"):
        if not sentence:
            print(f"Please pass the sentence or word before translation")
            return None
        static_file = self.microsoft_azure_get_voice_file(sentence, speed)
        if self.com_file.isfile(static_file):
            print(f"The audio files already exist, no need to download")
            return static_file
        down_dir = self.microsoft_azure_voice_download_dir()
        self.com_selenium.set_download_dir(down_dir)
        self.com_file.mkdir(down_dir)
        self.com_file.rmtree(down_dir)
        driver = self.com_selenium.is_exists_driver()
        if driver == False:
            self.com_selenium.open(
                f'https://azure.microsoft.com/{language.lower()}/products/cognitive-services/text-to-speech',
                not_wait=True, driver_type="edge", disable_gpu=True, headless=True)
        else:
            driver.refresh()
        time.sleep(1)
        azure_speech_download_js_file = self.com_config.get_libs("azure_speech_download.js")
        azure_speech_download_js = self.com_file.read_file(azure_speech_download_js_file)
        self.com_selenium.execute_js(azure_speech_download_js)
        self.microsoft_azure_voice_scrolllanguageandselect(language)
        self.microsoft_azure_voice_voiceselect(voice)
        self.microsoft_azure_voice_adjust_speed(speed)
        self.microsoft_azure_voice_fillintext(sentence)
        self.microsoft_azure_voice_play()
        wait_second = 4
        while wait_second > 0 and self.microsoft_azure_voice_is_play(1) == False:
            print("Waiting for voice playback.")
            wait_second -= 1
            time.sleep(0.5)
        if self.microsoft_azure_voice_error():
            print(f"Voice reading is unsuccessful")
            return self.microsoft_azure_to_voice(language=language, speed=speed, sentence=sentence)
        else:
            tampermonkey_downloadselector = "#donwloadli button"
            self.com_selenium.click(tampermonkey_downloadselector)
            voice_complete = self.microsoft_azure_voice_downloadcomplete()
            if voice_complete:
                down_voicefile = self.microsoft_azure_voice_extract_voicefile()
                if down_voicefile != None:
                    self.com_file.cut(down_voicefile, static_file)
                    return static_file
                else:
                    print(f"File download failed")
                    return None
            else:
                print(f"The voice download failed, re -translated.")
                return self.microsoft_azure_to_voice(language=language, speed=speed, sentence=sentence)

    def microsoft_azure_voice_play(self):
        self.com_selenium.click("#playbtn")

    def microsoft_azure_voice_is_play(self, wait_second=3):
        play_show = self.com_selenium.is_show("#playbtn")
        time.sleep(wait_second)
        error = self.microsoft_azure_voice_error()
        if not play_show and not error:
            return True
        else:
            return False

    def microsoft_azure_voice_error(self):
        ##ttsstatus 加载此演示时发生错误，请重载并重试
        error_selector = "#ttsstatus"
        err_info = self.com_selenium.find_text_content_by_js(error_selector)
        err_info = err_info.find("error")
        if err_info == -1:
            return False
        else:
            return True

    def microsoft_azure_voice_fillintext(self, sentence=""):
        selector = f"#ttstext"
        textarea = self.com_selenium.find_element(selector)
        textarea.click()
        textarea.clear()
        textarea.send_keys(sentence)

    def microsoft_azure_voice_scrolllanguageandselect(self, language="en-US"):
        language_selector = f"#languageselect"
        offset_top = self.com_selenium.offset_scrolltowindow(language_selector)
        offset_top = offset_top + self.com_string.random_num(0, 100)
        self.com_selenium.scroll_to(0, offset_top)
        self.com_selenium.select_wait(language_selector, language)

    def microsoft_azure_voice_voiceselect(self, voice):
        language_selector = f"#voiceselect"
        self.com_selenium.select_wait(language_selector, voice)

    def microsoft_azure_voice_adjust_speed(self, speed=0.3):
        speed_selector = "#speed"
        offset_top = self.com_selenium.offset_towindow(speed_selector)
        offset_left = self.com_selenium.offset_left(speed_selector)
        element_width = self.com_selenium.element_width(speed_selector)
        element_height = self.com_selenium.element_height(speed_selector)
        speed = speed / 2  # 因为宽度是2倍的从中间切开
        # speed_pix = element_width / 300
        x = offset_left + element_width * speed
        y = (element_height / 1.5) + offset_top
        self.com_selenium.screen_click(x, y)

    def microsoft_azure_voice_downloadcomplete(self, ):
        optiondiv_selector = "#optiondiv"
        process_reg = re.compile("[^0-9\.]+")
        pre_process = None
        process_count = 0

        def process_query():
            global pre_process
            global process_count
            process_selector = f"document.querySelector(`{optiondiv_selector}`).nextSibling.nextSibling.innerHTML"
            process_html = self.com_selenium.execute_js_code(process_selector)
            process_html = re.sub(process_reg, "", process_html)
            process = float(process_html)
            if process != pre_process:
                pre_process = process
                process_count = 0
                return True
            else:
                process_count += 1
                return False

        complete = f"return document.querySelector(`{optiondiv_selector}`).nextSibling.innerHTML"
        max_wait = 50
        no_process_second = 20
        wait = 0

        complete_html = self.com_selenium.execute_js_wait(complete, deep=10)
        if not complete_html:
            print(f"I did not start downloading.")
            return False

        complete_reg = re.compile(r"(complete|\u5b8c\u6210)")
        # 如果10秒没有进展及没有查找到complete则停止
        while len(re.findall(complete_reg, self.com_selenium.execute_js_wait(complete,
                                                                             deep=10))) > 0 and wait < max_wait and process_count < no_process_second:
            print(f"Waiting for voice download has been waiting for {wait / 2} seconds")
            wait += 1
            process_query()
            time.sleep(0.5)
        if process_count >= no_process_second:
            print(f"No progress in {no_process_second / 2} seconds")
            return False
        if wait >= max_wait:
            print(f"Waiting for {wait / 2} timeout")
            return False
        else:
            return True

    def microsoft_azure_voice_download_dir(self):
        static_folder = self.get_static()
        down_dir = self.load_module.get_control_dir(f"{static_folder}/azure_voice_downloadtemp")
        down_dir = self.com_string.dir_normal(down_dir)
        return down_dir

    def microsoft_azure_voice_static_dir(self, filename=None):
        static_folder = self.get_static()
        down_dir = self.load_module.get_control_dir(f"{static_folder}/azure_voice")
        if filename:
            down_dir = os.path.join(down_dir, filename)
        down_dir = self.com_string.dir_normal(down_dir)
        return down_dir

    def microsoft_azure_voice_extract_voicefile(self):
        download_dir = self.microsoft_azure_voice_download_dir()
        index = 0
        timeout_second = 50
        while len(os.listdir(download_dir)) == 0 and index < timeout_second:
            print(f"Wait for the audio to download")
            time.sleep(1)
            index += 1
        if index >= timeout_second:
            print(f"Timeout download unfinished {index} second")
            return None
        download_file = os.listdir(download_dir)
        file = download_file[0]
        file = os.path.join(download_dir, file)
        file = self.com_file.rename_remove_space(file)
        return file

    def microsoft_azure_voice_close(self):
        self.com_selenium.quit()

    def microsoft_azure_get_voice_file(self, sentence, speed, file_suffix=".mp3"):
        static_file = f"{speed}speed_{self.com_string.md5(sentence)}{file_suffix}"
        static_file = self.microsoft_azure_voice_static_dir(static_file)
        return static_file

    def _microsoft_azure_to_voice(self, words=None, wait=False, condition=None, debug=False, headless=True):
        global threadQueue
        if threadQueue == None:
            threadQueue = Queue()
        threadQueue = self.com_thread.update_queue(threadQueue, words)
        thread_args = {
            "task": threadQueue,
            "save_db": True,
            # "save_db":False,
            "info": False,
            "headless": headless,
            "debug": debug,
            "tasks_per_thread": 1000,
        }
        result_list = self.com_thread.create_thread_pool("translate", args=thread_args, wait=wait, )
        return result_list


    def youdao_engine_get_voice_file(self, sentence):
        r = requests.get(f'https://tts.youdao.com/fanyivoice?le=auto&word={sentence}')  # 发送请求
        # 保存
        voiceDownloadDir = self.com_config.get_public("downfile")
        filename = self.com_string.md5(sentence)
        filename = os.path.join(f'{voiceDownloadDir}/{filename}.wav')
        with open(f'{filename}', 'wb+') as f:
            f.write(r.content)
            f.close()
            print(f"[voice_engine_youdao]:{filename}")
            return filename

    def to_voice_engine_microsoftazure(self, sentence="", speed=0.3, voice="en-US-JennyNeural", language="en-US"):
        return self.microsoft_azure_to_voice(sentence=sentence, speed=speed, voice=voice, language=language)

    def encoding_to(self, translate_dir):
        self.com_file.dir_to(translate_dir)
        return translate_dir

    def srt_translate_to_voice(self, flask):
        translate_dir = self.srt_to_utfcode()
        filename = os.path.join(translate_dir,
                                "Game.of.Thrones.S04E01.Two.Swords.2160p.UHD.BluRay.10bit.HDR.x265-HazMatt.ass")
        text = self.com_file.srt(filename)

    def group_doc_filtervoicelists(self, sentences):
        def sentences_lencheck(sentences_checklist):
            isalpha = re.compile(r'^[^a-zA-Z]+$')
            noalpha = re.compile(r'[^a-zA-Z]+')
            isalpha_count = 0
            for sentence in sentences_checklist:
                sentence = re.sub(noalpha, "", sentence)
                if re.search(isalpha, sentence):
                    continue
                if len(sentence) < 3:
                    continue
                isalpha_count += 1
            if isalpha_count > 1:
                return True
            else:
                return False

        sentences_list = []
        for sentence in sentences:
            sentence = sentence.strip()
            pattern = re.compile(r'^[^a-zA-Z0-9(]+')
            sentence = re.sub(pattern, "", sentence)
            pattern = re.compile(r'\s+')
            sentences_checklist = re.split(pattern, sentence)
            if sentences_lencheck(sentences_checklist) == False:
                continue
            sentence = " ".join(sentences_checklist)
            sentences_list.append(sentence)
        return sentences_list

    def group_link_word(self, flask, group_id=None, words=None):
        if group_id == None:
            group_id = flask.flask_request.args.get("group_id")

        condition = self.get_idcondition(group_id)
        if words == None:
            groups = self.com_db.read(self.com_db.get_translation_group(), condition, result_object=True)
            words = groups[0][7]
            words = self.com_util.to_english_array(words)
            # group_contents = str(group_contents)
            # group_contents = re.sub(re.compile(r"\\'"),"'",group_contents)
            # group_contents = group_contents.strip("'")
            # group_contents = group_contents.replace("'[",'[')
            # group_contents = group_contents.replace("]'",']')
            # words = self.count_document_words(group_contents)
        group_line_word = self.com_db.read(self.com_db.get_translation_dictionary(), {
            "word": words
        }, limit=None, select="id")

        group_line_word = [str(id[0]) for id in group_line_word]
        linked_count = len(group_line_word)
        group_line_word = ",".join(group_line_word)
        # print(group_line_word)
        self.com_db.update(self.com_db.get_translation_group(), {
            "link_words": group_line_word,
            "include_words": json.dumps(words),
        }, condition)
        group_info = f"success {linked_count} linked."
        result = self.com_util.print_result(data=group_info)
        return result

    def group_doctran_list(self, doc):
        doc_content = self.com_db.decode(doc)
        sentences = json.loads(doc_content)
        sentences = self.com_util.clear_value(sentences)
        sentence_content = "\n".join(sentences)
        pattern = re.compile(r'\(\s+\)')
        sentence_content = re.sub(pattern, "", sentence_content)
        pattern = re.compile(r'\(\s+')
        sentence_content = re.sub(pattern, "(", sentence_content)
        pattern = re.compile(r'\s+\)')
        sentence_content = re.sub(pattern, ")", sentence_content)
        pattern = re.compile(r'\\\s+[nN]')
        sentence_content = re.sub(pattern, "\n", sentence_content)
        pattern = re.compile(r'\,+')
        sentence_content = re.sub(pattern, ",\n", sentence_content)
        pattern = re.compile(r'\，+')
        sentence_content = re.sub(pattern, ",\n", sentence_content)
        pattern = re.compile(r'\.+')
        sentence_content = re.sub(pattern, ".\n", sentence_content)
        pattern = re.compile(r'\。+')
        sentence_content = re.sub(pattern, ".\n", sentence_content)
        pattern = re.compile(r'\？+')
        sentence_content = re.sub(pattern, "?\n", sentence_content)
        pattern = re.compile(r'\?+')
        sentence_content = re.sub(pattern, "?\n", sentence_content)
        pattern = re.compile(r'\!+')
        sentence_content = re.sub(pattern, "!\n", sentence_content)
        pattern = re.compile(r'\！+')
        sentence_content = re.sub(pattern, "!\n", sentence_content)
        pattern = re.compile(r'\;+')
        sentence_content = re.sub(pattern, ";\n", sentence_content)
        pattern = re.compile(r'\；+')
        sentence_content = re.sub(pattern, ";\n", sentence_content)
        pattern = re.compile(r'\n+')
        sentences_list = re.split(pattern, sentence_content)
        return sentences_list

    def get_trans_groups(self, user=None):
        groups = self.com_db.read(self.com_db.get_translation_group(), {
            'u_group': user
        }, select="id,u_group,group_n,language,last_time,read,time,count", sort="id ASC")
        return groups

    def get_trans_groupnames(self, user=None, index=2):
        groups = self.get_trans_groups(user)
        groupnames = [name[index] for name in groups]
        return groupnames

    def load_local_transwords(self, flask=None, user=None, force=False):
        translate_dir = self.com_config.get_public('translate_file')
        translate_types = os.listdir(translate_dir)
        word_acount = {
            'loaded': 0,
            'info': [],
        }
        if user == None and flask != None:
            user = flask.flask_request.args.get('user')
        for file_type in translate_types:
            file_type_dir = os.path.join(translate_dir, file_type)
            self.encoding_to(file_type_dir)
            translate_files = os.listdir(file_type_dir)
            for file in translate_files:
                file = os.path.join(file_type_dir, file)
                if self.com_file.isfile(file):
                    file = self.com_file.rename_remove_space(file)
                    t_group = os.path.basename(file)
                    if self.is_group(t_group) == False:
                        file_content = self.com_file.read_file(file, encoding="utf-16le")
                        if file_type == "str":
                            file_content = self.com_file.srt(file)
                        result = self.put_group(None, file_content, t_group=t_group, user=user, file_type=file_type,
                                                start_thread=False)
                        word_acount['info'].append(f"group: {t_group} - {result}")
                    else:
                        self.com_util.print_info(f"group {t_group} exists.")
        # 启动线程翻译
        # self.thread_translate(wait=False)
        result = self.com_util.print_result(data=word_acount)
        return result

    def get_trans_words(self, flask):
        try:
            limit = flask.flask_request.args.get("limit")
        except:
            limit = (0, 1000)
        words = self.get_words_db(limit)
        result = self.com_util.print_result(data=words)
        return result

    def put_translate_words(self, flask):
        doc = flask.flask_request.form.get("doc")
        t_group = flask.flask_request.form.get("t_group")
        message = "no form %s parameter"
        if not doc:
            message = message % "doc"
            return self.com_util.print_info(message)
        if not t_group:
            message = message % "t_group"
            return self.com_util.print_info(message)

        result = self.add_wordtodictinary(doc)
        # 启动线程翻译
        # self.thread_translate(wait=False)
        result = self.com_util.print_info(result)
        # 启动一个线程用于翻译
        return result

    def retranslate_word(self, flask):
        words = flask.flask_request.form.get("words")
        words = self.count_document_words(words)
        if words == None:
            result = f"no {words} need by re-translate"
            result = self.com_util.print_result(data=result)
            return result
        self.not_translatedtoqueue(words)
        result = f"{words} add to translate-tasks"
        result = self.com_util.print_result(data=result)
        return result

    def trans_word(self, flask, word=None, trans=None, image=None, voice=None):
        result = f"{word} has been submitted for background translation"
        sample_images = None
        voice_files = None
        if word == None:
            word = flask.flask_request.form.get("word")
            trans = flask.flask_request.form.get("trans")
            sample_images = flask.flask_request.form.get("sample_images",None)
            voice_files = flask.flask_request.form.get("voice_files",None)
        word = self.com_string.clear_string(word)
        if word == "" or word == None:
            message = "Need a word"
            return self.com_util.print_info(message)
        if trans == None:
            self.delete_word(word)
        # self.com_translate.update_translate_db({
        #     "word": word,
        #     "translate_bing": trans,
        # })
        for key,val in flask.flask_request.form.items():
            print(type(val) ,val)
        # print(trans)
        # if sample_images != None:
        #     print(sample_images)
        # if voice_files != None:
        #     print(voice_files)
        return result

    def delete_word(self,word,info=True):
        translation_dictionary = self.com_db.get_translation_dictionary()
        if info == True:
            self.com_util.print_warn(f"not translated {word} and delete one.")
        self.com_db.delete(translation_dictionary, {
            "word": word
        })

    def put_bing_translation_field(self, flask):
        try:
            word = flask.flask_request.form.get("word")
            translate_field = flask.flask_request.form.get("translate_field")
            mobile = flask.flask_request.form.get("mobile")
        except:
            return None
        word = {
            "word": word,
            "translate_bing": translate_field,
        }
        result = self.update_translate_db(word)
        result = self.com_util.print_info(result)
        return result

    def get_word(self, flask, word=None):
        if word == None:
            word = flask.flask_request.args.get("word")
        word_trans = self.com_db.read(self.com_db.get_translation_dictionary(), {
            'word': word
        })
        result = self.com_util.print_result(data=word_trans)
        return result

    def get_group(self, flask, group_id=None, load_eudic=None):
        limit = None
        read_time = None
        if group_id == None:
            group_id = flask.flask_request.args.get("group_id")
            limit = flask.flask_request.args.get("limit")
            load_eudic = flask.flask_request.args.get("load_external")
            read_time = flask.flask_request.args.get("read_time")
        if not limit:
            limit = (0, 1000)

        eudic_group_name = self.com_api.get_eudic_groupname()
        if load_eudic == eudic_group_name:
            eudic_group = self.is_group(eudic_group_name)
            is_updateeudict = False
            if eudic_group == False:
                is_updateeudict = True
            else:
                last_time = eudic_group[4]
                # group_id = eudic_group[0]
                today_time = self.com_string.create_time("%Y-%m-%d")
                last_time = last_time.split(" ")[0]
                equel_time = self.com_util.equal_time(last_time, today_time, "%Y-%m-%d")
                if equel_time:
                    is_updateeudict = True
            if is_updateeudict:
                self.com_util.print_info(f"update {load_eudic}")
                file_content = self.com_api.get_eudic_words()
                file_content = " ".join(file_content)
                self.put_group(None, file_content=file_content, t_group=eudic_group_name, file_type="doc")

        link_words = self.com_db.read(self.com_db.get_translation_group(), {
            'id': group_id
        }, select="link_words")
        translation_dictionary = self.com_db.get_translation_dictionary()

        if len(link_words) > 0:
            link_words = re.sub(re.compile(r'[^0-9\,]'), "", link_words[0][0]).split(",")
            condition = {
                'id': link_words
            }
            if read_time.find("-") != -1:
                condition['read_time'] = f"%{read_time}%"
            count_sql = self.com_db.count(translation_dictionary, condition, select="id",return_sql=True)
            unread_count = self.com_db.count(translation_dictionary, {'id': link_words,'read_time':None}, select="id")
            group_words = self.com_db.read(translation_dictionary, condition, select="*", limit=limit,
                                           sort={
                                               "read_time": "ASC",
                                               "read": "ASC",
                                           },
                                           select_as ={
                                               "count": count_sql,
                                               "unread": unread_count
                                           },
                                           print_sql = False)
        else:
            self.com_util.print_warn(f"group {link_words} not found")
            group_words = []
        result = self.com_util.print_result(data=group_words)
        return result

    def get_review(self, flask, read_time=None):
        limit = (0, 100)
        if read_time == None:
            read_time = flask.flask_request.args.get("read_time")
            limit = flask.flask_request.args.get("limit")

        condition = {}
        condition['read_time'] = f"%{read_time}%"
        group_words = self.com_db.read(self.com_db.get_translation_dictionary(), condition, select="*", limit=limit,
                                       sort={
                                           "read_time": "ASC",
                                           "read": "ASC",
                                       })
        result = self.com_util.print_result(data=group_words)
        return result

    def get_review_count(self, flask, group_id=None):
        if group_id == None:
            group_id = flask.flask_request.args.get("group_id")
        read_time = flask.flask_request.args.get("read_time")
        translation_dictionary = self.com_db.get_translation_dictionary()
        condition = {
            'read_time': f"%{read_time}%"
        }
        count = self.com_db.count(translation_dictionary, condition)
        result = self.com_util.print_result(data=count)
        return result

    def get_review_allcount(self, flask, group_id=None):
        if group_id == None:
            group_id = flask.flask_request.args.get("group_id")
        read_times = flask.flask_request.args.get("read_time")
        if read_times == None or type(read_times) != int:
            read_times = 30
        day = 60*60*24
        date_timestamp = self.com_util.date_totimestamp()
        read_times = date_timestamp - ( read_times * day )
        translation_dictionary = self.com_db.get_translation_dictionary()
        count_select = {}
        while date_timestamp > read_times:
            review_day = self.com_util.timestamp_todate(date_timestamp)
            review_day = review_day.split(' ')[0]
            condition = {
                'read_time': f"%{review_day}%"
            }
            count_sql = self.com_db.count(translation_dictionary, condition, select="id",return_sql=True)
            k = review_day.replace("-","_")
            count_select[k] = count_sql
            date_timestamp -= day
        count_select = self.com_db.count(translation_dictionary, conditions={
            'id':1,# 是为了不查出过多的数据以免数据过大
        }, select_as=count_select,)
        result = self.com_util.print_result(data=count_select)
        return result

    def get_idcondition(self, idname, default_key="group_n", is_groupcondition=False, user=None):
        is_num = re.compile(r'^\d+$')
        if is_num.search(idname) != None:
            condition = {
                "id": idname
            }
        else:
            condition = {
                default_key: idname
            }
        if is_groupcondition:
            condition["u_group"] = user
        return condition

    def is_group(self, t_group, user=None):
        condition = self.get_idcondition(t_group, user=user, is_groupcondition=True)
        groups = self.com_db.read(self.com_db.get_translation_group(), conditions=condition, result_object=True)
        if len(groups) == 0:
            return False
        return groups[0]

    def put_word(self, flask, word=None, group_nameid=None, reference_url=None):
        if word == None:
            word = flask.flask_request.args.get("word")
            reference_url = flask.flask_request.args.get("reference_url")
            group_nameid = flask.flask_request.args.get("group")
        if not word:
            message = f"no word,word {word}"
            message = self.com_util.print_result(data=message)
            return message
        if not group_nameid:
            message = f"no group_nameid,group_nameid {group_nameid}"
            message = self.com_util.print_result(data=message)
            return message
        result = self.update_oraddgroup(group_nameid, word)

        if not (type(result) == str and result.find("is existing") != -1):
            self.put_notebook(None, word, reference_url)
        notebook_count = self.notebook_count(inline=True)
        if type(result) == str:
            result = {
                "message": result[0:60]
            }
        result["notebook_count"] = notebook_count
        result = self.com_util.print_result(data=result)
        return result

    def notebook_count(self, flask=None, group_id=None, user_id=None, reference_url=None, inline=False):
        if flask != None:
            reference_url = flask.flask_request.args.get("reference_url")
            group_id = flask.flask_request.args.get("group_id")
            user_id = flask.flask_request.args.get("user_id")
        notebook_count = self.com_db.count(self.com_db.get_translation_notebook(), {
            "time": f'%{self.com_string.create_time("%Y-%m-%d")}%',
            "group_id": group_id,
            "user_id": user_id,
        })
        if inline == True:
            return notebook_count
        result = self.com_util.print_result(data=notebook_count)
        return result

    def put_notebook(self, flask, word=None, reference_url=None, group_id=None, user_id=None):
        if word == None:
            word = flask.flask_request.args.get("word")
            reference_url = flask.flask_request.args.get("reference_url")
            group_id = flask.flask_request.args.get("group_id")
            user_id = flask.flask_request.args.get("user_id")

        local_word = self.com_db.read(self.com_db.get_translation_dictionary(), {"word": word})
        if local_word == None or len(local_word) == 0:
            message = f"'{word}' does not exist in the dictionary"
            self.com_util.print_warn(message)
            message = self.com_util.print_result(data=message)
            return message
        else:
            word_id = local_word[0][0]

            notebook = {
                "group_id": group_id,
                "user_id": user_id,
                "word_id": word_id,
                "reference_url": reference_url,
            }
            self.com_db.save(self.com_db.get_translation_notebook(), notebook)
            message = f"'{word}' add to notebook"
            self.com_util.print_info(message)
            message = self.com_util.print_result(data=message)
            return message

    def update_oraddgroup(self, t_group, doc, file_type="doc", user=None):
        groug = self.is_group(t_group)
        add = True
        if groug != False:
            add = False
            include_words = groug[7]
            doc = self.com_util.to_english_array(doc)
            exists_word = []
            exists_all = True
            for word in doc:
                if word in include_words:
                    exists_word.append(word)
                else:
                    exists_all = False
                    include_words.append(word)
            if exists_all:
                exists_word = ",".join(exists_word)
                result = f"word {exists_word} is existing"
                return result
            doc = " ".join(include_words)
        if type(doc) == list:
            doc = " ".join(doc)
        words = self.count_document_words(doc)
        include_words = words
        srt = doc
        if file_type != "srt":
            srt = self.com_util.to_english_array(srt)
            include_words = srt
        include_words = self.com_util.unique_list(include_words)
        words_len = len(include_words)
        doc_words = self.document_to_words(words)
        serial = json.dumps(srt)
        group_data = {
            "include_words": include_words,
            "origin": serial,
            "count": words_len,
            "group_type": file_type,
        }
        condition = self.get_idcondition(t_group)
        if add == True:
            self.com_util.print_info(f"add {t_group} to groups")
            group_data["group_n"] = t_group
            group_data["language"] = "en"
            group_data["u_group"] = user
            # self.com_util.pprint(group_data)
            self.sava_to_db(group_data, "group")
        else:
            self.com_util.print_info(f"update {t_group} of group")
            group_data["last_time"] = self.com_string.create_time()
            self.com_db.update(self.com_db.get_translation_group(), group_data, conditions=condition)
        self.add_wordtodictinary(doc_words)
        result = self.group_link_word(flask=None, group_id=t_group)
        return result

    def get_not_translated(self,flask=None,group_id=None):
        words = self.read_not_translated()
        result = self.com_util.print_result(data=words)
        return result

    def put_group(self, flask, file_content=None, t_group=None, user=None, file_type="doc", start_thread=True):
        if t_group == None or file_content == None:
            t_group = flask.flask_request.form.get("group_name")
            file_content = flask.flask_request.form.get("doc")
            file_type = flask.flask_request.form.get("type")
            user = flask.flask_request.form.get("user")
        if t_group == None or file_content == None:
            message = f"group_name {t_group} error or doc content."
            result = self.com_util.print_result(data=message)
            return result
        t_group = self.com_string.clear_string(t_group)
        if t_group == "":
            t_group = self.com_api.get_eudic_groupname()
        result = self.update_oraddgroup(t_group, file_content, file_type, user)
        result = self.com_util.print_result(data=result)
        # if start_thread:
        #     self.thread_translate(wait=False, headless=True)
        return result

    def get_groups(self, flask, user=None):
        linked = None
        if user == None:
            user = flask.flask_request.args.get("user")
            linked = flask.flask_request.args.get("linked")
        groups = self.get_trans_groups(user)
        if linked and linked != None:
            for group in groups:
                group_id = group[0]
                self.group_link_word(flask=None, group_id=group_id)
        result = self.com_util.print_result(data=groups)
        return result

    def submit_haveread(self, flask, user=None):
        if user == None:
            user = flask.flask_request.args.get("user")
        word = flask.flask_request.args.get("word")
        read = flask.flask_request.args.get("read")
        if read.startswith("+") == -1 and read.startswith("-") == -1:
            read = "+0.2"
        groups = self.com_db.update(self.com_db.get_translation_dictionary(), {
            "read": read,"read_time": self.com_string.create_time(),
        }, {"word": word, })
        result = self.com_util.print_result(data=groups)
        return result

    def doc_to_voice(self, flask, doc=None, user=None):
        if doc == None:
            docs = self.com_db.read(self.com_db.get_translation_group(), {}, select="*")
        else:
            docs = [doc]
        for doc in docs:
            group_name = doc[1]
            doc_content = doc[7]
            sentences_list = self.group_doctran_list(doc_content)
            sentences_list = self.group_doc_filtervoicelists(sentences_list)
            for sentence in sentences_list:
                pass
                # print(sentence)
            print(len(sentences_list))
            break
        # result = self.to_voice(sentence)
        return docs

    def google_translate(self, flask):
        sentence = flask.flask_request.args.get("word")
        dest = flask.flask_request.args.get("dest")
        src = flask.flask_request.args.get("src")
        if dest == None:
            dest = "zh-CN"
        if src == None:
            src = "en"
        # read = flask.flask_request.args.get("read")
        result = self.translate_from_google(sentence, dest=dest, src=src, )
        # result = self.com_translate.translate_from_google(sentence,dest="zh-CN",src="en",)
        result = self.com_util.print_result(data=result)
        return result

    def debug(self, flask):
        print(self.com_selenium.get_current_url())

        return {
            "debug": True
        }
