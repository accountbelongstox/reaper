class AnnouncementClass {

    all_coins = [];
    exchange_date_list = []
    exchange_coin_type_just_now_dict = {}

    get_coins_tableselector(suffix = "") {
        let id = `.table-box tr ${suffix}`
        return id
    }

    get_all_coin(callback, type = 'request') {
        if (type == 'innerHTML') {
            this.get_allcoins_byhtml(callback)
        } else if (type == 'request') {
            this.get_allcoins_byrequest(callback)
        }
    }

    get_allcoins_byhtml(callback) {
        let coins_tableselector = this.get_coins_tableselector(`.td-name span`)
        let trs = document.querySelectorAll(coins_tableselector)
        let coins = []
        trs.forEach(ele => {
            let coin_name = ele.innerHTML
            coins.push(coin_name)
        })
        if (callback) {
            return callback(coins)
        }
        return coins
    }

    get_allcoins_byrequest(callback) {
        this.get_market_dynamic((data) => {
            let coins = []
            data.forEach(ele => {
                let coin_name = ele.instId
                coins.push(coin_name)
            })
            if (callback) {
                return callback(coins)
            }
        })
    }

    monitoring_coin_change() {
        this.set_compare_stagetitle()
        this.get_all_coin(coins => {
            // Panel.set_info('币总数', coins.length,0)
            coins = Util.coin_name_standardization(coins)
            //是否有新币
            let is_new_coin = this.is_new_coin(coins)
            if (is_new_coin) {
                this.found_new_coinandbuy(is_new_coin)
            }
            this.set_exchange_type_list(coins)
            this.monitoring_coin_change_tick()
        })
    }

    monitoring_coin_change_tick() {
        this.get_market_dynamic((data, time) => {
            this.clear_exchange_type_list('60s', time)
            this.compare_exchange_type_list(data)
            // complished after insert
            this.insert_exchange_type_list(data)
            setTimeout(() => {
                this.monitoring_coin_change_tick()
            }, 1000)
        })
    }

    set_exchange_type_list(coin_names) {
        coin_names.forEach(coin => {
            if (!this.exchange_coin_type_just_now_dict[coin]) {
                this.exchange_coin_type_just_now_dict[coin] = []
            }
        })
    }

    insert_exchange_type_list(data) {
        data.forEach(coin_realtime_data => {
            let coin_name = coin_realtime_data.instId
            this.exchange_coin_type_just_now_dict[coin_name].push(coin_realtime_data)
        })
    }

    get_exchange_type_list(coin_name) {
        return this.exchange_coin_type_just_now_dict[coin_name]
    }

    set_compare_stagetitle() {
        Panel.set_title('5s')
        Panel.set_title('15s')
        Panel.set_title('30s')
        Panel.set_title('45s')
        Panel.set_title('60s')
    }

    compare_exchange_type_list(data) {
        let second_range = (s) => {
            let s_parse = Util.split_wordnumber(s)
            let range = s_parse[0]
            return range
        }
        let second_contrast = {
            '5s': [],
            '15s': [],
            '30s': [],
            '45s': [],
            '60s': [],
        }
        for (let i = 0; i < data.length; i++) {
            let coin_realtime_data = data[i]
            let coin_name = coin_realtime_data.instId
            let now_time = coin_realtime_data.time
            let new_price = coin_realtime_data.lastPrice
            let current_price = coin_realtime_data.lastPrice
            let just_now_list = this.get_exchange_type_list(coin_name)
            just_now_list.forEach(ele => {
                let simple_compare_result = {}
                let last_time = ele.time
                let lastPrice = ele.lastPrice
                let reference_coin = ele.instId
                let time_diff = (now_time - last_time) / 1000
                let price_diff = current_price - lastPrice
                let rate_diff = Rate.rate(current_price, lastPrice)
                simple_compare_result['coin_name'] = coin_name
                simple_compare_result['rate_diff'] = rate_diff
                simple_compare_result['time_diff'] = time_diff
                simple_compare_result['price_diff'] = price_diff
                simple_compare_result['new_price'] = new_price
                simple_compare_result['pre_price'] = lastPrice
                simple_compare_result['reference_coin'] = reference_coin
                if (second_range('5s') == time_diff) {
                    second_contrast['5s'].push(simple_compare_result)
                } else if (second_range('15s') == time_diff) {
                    second_contrast['15s'].push(simple_compare_result)
                } else if (second_range('30s') == time_diff) {
                    second_contrast['30s'].push(simple_compare_result)
                } else if (second_range('45s') == time_diff) {
                    second_contrast['45s'].push(simple_compare_result)
                } else if (second_range('60s') == time_diff) {
                    second_contrast['60s'].push(simple_compare_result)
                }
            })
        }
        this.paste_topanel(second_contrast)
    }

    paste_topanel(second_contrast) {
        // TODO: 需要做三个榜
        // 一个下跌榜,一个上涨榜,一个爬升榜.
        let standardization_coin_name = (coin_name) => {
            return coin_name.split(`-`)[0]
        }
        for (let key in second_contrast) {
            let market_increase = second_contrast[key]
            market_increase.sort((ele, contrast_ele) => {
                return ele.rate_diff > contrast_ele.rate_diff
            })
            let marketinfo_htmllist = ``
            market_increase.forEach((ele) => {
                let coin_name = standardization_coin_name(ele.coin_name)
                let rate_diff = ele.rate_diff
                let reference_coin = standardization_coin_name(ele.reference_coin)
                if (reference_coin == coin_name) {
                    reference_coin = ''
                }else{
                    reference_coin = `/${reference_coin}`
                }
                let time_diff = ele.time_diff
                let new_price = ele.new_price
                let pre_price = ele.pre_price
                let type = ``
                if(rate_diff > 0){
                    type = `green`
                }else{
                    type = `orange`
                }
                marketinfo_htmllist += `<span style="color:${type}">${coin_name}${reference_coin}: ${time_diff}s, rate-dif:${rate_diff},nPrice:${new_price},oPrice:${pre_price}</span><br />`
            })
            if (marketinfo_htmllist) {
                Panel.set_message(marketinfo_htmllist, `success`, key, 1)
            }
        }
    }

    clear_exchange_type_list(before_time = '60s', time) {
        if (!time) {
            time = $$.date_totimestamp()
        }
        let type_just_now_dict = this.exchange_coin_type_just_now_dict
        before_time = Util.get_historydata_beforetime(time, before_time)
        for (let key in type_just_now_dict) {
            let type_just_now_list = type_just_now_dict[key]
            type_just_now_dict[key] = Util.delete_afterdate(type_just_now_list, 'time', before_time)
        }
        this.exchange_coin_type_just_now_dict = type_just_now_dict
    }

    set_date_time(data, time) {
        if (!time) {
            time = $$.date_totimestamp()
        }
        data.forEach((item, index) => {
            item.time = time
            data[index] = item
        })
        return data
    }

    get_market_dynamic(callback) {
        let url = `https://www.okx.com/priapi/v5/rubik/app/public/up-down-rank?t=1667652861556&period=1D&zone=utc8&type=USDT`
        $$.get(url).then((data) => {
            let time = $$.date_totimestamp()
            data = data.data[0]
            let utc8data = data.utc8
            utc8data = this.set_date_time(utc8data, time)
            if (callback) {
                callback(utc8data, time)
            }
        })
    }

    is_new_coin(coins) {
        let new_coins = false
        if (this.all_coins.length != 0) {
            coins.forEach(coin_name => {
                if (!this.all_coins.includes(coin_name)) {
                    new_coins = coin_name
                    return coin_name
                }
            })
        }
        this.all_coins = coins
        return new_coins
    }

    found_new_coinandbuy(new_coin) {
        //新币发行,全买.
        Okx.buy_allnewcoin(new_coin)
    }

    initial() {
        $$.wait_value(`.table-box tr .td-name span`, 'innerHTML', 'string', () => {
            this.monitoring_coin_change()
        })
    }

}

const Announcement = new AnnouncementClass()
export {
    Announcement
}