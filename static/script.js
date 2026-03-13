const chatBox = document.getElementById("chat-box")
const input = document.getElementById("user-input")


function addMessage(sender,text){

    const msg = document.createElement("div")

    msg.classList.add("message")

    if(sender==="user"){
        msg.classList.add("user")
    }else{
        msg.classList.add("mochi")
    }

    msg.innerText=text

    chatBox.appendChild(msg)

    chatBox.scrollTop = chatBox.scrollHeight
}



async function sendMessage(){

    const text = input.value.trim()

    if(!text) return

    addMessage("user",text)

    input.value=""

    const res = await fetch("/command",{
        method:"POST",
        headers:{"Content-Type":"application/json"},
        body:JSON.stringify({message:text})
    })

    const data = await res.json()

    addMessage("mochi",data.response)

    loadTasks()
    loadUpcoming()
}



async function loadTasks(){

    const res = await fetch("/tasks")

    const tasks = await res.json()

    const list = document.getElementById("task-list")

    list.innerHTML=""

    tasks.forEach((task,index)=>{

        const div = document.createElement("div")

        div.className="task-item"

        const text = document.createElement("span")

        if(task.due){
            text.innerText = task.content + " ("+task.due+")"
        }else{
            text.innerText = task.content
        }

        const del = document.createElement("span")

        del.innerText="🗑"

        del.className="delete-btn"

        del.onclick=()=>deleteTask(index)

        div.appendChild(text)
        div.appendChild(del)

        list.appendChild(div)

    })
}



async function deleteTask(index){

    await fetch("/delete_task",{
        method:"POST",
        headers:{"Content-Type":"application/json"},
        body:JSON.stringify({index:index})
    })

    loadTasks()
    loadUpcoming()
}



async function loadUpcoming(){

    const res = await fetch("/tasks")

    const tasks = await res.json()

    const list = document.getElementById("upcoming-list")

    list.innerHTML=""

    const upcoming = tasks
        .filter(t=>t.due)
        .sort((a,b)=>new Date(a.due)-new Date(b.due))
        .slice(0,5)

    upcoming.forEach(task=>{

        const div = document.createElement("div")

        div.className="task-item"

        div.innerText = task.content + " ("+task.due+")"

        list.appendChild(div)

    })
}



async function dailyBriefing(){

    const res = await fetch("/briefing")

    const text = await res.text()

    addMessage("mochi",text)

}



window.onload=()=>{

    loadTasks()

    loadUpcoming()

    dailyBriefing()

}



input.addEventListener("keypress",(e)=>{

    if(e.key==="Enter"){
        sendMessage()
    }

})



setInterval(async ()=>{

    const res = await fetch("/tasks")

    const tasks = await res.json()

    const now = new Date()

    tasks.forEach(task=>{

        if(!task.due) return

        const due = new Date(task.due)

        const diff = (due-now)/1000/60

        if(diff>0 && diff<1){

            alert("Reminder: "+task.content)

        }

    })

},60000)