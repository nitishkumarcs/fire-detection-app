
# Database models placeholder (SQLAlchemy can be added here later)
from flask_sqlalchemy import SQLAlchemy

db = SQLAlchemy()

class FireAlert(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    timestamp = db.Column(db.DateTime, nullable=False)
    location = db.Column(db.String(100))
    detected = db.Column(db.Boolean, default=False)
