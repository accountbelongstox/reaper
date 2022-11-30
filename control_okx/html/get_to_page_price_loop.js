(()=>{
	class Util{
		#key = '9LrQN0~14,dSmoO^';
		#flask_port = 8800;
		local_url = "http://127.0.0.1";
		api_address = "api";

		constructor(){
			this.load_jquery();
		}

		load_jquery (){
			let js_dir = this.get_local_url("static/js/jquery-3.6.1.min.js");
			this.create_script(js_dir);
			let noConflict = setInterval(()=>{
				if (typeof $ != 'undefined' && $.noConflict){
					clearInterval(noConflict);
					/*JQuery释放$标识符*/
					console.log("Release the JQuery flag.");
					$.noConflict();
				}else{
					console.log("not find $ pramameter.");
				}
			},500)
		}

		create_script(js_dir){
			let element = this.create_element('script');
			element.src = js_dir
			this.add_element(element)
		}

		create_element(element_type = 'script'){
			var element = document.createElement(element_type);
			return element
		}

		add_element(element){
			var body = document.querySelector('body');
			body.appendChild(element);
		}

		get_current_url(){
			return location.pathname
		}

		get_local_url (path){
			let url = `${this.local_url}:${this.#flask_port}`;
			if (path){
				url += `/${path}`;
			}
			return url
		}

		get_api_url(){
			return this.get_local_url(this.api_address)
		}

		float(price){
			return parseFloat(price)
		}

		post(data,callback){
			let post_url = this.get_api_url();
			if(typeof data == 'string'){
				data = {
					data
				}
			}
			/* 添加密钥 */
			data.key = this.key;
			JQuery.getJSON(post_url,data, 
			function(json){
				if (callback){
					callback(json)
				}
			});
		}
	}

	let util = new Util();

	class Main{
		coin_name;
		#market_wind_direction = null;
		increase_interval_time = new Date().getTime();
		rise_benchmark_price = null;
		fell_benchmark_price = null;
		previous_ticker_price = null;
		current_ticker_price = null;
		
		gain_rate = 7;
		decline_rate;
		#debug = false;
		
		constructor(){
			this.decline_rate = this.calculate_decline_rate();
		}

		set_coin_name (){
			/* 系统启动时,先要遇到市场的拐角点,才设置基准点*/
			/* 其中如果拐角点是向上,则设置benchmark+price基准点*/
			/* 如果拐角点是向下,则设置顶点基准点.*/
			/* 有基准点才进行比较,没有基准点仅进行数据采集*/
			/* 将 https://www.okx.com/trade-spot/rsr-usdt 形式的币名提取出来*/
			let url = util.get_window_url();
			let url_len = url.split('/');
			this.coin_name = url_len[url_len.length-1]
			this.coin_name = coin_name.split('-')[0]
			return this.coin_name;
		}
		
		parse_history_data(history_json_string) {
			if(this.#debug){
				history_json_string = `{"code":"0","msg":"","data":[["1664027100000","0.00723","0.00724","0.00723","0.00724","986362.554952","7131.664243"],["1664027040000","0.00722","0.00722","0.00722","0.00722","173265.566938","1250.977393"],["1664026980000","0.00722","0.00722","0.00722","0.00722","48635.873535","351.151006"],["1664026920000","0.00721","0.00722","0.00721","0.00722","162166.790741","1170.561713"],["1664026860000","0.0072","0.00721","0.0072","0.00721","331298.451196","2385.698316"],["1664026800000","0.0072","0.0072","0.0072","0.0072","70051.83143","504.373186"],["1664026740000","0.0072","0.0072","0.0072","0.0072","165677.868114","1192.88065"],["1664026680000","0.0072","0.0072","0.0072","0.0072","541954.754285","3902.07423"],["1664026620000","0.0072","0.00721","0.0072","0.0072","168873.23308","1216.081797"],["1664026560000","0.0072","0.00721","0.0072","0.0072","141080.074543","1016.035608"],["1664026500000","0.0072","0.0072","0.0072","0.0072","58778.308093","423.203818"],["1664026440000","0.00721","0.00721","0.0072","0.0072","524521.674008","3780.210697"],["1664026380000","0.00719","0.0072","0.00718","0.00718","72484.978964","521.496679"],["1664026320000","0.00719","0.00719","0.00719","0.00719","171851.305483","1235.610886"],["1664026260000","0.0072","0.0072","0.00719","0.00719","463981.729471","3336.089704"],["1664026200000","0.0072","0.00721","0.0072","0.00721","337333.651253","2431.402289"],["1664026140000","0.0072","0.0072","0.0072","0.0072","414681.615223","2985.707629"],["1664026080000","0.0072","0.0072","0.0072","0.0072","1151540.266444","8291.089918"],["1664026020000","0.0072","0.0072","0.0072","0.0072","0","0"],["1664025960000","0.0072","0.0072","0.0072","0.0072","12833.022955","92.397765"],["1664025900000","0.0072","0.0072","0.0072","0.0072","0","0"],["1664025840000","0.0072","0.00721","0.0072","0.0072","131916.658358","949.800465"],["1664025780000","0.0072","0.0072","0.0072","0.0072","412577.944619","2970.561201"],["1664025720000","0.0072","0.0072","0.0072","0.0072","18385.0581","132.372418"],["1664025660000","0.00722","0.00722","0.00721","0.00722","168646.934838","1216.242869"],["1664025600000","0.00723","0.00723","0.00722","0.00722","24436.919201","176.47015"],["1664025540000","0.00723","0.00723","0.00722","0.00722","3445.163521","24.88396"],["1664025480000","0.00723","0.00723","0.00723","0.00723","2603468.767214","18823.079186"],["1664025420000","0.00724","0.00724","0.00723","0.00724","1749486.325285","12666.259978"],["1664025360000","0.00727","0.00727","0.00724","0.00724","287676.206962","2087.440275"],["1664025300000","0.00728","0.00728","0.00727","0.00727","394727.922093","2871.682482"],["1664025240000","0.00728","0.00728","0.00728","0.00728","3240.471454","23.590632"],["1664025180000","0.00728","0.00728","0.00727","0.00728","219687.475178","1599.291193"],["1664025120000","0.00726","0.00728","0.00726","0.00728","1155940.540416","8415.168463"],["1664025060000","0.00726","0.00726","0.00726","0.00726","1123296.931429","8155.135722"],["1664025000000","0.00727","0.00728","0.00727","0.00728","914683.966501","6658.898761"],["1664024940000","0.00726","0.00728","0.00726","0.00728","4655457.072108","33888.593679"],["1664024880000","0.00725","0.00725","0.00725","0.00725","77.738408","0.563603"],["1664024820000","0.00726","0.00726","0.00726","0.00726","15477.757025","112.368516"],["1664024760000","0.00727","0.00728","0.00727","0.00727","324519.495267","2359.89573"],["1664024700000","0.00724","0.00727","0.00724","0.00727","121484.914291","881.967371"],["1664024640000","0.00723","0.00723","0.00723","0.00723","0","0"],["1664024580000","0.00723","0.00723","0.00723","0.00723","32923.289876","238.035385"],["1664024520000","0.00722","0.00724","0.00722","0.00724","165839.86909","1198.856427"],["1664024460000","0.00722","0.00722","0.00721","0.00722","3017670.327621","21787.579243"],["1664024400000","0.00722","0.00723","0.00721","0.00723","4861145.632111","35058.067537"],["1664024340000","0.00721","0.00721","0.00721","0.00721","376245.421956","2712.729492"],["1664024280000","0.00721","0.00721","0.00721","0.00721","52.000219","0.374921"],["1664024220000","0.0072","0.0072","0.0072","0.0072","404297.563784","2910.942459"],["1664024160000","0.00719","0.00719","0.00719","0.00719","76144.836701","547.481375"],["1664024100000","0.0072","0.0072","0.00718","0.00719","376778.006314","2706.078765"],["1664024040000","0.00721","0.00721","0.00721","0.00721","0","0"],["1664023980000","0.00721","0.00721","0.00721","0.00721","0","0"],["1664023920000","0.00721","0.00721","0.00721","0.00721","0","0"],["1664023860000","0.00722","0.00722","0.00721","0.00721","471778.909679","3401.593727"],["1664023800000","0.00722","0.00722","0.00722","0.00722","16905.64441","122.058752"],["1664023740000","0.00721","0.00723","0.00721","0.00723","138416.048466","999.049709"],["1664023680000","0.0072","0.0072","0.0072","0.0072","0","0"],["1664023620000","0.00721","0.00721","0.0072","0.0072","20643.284","148.826211"],["1664023560000","0.00722","0.00722","0.00721","0.00721","397616.702865","2867.599499"],["1664023500000","0.00724","0.00724","0.00721","0.00721","850281.006211","6142.848893"],["1664023440000","0.00723","0.00723","0.00722","0.00722","413498.074544","2989.58699"],["1664023380000","0.00723","0.00723","0.00722","0.00722","57067.099246","412.092132"],["1664023320000","0.00722","0.00722","0.00722","0.00722","146280.880821","1056.147959"],["1664023260000","0.00722","0.00722","0.00722","0.00722","117788.361045","850.431966"],["1664023200000","0.00724","0.00724","0.00722","0.00722","501287.852864","3628.72597"],["1664023140000","0.00724","0.00724","0.00724","0.00724","472134.17145","3418.251401"],["1664023080000","0.00722","0.00723","0.00722","0.00723","355318.322139","2566.163796"],["1664023020000","0.00722","0.00722","0.00722","0.00722","0","0"],["1664022960000","0.00719","0.00725","0.00719","0.00722","3810924.449374","27578.295549"],["1664022900000","0.00718","0.00718","0.00718","0.00718","65000","466.7"],["1664022840000","0.00717","0.00717","0.00717","0.00717","68646.233406","492.193493"],["1664022780000","0.00715","0.00715","0.00715","0.00715","0","0"],["1664022720000","0.00715","0.00715","0.00715","0.00715","65000","464.75"],["1664022660000","0.00716","0.00716","0.00716","0.00716","0","0"],["1664022600000","0.00716","0.00716","0.00716","0.00716","417273.221958","2987.676269"],["1664022540000","0.00715","0.00715","0.00715","0.00715","0","0"],["1664022480000","0.00715","0.00715","0.00715","0.00715","0","0"],["1664022420000","0.00715","0.00715","0.00715","0.00715","8699.838045","62.203842"],["1664022360000","0.00716","0.00716","0.00715","0.00716","159011.762834","1138.383517"],["1664022300000","0.00717","0.00719","0.00716","0.00716","1413397.56505","10159.453607"],["1664022240000","0.00717","0.00718","0.00717","0.00718","17633.005911","126.429301"],["1664022180000","0.00716","0.00718","0.00716","0.00718","464200.172859","3328.176694"],["1664022120000","0.00715","0.00715","0.00715","0.00715","65000","464.75"],["1664022060000","0.00714","0.00714","0.00714","0.00714","0","0"],["1664022000000","0.00714","0.00714","0.00714","0.00714","0","0"],["1664021940000","0.00714","0.00714","0.00714","0.00714","26.695538","0.190606"],["1664021880000","0.00714","0.00714","0.00714","0.00714","0","0"],["1664021820000","0.00714","0.00714","0.00714","0.00714","65000","464.1"],["1664021760000","0.00714","0.00714","0.00714","0.00714","620464.489886","4430.116457"],["1664021700000","0.00714","0.00714","0.00714","0.00714","3738.519965","26.693032"],["1664021640000","0.00713","0.00714","0.00713","0.00714","260158.936469","1856.745927"],["1664021580000","0.00713","0.00713","0.00713","0.00713","27493.305492","196.027268"],["1664021520000","0.00714","0.00714","0.00714","0.00714","9093.37304","64.926683"],["1664021460000","0.00713","0.00713","0.00713","0.00713","9194.701262","65.558219"],["1664021400000","0.00714","0.00714","0.00714","0.00714","183093.151339","1307.2851"],["1664021340000","0.00715","0.00715","0.00715","0.00715","147236.31723","1052.739668"],["1664021280000","0.00715","0.00715","0.00714","0.00714","86812.92097","620.711583"],["1664021220000","0.00714","0.00714","0.00714","0.00714","205670.389528","1468.486581"],["1664021160000","0.00714","0.00714","0.00714","0.00714","64756.548655","462.361757"]]}`;
			}
			let history_json = JSON.parse(history_json_string);
			let history_data = history_json.data;
			return history_data;
		}

		calculate_decline_rate(){
			return -this.gain_rate;
		}

		get_history_data(){
			let url = "https://www.okx.com/priapi/v5/market/history-candles?instId=RSR-USDT&bar=1m&after=1663894920000&limit=100&t=1663957030130"
		}

		get_real_time_prices (){
			let ticker_price_selector = `.price-wrap > .ticker-price`;
			if(!this.price_displayer){
				this.price_displayer = document.querySelector(ticker_price_selector);
			}
			let ticker_price = this.price_displayer.textContent;
			ticker_price = util.float(ticker_price)
			return ticker_price;
		}

		whether_to_increase(){
			let is_increase;
			//首先如果之前的值没有则刚启动不能判断.
			if(!this.previous_ticker_price || this.current_ticker_price == this.previous_ticker_price){
				is_increase = null;
			}else if(this.current_ticker_price > this.previous_ticker_price){
				is_increase = true;
			}else{
				is_increase = false;
			}
			return is_increase
		}

		set_benchmark_price(ticker_price,replace=false){
			if (!this.benchmark_price || replace == true){
				this.benchmark_price = ticker_price
			}
		}
		
		up_to_standard(dynamic_gain_ratio,is_increase){
			dynamic_gain_ratio = Math.abs(dynamic_gain_ratio)
			let result;
			if(is_increase){
				if(dynamic_gain_ratio >= this.gain_rate) result=true;
			}else{
				if(dynamic_gain_ratio <= this.decline_rate) result=false;
			}
		}

		gain_compare(ticker_price,is_increase){
			// 返回值为:
			// 超过涨幅比率则为true
			// 跌出跌幅比率则为false
			// 区间价格则为null
			let poor_increase;
			if (is_increase){
				poor_increase = ticker_price - this.benchmark_price;
			}else{
				poor_increase = this.benchmark_price - ticker_price;
			}
			let dynamic_gain_ratio = (poor_increase / this.benchmark_price) * 100;
			if(is_increase){
				dynamic_gain_ratio = +dynamic_gain_ratio;
			}else{
				dynamic_gain_ratio = -dynamic_gain_ratio;
			}
			return dynamic_gain_ratio
		}

		set_market_wind_direction(market_wind_direction){
			this.#market_wind_direction = market_wind_direction;
		}		

		market_turning_point(is_increase){
			//当市场反转时,没有跌破幅度不重新设置高点
			//当市场反转为上涨时,设置有一个幅度
			if(is_increase !== this.#market_wind_direction){
				this.#market_wind_direction = is_increase;
				return true;
			}
			return false;
		}

		can_be_traded_in_the_event_of_a_market_reversal(ticker_price){
			let is_market_turning_point = this.market_turning_point();
			if(!is_market_turning_point)return;
			//当市场上涨达预期时,则在以下开始交易.
			let gain_expect = this.gain_compare(ticker_price,this.#market_wind_direction);
			if(this.#market_wind_direction){
				//当市场反转时,在没有涨到基础预期时不交易但涨到了基本预期则交易
				if(gain_expect >= this.up_to_standard ){
					console.log(`ticker price already up to standard: ${gain_expect}, ticker_price is ${ticker_price}`);
					console.log(`buy coin by price ${ticker_price}`);
					return
				}
				console.log(`未达预期则只继续监控.`)
			}else{
				if(Math.abs(gain_expect) > this.fell_benchmark_price){
					console.log(`sell coin by price ${ticker_price}`);
					return false;
				}else{
					console.log(`未降到预期继续观察.`)
				}
			}
			return null
		}

		ticker_price_source(){
			let ticker_price;
			if(!this.#debug){
				// 非测试状态下拿实时数据.
				ticker_price = this.get_real_time_prices();
			}else{
				if(!this.debug_test_ticker_price_index){
					this.debug_test_ticker_price_index = 0;
				}
				if(!this.debug_test_ticker_price_data){
					this.debug_test_ticker_price_data = this.parse_history_data();
				}
				if(this.debug_test_ticker_price_index == this.debug_test_ticker_price_data.length){
					this.debug_test_ticker_price_index = 0;
				}
				ticker_price = this.debug_test_ticker_price_data[this.debug_test_ticker_price_index][1];
				this.debug_test_ticker_price_index++;
			}
			this.current_ticker_price = ticker_price;
			return ticker_price;
		}

		get_to_page_price_loop(){
			// 如果是测试模式,则直接拿内置数据
			// 否则拿实时数据
			let ticker_price = this.ticker_price_source();
			this.set_benchmark_price(ticker_price);
			// 价格没有改变的时候不作任何操作,以节省内存
			if (!this.is_ticker_price_change(ticker_price)){
				return;
			}
			//价格有改变时由先设计价格方
			let is_increase = this.whether_to_increase();
			this.set_market_wind_direction(is_increase);
			if(this.#debug){
				let chart = new Chart();
				chart.set_axis_chart(ticker_price);
			}
			this.can_be_traded_in_the_event_of_a_market_reversal(ticker_price);//当时交易时机的时候交易
			return ticker_price;
			// let is_increase = this.whether_to_increase();
			// let dynamic_gain_ratio_price = this.gain_compare(ticker_price,is_increase);
			// let up_to_standard = this.up_to_standard(dynamic_gain_ratio_price,is_increase);
			// if (up_to_standard === true){/*涨了7%*/
			// 	let data = {
			// 		'ticker_price': ticker_price,
			// 		'method': 'get_page_per_ticker_price',
			// 		'is_increase':is_increase
			// 	};
			// 	if (!this.#debug){
			// 		util.post(data)/*将消息传回服务器*/
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

		compare_data_prices(){
			let tick = 0;
			setInterval(()=>{
				this.get_to_page_price_loop();
				tick++;
			},1000)
		}
		
	}
	let main = new Main();
	main.compare_data_prices()

	class Chart{
		set_axis_chart(ticker_price) {
			if(!this.history_ticker_price_list){
				this.history_ticker_price_list = [];
			}
			this.history_ticker_price_list.push(ticker_price);
			this.test_chart_set();
		}

		test_chart_set(){
			let css_chart = "#axis-timezone";
			let test_chart = c3.generate({
				bindto: css_chart,
				size: { height: 350 },
				color: { pattern: ["#3f51b5", "#faa700"] },
				data: {
					columns: [
						["test_data", 0]
					]
				},
				axis: { y: { max: 0.008, min: 0.007 } },
				grid: { y: { show: !0 } }
			});
			let current_data = {
				columns: [
					['test_data', ...this.history_ticker_price_list]
				]
			};
			test_chart.load(current_data)
		}

		is_ticker_price_change(ticker_price){
			return this.previous_ticker_price != ticker_price;
		}
	}
})()