from queue import Queue

from kernel.base.base import *
#import os
import json
import os.path
import pprint
import time
import datetime
#import time
#from queue import Queue
import re

class Main(BaseClass):
    __ping_website = 'https://ping.chinaz.com'

    def __init__(self,args):
        pass

    def main(self,args):
        self.com_http.website_speedcheck(url=args,headless=False)




