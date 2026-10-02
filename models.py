from datetime import datetime
from app import db


class Task(db.Model):
    __tablename__ = 'tasks'

    id = db.Column(db.Integer, primary_key=True)
    content = db.Column(db.String(200), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    done = db.Column(db.Boolean, default=False, nullable=False)

    def __repr__(self):
        return f'<Task {self.id}: {self.content[:30]}>'