from flask import Flask, render_template, request, redirect, url_for, jsonify
from flask_sqlalchemy import SQLAlchemy
import requests  # Для запросов к ИИ

app = Flask(__name__)
# Настройка базы данных SQLite
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///notes.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(app)


# --- МОДЕЛЬ БАЗЫ ДАННЫХ ---
class Note(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    content = db.Column(db.Text, nullable=False)
    ai_response = db.Column(db.Text, nullable=True)  # Здесь храним ответ ИИ

    def __repr__(self):
        return f'<Note {self.id}>'


# --- ФУНКЦИЯ ИИ (ЗАГЛУШКА) ---
def ask_ai(prompt):
    """
    Здесь должна быть логика обращения к реальному API.
    Пока это просто имитация ответа.
    """
    # ПРИМЕР для OpenAI (нужен ключ):
    # headers = {"Authorization": f"Bearer YOUR_OPENAI_KEY"}
    # response = requests.post("https://api.openai.com/v1/chat/completions",
    #                          json={"model": "gpt-3.5-turbo", "messages": [{"role": "user", "content": prompt}]},
    #                          headers=headers)
    # return response.json()['choices'][0]['message']['content']

    # А пока просто возвращаем эхо-ответ для теста:
    return f"ИИ-помощник прочитал вашу заметку: '{prompt}'. Вот что я думаю: это интересная мысль!"


# --- МАРШРУТЫ (ROUTES) ---

@app.route('/', methods=['GET', 'POST'])
def index():
    if request.method == 'POST':
        note_content = request.form['content']

        # 1. Создаем заметку
        new_note = Note(content=note_content)

        # 2. Спрашиваем ИИ
        ai_ans = ask_ai(note_content)
        new_note.ai_response = ai_ans

        # 3. Сохраняем в БД
        try:
            db.session.add(new_note)
            db.session.commit()
            return redirect('/')
        except Exception as e:
            return f"Ошибка при добавлении: {e}"

    else:
        notes = Note.query.order_by(Note.id.desc()).all()
        return render_template('index.html', notes=notes)


@app.route('/delete/<int:id>')
def delete(id):
    note_to_delete = Note.query.get_or_404(id)
    try:
        db.session.delete(note_to_delete)
        db.session.commit()
        return redirect('/')
    except Exception as e:
        return f"Ошибка при удалении: {e}"


# --- ЗАПУСК ---
if __name__ == "__main__":
    with app.app_context():
        db.create_all()  # Создаем таблицы, если их нет
    app.run(debug=True)