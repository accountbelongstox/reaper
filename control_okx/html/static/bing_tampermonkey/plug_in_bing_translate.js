(() => {
    if (typeof window != 'undefined' && !window.$) {
        window.$ = {
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
                if (!URL.includes('?')) {
                    joiner = "?"
                } else {
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
            _queryjson2querystring: function (json) {
                var arr = [];
                for (var k in json) {
                    arr.push(k + "=" + encodeURIComponent(json[k]));
                }
                return arr.join("&");
            }
        }
    }

    class MyDictClass {
        force_translate = false;
        get_trans_word_index = 2;
        mobile_browser = 0
        data_start = 0
        data_end = 0
        trans_data = []
        remove_redundancy
        defult_group_limit = null
        // defult_group_limit = default_per_words
        default_per_words = 100
        per_dayreadwords = 1000//每天阅读单词任务
        group_info = {}
        showed_word = null//当前显示的项目
        music_players = [] //正在播放元素
        voice_playevent = null //语音播放事件
        voice_autoplaing = null
        maximum_numberofplays = 3
        readed_count = []
        // is_review = null
        is_get_grouping = false
        current_word_id = 0
        current_wordshowed = null
        review_model = null
        tailshowing = null
        //最在复习天数
        max_reviewday = 60
        re_translatewordsarray = []

        constructor() {
           this.load_js([
                "js/pinyin-pro.js"
           ]) 
        }

        set_review() {
            if (this.is_tailshowing()) {
                this.scroll_top()
                this.tailshowing = null
                this.current_wordshowed = null
            }
            // this.is_review = review
            // $('#review').toggleClass('btn_active')
            if (!(this.maximum_numberofplays == 1)) {
                this.maximum_numberofplays = 1
                $('#review').addClass('btn-success')
                $('#review').addClass('btn_active')
            } else {
                this.maximum_numberofplays = 3 + 1
                $('#review').removeClass('btn-success')
                $('#review').removeClass('btn_active')
            }
            // console.log(this.maximum_numberofplays)
        }

        get_defult_group_limit() {
            this.defult_group_limit = `0,${this.default_per_words}`
            return this.defult_group_limit
        }

        init_browser() {
            this.listing_button()
            this.get_groups()
        }

        get_groups() {
            this.info('start fetch groups.')
            let current_group_id = this.get_parameter('gid')
            if (!current_group_id) {
                current_group_id = this.get_cruurent_group('group_id')
            }
            let project_mode = this.get_project_mode()
            this.set_project_bar(project_mode)
            this.get("get_groups").then((result_data) => {
                let group_html = ""
                for (let item of result_data.data) {
                    let group_id = item[0],
                        group_name = item[2],
                        group_language = item[3],
                        group_last_time = item[6],
                        group_count = item[7]
                        ;
                    let group_info = {
                        group_id,
                        group_name,
                        group_language,
                        group_last_time,
                        group_count,
                    }
                    this.group_info[group_id] = group_info
                    if (!current_group_id) {
                        this.set_cruurent_group(group_info)
                        current_group_id = this.get_cruurent_group('group_id')
                    }
                    group_html += `
					<div class="media py-10 px-0" >
					  <a class="avatar avatar-lg status-success" data-groupid="${group_id}" onclick="MyDict.get_group(this)" href="javascript:">
						<img src="static/picture/cor-logo-3.png" alt="...">
					  </a>
					  <div class="media-body">
						<p class="font-size-16">
						  <a class="hover-primary" href="javascript:" data-groupid="${group_id}" onclick="MyDict.get_group(this)"><strong>${group_name}</strong></a>
						</p>
						<p>
                        <code>${group_language}</code>, <code>${group_count}</code></p>
						  <span>${group_last_time}</span>
					  </div>
					</div>
					`
                }
                this.info('groups fetch success')
                $('.media-list.media-list-hover.mt-20').html(group_html)
                this.set_groups_info(this.group_info)
                if (current_group_id) this.get_group(current_group_id)
            })

        }

        get_parameter(name) {
            var reg = new RegExp("(^|&)" + name + "=([^&]*)(&|$)");
            var r = window.location.search.substr(1).match(reg);
            if (r != null) {
                return decodeURI(r[2]);
            }
            return null;
        }

        get_group(group_id, limit, read_time, callback) {
            if (this.is_get_grouping) {
                return
            }
            this.readed_count = []
            this.is_get_grouping = true
            let group_type = typeof group_id
            if (group_type != "string" && group_type != "number") {
                group_id = group_id.dataset.groupid
            }
            this.info(`request group_id ${group_id} data.`)
            limit = this.get_limit(group_id,limit)
            this.set_cruurent_group(group_id)
            let group_info = this.get_groups_info(group_id)
            if (!group_info) {
                this.is_get_grouping = false
                alert('当前组不存在.')
                return
            }
            let group_name = group_info.group_name
            let page_count = Math.floor(group_info.group_count / this.default_per_words)
            $(".page_count").html(page_count)

            $('.current_group_tab').html(group_name)
            $("#loader").show()
            $("#loader").css('opacity', 0.6)
            if (!read_time) {
                read_time = null
            }
            this.get("get_group", {
                group_id,
                read_time,
                'load_external': group_name,
                limit
            }).then((result_data) => {
                this.set_groupwords(result_data,group_id,limit)
            })
        }

        get_grouptojson(result_data){
            let data = result_data.data;
            let translateindex = 3
            data.forEach((item,index) => {
                let translate = item[translateindex]
                translate = this.to_json(translate)
                data[index][translateindex] = translate
            })
            return data
        }

        get_limit(group_id,limit){
            if(!limit){
                limit = this.get_group_current_limit(group_id)
            }
            limit = limit ? limit : this.get_defult_group_limit()
            return limit
        }

        set_groupwords(data,group_id,limit,callback){
            data = this.get_grouptojson(data)
            console.log(data)
            let project_mode = this.get_project_mode()
            let brief_mode = this.get_brief_mode()
            this.is_get_grouping = false
            let wordbox_html = "";
            let read_count = 0
            this.info(`group requested ${data.length} data.`)
            let index = 0
            limit = this.get_limit(group_id,limit)
            let count = null
            let unread_count = null
            let read_allrate = 0
            data.forEach((item) => {
                let
                    word = item[1],
                    word_id = this.create_id(word),
                    read = item[5],
                    word_json = item[3],
                    last_time = item[7]
                    ;
                if(count === null){
                    count = item[8]
                    unread_count = item[9]
                    read_count = count - unread_count
                    read_allrate = (read_count / count) * 100
                }
                let advanced_translate = this.get_word_property(word_json, "advanced_translate"),
                    advanced_translate_type = this.get_word_property(word_json, "advanced_translate_type"),
                    phonetic_symbol = this.get_word_property(word_json, "phonetic_symbol"),
                    plural_form = this.get_word_property(word_json, "plural_form"),
                    sample_images = this.get_word_property(word_json, "sample_images"),
                    synonyms = this.get_word_property(word_json, "synonyms"),
                    synonyms_type = this.get_word_property(word_json, "synonyms_type"),
                    voice_files = this.get_word_property(word_json, "voice_files"),
                    word_translation = this.get_word_property(word_json, "word_translation","translate_text")
                ;
                let translation_html = this.create_translation_html(word,word_translation)
                let phonetic_symbol_html = this.create_phonetic_symbol_html(word, word_id, voice_files)
                let sampleimages_html = this.create_sampleimages_html(word,sample_images)
                let haveread_html = this.create_haveread_html(word, word_translation)
                let advanced_translate_html = ``
                let synonyms_html = ``
                let plural_html = ``
                if (!brief_mode && !project_mode) {
                    // haveread_html = this.create_haveread_html(word, word_translation)
                    advanced_translate_html = this.create_advanced_html(word, word_id, advanced_translate_type, advanced_translate)
                    synonyms_html = this.create_synonyms_html(word, word_id, synonyms_type, synonyms)
                    plural_html = this.create_plural_html(plural_form)
                }
                wordbox_html += this.create_wordbox_html(
                    word,
                    word_id,
                    phonetic_symbol_html,
                    translation_html,
                    sampleimages_html,
                    advanced_translate_html,
                    synonyms_html,
                    plural_html,
                    haveread_html,
                    index,
                )
                index++
                // console.log(word_json)
            })
            let page = Math.floor(parseInt(limit.split(',')[0]) / this.default_per_words) + 1
            $(".page_current").html(page)
            $("#wordbox_contents_html").html(wordbox_html)
            this.set_haveread_html(read_count)
            this.set_window_scroll()
            this.get_review_count()
            document.querySelector(".control-sidebar").setAttribute("class", 'control-sidebar')
            $("#loader").hide()
            this.set_readcount(count,unread_count,read_count,read_allrate)
            this.re_translatewords()
            if (callback) {
                callback()
            }
        }

        get_project_mode() {
            let mx = 750
            let mn = 740
            let w = window.innerWidth
            if (w > mn && w < mx) {
                return true
            }
            let project_mode = this.local_storage(`project_mode`)
            return project_mode
        }

        set_project_mode() {
            let project_mode = this.local_storage(`project_mode`)
            project_mode = !project_mode
            let word_title = `.box-header-translate .box-title`
            let word_subtitle = `.box-header-translate .word_subtitle`

            if (project_mode) {
                this.add_class(word_title, `project_title`)
                this.add_class(word_subtitle, `project_subtitle`)
            } else {
                this.remove_class(word_title, `project_title`)
                this.remove_class(word_subtitle, `project_subtitle`)
            }
            this.set_brief_mode(project_mode,null)
            this.set_project_bar(project_mode)
            this.local_storage(`project_mode`, project_mode)
        }

        set_brief_show(brief_mode) {
            let customvtab = `.box-body .customvtab`
            // let box_footer = `.box-body .box-footer`

            if (brief_mode) {
                this.add_class(customvtab, `project_hide`)
                // this.add_class(box_footer, `project_hide`)
            } else {
                this.remove_class(customvtab, `project_hide`)
                // this.remove_class(box_footer, `project_hide`)
            }
        }

        set_project_bar(project_mode) {
            let chat_box_body = `#chat-box-body`
            let sticky_toolbar_bar = `.sticky-toolbar-bar`
            let sticky_toolbar_left = `sticky-toolbar-left`
            let sticky_toolbar_left_toggle = `sticky-toolbar-project-screen`
            // let sticky_toolbar_left_bar = `sticky-toolbar-left-bar`
            // let sticky_toolbar_screen = `sticky-toolbar-screen`
            // let sticky_toolbar = `sticky-toolbar`
            let main_header = `main-header`
            let main_header_app_menu = `${main_header} .app-menu`

            if (project_mode) {
                this.add_class(chat_box_body, `project_hide`)
                
                this.add_class(sticky_toolbar_bar, sticky_toolbar_left_toggle)
                this.remove_class(sticky_toolbar_bar, sticky_toolbar_left)

                // this.add_class(sticky_toolbar_left_bar, sticky_toolbar_screen)
                // this.remove_class(sticky_toolbar_left_bar, sticky_toolbar)

                this.add_class(main_header, `main-header-screen`
                )
                this.add_class(main_header_app_menu, `project_visible`)
            } else {
                this.remove_class(chat_box_body, `project_hide`)

                this.add_class(sticky_toolbar_bar, sticky_toolbar_left)
                this.remove_class(sticky_toolbar_bar, sticky_toolbar_left_toggle)

                // this.add_class(sticky_toolbar_left_bar, sticky_toolbar)
                // this.remove_class(sticky_toolbar_left_bar, sticky_toolbar_screen)

                this.remove_class(main_header, `main-header-screen`)

                this.remove_class(main_header_app_menu, `project_visible`)
            }
        }

        
        get_brief_mode(){
            let brief_mode = this.local_storage(`brief_mode`)
            return brief_mode
        }

        set_brief_mode(brief_mode=undefined,notice=true){
            if(notice){
                if(!confirm('是否设置简洁模式')){
                    return false
                }
            }
            if(brief_mode === undefined){
                brief_mode = this.get_brief_mode()
                brief_mode = !brief_mode
                this.local_storage(`brief_mode`,brief_mode)
            }
            this.set_brief_show(brief_mode)
        }

        set_review_html(count, time) {
            let review_class = `review-${time}`
            let reviewtime_class = `reviewtime-${time}`
            let review_item = this.queryElement(review_class)
            if(review_item && count){
                this.queryElement(reviewtime_class).innerHTML = `[${count}]`
                this.queryElement(review_class).style.display = `block`
                return
            }
            let count_text = ' - '
            let display = 'none'
            if(count){
                count_text = `[${count}]`
                display = 'block'
            }
            let html = `<li class="${review_class}" style='display:${display}'>
                    <a href="javascript:;" data-readtime="${time}" onclick="window.MyDict.get_review_group(this)">
                        <i class="fa fa-users text-info"></i> ${time} <span style="color:red;" class="${reviewtime_class}">${count_text}</span>
                    </a>
                </li>`
            $('.review-list').append(html)
            
        }

        set_readcount(count,unread_count,read_count,read_allrate){
            this.set_dayreadedcount()
            let ele = this.queryElement(`read_allrate`)
            if(ele){
                ele.style.width = `${read_allrate}%`
            }
            ele = this.queryElement(`word_count`)
            if(ele){
                ele.innerHTML = count
            }
            ele = this.queryElement(`unread_count`)
            if(ele){
                ele.innerHTML = unread_count
            }
        }

        get_query_selector(selector) {
            selector = selector.trim()
            if (!selector.startsWith('.') && !selector.startsWith('#')) {
                selector = `.${selector}`
            }
            return selector
        }
        
        queryElement(selector) {
            selector = this.get_query_selector(selector)
            let ele = document.querySelector(selector)
            return ele
        }

        queryElementAll(selector) {
            selector = this.get_query_selector(selector)
            let eles = []
            document.querySelectorAll(selector).forEach(ele=>{
                eles.push(ele)
            })
            return eles
        }
        array_remove(array, val) {
            for (var i = 0; i < array.length; i++) {
                if (array[i] == val) {
                    array.splice(i, 1);
                    i--;
                }
            }
            return array;
        }
        get_removeclassandaddclasselements(ele) {
            if (typeof ele == 'string') {
                ele = this.queryElementAll(ele)
            }
            if (!ele.length) {
                ele = [ele]
            }
            return ele
        }
        add_class(ele, class_name) {
            ele = this.get_removeclassandaddclasselements(ele)
            for (let i = 0; i < ele.length; i++) {
                let child = ele[i]
                let class_names = child.className
                if (!class_names) {
                    class_names = ``
                }
                class_names = class_names.split(/\s+/)
                if (!class_names.includes(class_name)) {
                    class_names.push(class_name)
                }
                child.className = class_names.join(` `)
            }
        }
        remove_class(ele, class_name) {
            ele = this.get_removeclassandaddclasselements(ele)
            for (let i = 0; i < ele.length; i++) {
                let child = ele[i]
                let class_names = child.className
                if (!class_names) {
                    class_names = ``
                }
                class_names = class_names.split(/\s+/)
                class_names = this.array_remove(class_names, class_name)
                child.className = class_names.join(` `)
            }
        }
        get_review_group(ele) {
            let read_time = ele.dataset.readtime
            let limit = this.get_group_current_limit()
            this.review_model = true
            this.get(`get_review`, {read_time,limit}).then((data)=>{
                let group_id = this.get_cruurent_group("group_id")
                this.set_groupwords(data,group_id)
                this.scroll_top()
            })
        }

        
        get_review_allcount() {
            let review_count = this.get_localreview_count()
            let gid = this.get_cruurent_group("group_id")
            let local_reviewcount_data = null
            try{
                if(typeof review_count.data[0] == 'object'){
                    local_reviewcount_data = true
                }
            }catch(e){

            }
            if(local_reviewcount_data){
                console.log('local',review_count)
                this.set_reviewcount_html(review_count)
            }else{
                this.get("get_review_allcount", {
                    gid,
                    read_time:this.max_reviewday,
                }).then((result_data) => {
                    console.log(result_data)
                    this.set_localreview_count(result_data)
                    this.set_reviewcount_html(result_data)
                })
            }
        }

        create_reviewtimes(){
            let c_timastamp = this.date_totimestamp()
            let day = 60*60*24*1000
            let last_reviewdays = c_timastamp - day * this.max_reviewday
            let times = []
            while (c_timastamp > last_reviewdays){
                let read_time = this.timestamp_todate(c_timastamp,'Y-M-D')
                c_timastamp -= day
                times.push(read_time)
            }
            return times
        }

        set_reviewcount_html(result_data){
            let times = this.create_reviewtimes()
            try {
                result_data = result_data.data[0]
            } catch(e){
                console.log(e)
                return
            } finally {
                console.log(result_data)
            }
            if(result_data){
                result_data.forEach((review_count,index) =>{
                    if(review_count){
                        this.set_review_html(review_count, times[index])
                    }
                })
            }
        }

        set_localreview_count(review_count){
            this.local_storage_today('review_allcount',review_count)
        }

        get_localreview_count(){
            let review_count = this.local_storage_today('review_allcount')
            console.log(review_count)
            if(!review_count || !review_count.data)return null
            return review_count
        }

        local_storage_today(key,value=undefined){
            if(value === undefined){
                return this.get_local_storagetoday(key)
            }else{
                this.set_local_storagetoday(key,value)
            }
        }

        set_local_storagetoday(key,data){
            data = {data}
            data['time'] = this.timestamp_todate(new Date(),'Y-M-D')
            data = JSON.stringify(data)
            this.local_storage(key,data)
        }

        get_local_storagetoday(key){
            let data = this.local_storage(key)
            
            let today = this.timestamp_todate(new Date(),'Y-M-D')
            if(!data){
                return null
            }
            data = JSON.parse(data)
            if(data.time != today){
                return null
            }
            data = data.data
            return data
        }

        get_review_count() {
            let gid = this.get_cruurent_group("group_id")
            let c_timastamp = this.date_totimestamp()
            let day = 60*60*24*1000
            let max_reviewday = c_timastamp - day * this.max_reviewday
            while (c_timastamp > max_reviewday){
                c_timastamp -= day
                let read_time = this.timestamp_todate(c_timastamp,'Y-M-D')
                let review_count = this.local_storage_today('review_count')
                if(false && review_count && review_count[read_time]){
                    console.log(`local`,review_count[read_time])
                    this.set_review_html(review_count[read_time], read_time)
                }else{
                    this.set_review_html(0, read_time)
                    this.get("get_review_count", {
                        gid,
                        read_time,
                    }).then((result_data) => {
                        let count = 0
                        try{
                            count = result_data.data[0]
                        }catch(e){
                            console.log(e)
                        }
                        this.set_review_local(read_time,count)
                        this.set_review_html(count, read_time)
                    })
                }
            }
        }

        set_review_local(read_time,count){
            let review_count = this.local_storage_today('review_count')
            if(!review_count){
                review_count = {}
            }
            review_count[read_time] = count
            this.local_storage_today('review_count',review_count)
        }

        review_count_minus(){
            let review_count = this.local_storage_today('review_count')
        }

        set_haveread_html(read_count) {
            let have_readed = document.querySelector(".have_readed")
            if(!have_readed){
                return
            }
            let have_readed_int = parseInt(have_readed.innerHTML)
            have_readed_int += read_count
            have_readed.innerHTML = have_readed_int
            let cruurent_group_id = this.get_cruurent_group('group_id')
            let groups_info = this.get_groups_info(cruurent_group_id)
            let have_unread = document.querySelector(".have_unread")
            have_unread.innerHTML = groups_info.group_count - have_readed_int
        }

        set_groups_info(groups_info) {
            groups_info = JSON.stringify(groups_info)
            this.local_storage(`groups_info`, groups_info)
        }

        get_groups_info(group_id) {
            if (this.group_info) {
                if (group_id) {
                    return this.group_info[group_id]
                }
                return this.group_info
            }
            let groups_info = this.local_storage(`groups_info`)
            if (!groups_info) {
                return null
            }
            groups_info = JSON.parse(groups_info)
            if (group_id) {
                return groups_info[group_id]
            }
            return groups_info

        }

        set_group_current_limit(limit, group_id) {
            if (!limit) {
                limit = this.get_defult_group_limit()

            }
            if (!group_id) {
                group_id = this.get_cruurent_group('group_id')
            }
            if (!group_id) {
                return null
            }
            this.local_storage(`group_id${group_id}_current_limit`, limit)
        }

        get_likely_word(word, means, phonetic_symbol) {
            this.get('get_likely_word', { word, means, phonetic_symbol }).then((data) => {
                console.log(data)
            })
        }

        get_group_current_limit(group_id) {
            if (!group_id) {
                group_id = this.get_cruurent_group('group_id')
            }
            if (!group_id) {
                return null
            }
            let limit = this.local_storage(`group_id${group_id}_current_limit`)
            if (!limit) {
                return this.get_defult_group_limit()
            }
            return limit
        }

        set_cruurent_group(key_groupid, value) {
            let group_info = this.get_cruurent_group()
            if (typeof key_groupid == 'object') {
                if (group_info) {
                    group_info = { ...group_info, ...key_groupid }
                } else {
                    group_info = key_groupid
                }
            } else {
                if (value) {
                    group_info[key_groupid] = value
                } else {
                    group_info = this.get_groups_info(key_groupid)
                }
            }
            group_info = JSON.stringify(group_info)
            this.local_storage("current_group_info", group_info)
        }

        get_cruurent_group(key) {
            let group_info = this.local_storage("current_group_info")
            group_info = JSON.parse(group_info)
            if (!group_info) {
                return null
            }
            if (key) {
                return group_info[key]
            }
            return group_info
        }

        create_wordbox_html(
            word,
            word_id,
            phonetic_symbol_html,
            translation_html,
            sampleimages_html,
            advanced_translate_html,
            synonyms_html,
            plural_html,
            haveread_html,
            index,
        ) {
            if (
                !phonetic_symbol_html &&
                !translation_html &&
                !sampleimages_html &&
                !advanced_translate_html &&
                !synonyms_html &&
                !plural_html &&
                !haveread_html
            ) {
                //advanced_translate_html = `No translations found`
            }
            index += 1
            let title_class = this.get_word_title()
            let html = `
            <div class="col-12" id="scroll_id${word_id}" data-word="${word}" data-index="${index}" data-voiceid="voice_us${word_id}">
			  <div class="box box-default">
				<div class="box-header-translate">
				  <h5 class="${title_class} word_h5">${word}</h5>
				  ${phonetic_symbol_html}
				  ${translation_html}
				  ${plural_html}
				</div>
				<!-- /.box-header -->
				<div class="box-body">
                    ${sampleimages_html}
                    ${synonyms_html}
                    ${advanced_translate_html}
                    ${haveread_html}
					<!-- Nav tabs -->
				</div>
				<!-- /.box-body -->
			  </div>
			  <!-- /.box -->
			</div>
            `
            return html
        }

        get_word_title() {
            let class_name = `box-title`
            if (this.get_project_mode()) {
                class_name += ` project_title`
            }
            return class_name
        }

        get_word_subtitle() {
            let class_name = `word_subtitle`
            if (this.get_project_mode()) {
                class_name += ` project_subtitle`
            }
            return class_name
        }

        create_haveread_html(word, word_translation) {
            let html = ``
            if (word_translation.length > 0) {
                html += `
                <div class="box-footer" style="padding:0px;">
                    <button data-word="${word}" onclick="window.MyDict.submit_haveread(this,'+1')" class="btn btn-success btn-flat"><i class="fa fa-check-circle" aria-hidden="true"></i> ${word}</button>
                    <button data-word="${word}" onclick="window.MyDict.submit_haveread(this,'-1')" class="btn btn-flat btn-secondary"><i class="fa fa-coffee" aria-hidden="true"></i> ${word}</button>
                </div>
                `
            }
            return html
        }

        create_plural_html(plural_form) {
            let html_tab = ""
            let html = ""
            let plural_html = ""

            plural_form.forEach((item, index) => {
                let delimiter = item.indexOf("Form") != -1
                if (delimiter) {
                    if (plural_html) {
                        html_tab += `
                        <code >${plural_html}</code> 
                        `
                        plural_html = ""
                    }
                    plural_html = `<span class="text-muted">${item}</code>`
                } else {
                    plural_html += ` ${item}`
                }
            })
            if (html_tab) {
                html = `
                <h6 class="box-subtitle">
                    ${html_tab}
                </h6>
                `
            }
            return html
        }

        create_synonyms_html(word, word_id, advanced_translate_type, advanced_translate) {
            let html_tab = ""
            let html = ""
            let tab_content_html = ""
            advanced_translate_type.forEach((item, index) => {
                let random_string = this.gen_randomstring(32)
                word_id = `tab_${word_id}${random_string}`
                item = this.split_html(item)
                let active_class = ""
                if (index == 0) {
                    active_class = "active"
                }
                html_tab += `
                        <li class="nav-item"> <a class="nav-link ${active_class}" data-toggle="tab" href="#${word_id}" role="tab">
                            <span class="hidden-sm-up">
                            </span> <span class="">${item}</span></a> 
                        </li>
                `
                let advanced_translate_item = advanced_translate[index]
                if (!advanced_translate_item) {
                    advanced_translate_item = []
                }
                let advanced_translate_html = this.analyze_advanced_translate(advanced_translate_item, "", "code", word)
                tab_content_html += `
                        <div class="tab-pane ${active_class}" id="${word_id}" role="tabpanel">
                            <div class="p-0">
                                    ${advanced_translate_html}
                            </div>
                        </div>
                `
            })
            if (html_tab) {
                html = `
                    <div class="customvtab">
						<ul class="nav nav-tabs customtab2" role="tablist">
                            ${html_tab}
						</ul>
						<!-- Tab panes -->
						<div class="tab-content">
                            ${tab_content_html}
						</div>
					</div>
                `
            }
            return html
        }

        create_advanced_html(word, word_id, advanced_translate_type, advanced_translate) {
            let html_tab = ""
            let html = ""
            let tab_content_html = ""
            advanced_translate_type.forEach((item, index) => {
                item = this.split_html(item)
                let random_string = this.gen_randomstring(32)
                word_id = `tab_${word_id}${random_string}`
                let active_class = ""
                if (index == 0) {
                    active_class = "active"
                }
                html_tab += `
                        <li class="nav-item">
                        <a class="nav-link ${active_class}" data-toggle="tab" href="#${word_id}" role="tab">
                            <span class="hidden-sm-up">
                            </span> <span class="">${item}</span></a> 
                        </li>
                `
                let advanced_translate_html = this.analyze_advanced_translate(advanced_translate[index], "<br />", "w_css", word)
                tab_content_html += `
                        <div class="tab-pane ${active_class}" id="${word_id}" role="tabpanel">
                            <div class="p-0">
                                <p>
                                    ${advanced_translate_html}
                                </p>
                            </div>
                        </div>
                `
            })
            if (html_tab) {
                html = `
                    <div class="customvtab">
						<ul class="nav nav-tabs customtab2" role="tablist">
                            ${html_tab}
						</ul>
						<!-- Tab panes -->
						<div class="tab-content">
                            ${tab_content_html}
						</div>
					</div>
                `
            }
            return html
        }

        analyze_advanced_translate(advanced_translate, br = "", tag_class = "w_css", word) {
            let html = ``
            let continuous = null
            let explanation_html = null
            let code_content_html = `<div class="de_co"><div class="def_pa">`
            let code_content_close = `</div></div>`
            if (tag_class == "code") {
                code_content_html = `<span>`
                code_content_close = `</span><br />`
                br = ",&nbsp;"
            }
            if (!advanced_translate) {
                advanced_translate = []
            }
            advanced_translate.forEach((trans_item, index) => {
                if (this.is_word_self(index, word, trans_item)) {
                    html += `<div class="word-title">${trans_item}${br}</div>`
                } else if (this.is_word_redandancy(trans_item)) {

                } else if (this.is_word_type(trans_item)) {
                    continuous = null
                    if (explanation_html) {
                        explanation_html = null
                        html += code_content_close
                    }
                    if (tag_class == "code") {
                        html += `
                        <code>${trans_item}</code>
                        `
                    } else {
                        html += `
                        <div class="pos_lin">
                        <div class="pos pull-left ">${trans_item}</div>
                        </div>
                        `
                    }
                } else if (this.is_word_number(trans_item)) {
                    continuous = null
                    if (explanation_html) {
                        explanation_html = null
                        html += code_content_close
                    }
                    html += `<div class="se_n_d">${trans_item}</div>`
                } else if (this.is_word_notes(trans_item)) {
                    html += `<code>${trans_item}</code>`
                } else {
                    if (!continuous) {
                        explanation_html = code_content_html
                        html += explanation_html
                        continuous = true
                    }
                    html += `${trans_item}${br}`
                }
            })
            if (explanation_html && continuous) {
                explanation_html = null
                html += code_content_close
            }
            return html
        }

        is_word_redandancy(word_type) {
            word_type = word_type.trim()
            if (word_type == "Show examples") {
                return true
            }
            return null
        }

        is_word_self(index, word, word_type) {
            word_type = word_type.trim()
            if (word_type == word && index == 0) {
                return true
            }
            return null
        }

        is_word_notes(word_type) {
            word_type = word_type.trim()
            if (/^\[.+\]$/.test(word_type)) {
                return word_type
            }
            return null
        }

        is_word_number(word_type) {
            word_type = word_type.trim()
            if (/^[0-9]+\./.test(word_type)) {
                return word_type
            }
            return null
        }

        is_word_type(word_type) {
            let word_types = [
                "n.",
                "v.",
                "Web",
                "prep.",
                "abbr.",
                "n.",
                "adj.",
                "vt.",
                "adj.",
                "IDM",
                "pron.",
                "adv.",
                "etc.",
                "pron.",
            ]
            let result = null
            word_types.forEach(function (type_oneitem) {
                word_type = word_type.toLowerCase().trim()
                if (word_type.startsWith(type_oneitem.toLowerCase())) {
                    result = word_type
                    return
                }
            })
            return result
        }

        create_sampleimages_html(word,sample_images) {
            let html = ""
            let w = this.get_project_mode() ? `140` : `80`
            for (let item in sample_images) {
                let item_term = sample_images[item]
                let src = item_term.save_filename
                if(src.split(/\./).pop().toLowerCase() == 'none'){
                    this.add_retranslatewords(word)
                }else{
                    html += `
                    <a href="javascript:;" class="bg-warning-light h-${w} w-${w} l-h-${w} rounded text-center overflow-hidden">
                        <img height="${w}" height="${w}" src="${item_term.save_filename}" class="h-${w} align-self-end" alt="">
                    </a>
                    `
                }
            }
            if (html) {
                html = `
                <div class="d-flex box-bottom-10px">
                    <div class="d-flex-image">
                        ${html}
                    </div>
                </div>
                `
            }
            return html
        }

        submit_haveread(ele, read) {
            let word = ele
            // console.log(ele)
            if (typeof ele != "string") {
                word = ele.dataset.word
            }
            this.get("submit_haveread", {
                word,
                read,
            })
        }

        scroll_top() {
            window.scrollTo(document.body.scrollHeight, 0)
        }

        scroll_bottom() {
            window.scrollTo(0, document.body.scrollHeight)
        }

        scroll_to(top) {
            window.scrollTo(document.body.scrollHeight, top)
        }

        scroll_removing(ele_selector) {
            if (typeof ele_selector == 'string') {
                ele_selector = document.querySelector(ele_selector)
            }
            let top = this.getElementTop(ele_selector, document.querySelector(`html`)) - (document.body.scrollTop + document.documentElement.scrollTop)
            return top
        }

        is_showscreen(el) {
            if(typeof el == 'string') {
                el = document.querySelector(el)
            }
            let BoundingClientRect = el.getBoundingClientRect()
            let wh = window.innerHeight
            let cp = BoundingClientRect.top
            let cb = BoundingClientRect.buttom
            if(cp > 0 && cp < wh){
                return true
            }
            if(cb > 0 && cb < wh){
                return true
            }
            return false
        }
        
        is_showing(el) {
            if(typeof el == 'string') {
                el = document.querySelector(el)
            }
            let BoundingClientRect = el.getBoundingClientRect()
            // console.log('BoundingClientRect',BoundingClientRect)
            let wh = window.innerHeight
            let cp = BoundingClientRect.top
            let bh = BoundingClientRect.height + cp
            // console.log("wh",wh,"cp",cp,"bh",bh)
            if(cp > 0 && cp < wh){
                return true
            }
            if(bh > wh){
                return true
            }
            return false
        }
        
        get_firstshowing() {
            if(this.tailshowing){
                return this.tailshowing
            }
            let showing = this.get_showings()
            if(showing.length > 0){
                return showing[0]
            }
            let showscreen = this.get_showscreens()
            if(showscreen.length > 0){
                return showscreen[0]
            }
            alert("Not found the first showing-word.")
        }

        is_tailshowing() {
            let we = this.get_allwordeles()
            we = we.pop()
            if(this.is_showscreen(we)){
                return true
            }else{
                return false
            }
        }

        get_nextshowing() {
            let showing = this.get_firstshowing()
            let is_tailshowing = this.is_tailshowing()
            if(is_tailshowing){
                if(!this.tailshowing){
                    this.tailshowing = showing
                }else{
                    showing = this.tailshowing
                }
            }else{
                this.tailshowing = null
            }
            let next = showing
            if(next == this.current_wordshowed){
                console.log(showing)
                next = showing.nextElementSibling
            }
            if (!next) {
                next = showing
            }
            if(is_tailshowing && this.tailshowing ){
                this.tailshowing = next
            }
            this.current_wordshowed = next
            return next
        }

        get_prevshowing() {
            let showing = this.get_firstshowing()
            let is_tailshowing = this.is_tailshowing()
            if(is_tailshowing){
                if(this.tailshowing){
                    showing = this.tailshowing
                }
            }else{
                this.tailshowing = null
            }
            let prev = showing
            if(prev == this.current_wordshowed){
                prev = showing.previousElementSibling
            }
            if (!prev) {
                prev = showing
            }
            if(is_tailshowing && this.tailshowing ){
                this.tailshowing = prev
            }
            this.current_wordshowed = prev
            return prev
        }

        get_showings() {
            let we = this.get_allwordeles()
            let showing = []
            we.forEach(ele=>{
                if(this.is_showing(ele)){
                    showing.push(ele)
                }
            })
            return showing
        }

        get_allwordeles(){
            let we = this.queryElementAll(`#wordbox_contents_html > div`)
            return we
        }

        get_showscreens() {
            let we = this.get_allwordeles()
            let showscreen = []
            we.forEach(ele=>{
                if(this.is_showscreen(ele)){
                    showscreen.push(ele)
                }
            })
            return showscreen
        }
        
        get_lastshowing() {
            let showscreens = this.get_showscreens()
            return showscreens.pop()
        }

        is_shown(el) {
            if(typeof el == 'string') {
                el = document.querySelector(el)
            }
            let BoundingClientRect = el.getBoundingClientRect()
            let cp = BoundingClientRect.top
            if(cp < 0 ){
                return true
            }
            return false
        }

        getElementTop(el, target_ele) {
            if (!target_ele) target_ele = document.querySelector('html')
            let parent = el.offsetParent;
            let top = el.offsetTop;
            return parent && parent !== target_ele ? this.getElementTop(parent, target_ele) + top : top;
        }

        info(info) {
            let print_info = document.querySelector('.print_info')
            if(!print_info){
                return
            }
            print_info.innerHTML = info
            print_info.style.display = 'block'
            setTimeout(() => {
                print_info.style.display = 'none'
            }, 2000);
        }

        create_time(format, index = 0) {
            let dateTime = new Date()
            if (typeof format === 'string') {
                let date_format = format.split(' ')
                date_format = date_format[0]
                date_format = date_format.split('-')
                let year = date_format[0]
                let month = date_format[1]
                let day = date_format[2]
                let is_int = /^\d+$/
                if (is_int.test(year) && is_int.test(month) && is_int.test(day)) {
                    year = parseInt(year)
                    month = parseInt(month)
                    day = parseInt(day)
                    dateTime.setFullYear(year, month, day)
                    if (date_format.length > 1) {
                        format = `yyyy-MM-dd hh:mm:ss`
                    } else {
                        format = `yyyy-MM-dd`
                    }
                }
            } else {
                format = `yyyy-MM-dd hh:mm:ss`
            }
            var z = {
                y: dateTime.getFullYear(),
                M: dateTime.getMonth() + 1,
                d: dateTime.getDate() + index,
                h: dateTime.getHours(),
                m: dateTime.getMinutes(),
                s: dateTime.getSeconds()
            };
            return format.replace(/(y+|M+|d+|h+|m+|s+)/g, function (v) {
                return ((v.length > 1 ? "0" : "") + eval("z." + v.slice(-1))).slice(-(v.length > 2 ? v.length : 2))
            })
        }

        fill_alphabet(s, l, fill_s = "0") {
            s = s+""
            s = s.padStart(l, fill_s)
            return s
        }

        numeric(n) {
            let numbric = /^\d+$/
            if (numbric.test(n)) {
                return true
            }
            return false
        }

        date_totimestamp(time) {
            if (!time) {
                time = new Date()
            } else if (typeof time == 'string' || typeof time == 'number') {
                time = new Date(time)
            }
            let timesdamp = Date.parse(time)
            return timesdamp
        }

        timestamp_todate(time, format = 'Y-M-D h:m:s') {
            let date
            if (typeof time == 'object') {
                date = time
            } else {
                if (this.numeric(time)) {
                    time = parseInt(time)
                }
                date = new Date(time)
            }
            let Y = date.getFullYear();
            let M = this.fill_alphabet(date.getMonth() + 1, 2, '0');
            let D = this.fill_alphabet(date.getDate(), 2, '0');
            let h = this.fill_alphabet(date.getHours(), 2, '0');
            let m = this.fill_alphabet(date.getMinutes(), 2, '0');
            let s = this.fill_alphabet(date.getSeconds(), 2, '0');
            format = format.replace('Y', Y)
            format = format.replace('M', M)
            format = format.replace('D', D)
            format = format.replace('h', h)
            format = format.replace('m', m)
            format = format.replace('s', s)
            return format
        }

        get_id(ele) {
            if (ele.dataset.voiceid) {
                let dataset = ele.dataset
                let word = dataset.word
                let index = dataset.index
                let voiceid = ele.dataset.voiceid
                let id = voiceid.replace(/^voice_[a-z]{2}/, '')
                let scrollid = `scroll_id${id}`
                return {
                    id,
                    voiceid,
                    scrollid,
                    word,
                    index,
                }
            } else {
                return this.get_id(ele.parentElement || ele.parentNode)
            }
        }

        set_dayreadedcount(){
            let dayreadedcount = this.get_dayreadedcount()
            if(typeof dayreadedcount != 'number'){
                dayreadedcount= 0
            }else{
                dayreadedcount++
            }
            let today_process = (dayreadedcount / this.per_dayreadwords) * 100
            let ele = this.queryElement(`dayreadedcount`)
            if(!ele){
                return false
            }
            ele.style.width = `${today_process}%`
            this.local_storage_today(`dayreadedc`,dayreadedcount)
        }

        get_dayreadedcount(){
            let count = this.local_storage_today(`dayreadedc`)
            return count
        }

        set_readed_count(){
            let ele = this.queryElement(`readed_allrate`)
            if(!ele){
                return false
            }
            let readed = this.readed_count.length
            readed = (readed / this.default_per_words) * 100
            ele.style.width = `${readed}%`
        }

        play_voice(ele, stop, callback, views_index) {
            let ids = this.get_id(ele)
            let scrollid = ids.scrollid
            let word = ids.word
            let index = ids.index
            if(!this.readed_count.includes(index)){
                this.readed_count.push(index)
                this.set_readed_count()
                if(!this.review_model){
                    this.set_dayreadedcount()
                }else{
                    this.review_count_minus()
                }
            }
            scrollid = `#${scrollid} audio`
            let voice = document.querySelectorAll(scrollid)
            if (voice.length == 0) {
                //如果没有发音,则切换到英语发音
                this.re_translatewords(word)
                return
            }
            voice = voice[0]//总是读取第一个发音
            if (views_index >= this.maximum_numberofplays) {
                //重点词汇-1
                this.submit_haveread(word, "-0.1")
            } else if (this.maximum_numberofplays > 1 && views_index == this.maximum_numberofplays - 1) {
                //调整权重
                this.submit_haveread(word, "-0.1")
            } else {
                this.submit_haveread(word, "+0.2")
            }

            //复习逻辑hi
            // if(this.is_review){
            //     let scrollid = ids.scrollid
            //     let scrolele = $(`#${scrollid}`)
            //     if(views_index == 0){
            //         let html = scrolele.find('.box-title').html()
            //         console.log(html)
            //         scrolele.attr(`data-html`,html)
            //     }else{
            //         scrolele.html(scrolele.attr(`data-html`))
            //     }
            // }
            this.current_word_id = index
            this.info(`${word} ${index}/${this.default_per_words} plaing... `)
            // this.music_players.push(voice)
            if (voice) {
                voice.play()
            }
            if (callback) {
                let duration = false
                if (voice) {
                    duration = voice.duration
                }
                if (!duration && duration !== false || duration < 2) {
                    duration = 2
                }
                callback(duration)
            }
            if (stop) {
                this.voice_stopplay()
            }
        }

        voice_playtoggle() {
            if (!this.voice_playevent) {
                this.voice_autoplay()
            } else {
                this.voice_stopplay()
            }
        }

        voice_autoplay() {
            let showing = this.get_firstshowing()
            if (showing) {
                let ele_icon = document.querySelector('#auto_play span')
                if (ele_icon) ele_icon.setAttribute('class', 'si-control-pause si')
                let index = 0
                this.sleep(0.5)
                index++
                this.play_voice(showing, false, (duration) => {
                    if (duration === false) {
                        setTimeout(() => {
                            this.voice_stopplay()
                            this.word_skip("next")
                        }, 3000)
                        return
                    }
                    let duration_ms = duration * 1000 * 1.2
                    if (index > this.maximum_numberofplays) {
                        setTimeout(() => {
                            this.voice_stopplay()
                            this.word_skip("next")
                        }, duration_ms)
                        return
                    } else {
                        this.voice_playevent = setInterval(() => {
                            if (index > this.maximum_numberofplays) {
                                this.voice_stopplay()
                                this.word_skip("next")
                            } else {
                                index++
                                this.play_voice(showing, false, null, index)
                            }
                        }, duration_ms)
                    }
                }, index)
            } else {
                alert(`the showing is Not found.`,showing)
            }
        }

        voice_stopplay() {
            let ele_icon = document.querySelector('#auto_play span')
            if (ele_icon) ele_icon.setAttribute('class', 'si-control-play si')
            if (this.voice_playevent) {
                clearInterval(this.voice_playevent)
                this.voice_playevent = null
            }
        }

        sleep(time) {
            var startTime = new Date().getTime() + parseInt(time, 10);
            while (new Date().getTime() < startTime) { }
        }

        create_translation_html(word,word_translation) {
            let html = ""
            if(word_translation.length == 0){
                this.add_retranslatewords(word)
                return html
            }
            let subtitleclassname = this.get_word_subtitle()
            word_translation.forEach((item, index) => {
                let trans_type = this.get_array_value(item, 0)
                let trans_info = item.slice(1).join("")
                let html_item = ""
                let html_css = "bg-primary-light"
                if (trans_type && trans_type.toLowerCase() == "web") {
                    html_css = "bg-success-light"
                }
                if (trans_type) {
                    let pinyin_text = pinyinPro.pinyin(trans_info)
                    html_item = `
                    <h6 class="box-subtitle ${subtitleclassname}">
                    <span class="pull-left ${html_css}">${trans_type}</span> 
                    <span class="translate_span" >${trans_info}</span><button type="button" onclick="window.MyDict.showpinyin(this)" class="waves-effect btn btn-circle btn-xs-py mb-0"><i class="mdi mdi-file-powerpoint-box"></i></button>
                    </h6>
                    <h6 class="box-pinyintitle ${subtitleclassname}" style="display:none;">
                    <span class="translate_pinyinspan" >${pinyin_text}</span>
                    </h6>
                    `
                    html += html_item
                }
            })
            return html
        }

        create_phonetic_symbol_html(word, word_id, voice_files) {
            let html = ""
            if(Object.keys(voice_files).length == 0 ){
                this.add_retranslatewords(word)
                return html
            }
            let index = 1
            for (let item in voice_files) {
                let voice = voice_files[item]
                let voice_name = "undefined"
                if (voice.iterate_name) {
                    voice_name = voice.iterate_name.replace(/(?<=[a-zA-Z]{2}).+/, "").toLowerCase()
                }
                let voice_id = `voice_${voice_name}${word_id}`
                if (!voice.save_filename || voice.save_filename.split('.').pop() == "None") {
                    this.add_retranslatewords(word)
                }

                let voice_nickname = voice.iterate_name ? voice.iterate_name : ""
                html += `
                <span class="phonetic_span">${voice_nickname}</span>
                <audio id="${voice_id}" class="phoneticvoice" preload="auto">
                    <source src="${voice.save_filename}" type="audio/mp3">
                </audio>
                <a class="waves-effect waves-light btn btn-xs btn-warning-light" data-word="${word}" data-index="${index}" data-voiceid="${voice_id}" href="javascript:;" onclick="MyDict.play_voice(this,true)">
                    <i class="fa fa-volume-up"></i>
                </a>
                `
                index++
            }
            if (html) {
                html = `
                <h6 class="box-subtitle" style="margin-top: 10px;margin-bottom: 10px;">
                    ${html}
                </h6>
                `
            }
            return html
        }

        add_retranslatewords(word){
            if(!this.re_translatewordsarray.includes(word)){
                this.re_translatewordsarray.push(word)
            }
        }

        re_translatewords(words) {
            if(!words){
                words = this.re_translatewordsarray.toString()
                this.re_translatewordsarray = []
            }else{
                if(typeof words == 'string'){
                    words = [words]
                }
                words = words.toString()
            }
            console.log('re-translate: ', words)
            this.post('retranslate_word', {
                words:words
            }, (data) => {
                console.log(data)
            })
        }

        create_id(word) {
            if ($ && $.md5 && word) {
                word = $.md5(word)
            }
            return word;
        }

        gen_randomstring(len = 32) {
            let chars = "abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ_"
            var result = '';
            for (var i = len; i > 0; --i) {
                result += chars[Math.floor(Math.random() * chars.length)];
            }
            return result;
        }

        get_array_value(array, index) {
            if (array.length >= index + 1) {
                return array[index]
            }
            return null
        }

        get_word_property(word_json, key, defult_value = []) {
            if (word_json && key in word_json) {
                return word_json[key];
            }
            if(typeof defult_value == "string"){
                key = defult_value
                defult_value = []
            }
            if(typeof word_json == "object" && word_json[key]){
                return word_json[key]
            }
            return defult_value
        }

        split_html(html) {
            html = html.replaceAll(/<.+?>/g, '')
            return html
        }

        get_group_content(group_name) {
            this.get("get_group", {
                group_name
            }).then((result_data) => {
                for (let item of result_data.data) {
                    console.log(item)
                    let group_name = item[2],
                        group_last_time = item[5]
                        ;
                }
            })
            let group_sentence = this.split(this.decode(item[7]))
        }

        local_storage(key, value = undefined) {
            if (value !== undefined) {
                localStorage.setItem(key, value)
            } else {
                let val = localStorage.getItem(key)
                if (val == 'false') {
                    val = false
                } else if (val == 'true') {
                    val = true
                } else if (val == 'null') {
                    val = null
                }
                return val
            }
        }

        initial_action() {
            let not_wordtranslated = this.not_translated()
            if (not_wordtranslated) {
                this.message(`need to be translate ${not_wordtranslated}`)
                this.translate_not_translatedwords(not_wordtranslated)
            } else {
                this.message("Not Translated, the system is ready.")
                this.is_include_area()
                this.listing_button()
            }
        }

        decode(value) {
            value = value.replaceAll("&apos;", "'")
            value = value.replaceAll("&quot;", '"')
            return value
        }

        to_json(value) {
            try {
                value = JSON.parse(value)
            } catch (e) {
                console.log(`to_json ${e}`)
                console.log(`value ${value}`)
                value = {}
            }
            return value
        }

        split(value) {
            console.log(value)
            value = value.trim("[")
            value = value.trim("]")
            value = value.trim(",")
            value = value.trim("'")
            value = value.trim()
            // value = value.split("'").join('\n')
            value = value.split("\\n").join('\n')
            value = value.split(",").join('\n')
            value = value.split("\n")
            value = value.filter(function (s) {
                return s && s.trim()
            })
            return value
        }

        group_limit(mathematical = "add") {
            let limit = this.get_group_current_limit()
            let limits = limit.split(',')
            limit = limits[1]
            let number = -parseInt(limit)
            if (mathematical == "add") {
                number = Math.abs(number)
            }
            let start_point = parseInt(limits[0]) + number
            if (start_point < 0) {
                start_point = 0
            }
            let current_group_id = this.get_cruurent_group("group_id")
            let group_info = this.get_groups_info(current_group_id)
            let group_count = group_info.group_count
            console.log(start_point, group_count)
            if (start_point > group_count) {
                console.log(`Maximum group request ${start_point},${limit}`)
                //start_point = group_count
                return
            }
            limit = `${start_point},${limit}`
            this.set_group_current_limit(limit)
            this.get_group(current_group_id, limit, () => {
                this.scroll_top()
            })
            return limit
        }

        get_show_word(set = true) {
            return this.get_firstshowing()
        }

        word_skip(action = "next") {
            this.voice_stopplay()
            let topheight = 60

            if(this.get_project_mode()){
                topheight = 0
            }

            if (action == "next") {
                let next = this.get_nextshowing()
                next.scrollIntoView()
                let scrollTop = document.documentElement.scrollTop || document.body.scrollTop;
                window.scrollTo(0, scrollTop - topheight)
                // this.tailshowing = next
                this.voice_autoplay()
            }else if (action == "prev") {
                let prev = this.get_prevshowing()
                prev.scrollIntoView()
                let scrollTop = document.documentElement.scrollTop || document.body.scrollTop;
                window.scrollTo(0, scrollTop - topheight)
                // this.tailshowing = prev
                this.voice_autoplay()
            }
        }

        set_window_scroll() {
            // let scroll = this.get_scrolltop()
            // this.scroll_to(scroll)
        }

        set_scrolltop(scroll_top) {
            this.set_cruurent_group('window_scrolltop', scroll_top)
            // console.log(scroll)
        }

        get_scrolltop() {
            let scroll = this.get_cruurent_group('window_scrolltop')
            return scroll
        }


        handling_remote_access_to_information() {
            this.message("handling_remote_access_to_information")
            let not_translated = []
            for (let i = 0; i < this.trans_data.length; i++) {
                let word = this.trans_data[i]
                if (word[this.get_trans_word_index] == null || this.force_translate) {
                    not_translated.push(word[1])
                }
            }
            if (not_translated.length == 0) {
                this.add_translate_to_html(true)
            } else {
                this.message(`not_translated ${not_translated}`)
                this.not_translated(not_translated)
                this.translate_not_translatedwords()
            }
        }

        translate_not_translatedwords(word) {
            if (!word) {
                word = this.not_translated()
            }
            if (!word) {
                return
            } else {
                this.translate(word)
            }
        }

        put_bing_translation_field(word, local_html, callback) {
            let url = this.remote_url("put_bing_translation_field")
            $.post(url, {
                word: word,
                translate_field: local_html,
                mobile: this.mobile_browser
            }, (data) => {
                if (callback) {
                    callback(data)
                }
            })
        }


        not_translated(words) {
            let store_key = "not_translated"
            if (words) {
                words = words.join(',')
                localStorage.setItem(store_key, words)
            } else {
                let words = localStorage.getItem(store_key)
                if (words) {
                    words = words.split(',')
                    let word = words.pop()
                    this.not_translated(words)
                    return word
                } else {
                    return words
                }
            }
        }

        is_mobile_browser() {
            let mobile_match = navigator.userAgent.match(
                /(phone|pad|pod|iPhone|iPod|ios|iPad|Android|Mobile|BlackBerry|IEMobile|MQQBrowser|JUC|Fennec|wOSBrowser|BrowserNG|WebOS|Symbian|Windows Phone)/i
            )
            if (mobile_match) {
                this.get_trans_word_index = 2
                this.mobile_browser = 1
            } else {
                this.get_trans_word_index = 3
                this.mobile_browser = 0
            }
        }

        remove(selector) {
            let ele = document.querySelector(selector)
            if (ele) {
                ele.remove()
            }
        }

        put_to_remote_local_vocabulary(callback) {
            let doc = this.local_textarea_text();
            doc = doc.trim()
            if (doc) {
                let url = this.remote_url('put_translate_words')
                $.post(url, {
                    "doc": doc
                }, (data) => {
                    this.message(`put_to_remote_local_vocabulary ${data}`)
                    if (callback) {
                        callback(data)
                    }
                })
            } else {
                this.message(`put_to_remote_local_vocabulary`)
                if (callback) {
                    callback()
                }
            }
        }


        remote_resourceurl(suffix) {
            let base_remote_url = window.location.origin
            let url = `${base_remote_url}/static/${suffix}`;
            return url
        }

        remote_url(method) {
            let base_remote_url = window.location.origin
            let url = `${base_remote_url}/api?method=${method}&module=com_translate&key=9LrQN0~14,dSmoO^`;
            // console.log(url)
            return url
        }

        get(method, request_data) {
            let url = this.remote_url(method)
            return new Promise((resolve, reject) => {
                $.get(url, request_data, (data) => {
                    resolve(data)
                })
            })
        }

        post(method, data) {
            let url = this.remote_url(method)
            return new Promise((resolve, reject) => {
                $.post(url, data, (data) => {
                    resolve(data)
                })
            })
        }

        local_textarea_text(text) {
            let text_area = document.querySelector('#my_bing_words_translate')
            if (text) {
                text_area.value = text
            } else {
                return text_area.value
            }
        }

        set_localStorage(textarea_text) {
            if (textarea_text) {
                localStorage.setItem('local_words', textarea_text)
            } else {
                let local_words = localStorage.getItem('local_words')
                this.local_textarea_text(local_words)
            }
        }

        translate(word, callback) {
            document.querySelector('#sb_form_q').value = word
            this.set_need_to_get_word_HTML(word)
            document.querySelector('#sb_form_go').click();
        }

        set_need_to_get_word_HTML(word) {
            let need_to_get_word_key = "need_to_get_html_word"
            if (word) {
                localStorage.setItem(need_to_get_word_key, word)
            } else {
                let word = localStorage.getItem(need_to_get_word_key)
                localStorage.setItem(need_to_get_word_key, "")
                return word
            }
        }

        get_translate_html() {
            this.remove_redundancy_html()
            let local_html = document.querySelector('.lf_area>div').innerHTML;
            return local_html
        }

        remove_redundancy_html() {
            if (this.remove_redundancy) {
                this.message(`remove_redundancy_html has been executed`)
                return
            }
            this.remove_redundancy = true
            this.message(`remove_redundancy_html`)
            let css = ['.df_div', '.se_div']
            for (let i = 0; i < css.length; i++) {
                let div = document.querySelector(css[i])
                if (div) {
                    div.remove()
                }
            }
        }

        transdata_translate_html() {
            let area_data = this.trans_data.slice(this.data_start, this.data_end)
            let local_html = ""
            for (let i = 0; i < area_data.length; i++) {
                let word = area_data[i];
                local_html += `<div class="qdef">${word[this.get_trans_word_index]}</div>`
            }
            local_html = local_html.replaceAll("&apos;", "'")
            local_html = local_html.replaceAll("&quot;", '"')
            return local_html
        }

        showpinyin(ele){
            if(ele){
                ele = ele.parentElement.nextElementSibling
                if(ele){
                    let display = 'block'
                    if(ele.style.display == "block"){
                        display = 'none'
                    }
                    ele.style.display = display
                }
            }
        }
        
        is_include_area() {
            let lf_area = document.querySelector('.lf_area')
            if (!lf_area) {
                this.translate('bing')
            }
        }
        message(message) {
            document.querySelector('#my_bing_output_info').innerHTML = message
        }

        //给添加的元素添加监听事件
        listing(selector, event, callback) {
            let ele = document.querySelector(selector)
            if (ele) {
                ele.addEventListener(event, () => {
                    callback()
                })
            }
        }


        load_js(jssrc){
            if(typeof jssrc === 'string'){
                jssrc = [jssrc]
            }
            jssrc.forEach(src=>{
                if(!src.startsWith('http:')){
                    src = this.remote_resourceurl(src)
                }
                this.create_ele('script',{
                    src: src,
                    type:"text/javascript"
                })
            })
        }
        
        create_ele(tag, types) {
            let ele = document.createElement(tag)
            for (let key in types) {
                let val = types[key]
                ele[key] = val
            }
            document.querySelector(`body`).insertAdjacentElement('beforeEnd', ele)
            console.log(`creat element ${tag} successfully.`)
        }
        
        listing_button() {
            this.listing('#previou_page_group', 'click', () => {
                // window.location.reload()
                // this.scroll_top()
                this.group_limit("sub")
            })
            this.listing('#next_page_group', 'click', () => {
                // window.location.reload()
                // this.scroll_bottom()
                this.group_limit("add")
            })
            this.listing('#review', 'click', () => {
                this.set_review()
            })
            this.listing('#trans_refresh', 'click', () => {
                if(!confirm('是否刷新')){
                    return false
                }
                window.location.reload()
                this.scroll_top()
            })
            this.listing('#show_groups', 'click', () => {
            })
            this.listing('#previou_word', 'click', () => {
                this.word_skip("prev")
            })
            this.listing('#next_word', 'click', () => {
                this.word_skip("next")
            })
            this.listing('#auto_play', 'click', () => {
                this.voice_playtoggle()
            })
            this.listing('#set_project_mode', 'click', () => {
                this.set_project_mode()
            })
            this.listing('#set_brief_mode', 'click', () => {
                this.set_brief_mode()
            })
            // this.listing('#review_yesterday','click',()=>{
            //     this.voice_playtoggle()
            // })
            window.onscroll = function () {
                //为了保证兼容性，这里取两个值，哪个有值取哪一个
                //scrollTop就是触发滚轮事件时滚轮的高度

                let scrollTop = document.documentElement.scrollTop || document.body.scrollTop;
                window.MyDict.set_scrolltop(scrollTop)

            }
            return true //以下不加载
            this.listing('#my_bing_dictionary', 'click', () => {
                this.put_to_remote_local_vocabulary(() => {
                    this.message(`success : put_to_remote_local_vocabulary, then get_trans_words.`)
                    let data = this.get_group(group_id)
                    this.message(`get_trans_words ${data}`)
                    this.handling_remote_access_to_information()
                })
            })
            this.listing('#my_bing_words_translate', 'input', () => {
                let textarea_text = this.local_textarea_text()
                this.set_localStorage(textarea_text)
            })
            this.listing('#up_transdata_button', 'click', () => {
                this.add_translate_to_html(true)
            })
            this.listing('#down_transdata_button', 'click', () => {
                this.add_translate_to_html(false)
            })
        }
    }

    window.MyDict = new MyDictClass()
    window.MyDict.init_browser()
})()