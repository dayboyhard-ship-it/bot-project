import json
from flask import Flask, render_template, request, redirect
from flask_sqlalchemy import SQLAlchemy
from gigachat import GigaChat

# ---------- НАСТРОЙКА ----------
app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///notes.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(app)

# Вставь свой ключ авторизации из Sber Developers Studio
GIGACHAT_CREDENTIALS = "ТВОЙ_КЛЮЧ_ЗДЕСЬ"


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


# ---------- ФУНКЦИЯ ИИ (GIGACHAT) ----------
def ask_ai(prompt):
    if GIGACHAT_CREDENTIALS == "ТВОЙ_КЛЮЧ_ЗДЕСЬ":
        return {
            "summary": "ИИ не подключён — вставьте ключ GigaChat в main.py.",
            "improvements": [
                "Создайте проект в Sber Developers Studio",
                "Скопируйте Authorization Key",
                "Вставьте его в переменную GIGACHAT_CREDENTIALS",
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
            model="GigaChat",
            verify_ssl_certs=False,
        ) as client:
            messages = [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": f"Вот заметка:\n\n{prompt}"}
            ]
            response = client.chat(messages)
            content = response.choices[0].message.content
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
if __name__ == "__main__":
    with app.app_context():
        db.create_all()
    app.run(debug=True)