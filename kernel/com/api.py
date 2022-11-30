import time

from kernel.base.base import *
import os
import json
import re


class Api(BaseClass):
    __eudit_authorization = "NIS q6Ub38GX5BPuUaOO+cm2rcVwrmTzimxzXIxIICziWCx+eyn0n52uiA=="


    def __init__(self,args=None):
        pass

    def get_eudic_groupname(self):
        return f"default_notebook"

    def get_eudic_category(self):
        data = {
            "language":"en",
        }
        api = f"https://api.frdic.com/api/open/v1/studylist/category"
        category = self.eudic_get(api,data)
        category = category["data"][0]
        name = category["name"]
        id = category["id"]
        category = {
            "name":name,
            "id":id,
        }
        return category

    def get_eudic_words(self,id=None,page_id=1,page_size=1000):
        if id == None:
            eudic = self.get_eudic_category()
            # group_name = eudic.get("name")
            id = eudic.get("id")
        data = {
            "id":id,
            "language":"en",
            # "page":page_id,
            "page_size":page_size,
        }
        api = f"https://api.frdic.com/api/open/v1/studylist/words/{id}"
        data = self.eudic_get(api,data)
        data = data["data"]
        words = []
        for datum in data:
            word = datum.get("word").lower()
            words.append(word)
        return words

    def eudic_get(self,url,data):
        result = self.com_http.get(url, data=data,headers={'Authorization': self.__eudit_authorization})
        result = result.replace('\\', '\\\\')
        result = json.loads(result)
        return result

    def update_ip_towebsitelisten(self):
        if self.load_module.is_windows():
            th = self.com_thread.create_thread("com",target=self.update_ip_towebsite)
            th.start()

    def update_ip_towebsite(self,args=None,parse_record=None,headless = True):
        update_interval = 60*1#min
        def get_domainaccount():
            account_text = "temp/west_account.txt"
            west_account_file = self.com_config.get_public(account_text)
            west_account = self.com_file.read(west_account_file)
            account = re.split(r'\n+',west_account)
            account = [s.strip() for s in account]
            result = {}
            result["user"] = account[0]
            result["pwd"] = account[1]
            return result

        def login_domainmanageweb():
            account = get_domainaccount()
            try:
                self.com_selenium.send_keys('#J_loginPage_u_name',account["user"])
                self.com_selenium.send_keys('#J_loginPage_u_password',account["pwd"])
                self.com_selenium.click('.g-common-btn.g-blue-btn[type="submit"]')
            except Exception as e:
                self.com_util.print_warn(e)

        def analyze_domain(parse_record):
            analyze_url = 'https://www.west.cn/manager/domainnew/rsall.asp?domainid=15030234'
            self.com_selenium.open(analyze_url,headless=headless)
            row_selector = '.el-table__row'
            time.sleep(3)
            table_row = self.com_selenium.find_text_content_list(row_selector, html_split=True)
            if len(table_row) == 0:
                time.sleep(3)
                login_domainmanageweb()
                analyze_domain(parse_record)
                return
            if parse_record == None:
                parse_record = ['local', 'api.local']
            def check_row(row):
                for record in parse_record:
                    record = record.strip()
                    row = row.strip()
                    if row.find(record) != -1 and len(row) == len(record):
                        return True
                return False

            indexlist = []
            print(table_row)
            for index in range(len(table_row)):
                row = table_row[index]
                record = row[0]
                record = record.strip()
                if check_row(record) == True:
                    indexlist.append(index)
            modifier = "('a')[1].click()"
            modifier_confirm = f"('button')[0].click()"
            for index in indexlist:
                selector = f"document.querySelectorAll(`{row_selector}`)[{index}].querySelectorAll"
                modifier_js = selector + modifier
                self.com_selenium.execute_js(modifier_js)
                ipaddress_selector = f'//*[@id="pane-dnsrecord"]/div[3]/div[3]/table/tbody/tr[{index + 1}]/td[5]/div/span/div/input'
                ipaddress = self.com_selenium.find_element(ipaddress_selector)
                ipaddress.clear()
                ipaddress.send_keys(ip)
                modifier_confirm_js = selector + modifier_confirm
                self.com_selenium.execute_js(modifier_confirm_js)
            self.com_selenium.click('.el-button.el-button--primary.el-button--medium:first-child')

        while True:
            self.com_util.print_info(f"listen ip_address change and update to westIDC.")
            ip = self.com_http.get_remote_ip(headless=headless)
            if type(ip) != list:
                self.com_util.print_warn(f"ipAddress {ip} get error.")
                time.sleep(update_interval)
                continue
            ip = ip[0]
            ip_temp = self.com_config.get_public('temp/ip_temp.txt')
            preip = self.com_file.read(ip_temp)
            if ip == preip:
                # self.com_selenium.quit()
                self.com_util.print_info(f"ipAddress {ip} has been modified.")
                time.sleep(update_interval)
                continue
            analyze_domain(parse_record)
            self.com_file.save(ip_temp,ip,overwrite=True)
            time.sleep(update_interval)

    def router_control(self):
        url = "http://192.168.2.1"
        password = ""

    def get_static_files(self,flask=None):
        file = flask.flask_request.args.get('file')
        content = None
        if file != None:
            file = self.load_module.get_control_dir(f'html/{file}')
            content = self.com_file.read(file)
        result = self.com_util.print_result(data=content)
        return result
