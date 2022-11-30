(()=>{
    class ListenTask{
        oldtasks = []
        
        get_tasks(){
            let tasks = document.querySelectorAll('.list-content-3dI_h div > div.item-container-2Txk_')
            let tasks_arr = []
            tasks.forEach(task=>{
                tasks_arr.push(task)
            })
            return tasks_arr
        }

        init(){
            this.oldtasks = this.get_tasks()
        }

        listen(){
            setInterval(()=>{
                this.get_tasks().forEach(task=>{
                    if(!this.oldtasks.includes(task)){
                        //发新新的
                        //请求发邮箱api
                    }else{
                        console.log('没有新任务')
                    }
                }) 
            },1000)
        }
    }   
    let listenTask = new ListenTask()
    listenTask.init()
    listenTask.listen()
})()