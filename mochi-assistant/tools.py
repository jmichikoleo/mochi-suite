import json

TASK_FILE = "tasks.json"


def load_tasks():

    try:
        with open(TASK_FILE) as f:
            return json.load(f)
    except:
        return []


def save_tasks(tasks):

    with open(TASK_FILE, "w") as f:
        json.dump(tasks, f, indent=2)


def add_task(text, due=None):

    tasks = load_tasks()

    task = {
        "content": text,
        "due": due,
        "done": False
    }

    tasks.append(task)

    # SORT BY DEADLINE
    tasks.sort(key=lambda x: x["due"] if x["due"] else "9999-99-99")

    save_tasks(tasks)

def list_tasks():
    return load_tasks()


def delete_task(index):

    tasks = load_tasks()

    if 0 <= index < len(tasks):
        tasks.pop(index)

    save_tasks(tasks)