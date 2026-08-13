from flask_sqlalchemy import SQLAlchemy
from datetime import datetime

db = SQLAlchemy()

class Setting(db.Model):
    __tablename__ = "settings"
    id = db.Column(db.Integer, primary_key=True)
    key = db.Column(db.String(100), unique=True, nullable=False)
    value = db.Column(db.Text, default="")
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

class RenameJob(db.Model):
    __tablename__ = "rename_jobs"
    id = db.Column(db.Integer, primary_key=True)
    original_name = db.Column(db.String(500))
    renamed_to = db.Column(db.String(500))
    rule = db.Column(db.String(200))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

class CheatSheet(db.Model):
    __tablename__ = "cheatsheets"
    id = db.Column(db.Integer, primary_key=True)
    language = db.Column(db.String(100))
    content = db.Column(db.Text)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

class NDADocument(db.Model):
    __tablename__ = "nda_documents"
    id = db.Column(db.Integer, primary_key=True)
    party_a = db.Column(db.String(200))
    party_b = db.Column(db.String(200))
    content = db.Column(db.Text)
    signature_a = db.Column(db.Text)
    signature_b = db.Column(db.Text)
    signed_at = db.Column(db.DateTime)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

class Screenshot(db.Model):
    __tablename__ = "screenshots"
    id = db.Column(db.Integer, primary_key=True)
    url = db.Column(db.String(1000))
    filename = db.Column(db.String(300))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
