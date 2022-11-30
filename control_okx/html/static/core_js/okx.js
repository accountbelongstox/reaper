import { Panel } from 'https://local.12gm.com/static/core_js/panel.js'
import { Chart } from 'https://local.12gm.com/static/core_js/chart.js'
import { Util } from 'https://local.12gm.com/static/core_js/utility.js'
import { Rate } from 'https://local.12gm.com/static/core_js/rate.js'
import { Test } from 'https://local.12gm.com/static/core_js/test_data.js'
import { Announcement } from 'https://local.12gm.com/static/core_js/announcement.js'
window.Panel = Panel
window.Chart = Chart
window.Util = Util
window.Test = Test
window.Rate = Rate
window.Announcement = Announcement
if (typeof window != 'undefined' && !window.$$) {
    window.$$ = document.$$;
}

class OkxClass {
    // TODO: 网页需要恢复机制 
    coin_name;
    previous_market_direction = null//上一个市场方向,如果与现在的方向相反即说明出现市场反转
    increase_interval_time = new Date().getTime();
    highestpoint_from_benchmarkpoint = null//基于市场基准点的最高点
    highestpoint_from_benchmarkpoints = [];//最高点组,将用来分析市场趋势时与最低点集比较
    //从基准点到当前的数据队列
    //为保证该数据安全,数据需要存到数据库
    lowestpoint_from_benchmarkpoint = null//基于市场基准点的最低点
    lowestpoint_from_benchmarkpoints = [];//最低点组,将用来分析市场趋势时与最高点集比较
    change_status = null//当前交易状态,true为持有/false为未持有
    tick_count = 0

    benchmark_price = null//初始市场基准点
    queue_from_benchmark_point_to_current = []
    rise_benchmark_price = null;
    fell_benchmark_price = null;
    previous_ticker_price = null;
    gain_rate = 0.026;
    sale_rate = 0.01;
    investment_amount = 10000//测试投入金额
    profit_and_loss = 10000
    decline_rate;
    #debug = null;
    ticker_price_element = null;//为减小重复查找元素设置的类属性
    buy_ticker_price = 0;
    //忽然下跌只要微微上涨就要买
    //长期横盘将直接出掉.
    //价格走出下跌势时这支股票出掉(即亏掉一部份钱后)
    //急跌模式,急涨模式判断 两个价格之间忽然悬殊X定为急跌 或在多少秒内价格多个证实悬殊
    //要随时用1万块钱去炒
    //市场总体不向好的时候预期调低
    expect = 0.2

    fluctuation = 0.0025143678160919965//标准振幅范围
    thirtysecond_sharp_rise = 0.0230905861456483//30秒上涨比例
    #market_direction = null
    #market_direction_ups = []
    #market_direction_downs = []
    vibration_previous_price = 0

    constructor() {

    }

    initial() {
        //交易方法会排斥以下方法
        let pathname = window.location.pathname
        let hostname = window.location.hostname
        console.log('Okx load ok.')
        if (pathname.startsWith('/trade-spot/')) {
            this.monitoring_changes()//会排斥以下方法
        } else if (pathname.startsWith('/markets/explore/')) {
            this.nonitoring_gainers_losers()
        } else if (hostname.startsWith('local.12gm.com')) {
            this.test_change_data_front()
        }
    }

    monitoring_changes() {
        let ticker_price_selector = this.get_ticker_price_selector()
        $$.wait_value(ticker_price_selector, 'innerHTML', 'float', () => {
            this.intialize_ofhtml()
            this.listen_buttom()
            console.log('start monitoring changes')
            this.#debug = false
            $$.set_stop_wait_ele(true)
            this.monitoring_change_tick()
        })
    }

    nonitoring_gainers_losers() {
        this.intialize_ofhtml()
        this.listen_buttom()
        console.log('start nonitoringgainers_losers')
        Announcement.initial()
    }

    test_change_data_front() {
        const test_url = `local.12gm.com`
        if (window.location.hostname == test_url) {
            this.intialize_ofhtml('#chat-box-body .chat-box', "")
            this.#debug = true
            $$.set_stop_wait_value(true)
            Chart.set_Okx(this)
            Chart.start_draw()
        }
    }

    intialize_ofhtml(insert_panel_selector = 'body', panel_id = null) {
        Panel.set_panel_html(insert_panel_selector)
        if (panel_id === null) {
            panel_id = Panel.get_panel_id("#")
        }
        $$.bind(this, panel_id, Panel, Chart)
    }

