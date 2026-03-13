from flask import Flask, render_template, request, jsonify
from mochi_agent import handle_command
from tools import load_tasks, save_tasks
from datetime import datetime

app = Flask(__name__)


# -----------------------------
# Homepage
# -----------------------------
@app.route("/")
def home():
    return render_template("index.html")


# -----------------------------
# Command endpoint
# -----------------------------
@app.route("/command", methods=["POST"])
def command():

    data = request.json
    message = data.get("message", "")

    response = handle_command(message)

    return jsonify({"response": response})


# -----------------------------
# Get all tasks
# -----------------------------
@app.route("/tasks")
def get_tasks():

    tasks = load_tasks()

    return jsonify(tasks)


# -----------------------------
# Delete task
# -----------------------------
@app.route("/delete_task", methods=["POST"])
def delete_task():

    data = request.json
    index = data.get("index")

    tasks = load_tasks()

    if index is not None and 0 <= index < len(tasks):
        tasks.pop(index)
        save_tasks(tasks)

    return jsonify({"status": "deleted"})


# -----------------------------
# Daily briefing
# -----------------------------
@app.route("/briefing")
def briefing():

    tasks = load_tasks()

    today = datetime.now().strftime("%Y-%m-%d")

    today_tasks = []

    for t in tasks:

        if t.get("due") and t["due"].startswith(today):
            today_tasks.append(t)

    message = "☀️ Good morning.\n\n"

    if not today_tasks:
        message += "You have no scheduled tasks today."

    else:

        message += f"You have {len(today_tasks)} task(s) today:\n\n"

        for t in today_tasks:
            message += f"• {t['content']}\n"

    return message


# -----------------------------
# Run app
# -----------------------------
if __name__ == "__main__":
    print("🍡 Mochi Assistant starting...")
    app.run(host="0.0.0.0", port=5001, debug=True)