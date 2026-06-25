import hashlib
import secrets
from sqlalchemy.orm import Session as DBSession
from models import User, Session
from database import SessionLocal


def hash_password(password: str) -> str:
    salt = secrets.token_hex(16)
    h = hashlib.sha256((salt + password).encode()).hexdigest()
    return f"{salt}:{h}"


def verify_password(password: str, hashed: str) -> bool:
    parts = hashed.split(":")
    if len(parts) != 2:
        return False
    salt, h = parts
    return h == hashlib.sha256((salt + password).encode()).hexdigest()


def create_user(full_name: str, email: str, phone: str, password: str) -> User:
    db = SessionLocal()
    try:
        existing = db.query(User).filter(User.email == email).first()
        if existing:
            return None
        user = User(
            full_name=full_name,
            email=email,
            phone=phone,
            password_hash=hash_password(password),
        )
        db.add(user)
        db.commit()
        db.refresh(user)
        return user
    finally:
        db.close()


def authenticate_user(email: str, password: str) -> User | None:
    db = SessionLocal()
    try:
        user = db.query(User).filter(User.email == email).first()
        if not user or not verify_password(password, user.password_hash):
            return None
        return user
    finally:
        db.close()


def create_session_token(user_id: int) -> str:
    db = SessionLocal()
    try:
        token = secrets.token_hex(32)
        session = Session(user_id=user_id, token=token)
        db.add(session)
        db.commit()
        return token
    finally:
        db.close()


def get_user_by_token(token: str) -> User | None:
    db = SessionLocal()
    try:
        session = db.query(Session).filter(Session.token == token).first()
        if not session:
            return None
        return db.query(User).filter(User.id == session.user_id).first()
    finally:
        db.close()


def delete_session(token: str):
    db = SessionLocal()
    try:
        db.query(Session).filter(Session.token == token).delete()
        db.commit()
    finally:
        db.close()


def link_telegram(user: User, chat_id: str):
    db = SessionLocal()
    try:
        u = db.query(User).filter(User.id == user.id).first()
        if u:
            u.telegram_chat_id = str(chat_id)
            db.commit()
    finally:
        db.close()


def unlink_telegram(chat_id: str) -> dict | None:
    db = SessionLocal()
    try:
        user = db.query(User).filter(User.telegram_chat_id == str(chat_id)).first()
        if not user:
            return None
        info = {"id": user.id, "email": user.email, "full_name": user.full_name}
        user.telegram_chat_id = None
        db.commit()
        return info
    finally:
        db.close()


def get_user_by_chat_id(chat_id: str) -> User | None:
    db = SessionLocal()
    try:
        return db.query(User).filter(User.telegram_chat_id == str(chat_id)).first()
    finally:
        db.close()


def get_user_by_email(email: str) -> User | None:
    db = SessionLocal()
    try:
        return db.query(User).filter(User.email == email).first()
    finally:
        db.close()
