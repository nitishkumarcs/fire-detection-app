# db_config.py
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime

db = SQLAlchemy()

def init_db(app):
    # ---- MySQL Config ----
    app.config["SQLALCHEMY_DATABASE_URI"] = "mysql+pymysql://fire_db:1234@localhost/fire_detection"
    app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
    db.init_app(app)

    with app.app_context():
        db.create_all()

# ------------------ Model ------------------
class FireAlert(db.Model):
    __tablename__ = "fire_alerts"

    id = db.Column(db.Integer, primary_key=True)
    timestamp = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    location = db.Column(db.String(100))
    detected = db.Column(db.Boolean, default=False)
    confidence = db.Column(db.Float)
    image_name = db.Column(db.String(100))
