import secrets
from datetime import datetime

from . import db


class BookSettings(db.Model):
    __tablename__ = "memory_book_settings"

    id = db.Column(db.Integer, primary_key=True)
    password_hash = db.Column(db.Text, nullable=False)


class GiftSettings(db.Model):
    __tablename__ = "memory_gift_settings"

    id = db.Column(db.Integer, primary_key=True)
    password_hash = db.Column(db.Text, nullable=False)
    session_key = db.Column(db.String(64), nullable=False, default=lambda: secrets.token_hex(32))


class Memory(db.Model):
    __tablename__ = "memories"

    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(160), nullable=False)
    story = db.Column(db.Text, nullable=False)
    happened_on = db.Column(db.Date, nullable=True)
    created_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    photos = db.relationship(
        "MemoryPhoto",
        backref="memory",
        cascade="all, delete-orphan",
        order_by="MemoryPhoto.id",
        lazy=True,
    )


class MemoryPhoto(db.Model):
    __tablename__ = "memory_photos"

    id = db.Column(db.Integer, primary_key=True)
    memory_id = db.Column(db.Integer, db.ForeignKey("memories.id"), nullable=False)
    filename = db.Column(db.String(80), nullable=False, unique=True)
    mime_type = db.Column(db.String(32), nullable=False)


class LoginAttempt(db.Model):
    __tablename__ = "memory_login_attempts"

    key = db.Column(db.String(64), primary_key=True)
    failures = db.Column(db.Integer, nullable=False, default=0)
    locked_until = db.Column(db.DateTime, nullable=True)
