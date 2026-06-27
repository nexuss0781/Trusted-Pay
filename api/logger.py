import json
import datetime
from database import SessionLocal
from models import ActivityLog, Snapshot


def log_action(
    user_id: int | None,
    action: str,
    details: dict | None = None,
    ip_address: str | None = None,
):
    db = SessionLocal()
    try:
        entry = ActivityLog(
            user_id=user_id,
            action=action,
            details_json=json.dumps(details) if details else None,
            ip_address=ip_address,
        )
        db.add(entry)
        db.commit()
    finally:
        db.close()


async def create_snapshot():
    from models import Wallet, Transaction, User

    db = SessionLocal()
    try:
        wallets = db.query(Wallet).all()
        txns = db.query(Transaction).all()
        users = db.query(User).count()

        snapshot_data = {
            "timestamp": datetime.datetime.utcnow().isoformat(),
            "total_users": users,
            "total_wallets": len(wallets),
            "total_balance": float(sum(w.balance or 0 for w in wallets)),
            "total_transactions": len(txns),
            "pending_deposits": sum(1 for t in txns if t.type == "deposit" and t.status == "pending"),
            "pending_withdrawals": sum(1 for t in txns if t.type == "withdrawal" and t.status == "pending"),
            "approved_deposits": sum(1 for t in txns if t.type == "deposit" and t.status == "approved"),
            "completed_withdrawals": sum(1 for t in txns if t.type == "withdrawal" and t.status == "completed"),
        }

        snap = Snapshot(snapshot_type="auto_2h", data_json=json.dumps(snapshot_data))
        db.add(snap)
        db.commit()
    finally:
        db.close()


async def create_daily_aggregation():
    from models import Transaction

    db = SessionLocal()
    try:
        today = datetime.datetime.utcnow().date()
        start = datetime.datetime.combine(today, datetime.time.min)
        end = datetime.datetime.combine(today, datetime.time.max)

        txns = db.query(Transaction).filter(
            Transaction.created_at >= start,
            Transaction.created_at <= end,
        ).all()

        total_deposits = sum(t.amount for t in txns if t.type == "deposit" and t.status == "approved")
        total_withdrawals = sum(t.amount for t in txns if t.type == "withdrawal" and t.status == "completed")
        total_fees = sum(t.service_fee or 0 for t in txns if t.type == "deposit" and t.status == "approved")

        agg_data = {
            "date": today.isoformat(),
            "total_deposits": float(total_deposits),
            "total_withdrawals": float(total_withdrawals),
            "total_service_fees": float(total_fees),
            "transaction_count": len(txns),
        }

        snap = Snapshot(snapshot_type="daily", data_json=json.dumps(agg_data))
        db.add(snap)
        db.commit()
    finally:
        db.close()
