from queue import Queue
from kernel.base.base import *
import os
import re
import time
import threading

global_thread = {}

class TranslateThread(threading.Thread, BaseClass):
    __result = Queue()
    __words = None
    __word_num = 0
    __number_of_translations = 0
    __info = True
    __count = 0
    __resultList = []
    __save_db = False
    __language = "zh-CN"
    __headless = True
    __debug = False
    __type = "translate"  # "voice
    callback = None

    def __init__(self, args, thread_name=None, daemon=False):
        threading.Thread.__init__(self, name=thread_name, daemon=daemon)
        self.task = args.get('task')
        self.result = args.get('result')
        self.thread_lock = args.get('thread_lock')
        if type(args) == dict:
            if "save_db" in args:
                self.__save_db = args["save_db"]
            if "type" in args:
                self.__type = args["type"]
            if "info" in args:
                self.__info = args["info"]
            if "language" in args:
                self.__language = args["language"]
            if "headless" in args:
                self.__headless = args["headless"]
            if "debug" in args:
                self.__debug = args["debug"]
            if "callback" in args:
                self.callback = args["callback"]

        self.thread_name = thread_name
        # self.__count += self.__queue.qsize()
        # 为了异步调用,将调用于一个单独的队列
        # self.__words = Queue()
        #
        # if type(args) is not list:
        #     words = [args]
        # else:
        #     words = args
        # index = 0
        # for word in words:
        #     if type(word) == str:
        #         word_item = self.word_to_translateobject(word, index=index)
        #         self.__words.put(word_item)
        #     elif word.__class__.__name__ == "Queue":
        #         while word.qsize() > 0:
        #             word_item = word.get()
        #             word_item = self.word_to_translateobject(word_item, index=index)
        #             self.words.put(word_item)
        #     elif word.__class__.__name__ == "dict":
        #         word_item = self.word_to_translateobject(word,index=index)
        #         self.__words.put(word_item)
        #     else:
        #         self.__words.put(word)
        #     index +=1
        # self.__word_num = self.__words.qsize()

    def run(self):
        if self.__type == "translate":
            # if self.__is_running == True:
            self.run_translate()
        elif self.__type == "voice":
            self.run_microsoftvoice()

    def run_translate(self):
        url = f'https://www.bing.com/dict?mkt={self.__language}'
        headless = self.__headless
        self.com_selenium.open(url, width=600,height=400, mobile=False, not_wait=True, headless=headless, wait=1200000)

        self.com_selenium.find_element_by_js_wait("#sb_form_q")
        # translation_dictionary = self.com_db.get_translation_dictionary()
        while True:
            word = self.get_item()
            if word == None:
                #如果翻译完则更新列表
                self.com_translate.not_translatedtoqueue()
            if word == None:
                #更新列表后依然没有翻译任务则休眠
                time.sleep(60)
                continue
            word = word.strip()
            print(f"{word}, thread-name:{self.thread_name}, task:{self.task.qsize()}")
            if word == "":
                continue
            self.com_selenium.send_keys('#sb_form_q', word)
            self.com_selenium.click('#sb_form_go')
            time.sleep(0.2)
            word_trans = self.bing_engine_htmlextracttojson(word=word, debug=self.__debug)
            self.remaining_messages(word, word_trans)
            if self.__save_db:
                if word_trans == None:
                    self.com_translate.delete_word(word,info=False)
                else:
                    self.com_translate.update_translate_db({"word": word,"translate_bing": word_trans,})
            if self.callback != None:
                self.callback(word,word_trans)
            self.com_selenium.close_page()

    def remaining_messages(self, word, trans_result):
        qsize = self.task.qsize()
        if trans_result != None:
            self.com_util.print_info(f"{word} translation successful,also {qsize} words that are not translated.")
        else:
            if self.__save_db:
                self.com_util.print_warn(f"{word} not-translated and delete. also {qsize} task-queue.")
            else:
                self.com_util.print_warn(f"{word} not-translated. also {qsize} task-queue.")

    def get_item(self):
        if self.task.qsize() > 0:
            self.thread_lock.acquire()
            item = self.task.get()
            self.thread_lock.release()
            return item
        return None

    def no_result_wait(self, trans_area):
        results_selector = ".no_results"
        head_strong = ".hd_div strong"
        no_result = self.com_selenium.find_element_by_js(results_selector)
        word = self.com_selenium.find_element_by_js(head_strong)
        wait_max = 30
        index = 0
        while word == None and no_result == None and index < wait_max:
            time.sleep(0.5)
            no_result = self.com_selenium.find_element_by_js(results_selector)
            word = self.com_selenium.find_element_by_js(head_strong)
            if index >= 2:
                trans_text = self.com_selenium.find_text_content_list(trans_area, html_split=True)
                if len(trans_text) != 0:
                    return trans_text
                else:
                    trans_element = self.com_selenium.find_element_by_js(trans_area)
                    if trans_element or trans_element != None:
                        return True
            index += 1
        if index >= wait_max:
            return True
        if no_result == None:
            return False
        return True

    def run_microsoftvoice(self):
        self.microsoft_azure_to_voice()

    def bing_engine_htmlextracttojson(self, word, debug=True):
        trans_area = ".lf_area"
        no_result = self.no_result_wait(trans_area)
        word_trans = {}
        if no_result == True:
            return None
        if no_result != False:
            word_trans["word"] = word
            word_trans["translate_text"] = no_result
            return word_trans

        word = self.com_selenium.find_value_by_js_wait('.hd_div strong', )
        word_trans["word"] = word
        if debug: self.com_util.pprint(f"{word}")

        word_translation = self.com_selenium.find_text_content_list('.qdef .hd_area', "", ".nextSibling.childNodes",
                                                                    html_split=True)
        word_trans["word_translation"] = word_translation
        if debug: self.com_util.pprint(f"\tword_translation {word_translation}")
        try:
            phonetics = self.com_selenium.find_html_by_js('.hd_area [lang]')
        except Exception as e:
            self.com_util.print_warn(f"\t{word} not found phonetic")
            self.com_util.print_warn(e)
            phonetics = None
        if phonetics != None:
            temporary_separator = " -=- "
            pattern = re.compile(r"(?<=\]).+?(?=http)")
            phonetics = re.split(pattern, phonetics)
            phonetics = temporary_separator.join(phonetics)
            pattern = re.compile(r"(?<=mp3).+?>")
            phonetics = re.split(pattern, phonetics)
            phonetics = temporary_separator.join(phonetics)
            pattern = re.compile(r"<.+?>")
            phonetics = re.split(pattern, phonetics)
            phonetics = temporary_separator.join(phonetics)
            phonetics = phonetics.split(temporary_separator)
            phonetics = self.com_util.clear_value(phonetics)
            phonetic_dict = {}
            voices_srclist = []
            pre_phonetic = None
            for i in range(len(phonetics)):
                phonetic = phonetics[i]
                if self.com_http.is_url(phonetic) == False:
                    pre_phonetic = phonetic
                else:
                    # if phonetic_dict[phonetic] == "":
                    phonetic_dict[phonetic] = {
                        "url": phonetic,
                        "phonetic": pre_phonetic
                    }
                    voices_srclist.append(phonetic)
        else:
            voices_srclist = []
            phonetic_dict = {}

        voice_files = {}
        if len(voices_srclist) > 0:
            for down_url in voices_srclist:
                download = self.com_selenium.down_file(down_url, save=True)
                download = self.get_downs_staticfiles(word, download, file_iterate=phonetic_dict, file_type="voice")
                voice_files[down_url] = download
        #每个语音都添加有道发音
        down_url = "voice_youdao"
        voice_youdao = self.com_translate.youdao_engine_get_voice_file(word)
        download = {
            "save_filename": voice_youdao,
            "url": down_url,
            "dynamic_url": False,
        }
        self.com_util.pprint(f"\tword {word} voice from youdao-engine at {download}")
        download = self.get_downs_staticfiles(word, download, file_iterate=phonetic_dict, file_type="voice")
        voice_files[down_url] = download

        if debug: self.com_util.pprint(f"\tvoice_files_order {voice_files}")
        word_trans["voice_files"] = voice_files

        plural_form = self.com_selenium.find_text_content_list(".qdef .hd_if", "", html_split=True, )
        if debug: self.com_util.pprint(f"\tplural_form {plural_form}")
        word_trans["plural_form"] = plural_form

        sample_image = self.com_selenium.find_text_content_list(".qdef .simg", "img", attribute="src")

        # 线程锁给解开
        downs = {}
        for down_url in sample_image:
            download = self.com_selenium.down_file(down_url,save=True)
            download = self.get_downs_staticfiles(word, download, file_type="images")
            downs[down_url] = download

        if debug: self.com_util.pprint(f"\tsample_images {downs}")
        word_trans["sample_images"] = downs

        synonyms_type = self.com_selenium.find_text_content_list('.wd_div .tb_div h2', deduplication=False)
        if debug: self.com_util.pprint(f"\tsynonyms_type {synonyms_type}")
        word_trans["synonyms_type"] = synonyms_type

        synonyms = self.com_selenium.find_text_content_list('.wd_div .tb_div', "", ".nextSibling.childNodes",
                                                            html_split=True, deduplication=False)
        if debug: self.com_util.pprint(f"\tsynonyms {synonyms}")
        word_trans["synonyms"] = synonyms

        advanced_translate_type = self.com_selenium.find_text_content_list('.df_div .tb_div h2', deduplication=False)
        if debug: self.com_util.pprint(f"\tadvanced_translate_type {advanced_translate_type}")
        word_trans["advanced_translate_type"] = advanced_translate_type

        advanced_translate = self.com_selenium.find_text_content_list('.df_div .tb_div', "", ".nextSibling.childNodes",
                                                                      html_split=True, deduplication=False)
        if debug: self.com_util.pprint(f"\tadvanced_translate {advanced_translate}")
        word_trans["advanced_translate"] = advanced_translate

        return word_trans

    def get_downs_staticfiles(self, word, downitem, file_iterate=None, file_type="voice"):
        index = 0
        url = downitem.get('url')
        down_file = downitem["save_filename"]
        dynamic_url = downitem.get("dynamic_url")
        if down_file == None:
            self.com_util.print_warn(f"{word}, {url} not downloaded.")
        # try:
        file_suffix = self.com_file.file_type(down_file)
        if file_suffix != "":
            file_suffix = f".{file_suffix}"

        # file_iterate_name = self.com_util.get_list_value(file_iterate,index,"")
        file_iterate_name = self.com_util.get_dict_value(file_iterate, url, "")
        if 'phonetic' in file_iterate_name:
            file_iterate_name = file_iterate_name['phonetic']
            downitem["iterate_name"] = file_iterate_name
        if file_iterate_name == "":
            file_iterate_name = str(index)
        file_iterate_name = re.sub(re.compile(r"\&.+$"), "", file_iterate_name)
        static_file = self.com_translate.bing_engine_get_static_file(word, "", file_iterate_name, file_suffix,
                                                                    file_type=file_type,dynamic_url=dynamic_url)
        try:
            self.com_file.cut(down_file, static_file)
            self.com_util.print_info(f"down_file cut {static_file} by {down_file}")
        except Exception as e:
            self.com_util.print_warn(down_file)
            self.com_util.print_warn(static_file)
            self.com_util.print_warn(f"{word} downs_statistics error")
            self.com_util.print_warn(e)
        static_folder = self.com_config.get_global("flask_template_folder")
        save_name = static_file.split(static_folder)[1]
        save_name = self.com_string.dir_normal(save_name, linux=True)
        downitem["save_filename"] = save_name
        # except Exception as e:
        #     self.com_util.print_warn(f"translate_downs staticfiles error")
        #     self.com_util.print_warn(e)
        return downitem

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

    def done(self):
        if self.task.qsize() == 0:
            return True
        else:
            return False

    def result(self):
        self.__count = 0
        result = self.resultList
        self.resultList = []
        return result
    #
    # def word_to_translateobject(self,word,default_engine="google_cn",from_is="en",to="zh-cn",callback=None,index=0):
    #     if type(word) == str:
    #         word_dict = {
    #             "word": word
    #         }
    #     else:
    #         word_dict = word
    #
    #     if "from_is" not in word_dict:
    #         word_dict["from_is"] = from_is
    #     if "to" not in word_dict:
    #         word_dict["to"] = to
    #     if "engine" not in word_dict:
    #         word_dict["engine"] = default_engine
    #     if "callback" not in word_dict:
    #         word_dict["callback"] = callback
    #     if "index" not in word_dict:
    #         word_dict["index"] = index
    #     return word_dict

    #
    # def run(self):
    #     print(self.com_selenium)
    #     return
    #     while self.__words.qsize() > 0:
    #         word_translateobject = self.__words.get()
    #         word = word_translateobject.get("word")
    #         to = word_translateobject.get("to")
    #         index = word_translateobject.get("index",0)
    #         from_is = word_translateobject.get("from_is")
    #         callback = word_translateobject.get("callback")
    #         engine = word_translateobject.get("engine")
    #         if engine == "google":
    #             result = self.com_translate.translate_from_google(word=word,from_is=from_is,to=to,callback=None)
    #         elif engine == "google_cn":
    #             result = self.com_translate.translate_from_google_cn(word=word,from_is=from_is,to=to,callback=None)
    #         elif engine == "baidu":
    #             result = self.com_translate.translate_from_baidu(word=word,from_is=from_is,to=to,callback=None)
    #         elif engine == "youdao":
    #             result = self.com_translate.translate_from_youdao(word=word,from_is=from_is,to=to,callback=None)
    #         else:
    #             # No translation engine defaults to google
    #             result = self.com_translate.translate_from_google(word=word,from_is=from_is,to=to,callback=None)
    #         # 给翻译结果添加上编号
    #         try:
    #             result["index"] = index
    #             self.result.put(result)
    #             if callback is not None:
    #                 callback(result)
    #         except:
    #             print(f"Word {word} translation failure results is {result}.")
    #         self.__number_of_translations+=1
    #
    # def done(self):
    #     is_done = (self.__number_of_translations == self.result.qsize() and self.__words.qsize() == 0)
    #     return is_done
    #
    # def result(self):
    #     # while self.done() is False:
    #     #     time.sleep(1)
    #     return self.result
    # def all_results(self):
    #     while self.done() is False:
    #         time.sleep(1)
    #     return self.result
