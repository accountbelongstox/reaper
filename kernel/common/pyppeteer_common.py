from kernel.base.base import *
import re
import time
import os
import asyncio
from pyppeteer import launch
from pyppeteer import chromium_downloader


class PyppeteerCommon(BaseClass):

    def __init__(self,args):
        pass

    async def test(self):
        print("test")
        browser = await launch({'headless': False, 'ignoreHTTPSErrors':True, 'args': ['--disable-infobars', '--window-size=1920,1080', '--no-sandbox']})
        page = await browser.newPage()
        await page.evaluateOnNewDocument('''() =>{ Object.defineProperties(navigator,{ webdriver:{ get: () => false } }) }''')
        await page.goto('https://www.douyin.com')
        # login_key = await page.Jx('//*[@id="J_SubmitStatic"]')
        # login_key = await page.querySelectorAll('.dy-account-close')
        # await page.waitForNavigation()
        # await login_key[0].click()
        asyncio.wait(
            [page.waitForNavigation(),page.querySelectorAll('.dy-account-close').click()]
        )
        asyncio.sleep(3)
        # await page.screenshot({'path': 'example.png'})
        # await browser.close()