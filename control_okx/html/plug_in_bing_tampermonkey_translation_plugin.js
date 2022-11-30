// ==UserScript==
// @name         Bing在线词典工具
// @namespace 	 accountbelongstox@163.com
// @version      0.1
// @description  自动翻译词汇并生成网页供浏览.
// @author       accountbelongstox@163.com
// @match        *://www.bing.com/dict*
// @match        *://*.bing.com/dict*
// @license      AGPL License
// @grant        GM_download
// @grant        GM_openInTab
// @grant        GM_setValue
// @grant        GM_getValue
// @grant        GM_deleteValue
// @grant        GM_xmlhttpRequest
// @grant        GM_addStyle
// @grant        unsafeWindow
// @grant        GM_setClipboard
// @grant        GM_getResourceURL
// @grant        GM_getResourceText
// @grant        GM_info
// @grant        GM_registerMenuCommand
// @grant        GM_cookie
// ==/UserScript==

(function() {
    'use strict';
    let logo_imgbase64 = `https://api.12gm.com/static/image/bing_translate_logo.jpg`;
    let window_html =`
            <div class="b_focus" id="my_bing" style="
                                    width: 100%;
                                    align-content: center;
                                    padding-left: 20px;
                                    /* margin-top: 10px; */
                                    top: 0px;
                                    height: 50px;
                                    z-index: 10000;
                                    position: fixed;
                                    background: #fff;
                                    padding: 5px 0 0 5px;
            ">
                <div class="b_searchboxForm" style="
                                            width: 98%;
                                            float: left;
                    ">
                <textarea id="my_bing_words_translate" style="
                                                        float: left;   
                                                        min-width: auto;
                                                        width: 150px;
                                                        border: none;
                                                        outline: none;
                                                        -webkit-appearance: none;
                                                        z-index: 1;
                                                        display: inline-block;
                                                        -webkit-box-flex: 1;
                                                        -moz-box-flex: 1;
                                                        -webkit-flex: 1 0;
                                                        flex: 1 0;
                                                        -webkit-tap-highlight-color: transparent;
                                                        -webkit-hyphens: manual;
                                                        padding: 0 7px 0 12px;
                                                        resize: none;
                                                        overflow: hidden;
                                                        border-top: 7px solid transparent;
                                                        border-bottom: 7px solid transparent;
                                                        margin: 3px 0;
                                                        word-break: break-all;
                " value="" autocapitalize="off" autocorrect="off" autocomplete="off" spellcheck="false">            </textarea>
                <a class="sh_s" id="my_bing_dictionary" href="javascript:void(0);" style="background-image: url(${logo_imgbase64});
                                                            width: 20%;
                                                            height: 44px;
                                                            padding: 0;
                                                            margin: 0;
                                                            background-size: 100%;
                                                            background-repeat: no-repeat;
                                                            background-position-y: center;
                                                            display: block;
                                                            border: none;
                "></a>
                </div>
                <div id="my_bing_output_info" style="float: left;"></div>
            </div>
        `
        ;
        let down_html = `
        <div style="display: block;z-index: 1050;position: fixed;width: 60px;right: 7px;bottom: 26px;height: 55px; background-image:url(http://cn.bing.com/th?id=OJ.ZxGeQT9xvsaIcA&pid=MSNJVFeeds);background-size:100%">
        <img id="up_transdata_button" style="
        width: 41px;
        /* right: 7px; */
        /* bottom: 26px; */
        float: left;
        padding: 6px 0 0 10px;" src="http://cn.bing.com/th?id=OJ.7JC8lkGQatZjlA&amp;pid=MSNJVFeeds" >
        </div>
        `
        ;
        let up_html = `
        <div style="display: block;z-index: 1050;position: fixed;width: 60px;right: 7px;top: 140px;height: 55px; background-image:url(http://cn.bing.com/th?id=OJ.ZxGeQT9xvsaIcA&amp;pid=MSNJVFeeds);background-size:100%">
        <a href="javascript:void(0)" id="down_transdata_button"  style="
        display: block;
        width: 100%;
        float: left;
        padding: 6px 0 0 10px;
        color: #fff;
        font-weight: bold;
        font-size: 30px;
        line-height: 40px;
        ">Up</a>
        </div>
        `
    let $ = {
            get: function (URL, queryJSON, callback) {
                let xhr;
                if (window.XMLHttpRequest) {
                    xhr = new XMLHttpRequest();
                } else {
                    xhr = new ActiveXObject("Microsoft.XMLHTTP");
                }
                xhr.onreadystatechange = function () {
                    if (xhr.readyState == 4) {
                        if (xhr.status >= 200 && xhr.status < 300 || xhr.status == 304) {
                            callback(xhr.responseText);
                        } else {
                            callback(new Error("AJAX GET did not find the requested file"), undefined);
                        }
                    }
                }
                let querystring = this._queryjson2querystring(queryJSON);
                let joiner
                if (!URL.includes('?')){
                    joiner = "?"
                }else{
                    joiner = "&"
                }

                xhr.open("get", URL + joiner + querystring, true);
                xhr.send(null);
            },
            post: function (URL, queryJSON, callback) {
                let xhr;
                if (window.XMLHttpRequest) {
                    xhr = new window.XMLHttpRequest();
                } else {
                    xhr = new ActiveXObject("Microsoft.XMLHTTP");
                }
                xhr.onreadystatechange = function () {
                    if (xhr.readyState == 4) {
                        if (xhr.status >= 200 && xhr.status < 300 || xhr.status == 304) {
                            callback(xhr.responseText);
                        } else {
                            callback(new Error("AJAX POST did not find the requested file"), undefined);
                        }
                    }
                }
                let querystring = this._queryjson2querystring(queryJSON);
                xhr.open("post", URL, true);
                xhr.setRequestHeader("Content-Type", "application/x-www-form-urlencoded");
                xhr.send(querystring);
            },
            _queryjson2querystring : function(json){
                var arr = [];
                for(var k in json){
                    arr.push(k + "=" + encodeURIComponent(json[k]));
                }
                return arr.join("&");
            }
        }

    ;
    class Bing{
        force_translate = false;
        get_trans_word_index = 2;
        mobile_browser = 0
        base_remote_url = "https://api.12gm.com/"
        data_start = 0
        data_end = 0
        trans_data = []
        transdata_show_step = 30
        remove_redundancy

        constructor() {
        }

        init(){
            this.set_html()
            this.is_mobile_browser()
            let need_to_get_html_word = this.set_need_to_get_word_HTML()
            if(need_to_get_html_word){
                let translate_html = this.get_translate_html()
                this.put_bing_translation_field(need_to_get_html_word,translate_html,(data)=>{
                    this.message(`put_bing_translation_field ${data}`)
                    this.initial_action()
                })
            }else{
                this.initial_action()
            }
        }

        initial_action(){
            let not_wordtranslated = this.not_translated()
            if(not_wordtranslated){
                this.message(`need to be translate ${not_wordtranslated}`)
                this.translate_not_translatedwords(not_wordtranslated)
            }else{
                this.message("Not Translated, the system is ready.")
                this.is_include_area()
                this.listing()
            }
        }

        handling_remote_access_to_information (){
            this.message("handling_remote_access_to_information")
            let not_translated = []
            for(let i=0; i<this.trans_data.length; i++){
                let word = this.trans_data[i]
                if(word[this.get_trans_word_index] == null || this.force_translate){
                    not_translated.push(word[1])
                }
            }
            if(not_translated.length == 0){
                this.add_translate_to_html(true)
            }else{
                this.message(`not_translated ${not_translated}`)
                this.not_translated(not_translated)
                this.translate_not_translatedwords()
            }
        }

        translate_not_translatedwords(word){
            if(!word){
                word = this.not_translated()
            }
            if(!word){
                return
            }else{
                this.translate(word)
            }
        }

        put_bing_translation_field(word,local_html,callback){
            let url = this.remote_url("put_bing_translation_field")
            $.post(url,{
                word: word,
                translate_field: local_html,
                mobile:this.mobile_browser
            },(data)=>{
                if(callback){
                    callback(data)
                }
            })
        }

        not_translated(words){
            let store_key = "not_translated"
            if(words){
                words = words.join(',')
                localStorage.setItem(store_key,words)
            }else{
                let words = localStorage.getItem(store_key)
                if(words){
                    words = words.split(',')
                    let word = words.pop()
                    this.not_translated(words)
                    return word
                }else{
                    return words
                }
            }
        }

        is_mobile_browser(){
            let mobile_match = navigator.userAgent.match(
                /(phone|pad|pod|iPhone|iPod|ios|iPad|Android|Mobile|BlackBerry|IEMobile|MQQBrowser|JUC|Fennec|wOSBrowser|BrowserNG|WebOS|Symbian|Windows Phone)/i
            )
            if (mobile_match){
                this.get_trans_word_index = 2
                this.mobile_browser = 1
            }else{
                this.get_trans_word_index = 3
                this.mobile_browser = 0
            }
        }

        set_html (){
            this.remove('#miniBar')
            document.querySelector('body').insertAdjacentHTML("afterBegin",down_html);
            document.querySelector('body').insertAdjacentHTML("afterBegin",up_html);
            document.querySelector('body').insertAdjacentHTML("afterBegin",window_html);
        }

        remove(selector){
            let ele = document.querySelector(selector)
            if(ele){
                ele.remove()
            }
        }

        put_to_remote_local_vocabulary (callback){
            let doc = this.local_textarea_text();
            doc = doc.trim()
            if(doc){
                let url = this.remote_url('put_translate_words')
                $.post(url,{
                    "doc":doc
                },(data)=>{
                    this.message(`put_to_remote_local_vocabulary ${data}`)
                    if(callback){
                        callback(data)
                    }
                })
            }else{
                this.message(`put_to_remote_local_vocabulary`)
                if(callback){
                    callback()
                }
            }
        }

        get_trans_words (callback){
            let limit = {
                limit:[0,1000]
            }
            let url = this.remote_url('get_trans_words')
            $.get(url,limit,(data)=>{
                try{
                    this.trans_data = JSON.parse(data).data
                }catch (e) {
                    this.message(`get_trans_words请求数据错误不能请求到数据.`)
                }
                if(callback){
                    callback()
                }
            })
        }

        remote_url (method){
            let url = `${this.base_remote_url}/api?method=${method}&key=9LrQN0~14,dSmoO^`;
            return url
        }

        local_textarea_text (text){
            let text_area = document.querySelector('#my_bing_words_translate')
            if(text){
                text_area.value = text
            }else{
                return text_area.value
            }
        }

        set_localStorage (textarea_text) {
            if (textarea_text){
                localStorage.setItem('local_words',textarea_text)
            }else{
                let local_words = localStorage.getItem('local_words')
                this.local_textarea_text(local_words)
            }
        }

        translate (word,callback) {
            document.querySelector('#sb_form_q').value = word
            this.set_need_to_get_word_HTML(word)
            document.querySelector('#sb_form_go').click();
        }

        set_need_to_get_word_HTML(word){
            let need_to_get_word_key = "need_to_get_html_word"
            if(word){
                localStorage.setItem(need_to_get_word_key,word)
            }else{
                let word = localStorage.getItem(need_to_get_word_key)
                localStorage.setItem(need_to_get_word_key,"")
                return word
            }
        }

        get_translate_html(){
            this.remove_redundancy_html()
            let local_html = document.querySelector('.lf_area>div').innerHTML;
            return local_html
        }

        remove_redundancy_html(){
            if(this.remove_redundancy){
                this.message(`remove_redundancy_html has been executed`)
                return
            }
            this.remove_redundancy = true
            this.message(`remove_redundancy_html`)
            let css = ['.df_div','.se_div']
            for(let i = 0; i<css.length; i++){
                let div = document.querySelector(css[i])
                if(div){
                    div.remove()
                }
            }
        }

        transdata_translate_html () {
            let area_data = this.trans_data.slice(this.data_start,this.data_end)
            let local_html = ""
            for (let i =0;i<area_data.length; i++){
                let word = area_data[i];
                local_html += `<div class="qdef">${word[this.get_trans_word_index]}</div>`
            }
            local_html = local_html.replaceAll("&apos;", "'")
            local_html = local_html.replaceAll("&quot;", '"')
            return local_html
        }

        add_translate_to_html (up=true) {
            this.message(`add_translate_to_html`)
            if(up && this.data_end >= this.trans_data.length -1) {
                this.message(`Loading data is full ${this.data_end}>${this.trans_data.length}.`)
                return
            }
            if(!up && this.data_start <= 0) {
                this.message(`Loading data has been zeroed${this.data_start}${this.trans_data.length}.`)
                return
            }
            this.remove_redundancy_html()
            if(this.data_start || this.data_end){
                if(up){
                    this.data_start = this.data_end
                    this.data_end = this.data_start+this.transdata_show_step
                    if(this.data_end >= this.trans_data.length){
                        this.data_end = this.trans_data.length -1
                        this.data_start = this.data_end - this.transdata_show_step
                    }
                }else{
                    this.data_end = this.data_start
                    this.data_start = this.data_end-this.transdata_show_step
                    if(this.data_start < 0){
                        this.data_start = 0
                        this.data_end = this.data_start+this.transdata_show_step
                    }
                }
            }else{
                this.data_start = 0
                this.data_end = this.data_start + this.transdata_show_step
            }
            this.message(`正在添加第${this.data_start},${this.data_end}条.`)
            let local_html = this.transdata_translate_html()
            let lf_area = document.querySelector('.lf_area')
            lf_area.innerHTML = local_html;
            this.message(`${this.data_start},${this.data_end}条(总${this.trans_data.length}条)添加成功.`)
        }

        is_include_area(){
            let lf_area = document.querySelector('.lf_area')
            if(!lf_area){
                this.translate('bing')
            }
        }

        randomString (len=16) {
            len = len || 32;
            var $chars = 'ABCDEFGHJKMNPQRSTWXYZabcdefhijkmnprstwxyz2345678';
            var maxPos = $chars.length;
            var pwd = '';
            for (i = 0; i < len; i++) {
                pwd += $chars.charAt(Math.floor(Math.random() * maxPos));
            }
            return pwd;
        }

        message(message){
            document.querySelector('#my_bing_output_info').innerHTML = message
        }

        //给添加的元素添加监听事件
        listing(){
            document.querySelector('#my_bing_dictionary').addEventListener('click',()=>{
                this.put_to_remote_local_vocabulary(()=>{
                    this.message(`success : put_to_remote_local_vocabulary, then get_trans_words.`)
                    this.get_trans_words((data)=>{
                        this.message(`get_trans_words ${data}`)
                        this.handling_remote_access_to_information()
                    })
                })
            })
            document.querySelector('#my_bing_words_translate').addEventListener('input',()=>{
                let textarea_text = this.local_textarea_text()
                this.set_localStorage(textarea_text)
            })

            document.querySelector('#up_transdata_button').addEventListener('click',()=>{
                this.add_translate_to_html(true)
            })
            document.querySelector('#down_transdata_button').addEventListener('click',()=>{
                this.add_translate_to_html(false)
            })

        }
    }
    let bing = new Bing()
    bing.init()
})();