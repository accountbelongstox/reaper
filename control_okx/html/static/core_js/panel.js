class PanelClass {
    panel_element = {
        info: {},
        title: {}
    }

    get_panel_html() {
        let panel_id = this.get_panel_id()
        let html = `
        <div id="${panel_id}" class="zd-chat-container zd-chat theme-light" style="z-index:2100000000">
            <div>
                <div class="zd-widget-container visible">
                <div class="zd-status-container">信息面板
                    <div class="zd-minimize-button">
                    <div class="iconfont icon-cancel" id="on-toggle"></div>
                    </div>
                </div>
                <div class="zd-message-list-container">
                    <div class="message-list">
                        <div class="zd-system-msg-container zd-hide-sys">
                            <span class="zd-system-msg">
                            </span>
                        </div>
                        <div class="zd-system-msg-container zd-hide-sys">
                            <span class="zd-system-msg">
                            </span>
                        </div>
                        <div class="zd-you-like">
                            <div class="zd-tabs">
                            <div class="zd-flow-tabs zb-flow-tabs-info">
                                <!-- 信息标题此处 -->
                            </div>
                            <div class="zd-arrow-con">
                                <span class="zd-arrow iconfont icon-Unfold ">
                                </span>
                            </div>
                            </div>
                            <div class="zd-info-main ">
                            </div>
                        </div>
                        <div class="rolling_infoscreen">
                        </div>
                    </div>
                </div>
                <div class="zd-spinner-container">
                    <div class="okui-loader">
                    <div class="okui-loader-spin okui-loader-spin-md okui-loader-spin-primary">
                    </div>
                    </div>
                    <div class="zd-spinner-loader-pa">
                    </div>
                </div>
                <div class="zd-input-container">
                        <button class="zd-send-button" type="button" data-toggle="停止请求|">查询</button>
                        <button class="zd-send-button" type="button">发送</button>
                        <input autocomplete="off" class="zd-input" placeholder="输入命令 /?" value="">
                </div>
                </div>
                <div class="zd-chat-button visible" style="bottom: 100px;" id="on-toggle">
                <img style="max-width:80px;max-height:80px;" src="data:image/png;base64,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" alt="customer-service-icon" class="customer-service-icon-img">
                </div>
            </div>
        </div>`
        return html
    }

    message(message, type) {
        if (!type) {
            type = "info"
        }
        let color = "green"
        switch (type) {
            case "success":
                color = "green"
                break
            case "info":
                color = "green"
                break
            case "warn":
                color = "orange"
                break
            case "danger":
                color = "red"
                break
            case "error":
                color = "red"
                break
        }
        message = `
        <div class="zd-tag" >
            <div class="zd-tag-list-main">
                <p class="zd-tag-title" style="color:${color};font-size:12px;">
                    ${message}
                </p>
            </div>
        </div>
        `
        return message
    }

    get_panel_id(prefix = "", suffix = ``) {
        let panel_id = `${prefix}scratch-data-info-container ${suffix}`
        panel_id = panel_id.trim()
        return panel_id
    }

    toggle() {
        let panel_id = this.get_panel_id("#")
        $$.class_toggle(`${panel_id} .zd-widget-container`, 'visible')
        $$.class_toggle(`${panel_id} .zd-chat-button`, 'visible')
        $$.class_toggle(`${panel_id}`, 'hide-zd')
    }

    set_message(value, type = 'success', group_name = null, max_limit = 100) {
        if (!group_name) {
            group_name = this.get_group_defaultname()
        }
        let message_html = ``
        if (typeof value == 'object') {
            if (group_name) {
                //三个参数缩减到两个参数.
                max_limit = group_name
            }
            group_name = type

            value.forEach(ele => {
                if (typeof ele == 'string') {
                    message_html += this.message(ele, type)
                } else {
                    //数组对角形式消息列表格式
                    //message type
                    if (!ele.type) {
                        type == `su`
                    }
                    message_html += this.message(ele.message, type)
                }
            })
        } else {
            message_html = this.message(value, type)
        }
        let group_selector = this.get_group_selector(group_name)
        let message_selector = this.get_message_selector(group_selector)
        let group_message = this.queryElement(message_selector)
        if (!group_message) {
            group_message = this.set_message_group(group_selector)
        }
        if (message_html && max_limit) {
            let m_children = this.queryElementAll(`.rolling_infoscreen .zd-tag`)
            if (m_children.length > max_limit) {
                m_children[0].remove()
            }
        }
        group_message.insertAdjacentHTML('afterBegin', message_html)
    }

    queryElement(selector) {
        selector = this.get_query_selector(selector)
        let ele = document.querySelector(selector)
        return ele
    }

    queryElementAll(selector) {
        selector = this.get_query_selector(selector)
        let eles = document.querySelectorAll(selector)
        return eles
    }

    get_query_selector(selector) {
        selector = selector.trim()
        if (!selector.startsWith('.')) {
            selector = `.${selector}`
        }
        if (!selector.startsWith('#')) {
            selector = this.get_panel_id("#", selector)
        }
        return selector
    }

    get_titles() {
        let group_parentselector = this.get_group_parentselector()
        let count_group = this.queryElementAll(`${group_parentselector} .zd-tabs-cell`)
        return count_group
    }

    set_title(title, value = '') {
        let group_selector = this.get_group_selector(title)
        let group_titlevalueselector = this.get_group_titlevalueselector(group_selector)
        let group_infoselector = this.get_group_infoselector(group_selector)
        let group = this.queryElement(group_selector)
        if (group) {
            this.queryElement(group_titlevalueselector).innerHTML = value
        } else {
            if (value) {
                value = ` : <span class="${group_titlevalueselector}">${value}</span>`
            }
            let group_titlehtml = this.get_group_titlehtml(title, value, group_selector, group_infoselector)
            let selector_parentselector = this.get_group_parentselector()
            this.queryElement(selector_parentselector).innerHTML += group_titlehtml
            let group_infohtml = this.get_group_infohtml(group_infoselector)
            let groupinfo_parentselector = this.get_groupinfo_parentselector()
            this.queryElement(groupinfo_parentselector).insertAdjacentHTML("afterBegin", group_infohtml);
            group = this.queryElement(group_selector)
        }
        return group
    }

    set_message_group(group_selector) {
        let message_titlehtml = this.get_messagegrouphtml(group_selector)
        console.log(`message_titlehtml`,message_titlehtml)
        let message_parentselector = this.get_message_parentselector()
        console.log(`message_parentselector`,message_parentselector)
        let message_parent = this.queryElement(message_parentselector)
        console.log(`message_titlehtml`,message_titlehtml)
        console.log(`message_parent`,message_parent)
        message_parent.innerHTML += message_titlehtml
        return message_parent
    }

    set_info(title, value = '', group_title = null) {
        let element = this.panel_element.info[title]
        if (element) {
            element.innerHTML = value
        } else {
            if (group_title === null) {
                group_title = this.get_group_defaultname()
            }
            let group_selector = this.get_group_selector(group_title)
            let group = this.queryElement(group_selector)
            if (!group) {
                group = this.set_title(group_title)
            }
            let group_infoselector = this.get_group_infoselector(group_selector)
            let title_with_group = title + group_selector
            let class_name = Util.to_alpha(title_with_group)
            let info_item = this.get_info_html(title, value, class_name)
            this.queryElement(group_infoselector).insertAdjacentHTML("afterBegin", info_item);
            let element = this.queryElement(class_name)
            this.panel_element.info[title] = element
        }
    }

    get_group_parentselector() {
        return `zb-flow-tabs-info`
    }

    get_group_infohtml(group_infoselector) {
        let count_group = this.get_titles().length
        let active = 'zd-hide-info-cell'
        if (count_group < 2) {
            active = ``
        }
        let group_infohtml = `<div class="zd-info-cell ${active} ${group_infoselector}"></div>`
        return group_infohtml
    }

    get_group_titlehtml(title, value, group_selector, group_infoselector) {
        let count_group = this.get_titles().length
        let active = ''
        if (count_group == 0) {
            active = `zd-cur`
        }
        let group_titlehtml = `<div class="zd-tabs-cell ${active} ${group_selector}" data-group_class="${group_infoselector}" onclick='window.Panel.toggle_infotitle(this)'>
            <p class="zd-name">${title}${value}</p>
            <div class="zd-line">
            </div>
            </div>`
        return group_titlehtml
    }

    get_messagegrouphtml(group_selector) {
        let messageselector = this.get_message_selector(group_selector)
        let group_titlehtml = `<div class="${messageselector}"></div>`
        return group_titlehtml
    }

    get_groupinfo_parentselector() {
        return `.zd-info-main`
    }

    get_message_parentselector() {
        return `.rolling_infoscreen`
    }

    get_message_selector(group_selector) {
        return `group_messagelist_${group_selector}`
    }

    get_group_defaultname() {
        return `当前信息`
    }

    get_group_selector(title) {
        let group_selector
        if (typeof title == 'number') {
            let titles = Object.keys(this.panel_element.title)
            if (titles.length < title - 1) {
                return null
            }
            title = titles[title]
            group_selector = title.dataset.group_class
            return group_selector
        }
        if (!title) {
            title = this.get_group_defaultname()
        }
        group_selector = Util.to_alpha(title)
        return group_selector
    }

    get_group_titlevalueselector(group_selector) {
        return `${group_selector}value`
    }

    get_group_infoselector(group_selector) {
        return `zd-info-group-${group_selector}`
    }


    get_info_html(title, value, class_name) {
        if (title) {
            title = `${title} : `
        }
        let value_html = ``
        if (class_name) {
            value_html = `<span class="${class_name}">${value}</span>`
        } else {
            value_html = value
        }
        let info_item = `<div class="zd-des-title">
            <div class="zd-link" >
                <p class="zd-co">${title}${value_html}</p>
            </div>
            </div>`
        return info_item
    }

    set_html(values, goup_title, clear = false) {
        let values_html = ``
        values.forEach(value => {
            values_html += this.get_info_html('', value)
        })

        let group_selector = this.get_group_selector(goup_title)
        group_selector = this.get_group_infoselector(group_selector)
        let gele = this.queryElement(group_selector)
        if (clear) {
            gele.innerHTML = values_html
        } else {
            gele.insertAdjacentHTML("afterBegin", info_item);
        }
    }

    toggle_infotitle(ele) {
        let children = ele.parentElement.children
        Util.remove_class(children, `zd-cur`)
        Util.add_class(ele, `zd-cur`)

        let panel_id = this.get_panel_id("#")
        let group_selector = `${panel_id} .zd-info-main .zd-info-cell`
        Util.add_class(group_selector, `zd-hide-info-cell`)
        Util.remove_class(ele.dataset.group_class, `zd-hide-info-cell`)

        let message_group_selector = this.get_message_selector()
        Util.add_class(message_group_selector, `zd-hide-info-cell`)
        Util.remove_class(message_group_selector, `zd-hide-info-cell`)
    }

    set_panelvalue(selector, value = '') {
        let panel_id = this.get_panel_id("#")
        let eles = document.querySelectorAll(`${panel_id} ${selector}`)
        eles.forEach((ele) => {
            ele.innerHTML = value
        })
    }

    set_panel_html(insert_selector = 'body') {
        if (!insert_selector) {
            insert_selector = 'body'
        }
        let html = this.get_panel_html()
        document.querySelector(insert_selector).insertAdjacentHTML("afterBegin", html);
        $$.listen(`#${this.panel_id} .zd-chat-button`, 'click', () => {
            this.toggle();
        })
        $$.listen(`#${this.panel_id} .iconfont.icon-cancel`, 'click', () => {
            this.toggle();
        })
    }
}
const Panel = new PanelClass()

export {
    Panel
}
// exports.module.panel = PanelHTMLClass()