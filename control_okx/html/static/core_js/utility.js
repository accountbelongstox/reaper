class UtilityClass {
    constructor() {
    }

    load_jquery() {
        let js_dir = this.get_local_url("static/js/jquery-3.6.1.min.js");
        this.create_script(js_dir);
        let noConflict = setInterval(() => {
            if (typeof $ != 'undefined' && $.noConflict) {
                clearInterval(noConflict);
                /*JQuery释放$标识符*/
                console.log("Release the JQuery flag.");
                $.noConflict();
            } else {
                console.log("not find $ pramameter.");
            }
        }, 500)
    }

    get_historydata_beforetime(date, before = '1DAY') {
        before = this.split_wordnumber(before)
        let unit = before[1][0].toLowerCase()
        let base_number = before[0]
        let times = 1
        switch (unit) {
            case 'd':
                times = 60 * 60 * 24
                break
            case 'm':
                times = 60 * 60 * 24 * 30
                break
            case 'y':
                times = 60 * 60 * 24 * 30_12
                break
            case 'h':
                times = 60 * 60
                break
            case 'm':
                times = 60
                break
        }
        if (this.is_millisecond(date)) {
            times = times * 1000
        }
        let diference = base_number * times
        date = date - diference
        return date
    }

    delete_afterdate(array, key, val) {
        for (var i = 0; i < array.length; i++) {
            if (array[i][key] < val) {
                array.splice(i, 1);
                i--;
            }
        }
        return array;
    }

    fill_alphabet(s, l, fill_s = "0") {
        s = s + ""
        s = s.padStart(l, fill_s)
        return s
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

    coin_name_standardization(coin_name) {
        let format = (coin_name_alias) => {
            return coin_name_alias.replaceAll(/\/+/g, `-`).toUpperCase()
        }
        if (typeof coin_name == 'string') {
            return format(coin_name)
        }
        coin_name.forEach((coin_name_alias, index) => {
            coin_name[index] = format(coin_name_alias)
        })
        return coin_name
    }

    is_millisecond(second) {
        if (!(second.length == 10)) {
            return true
        }
        return false
    }

    timesecond_tomillisecond(second) {
        second = parseInt(second)
        if (!this.is_millisecond(second)) {
            second = second * 1000
        }
        return second
    }

    queryElement(selector) {
        selector = this.get_query_selector(selector)
        let ele = document.querySelector(selector)
        return ele
    }

    queryElementAll(selector) {
        selector = this.get_query_selector(selector)
        console.log(selector)
        let eles = document.querySelectorAll(selector)
        return eles
    }

    get_query_selector(selector) {
        selector = selector.trim()
        if (!selector.startsWith('.') && !selector.startsWith('#')) {
            selector = `.${selector}`
        }
        return selector
    }

    split_wordnumber(s) {
        s = s.split(/(?<=\d)\B(?=[a-zA-Z])/)
        return s
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

    split_class(class_names) {
        if (typeof class_names != 'string') {
            class_names = child.className
        }
        if (!class_names) {
            class_names = ``
        }
        class_names = class_names.split(/\s+/)
        return class_names
    }

    add_class(ele, class_name) {
        ele = this.get_removeclassandaddclasselements(ele)
        for (let i = 0; i < ele.length; i++) {
            let child = ele[i]
            let class_names = this.split_class(child)
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
            let class_names = this.split_class(child)
            class_names = this.array_remove(class_names, class_name)
            child.className = class_names.join(` `)
        }
    }

    to_unicode(c) {
        if (c == '') {
            return c
        }
        let u = '';
        for (let i = 0, iLength = c.length; i < iLength; i++) {
            u += '\\u' + c.charCodeAt(i).toString(16);
        }
        return u;
    }

    to_alpha(c) {
        let a = 'to_alpha';
        for (let i = 0, iLength = c.length; i < iLength; i++) {
            a += c.charCodeAt(i).toString(16);
        }
        return a;
    }

    create_script(js) {
        let e = this.create_element('script');
        e.src = js
        this.add_element(e)
    }

    create_element(e = 'script') {
        var e = document.createElement(e);
        return e
    }

    add_element(e) {
        var body = document.querySelector('body');
        body.appendChild(e);
    }

    get_current_url() {
        return location.pathname
    }

    float(price) {
        return parseFloat(price)
    }

}

const Util = new UtilityClass()
export {
    Util
}