    set_coin_name() {
        /* 系统启动时,先要遇到市场的拐角点,才设置基准点*/
        /* 其中如果拐角点是向上,则设置benchmark+price基准点*/
        /* 如果拐角点是向下,则设置顶点基准点.*/
        /* 有基准点才进行比较,没有基准点仅进行数据采集*/
        /* 将 https://www.okx.com/trade-spot/rsr-usdt 形式的币名提取出来*/
        let url = window.location.pathname;
        let url_len = url.split('/');
        this.coin_name = this.get_coin_name()
        return this.coin_name;
    }


    calculate_decline_rate() {
        return -this.gain_rate;
    }

    on_getallhistorydata(is_continue = true) {
        if (!this.get_coin_name()) {
            console.log('current page is not coin exchange page.')
            alert('the page is not coin exchange page')
            return
        }
        this.gettinghistorydatapause = is_continue
        if (is_continue) {
            this.get_all_historydata()
        }
    }

    put_transaction_data(point_data) {
        let coin_name = this.get_coin_name()
        $$.post('control:put_transaction_data', {
            coin_name: coin_name,
            transaction: JSON.stringify(point_data),
        }).then((data) => {
            console.log(data)
        })
    }

    get_transaction_data(time, limit = '1000') {
        let coin_name = this.get_coin_name()
        $$.get('control:get_transaction_data', {
            coin_name: coin_name,
            time: time,
            limit,
        }).then((data) => {
            console.log(data)
        })
    }

    parse_history_data(history_json_string) {
        let history_data = history_json_string
        if (typeof history_json_string === 'string') {
            history_data = JSON.parse(history_data);
        }
        history_data = history_data.data ? history_data.data : history_data;
        return history_data;
    }

    get_all_historydata(date, index = 0) {
        if (!date) {
            if (this.gettinghistorydatatampary) {
                date = this.gettinghistorydatatampary
                this.gettinghistorydatatampary = null
            }
            date = new Date()
        } else {
            if ($$.numeric(date)) {
                date = parseInt(date)
            }
            date = new Date(date)
        }
        let t = Date.parse(date);
        if (!this.gettinghistorydatapause) {
            this.gettinghistorydatatampary = t
            console.log(`request-pause:index=${index},pause-time=${this.gettinghistorydatatampary}`)
            return
        }
        this.get_history_data(t,).then((data) => {
            data = this.parse_history_data(data)
            if (!data) {
                console.log(`request-faid:index=${index},re-request=${t}`)
                setTimeout(() => {
                    this.get_all_historydata(t, index)
                }, 1000)
                return
            }
            this.put_transaction_data(data)
            let l = data.length
            let next_t = null
            if (l == 100) {
                next_t = data[100 - 1][0]
                next_t = parseInt(next_t) - 60000//此处为向前推60秒
            }
            if (next_t) {
                setTimeout(() => {
                    index++
                    this.get_all_historydata(next_t, index)
                }, 500)
            }
            next_t = $$.timestamp_todate(next_t)
            console.log(`requested:index=${index},length=${l},nextreqeust=${next_t}`)
            // data.forEach((item)=>{
            //     let time = item[0]
            //     time = $$.timestamp_todate(time)
            //     item[0] = time
            // })
        })
    }

    get_coin_name() {
        let coin_name_title = document.querySelector('h1.ticker-title')
        if (!coin_name_title) return null;

        let coin_name = coin_name_title.innerHTML.trim()
        if (!coin_name) {
            coin_name = window.location.pathname.split(/\/+/).pop()
            coin_name = coin_name.trim()
        }
        coin_name = Util.coin_name_standardization(coin_name)
        return coin_name
    }

    get_history_data(t, coin_name, bar = '1m') {
        let after = Util.get_historydata_beforetime(t, '1Day')
        after = Util.timesecond_tomillisecond(after)
        t = Util.timesecond_tomillisecond(t)
        if (!coin_name) {
            coin_name = this.get_coin_name()
        }
        if (!coin_name) {
            return null
        }
        coin_name = coin_name.replaceAll('/', '-')
        let url = `https://www.okx.com/priapi/v5/market/history-candles?instId=${coin_name}&bar=${bar}&after=${after}&limit=100&t=${t}`
        return new Promise((resolve, reject) => {
            $$.get(url).then((data) => {
                console.log(data)
                data = data.data
                if (data) {
                    data.forEach((ele, index) => {
                        let time = ele[0]
                        time = $$.timestamp_todate(time)
                        ele.push(time)
                        data[index] = ele
                    })
                }
                console.log(`request history_data`, data)
                resolve(data)
            })
        })
    }


