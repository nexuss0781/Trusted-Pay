from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, Text, Numeric, Boolean
from sqlalchemy.orm import relationship
from database import Base
import datetime


class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    full_name = Column(String(100), nullable=False)
    email = Column(String(100), unique=True, nullable=False, index=True)
    phone = Column(String(20), nullable=False)
    password_hash = Column(String(200), nullable=False)
    telegram_chat_id = Column(String(50), nullable=True, unique=True)
    role = Column(String(20), nullable=False, default="user")
    is_active = Column(Boolean, nullable=False, default=True)
    is_frozen = Column(Boolean, nullable=False, default=False)
    created_at = Column(DateTime, default=datetime.datetime.utcnow)

    sessions = relationship("Session", back_populates="user", cascade="all, delete-orphan")
    wallet = relationship("Wallet", back_populates="user", uselist=False, cascade="all, delete-orphan")
    transactions = relationship("Transaction", back_populates="user", foreign_keys="Transaction.user_id")


class Session(Base):
    __tablename__ = "sessions"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    token = Column(String(100), unique=True, nullable=False, index=True)
    created_at = Column(DateTime, default=datetime.datetime.utcnow)

    user = relationship("User", back_populates="sessions")


class Wallet(Base):
    __tablename__ = "wallets"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), unique=True, nullable=False)
    balance = Column(Numeric(12, 2), nullable=False, default=0.00)
    created_at = Column(DateTime, default=datetime.datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.datetime.utcnow, onupdate=datetime.datetime.utcnow)

    user = relationship("User", back_populates="wallet")


class Transaction(Base):
    __tablename__ = "transactions"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    type = Column(String(20), nullable=False)
    receipt_no = Column(String(50), nullable=True, index=True)
    amount = Column(Numeric(12, 2), nullable=False)
    service_fee = Column(Numeric(12, 2), nullable=True, default=0.00)
    total_paid = Column(Numeric(12, 2), nullable=True)
    payer_name = Column(String(100), nullable=True)
    payer_phone = Column(String(20), nullable=True)
    receiver_name = Column(String(100), nullable=True)
    receiver_phone = Column(String(20), nullable=True)
    status = Column(String(20), nullable=False, default="pending", index=True)
    admin_id = Column(Integer, ForeignKey("users.id"), nullable=True)
    admin_note = Column(Text, nullable=True)
    reason = Column(Text, nullable=True)
    attachment_path = Column(String(255), nullable=True)
    dispute_reason = Column(Text, nullable=True)
    resolved_at = Column(DateTime, nullable=True)
    created_at = Column(DateTime, default=datetime.datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.datetime.utcnow, onupdate=datetime.datetime.utcnow)

    user = relationship("User", back_populates="transactions", foreign_keys=[user_id])
    admin = relationship("User", foreign_keys=[admin_id])


class AdminSettings(Base):
    __tablename__ = "admin_settings"

    id = Column(Integer, primary_key=True, index=True)
    service_fee_percent = Column(Numeric(5, 2), nullable=False, default=0.00)
    base_phone_number = Column(String(20), nullable=True)
    full_name = Column(String(100), nullable=True)
    updated_at = Column(DateTime, default=datetime.datetime.utcnow, onupdate=datetime.datetime.utcnow)


class UserRestriction(Base):
    __tablename__ = "user_restrictions"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    restriction_type = Column(String(20), nullable=False)
    permissions_json = Column(Text, nullable=True)
    reason = Column(Text, nullable=True)
    expires_at = Column(DateTime, nullable=True)
    created_by = Column(Integer, ForeignKey("users.id"), nullable=False)
    created_at = Column(DateTime, default=datetime.datetime.utcnow)

    user = relationship("User", foreign_keys=[user_id])
    admin = relationship("User", foreign_keys=[created_by])


class ActivityLog(Base):
    __tablename__ = "activity_logs"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=True, index=True)
    action = Column(String(100), nullable=False)
    details_json = Column(Text, nullable=True)
    ip_address = Column(String(45), nullable=True)
    created_at = Column(DateTime, default=datetime.datetime.utcnow)

    user = relationship("User")


class Snapshot(Base):
    __tablename__ = "snapshots"

    id = Column(Integer, primary_key=True, index=True)
    snapshot_type = Column(String(20), nullable=False)
    data_json = Column(Text, nullable=False)
    created_at = Column(DateTime, default=datetime.datetime.utcnow)
