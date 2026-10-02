from app import app, db
from models import Task
from flask import render_template, request, redirect, url_for



@app.route("/")
def index():
    tasks = Task.query.order_by(Task.created_at.desc()).all()
    return render_template("index.html", tasks=tasks)


@app.route("/add", methods=["POST"])
def add_task():
    content = request.form.get("content", "").strip()
    if content:
        db.session.add(Task(content=content))
        db.session.commit()
    return redirect(url_for("index"))


@app.route("/delete/<int:task_id>")
def delete_task(task_id):
    task = Task.query.get_or_404(task_id)
    db.session.delete(task)
    db.session.commit()
    return redirect(url_for("index"))


@app.route("/toggle/<int:task_id>")
def toggle_task(task_id):
    task = Task.query.get_or_404(task_id)
    task.done = not task.done
    db.session.commit()
    return redirect(url_for("index"))


# Создание таблиц при первом запуске
with app.app_context():
    db.create_all()


if __name__ == "__main__":
    app.run(debug=True)