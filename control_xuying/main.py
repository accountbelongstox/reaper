from kernel.base.base import *
import json
class Main(BaseClass):
    def __init__(self, argv):
        pass

    def main(self, argv):
        #需要测试的代码
        # result = self.translate_common.translate_from_google_cn("测试","en","zh-CN")
        result = self.thread_common.create_thread(thread_type="selenium",thread_name="text",args=self.config)
        result.start()
        # print(result)
        # self.db_common.get_data_from_sqlite(conditions={"text":"text"})
        # self.db_common.get_data_from_sqlite(conditions=100)
        # json_file = open('./control_douyin/text.json',encoding="utf-8")
        # douyin_config = json.load(json_file)
        # self.db_common.save_data_to_sqlite(data=douyin_config)
        # self.http_common.push_url_user(url='http://www.scflcp.com/stream_5d03c0859ec2f/backend/')
        # self.http_common.push_url_user(url='https://person.17el.cn//Authentication/loadlogin?params=customer')
        # self.http_common.push_url_user(url='http://admin.dlszyht.com/login.php')
        self.http_common.push_url_text(url='https://demo.diyuncms.com/admin.php?s=news&c=home&m=add&catid=0')
        # self.http_common.get_base_down_dir()
        # self.db_common.save_data_to_sqlite()
        pass
