`交易中，每个新高一点的低点，相对于起始低点，但不替换`
`效果结束，替换新低点`
# 框架说明
    - 框架运行在python3.9之下
    - Kernel为整个框架的核心
    - kernel/mode 中的main方法会自动执行
# GoogleDriver Download url is:
    - https://chromedriver.storage.googleapis.com/index.html
    - https://registry.npmmirror.com/binary.html?path=chromedriver/
# 支持命令
    - 
# 依赖包
    - 已移到下面python包安装命令
## 安装openssl
    - mkdir -p /usr/tmp && cd /usr/tmp
    - wget https://www.openssl.org/source/openssl-1.1.1n.tar.gz
    - tar -zxvf openssl-1.1.1n.tar.gz
    - cd openssl-1.1.1n
    - make
    - make install
    - mv /usr/bin/openssl /usr/bin/openssl.bak
    - ln -sf /usr/local/openssl/bin/openssl /usr/bin/openssl
    - echo "/usr/local/openssl/lib" >> /etc/ld.so.conf
    - ldconfig -v
    - openssl version
# linux安装python
    - mkdir -p /usr/tmp && cd /usr/tmp
    - wget https://www.python.org/ftp/python/3.10.4/Python-3.10.4.tgz
    - tar -zxvf Python-3.10.4.tgz
    - cd Python-3.10.4
    - vim Modules/Setup
    - 修改行 line:210  # socket line above, and edit the OPENSSL variable:
    - 修改行 line:211  OPENSSL=/usr/local/openssl
    - 修改行 line:212  _ssl _ssl.c \
    - 修改行 line:213      -I$(OPENSSL)/include -L$(OPENSSL)/lib \
    - 修改行 line:214      -lssl -lcrypto
    - ./configure --enable-optimizations
    - yum -y install openssl-devel bzip2-devel expat-devel gdbm-devel readline-devel zlib-devel
    - make
    - make install
    - wget https://www.python.org/ftp/python/3.9.12/Python-3.9.12.tgz
    - tar -zxvf Python-3.9.12.tgz
    - cd Python-3.9.12
    - ./configure --prefix=/usr/local/python3.9 --enable-optimizations
    - make&&make install
    - ln -s /usr/local/python3.9/bin/python3 /usr/bin/python3.9
    - ln -s /usr/local/python3.9/bin/pip3 /usr/bin/pip3.9
    - yum install python36 python36-devel -y
    - python3.6 -m venv venv
    - touch ~/.pip/pip.conf
    - vim ~/.pip/pip.conf
    - 添加行 [global]
    - 添加行 index-url=http://mirrors.aliyun.com/pypi/simple/
    - 添加行 [install]
    - 添加行 trusted-host=mirrors.aliyun.com
    - cd /www/项目名
    - python3.10 venv -m venv
    - python3.9 venv -m venv
    - source /www/baidub2bwork/tutorial-env/bin/activate
    - paddleocr报错解决
    - 文件：public\liunx_usr_lib64 cp libstdc++.so.6.0.24 /usr/lib64/
    - rm -rf libstdc++.so.6
    - ln -s libstdc++.so.6.0.24 libstdc++.so.6
    - paddleocr "from . core_avx import *"报错解决 https://blog.csdn.net/u010674979/article/details/117224889
# 依赖包
    - python3.9 -m pip3.9 install --upgrade  pip3.9
    - pip3.9 install selenium
    - pip3.9 install redis
    - pip3.9 install requests
    - pip3.9 install pymongo
    - pip3.9 install beautifulsoup4
    - pip3.9 install cssselect
    - pip3.9 install lxml
    - pip3.9 install mimerender
    - pip3.9 install flask    
    - pip3.9 install twisted
    - pip3.9 install pillow
    - pip3.9 install googletrans==4.0.0-rc1
    - pip3.9 install paddlepaddle
    - pip3.9 install shapely
    - pip3.9 install paddleocr
    - pip3.9 install readmdict
    - pip3.9 install pyquery
    - pip3.9 install pyside6
    - tar -zxvf Python-3.10.4.tgz
    - yum-config-manager --add-repo https://download.opensuse.org/repositories/home:/Alexander_Pozdnyakov/CentOS_7/
    - sudo rpm --import https://build.opensuse.org/projects/home:Alexander_Pozdnyakov/public_key
    - yum update
    - yum install tesseract 
    - yum install tesseract-langpack-deu
# linux部署chrome，selenium
    - yum install https://dl.google.com/linux/direct/google-chrome-stable_current_x86_64.rpm
    - yum install mesa-libOSMesa-devel gnu-free-sans-fonts wqy-zenhei-fonts
    - google-chrome --version
    - cd /www/项目名
    - wget https://registry.npmmirror.com/-/binary/chromedriver/103.0.5060.134/chromedriver_linux64.zip
    - unzip chromedriver_linux64.zip
    - mv chromedriver chromedriver_linux64_v103.0.5060.134
    - chmod +x chromedriver_linux64_v103.0.5060.134
# 添加开机启动
    - cd /www/项目名
    - vim start.sh
    - 添加命令： nohup /www/项目名/venv/bin/python3.10 -u /www/项目名/main.py > /www/项目名/out.log 2>&1 &
# 添加开机启动
    - chmod +x start.sh
    - vim /etc/rc.local
    - 添加 /www/项目名/start.sh
    - ps -ef | grep start
    - bt后台设置nginx 域名端口映射(反向代理)
# selenium_common中的一些方法
```
查找元素
find_element (已实现)选择器 返回单个元素,查找到多个元素则选取第一个
查找元素
find_elements (已实现)选择器 返回多个元素
等待元素出现
wait_element (已实现)
查找元素等待
find_element_wait (已实现)
find_elements_by_tagname
find_elements_by_id
find_elements_by_xpath
find_elements_by_css
find_elements_by_tagname

查找元素等待
find_elements_wait (已实现)
统计元素
statistical_elements (已实现)
统计元素
statistical_elements_wait (已实现)
操作元素
action_element(已实现)
查找内容
find_content(已实现)
查找内容等待
find_content_wait(已实现)
查找属性
find_properties(已实现)
查找等待
find_property_wait(已实现)
存在元素
element_exist(已实现)
取得网页
get_html(已实现)
切换页面到
switch_to(已实现)
打开页面
open_url(已实现)
判断页面是否打开完毕
open_ready(已实现)
取得驱动对象
get_driver(已实现)
取得驱动路径
get_driver_path(已实现)
验证码识别
verification_code(已实现)
滑动验证码
verification_sliding(已实现)
文字点击验证码
verification_text_click_code(已实现)
参数：{
"hint":""
"identification_zone":""
"click_zone":"captcha-verify-image",
"submit":""
}
验证码截图
screenshot_of_element(已实现)
网页截图
screenshot_of_webpage(已实现)
载入JQuery
load_jquery(已实现)
取得当前网址
get_current_url(已实现)
执行JS
execute_js(已实现)
执行JS
execute_js_wait(已实现)
执行JS文件
execute_js_file(已实现)
执行JS代码
execute_js_code(已实现)
滑动元素
sliding_element(已实现)
滑动元素
move_element
搜索内容
search_content(已实现)
```

