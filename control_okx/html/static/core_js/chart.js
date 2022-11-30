class ChartClass {

    Okx//Okx操作主类
    chart_list = []
    chart_max_length = 500
    chart_entity = null//为避免重复渲染chart
    tick_count = 0
    chart_pause_draw_token = false
    basic_line_chart_mark_point = []
    data = []

    set_Okx(Okx){
        this.Okx = Okx;
    }

    start_draw() {
        let coin_name = `BAND-USDT`
        let limit = 60000
        let sort = 'desc'
        $$.get('control:get_transaction_data', {
            coin_name,
            limit,
            sort,
        }).then((data) => {
            this.data = data.data
            this.framed_test()
        })
    }

    get_chart_selector(suffix = "") {
        let chart_selector = `${suffix}test-transaction-data`
        return chart_selector
    }

    framed_test() {
        if(this.chart_pause_draw_token == true)return;
        if(this.data.length > 0) {
            let item = this.data.pop()
            let time = $$.timestamp_todate(item[1])
            let historial_price = item[4]
            let tick_info = this.Okx.price_monitoring_tick(historial_price)
            this.tick_count++
            this.basic_line_chart(tick_info,[time, historial_price])
            // setTimeout(() => {
            //     this.framed_test(data)
            // }, 100)
        }
    }

    chart_draw() {
        let max = Math.max(...this.chart_list)
        let min = Math.min(...this.chart_list)
        let test_chart = c3.generate({
            bindto: this.get_chart_selector("#"),
            size: { height: 350 },
            color: { pattern: ["#3f51b5", "#faa700"] },
            data: {
                columns: [
                    ["test_data", 0]
                ]
            },
            axis: { y: { max: max, min: min } },
            grid: { y: { show: !0 } }
        });
        let test_data = {
            columns: [
                ['test_data', ...this.chart_list]
            ]
        };
        test_chart.load(test_data)
    }

    chart_pause_draw() {
        this.chart_pause_draw_token = !this.chart_pause_draw_token
        if(this.chart_pause_draw_token == false){
            this.framed_test()
        }
    }

    basic_line_chart(tick_feedbackinfo,snippet_data){
        this.chart_list.push(snippet_data)
        let current_price = snippet_data[1]
        let current_date = snippet_data[0]
        if (this.chart_list.length > this.chart_max_length) {
            // let new_line_markpoint = []
            // console.log(`index,ele`,this.basic_line_chart_mark_point)
            // this.basic_line_chart_mark_point.forEach((ele,index)=>{
            //     // console.log(`index,ele`,index,ele)
            //     if(ele.coord){
            //         // console.log(`ele.coord`,ele.coord)
            //         ele.coord[0] = ele.coord[0]-1
            //         if(ele.coord[0] > 0){
            //             new_line_markpoint.push(ele)
            //         }
            //     }
            // })
            // // console.log(new_line_markpoint,this.tick_count)
            // this.basic_line_chart_mark_point = new_line_markpoint
            // console.log(`ele.coordafter`,this.basic_line_chart_mark_point)
            // this.chart_list.shift()
        }
        var dateList = this.chart_list.map(function (item) {
            return item[0];
        });
        var valueList = this.chart_list.map(function (item) {
            return item[1];
        });
        let get_publicmarket = (publicmarkey)=>{
            let public_market = {
                name: '',
                coord: [this.tick_count >= this.chart_max_length ? this.chart_list.length : this.tick_count,current_price],
                value:"",
                symbol:"arrow",//'circle', 'rect', 'roundRect', 'triangle', 'diamond', 'pin', 'arrow', 'none','image://http://example.website/a/b.png'
                symbolSize:10,
                // symbolRotate:[180],
                silent:false,
                itemStyle:{
                    color: 'red',
                }//'circle', 'rect', 'roundRect', 'triangle', 'diamond', 'pin', 'arrow', 'none','image://http://example.website/a/b.png'
            }
            if(publicmarkey){                
                for(let key in publicmarkey){
                    public_market[key] = publicmarkey[key]
                }
            }
            return public_market
        }
        // if(tick_feedbackinfo.highestpoint){
        //     this.basic_line_chart_mark_point.push(
        //         get_publicmarket({
        //             symbol:'circle',
        //             itemStyle:{'color':'red'},
        //             symbolSize:1,
        //         })
        //     )
        // }
        // if(tick_feedbackinfo.lowestpoint){
        //     this.basic_line_chart_mark_point.push(
        //         get_publicmarket({
        //             symbolSize:1,
        //             itemStyle:{'color':'green'},
        //         })
        //     )
        // }
        if(tick_feedbackinfo.is_buy === true){
            this.basic_line_chart_mark_point.push(
                get_publicmarket({
                })
            )
        }        
        if(tick_feedbackinfo.is_sale === true){
            this.basic_line_chart_mark_point.push(
                get_publicmarket({
                    itemStyle:{'color':'green'},
                    symbolRotate:[180],
                })
            )
        }
        let option = {
            grid: {
                left: '1%',
                right: '2%',
                bottom: '3%',
                containLabel: true
            },
            tooltip: {
                trigger: 'axis'
            },
            legend: {
                data: ['Max temp', 'Min temp']
            },
            color: ['#3db76b','#4974e0', ],
            calculable: true,
            xAxis: [
                {
                    type: 'category',
                    boundaryGap: true,
                    data: dateList
                }
            ],
            yAxis: [
                {
                    splitLine: { show: false }
                },
                {
                    type: 'value',
                    axisLabel: {
                        formatter: '{value} '
                    }
                }
            ],
            hoverLayerThreshold:3000,
            series: [
                {
                    name: 'exchange_history_data',
                    type: 'line',
                    data: valueList,
                    markPoint: {
                        data: this.basic_line_chart_mark_point
                    },
                    markLine: {
                        data: [
                            { 
                                type: 'min', 
                                name: 'min',
                                lineStyle:{
                                    color:"green" 
                                }
                            },
                            { 
                                type: 'max', 
                                name: 'max',
                                lineStyle:{
                                    color:"red"
                                }
                            }
                        ]
                    },
                    lineStyle: {
                        type :'dotted',
                        normal: {
                            width: 1,
                            shadowColor: 'rgba(0,0,0,0.1)',
                            shadowBlur: 0,
                            shadowOffsetY: 0
                        }
                    },
                }
            ]
        };
        
        if (!this.chart_entity_basic_line_chart) {
            this.chart_entity_basic_line_chart = echarts.init(document.getElementById('basic-line'));
        }
        this.chart_entity_basic_line_chart.setOption(option);
        setTimeout(()=>{
            this.framed_test()
        },2)
    }

    gradiant_line_chart() {
        var dateList = this.chart_list.map(function (item) {
            return item[0];
        });
        var valueList = this.chart_list.map(function (item) {
            return item[1];
        });
        var option = {
            // Make gradient line here
            visualMap: [{
                show: false,
                type: 'continuous',
                seriesIndex: 0,
                min: 0,
                max: 400
            }, {
                show: false,
                type: 'continuous',
                seriesIndex: 1,
                dimension: 0,
                min: 0,
                max: dateList.length - 1
            }],


            title: [{
                left: 'center',
                text: 'Gradient along the y axis'
            }, {
                top: '55%',
                left: 'center',
                text: 'Gradient along the x axis'
            }],
            tooltip: {
                trigger: 'axis'
            },

            xAxis: [{
                data: dateList
            }, {
                data: dateList,
                gridIndex: 1
            }],
            yAxis: [{
                splitLine: { show: false }
            }, {
                splitLine: { show: false },
                gridIndex: 1
            }],
            grid: [{
                bottom: '60%',
                left: '3%',
                right: '3%'
            }, {
                top: '60%',
                left: '3%',
                right: '3%'
            }],

            series: [{
                type: 'line',
                showSymbol: false,
                data: valueList
            }, {
                type: 'line',
                showSymbol: false,
                data: valueList,
                xAxisIndex: 1,
                yAxisIndex: 1
            }]
        };
        if (!this._gradiant_line_chart) {
            this._gradiant_line_chart = echarts.init(document.getElementById("g-line"));
            $(function () {
                // Resize chart on menu width change and window resize
                $(window).on('resize', resize);
                function resize() {
                    setTimeout(function () {
                        this._gradiant_line_chart.resize();
                    }, 200);
                }
            });
        }
        this._gradiant_line_chart.setOption(option);
    }
}

const Chart = new ChartClass()

export {
    Chart,
}