    get_ticker_price_selector() {
        let pricesid = `.ticker-last-box .last`
        return pricesid
    }

    get_real_time_prices() {
        if (!this.ticker_price_element) {
            let ticker_price_selector = this.get_ticker_price_selector()
            this.ticker_price_element = document.querySelector(ticker_price_selector)
        }
        let ticker_price = this.ticker_price_element.innerText;
        ticker_price = parseFloat(ticker_price)
        return ticker_price;
    }

    judging_sharp_decline(current_price) {
        let fluctuation = 0.003
        let fluctuation_bytime = 0.002
        let shock = $$.rate(current_price, this.vibration_previous_price)
        if (shock > fluctuation) {
            //出现趋势更新振幅判断趋势价格
            this.vibration_previous_price = current_price
            this.vibration_previous_time = $$.date_totimestamp()
            return true
        }
        //不出现振幅将不更新振幅判断价格
        let time = $$.date_totimestamp()
        if (time - this.vibration_previous_tim < 60 && shock > fluctuation_bytime) {
            return true
        }
    }

    //判断市场趋势根据网页上的标识
    whether_increase(current_price) {
        if (this.vibration_previous_price == 0) {
            this.vibration_previous_price = current_price
        }
        let shock = $$.rate(current_price, this.vibration_previous_price)
        if (Math.abs(shock) > this.fluctuation) {
            let time = $$.date_totimestamp()
            if (shock < 0) {
                this.#market_direction = true
                this.#market_direction_ups.push({
                    time: time,
                    market_direction: this.#market_direction
                })
            } else {
                this.#market_direction = false
                this.#market_direction_downs.push({
                    time: time,
                    market_direction: this.#market_direction
                })
            }
            //出现趋势更新振幅判断趋势价格
            this.vibration_previous_price = current_price
            this.vibration_previous_time = $$.date_totimestamp()
        }
        let vibration_difference = Math.abs(this.vibration_previous_price * this.fluctuation)
        let roof_vibration_price = this.vibration_previous_price + vibration_difference
        let botom_vibration_price = this.vibration_previous_price - vibration_difference
        Panel.set_info('市场趋势', `${this.#market_direction}`)
        Panel.set_info('振幅范围', `${roof_vibration_price} - ${botom_vibration_price}`)
        return this.#market_direction
    }

    set_benchmark_price(ticker_price, replace = false) {
        if (!this.benchmark_price || replace == true) {
            this.benchmark_price = ticker_price
            let time = $$.create_time()
            //设置基准点时,从基准点到当前的数据队列就要删空这是计算最高点和最低点的基准
            this.queue_from_benchmark_point_to_current = []
            //设置市场基准点的时候最高点和最低点都要清掉
            this.highestpoint_from_benchmarkpoint = null
            this.lowestpoint_from_benchmarkpoint = null
            Panel.set_info('基准点', `${ticker_price} /[${time}]`)
        }
    }

    get_benchmark_price() {
        return this.benchmark_price
    }

    //获取数据大体方向
    get_overall_market_directions() {
        // TODO: 除了对比涨跌次数,还要对比涨跌幅度
        let get_length = (ups_or_down) => {
            let ups_length = ups_or_down.length
            if (ups_length == 0) {
                return ups_or_down
            }
            let last_element = ups_or_down[ups_length - 1]
            let last_time = last_element.time
            let six_hour_after_time = $$.date_totimestamp() - 60 * 60 * 6
            //有6个小时之前的数据, 需要清除
            if (six_hour_after_time > last_time) {
                let new_ups = []
                ups_or_down.forEach((ele) => {
                    if (ele.time >= six_hour_after_time) {
                        new_ups.push(ele)
                    }
                })
                ups_or_down = new_ups
            }
            return ups_or_down
        }
        this.#market_direction_ups = get_length(this.#market_direction_ups)
        this.#market_direction_downs = get_length(this.#market_direction_downs)
        let overall_direction = this.#market_direction_ups.length > this.#market_direction_downs.length
        Panel.set_info('大体趋势', overall_direction)
        return overall_direction
    }

    get_highestpoint_from_benchmarkpoint() {
        if (this.highestpoint_from_benchmarkpoint === null) {
            //如果还没有值大于基准点则最高点就是基准点
            this.highestpoint_from_benchmarkpoint = this.benchmark_price
        }
        //如果已经有一个值大于基准点,则这个值是上一个最高点
        return this.highestpoint_from_benchmarkpoint
    }

    is_highestpoint_from_benchmarkpoint(point) {
        //如果当前值大于上一个最高点,即当前值是链中的最高点
        //则直接判断是否大于基准点,大于基准点即是最高点
        return point > this.get_highestpoint_from_benchmarkpoint()
    }

    set_highestpoint_from_benchmarkpoint(point) {
        let set_highestpoint = (highestpoint) => {
            this.highestpoint_from_benchmarkpoint = highestpoint
            let time = $$.create_time()
            this.highestpoint_from_benchmarkpoints.push({
                time,
                price: highestpoint,
            })
            Panel.set_info('最高点', `${this.highestpoint_from_benchmarkpoint} /[${time}]`)
        }

        if (this.highestpoint_from_benchmarkpoint === null) {
            //如果还没有值大于基准点则最高点就是基准点
            set_highestpoint(this.benchmark_price)
        }
        //满足大于上一最高点的前提下,
        //设置为最高点
        if (point > this.highestpoint_from_benchmarkpoint) {
            set_highestpoint(point)
            return true
        }
        return false
        // if(this.is_highestpoint_from_benchmarkpoint(point)){
        //     this.highestpoint_from_benchmarkpoint = point
        // }//不需要这段
    }

    get_lowestpoint_from_benchmarkpoint() {
        if (this.lowestpoint_from_benchmarkpoint === null) {
            //如果还没有值大于基准点则最高点就是基准点
            this.lowestpoint_from_benchmarkpoint = this.benchmark_price
        }
        //如果已经有一个值大于基准点,则这个值是上一个最高点
        return this.lowestpoint_from_benchmarkpoint
    }

    is_lowestpoint_from_benchmarkpoint(point) {
        //如果当前值大于上一个最高点,即当前值是链中的最高点
        //则直接判断是否大于基准点,大于基准点即是最高点
        return point < this.get_lowestpoint_from_benchmarkpoint()
    }

    set_lowestpoint_from_benchmarkpoint(point) {
        let set_lowestpoint = (lowestpoint) => {
            this.lowestpoint_from_benchmarkpoint = lowestpoint
            let time = $$.create_time()
            this.lowestpoint_from_benchmarkpoints.push({
                time,
                price: lowestpoint,
            })
            Panel.set_info('最低点', `${this.lowestpoint_from_benchmarkpoint} /[${time}]`)
        }

        if (this.lowestpoint_from_benchmarkpoint === null) {
            //如果还没有值大于基准点则最高点就是基准点
            set_lowestpoint(this.benchmark_price)
        }
        //满足大于上一最高点的前提下,
        //设置为最高点
        if (point < this.lowestpoint_from_benchmarkpoint) {
            set_lowestpoint(point)
            return true
        }
        return false
        // //不需要这段
    }

    is_sale_time(ticker_price) {
        let sale_price = this.highestpoint_from_benchmarkpoint * (1 - this.sale_rate)
        if (ticker_price <= sale_price || ticker_price < this.benchmark_price /*||*/) {
            return true
        }
        return sale_price
    }

    is_buy_time(ticker_price) {
        //买入时机还需要读前面的数据看是否已经一直在涨,
        //目前只是在测试
        let buy_price = this.lowestpoint_from_benchmarkpoint * (1 + this.gain_rate)
        if (ticker_price >= buy_price) {
            return true
        }
        return buy_price
    }

    up_to_standard(dynamic_gain_ratio, is_increase) {
        dynamic_gain_ratio = Math.abs(dynamic_gain_ratio)
        let result;
        if (is_increase) {
            if (dynamic_gain_ratio >= this.gain_rate) result = true;
        } else {
            if (dynamic_gain_ratio <= this.decline_rate) result = false;
        }
    }

    gain_compare(ticker_price, is_increase) {
        // 返回值为:
        // 超过涨幅比率则为true
        // 跌出跌幅比率则为false
        // 区间价格则为null
        let poor_increase;
        if (is_increase) {
            poor_increase = ticker_price - this.benchmark_price;
        } else {
            poor_increase = this.benchmark_price - ticker_price;
        }
        let dynamic_gain_ratio = (poor_increase / this.benchmark_price) * 100;
        if (is_increase) {
            dynamic_gain_ratio = +dynamic_gain_ratio;
        } else {
            dynamic_gain_ratio = -dynamic_gain_ratio;
        }
        return dynamic_gain_ratio
    }

    set_market_direction(market_direction) {
        this.#market_direction = market_direction;
    }

    //判断是否市场反转点
    is_market_turning_point() {
        //当市场反转时,没有跌破幅度不重新设置高点
        //当市场反转为上涨时,设置有一个幅度
        if (this.#market_direction !== this.previous_market_direction) {
            this.previous_market_direction = this.#market_direction
            this.get_overall_market_directions()
            return true
        }
        return false;
    }

    can_be_traded_in_the_event_of_a_market_reversal(ticker_price) {
        let is_market_turning_point = this.is_market_turning_point();
        if (!is_market_turning_point) return;
        //当市场上涨达预期时,则在以下开始交易.
        let gain_expect = this.gain_compare(ticker_price, this.#market_direction);
        if (this.#market_direction) {
            //当市场反转时,在没有涨到基础预期时不交易但涨到了基本预期则交易
            if (gain_expect >= this.up_to_standard) {
                console.log(`ticker price already up to standard: ${gain_expect}, ticker_price is ${ticker_price}`);
                console.log(`buy coin by price ${ticker_price}`);
                return
            }
            console.log(`未达预期则只继续监控.`)
        } else {
            if (Math.abs(gain_expect) > this.fell_benchmark_price) {
                console.log(`sell coin by price ${ticker_price}`);
                return false;
            } else {
                console.log(`未降到预期继续观察.`)
            }
        }
        return null
    }

    buy_actionexecute() {

    }

    buy_something(ticker_price) {
        this.change_status = true
        this.buy_info = {
            price: ticker_price,
            time: $$.create_time(),
        }
    }
    sale_allhold(ticker_price) {
        let sale_price = ticker_price
        let buy_price = this.buy_info.price
        let buy_time = this.buy_info.time
        let sale_time = $$.create_time('h:m')
        let difference = sale_price - buy_price
        difference = difference / sale_price
        let investment_amount = this.investment_amount
        let profit = this.investment_amount * difference
        this.profit_and_loss = this.investment_amount + profit
        this.investment_amount = this.profit_and_loss
        let warn = ""
        if (profit < 0) {
            warn = 'warn'
        }
        profit = Math.round(parseInt(profit))
        difference = $$.keep_pointtostring(difference, 3)
        investment_amount = parseInt(investment_amount)
        let balance = parseInt(this.investment_amount)
        let coin_name = this.get_coin_name()
        let url = window.location.hostname
        let message = `
        principal: ${investment_amount} / ${coin_name}<br/>
        buy: ${buy_price}, sale: ${sale_price} diff: ${difference} <br />
        balance: ${balance} lucro:${profit}<br />
        (${buy_time}-${sale_time})
        `
        this.change_status = false
        Panel.set_message(message, warn)
        Panel.set_info('盈利', this.profit_and_loss)
        $$.post('control:test_change_data', {
            coin_name,
            url,
            investment_amount,
            difference,
            balance,
            profit,
            buy_price,
            buy_time,
            sale_price,
            sale_time,
            message
        }).then((data) => {
            console.log(data)
        })
    }

    price_monitoring_tick(ticker_price) {
        if (!ticker_price) {// 如果是测试模式,则直接拿内置数据 // 否则拿实时数据
            ticker_price = this.get_real_time_prices();
        }
        let tick_time = $$.create_time()
        Panel.set_info('当前时间', tick_time)
        if (!this.is_ticker_price_change(ticker_price)) {// 价格没有改变的时候不作任何操作,以节省内存
            console.log(`price not changed ticker_price ${ticker_price},this.previous_ticker_price${this.previous_ticker_price}`)
            return;
        }
        this.set_benchmark_price(ticker_price);
        let the_tick_info = {}
        Panel.set_info('当前价格', ticker_price)
        let hold_status = this.change_status ? "持有" : "观察中";
        Panel.set_info('状态', `<font style="red">${hold_status}</fong>`)
        //价格有改变时由先设计价格方
        let is_increase = this.whether_increase(ticker_price);
        the_tick_info['is_increase'] = is_increase
        //如果当前已持有,则寻机卖出
        if (this.change_status) {
            //判断当前价格是否是最高点
            let is_highestpoint = this.set_highestpoint_from_benchmarkpoint(ticker_price)
            the_tick_info['is_highestpoint'] = is_highestpoint
            //如果已经是最高点,则不用判断出售.以减少运算量
            if (!is_highestpoint) {
                //对于非最高点的价格,需要判断是否在最佳出售时机
                let goodchance_sale_price = this.is_sale_time(ticker_price)
                the_tick_info['is_sale'] = goodchance_sale_price
                if (goodchance_sale_price === true) {
                    Panel.set_info('出售价', `${ticker_price} /[${tick_time}]`)
                    // 在此出售
                    this.sale_allhold(ticker_price)
                    // 出售后就重置基准值kill
                    this.set_benchmark_price(ticker_price, true);
                    the_tick_info['sale_price'] = ticker_price
                } else {
                    Panel.set_info('预期售价', goodchance_sale_price)
                    the_tick_info['sale_price'] = goodchance_sale_price
                }
            }
        }
        if (!this.change_status) {
            let is_lowestpoint = this.set_lowestpoint_from_benchmarkpoint(ticker_price)
            the_tick_info['is_lowestpoint'] = is_lowestpoint
            if (!is_lowestpoint) {
                //如果不是最低点,则可以考虑买入.
                let goodchance_buy_price = this.is_buy_time(ticker_price)
                the_tick_info['is_buy'] = goodchance_buy_price
                if (goodchance_buy_price === true) {
                    Panel.set_info('买入价', `${ticker_price} /[${tick_time}]`)
                    //在此买入
                    this.buy_something(ticker_price)
                    the_tick_info['buy_price'] = ticker_price
                } else {
                    Panel.set_info('预期买入价', goodchance_buy_price)
                    the_tick_info['buy_price'] = goodchance_buy_price
                }
            }
        }
        let market_turning_point = this.is_market_turning_point();
        if (market_turning_point == true) {
            Panel.set_info('市场反转点', `${ticker_price} /${tick_time}`)
        }
        the_tick_info['market_turning_point'] = market_turning_point
        if (false) {
            this.set_market_direction(is_increase);
            this.can_be_traded_in_the_event_of_a_market_reversal(ticker_price);//当时交易时机的时候交易
        }
        the_tick_info['hold_status'] = this.change_status
        the_tick_info['highestpoint'] = this.get_highestpoint_from_benchmarkpoint()
        the_tick_info['lowestpoint'] = this.get_lowestpoint_from_benchmarkpoint()
        the_tick_info['benchmark_price'] = this.set_benchmark_price()
        the_tick_info['tick_time'] = tick_time
        this.tick_count++
        Panel.set_info('市场监视tick', this.tick_count)
        return the_tick_info;
        // let is_increase = this.whether_increase();
        // let dynamic_gain_ratio_price = this.gain_compare(ticker_price,is_increase);
        // let up_to_standard = this.up_to_standard(dynamic_gain_ratio_price,is_increase);
        // if (up_to_standard === true){/*涨了7%*/
        // 	let data = {
        // 		'ticker_price': ticker_price,
        // 		'method': 'get_page_per_ticker_price',
        // 		'is_increase':is_increase
        // 	};
        // 	if (!this.#debug){
        // 		Util.post(data)/*将消息传回服务器*/
        // 	}else{
        // 		console.log(`Data is not sent back to the server, debug status.`)
        // 	}
        // 	/*#跟随走势走*/
        // 	this.set_benchmark_price(coin,replace=true)
        // }else if(up_to_standard === false){/*#跌了了7%*/
        // 	console.log(`\n{coin_name} coin fell 7%`)
        // 	this.set_benchmark_price(coin,replace=True)
        // }else{
        // 	console.log(`The current price is: ${ticker_price}, with no change.`)
        // }
    }

    is_ticker_price_change(ticker_price) {
        let is_price_changed = this.previous_ticker_price != ticker_price
        if (is_price_changed) {
            this.previous_ticker_price = ticker_price
        }
        return is_price_changed
    }

    monitoring_change_tick(interval = 500) {
        Panel.set_info('投资总额', this.investment_amount)
        setInterval(() => {
            this.price_monitoring_tick();
        }, interval)
    }

    key_events() {

    }

    //给添加的元素添加监听事件
    listen_buttom() {
        //this.translate_wordtotran()
        $$.listen('#my_bing_putwords_botton', 'click', () => {
            if (confirm(`是否确定使用OKX交易`)) {
                let point = 'up'
                $$.post("put_point", {
                    point: point,
                    incremental: true
                }).then((result) => {
                    console.log(result)
                })

            }
        })
        // window.onkeydown = this.key_events
    }
}
window.OkxClass = new OkxClass()
window.OkxClass.initial()