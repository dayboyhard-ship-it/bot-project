import json
import os
from dotenv import load_dotenv
from flask import Flask, render_template, request, redirect
from flask_sqlalchemy import SQLAlchemy
from gigachat import GigaChat

# ---------- НАСТРОЙКА ----------
app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///notes.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(app)

# Ключ авторизации из Sber Developers Studio берётся из файла .env
# (строка GIGACHAT_CREDENTIALS=...). Файл .env не попадает в git.
load_dotenv(os.path.join(os.path.dirname(os.path.abspath(__file__)), ".env"))
GIGACHAT_CREDENTIALS = os.getenv("GIGACHAT_CREDENTIALS", "").strip()


# ---------- МОДЕЛЬ БАЗЫ ДАННЫХ ----------
class Note(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    content = db.Column(db.Text, nullable=False)
    ai_response = db.Column(db.Text, nullable=True)

    def get_ai_data(self):
        if not self.ai_response:
            return None
        try:
            return json.loads(self.ai_response)
        except Exception:
            return None


# Создание таблиц (нужно и при запуске через gunicorn на Railway)
with app.app_context():
    db.create_all()


# ---------- ФУНКЦИЯ ИИ (GIGACHAT) ----------
def ask_ai(prompt):
    if not GIGACHAT_CREDENTIALS:
        return {
            "summary": "ИИ не подключён — добавьте ключ GigaChat в файл .env.",
            "improvements": [
                "Создайте проект в Sber Developers Studio",
                "Скопируйте Authorization Key",
                "Создайте файл .env рядом с app.py (по образцу .env.example) "
                "и вставьте ключ в строку GIGACHAT_CREDENTIALS=",
                "Перезапустите приложение",
            ],
            "title_suggestion": "Пример заголовка",
            "tags": ["демо", "тест"]
        }

    system_prompt = """Ты — помощник по работе с заметками.
Проанализируй заметку пользователя и предложи улучшения.

Отвечай СТРОГО в формате JSON, без markdown и лишнего текста:
{
  "summary": "краткое резюме заметки в одном предложении",
  "improvements": [
    "первое конкретное улучшение",
    "второе конкретное улучшение",
    "третье конкретное улучшение"
  ],
  "title_suggestion": "предложенный заголовок для заметки",
  "tags": ["тег1", "тег2", "тег3"]
}"""

    try:
        with GigaChat(
            credentials=GIGACHAT_CREDENTIALS,
            scope="GIGACHAT_API_PERS",
            model="GigaChat-2",
            verify_ssl_certs=False,
        ) as client:
            messages = [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": f"Вот заметка:\n\n{prompt}"}
            ]
            response = client.chat({"messages": messages})
            content = response.choices[0].message.content.strip()
            # Модель иногда оборачивает ответ в ```json ... ``` — убираем обёртку
            if content.startswith("```"):
                content = content.strip("`").removeprefix("json").strip()
            return json.loads(content)
    except Exception as e:
        return {
            "summary": f"Ошибка GigaChat: {e}",
            "improvements": [],
            "title_suggestion": "",
            "tags": []
        }


# ---------- МАРШРУТЫ ----------
@app.route("/", methods=["GET", "POST"])
def index():
    if request.method == "POST":
        note_content = request.form.get("content", "").strip()
        if not note_content:
            return redirect("/")

        new_note = Note(content=note_content)
        ai_data = ask_ai(note_content)
        new_note.ai_response = json.dumps(ai_data, ensure_ascii=False)

        try:
            db.session.add(new_note)
            db.session.commit()
        except Exception as e:
            return f"Ошибка при сохранении: {e}"
        return redirect("/")

    notes = Note.query.order_by(Note.id.desc()).all()
    return render_template("index.html", notes=notes)


@app.route("/delete/<int:id>")
def delete(id):
    note = Note.query.get_or_404(id)
    try:
        db.session.delete(note)
        db.session.commit()
    except Exception as e:
        return f"Ошибка при удалении: {e}"
    return redirect("/")


# ---------- ЗАПУСК ----------
# Локально: python app.py. На Railway запускается через gunicorn (см. railway.toml)
if __name__ == "__main__":
    app.run(debug=True)