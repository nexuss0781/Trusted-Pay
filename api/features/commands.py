from telegram import Update, Bot
from auth import (
    get_user_by_chat_id, link_telegram, unlink_telegram,
    authenticate_user, get_wallet, is_admin
)
from models import Transaction, User
from database import SessionLocal
from telebirr import verify_receipt
from logger import log_action
import os

BASE_URL = os.environ.get("BASE_URL", "https://trusted.vercel.app")
ADMIN_CHAT_IDS = os.environ.get("ADMIN_CHAT_IDS", "").split(",")


def _is_admin_chat(chat_id: str) -> bool:
    return chat_id in ADMIN_CHAT_IDS


def _format_amount(amount) -> str:
    try:
        return f"{float(amount):,.2f} ETB"
    except (ValueError, TypeError):
        return "0.00 ETB"


async def handle_update(update: Update, bot: Bot):
    text = update.message.text
    chat_id = update.effective_chat.id

    if text == "/start":
        await bot.send_message(
            chat_id=chat_id,
            text=(
                "Welcome to Trusted Bot!\n\n"
                "Available commands:\n"
                "/login - Connect your Telegram to your account\n"
                "/link <email> <password> - Link this chat to your account\n"
                "/logoff - Disconnect Telegram from your account\n"
                "/balance - Check your wallet balance\n"
                "/deposit <receipt_number> - Submit a deposit\n"
                "/status [id] - Check transaction status\n"
                "/help - Show this message"
            )
        )
    elif text == "/help":
        await bot.send_message(
            chat_id=chat_id,
            text=(
                "Available commands:\n"
                "/start - Welcome message\n"
                "/login - Get login link\n"
                "/link <email> <password> - Link this chat to your account\n"
                "/logoff - Disconnect Telegram from your account\n"
                "/balance - Check your wallet balance\n"
                "/deposit <receipt_number> - Submit a deposit\n"
                "/status [id] - Check your transaction status\n"
                "/help - This message"
            )
        )
    elif text.startswith("/login"):
        await bot.send_message(
            chat_id=chat_id,
            text=(
                f"Visit {BASE_URL}/login to log in to your account.\n\n"
                f"Use /link youremail@example.com yourpassword to connect this chat."
            )
        )
    elif text.startswith("/link"):
        parts = text.split(maxsplit=2)
        if len(parts) < 3:
            await bot.send_message(
                chat_id=chat_id,
                text="Usage: /link youremail@example.com yourpassword"
            )
            return
        email = parts[1].strip()
        password = parts[2].strip()
        user = authenticate_user(email, password)
        if not user:
            await bot.send_message(
                chat_id=chat_id,
                text="Invalid email or password. Sign up at " + BASE_URL + "/signup"
            )
            return
        if user.telegram_chat_id:
            await bot.send_message(
                chat_id=chat_id,
                text="This email is already linked to a Telegram account."
            )
            return
        link_telegram(user, str(chat_id))
        log_action(user.id, "telegram.link", {"chat_id": str(chat_id)})
        await bot.send_message(
            chat_id=chat_id,
            text=f"✅ Telegram linked to {email} successfully!"
        )
    elif text.startswith("/logoff"):
        user = get_user_by_chat_id(str(chat_id))
        if user:
            unlink_telegram(str(chat_id))
            log_action(user.id, "telegram.unlink", {"chat_id": str(chat_id)})
            await bot.send_message(
                chat_id=chat_id,
                text="Your Telegram account has been disconnected."
            )
        else:
            await bot.send_message(
                chat_id=chat_id,
                text="Your Telegram is not linked to any account."
            )
    elif text.startswith("/balance"):
        user = get_user_by_chat_id(str(chat_id))
        if not user:
            await bot.send_message(
                chat_id=chat_id,
                text="Your Telegram is not linked. Use /link <email> <password> first."
            )
            return
        wallet = get_wallet(user.id)
        balance = wallet.balance if wallet else 0
        msg = (
            f"💰 *Wallet Balance*\n\n"
            f"Balance: {_format_amount(balance)}\n\n"
            f"Use /deposit <receipt_number> to add funds.\n"
            f"Visit {BASE_URL}/dashboard to withdraw."
        )
        await bot.send_message(chat_id=chat_id, text=msg, parse_mode="Markdown")
    elif text.startswith("/deposit"):
        parts = text.split(maxsplit=1)
        if len(parts) < 2:
            await bot.send_message(
                chat_id=chat_id,
                text="Usage: /deposit <receipt_number>\n\n"
                     "Example: /deposit DFR9BROP2Z"
            )
            return
        user = get_user_by_chat_id(str(chat_id))
        if not user:
            await bot.send_message(
                chat_id=chat_id,
                text="Your Telegram is not linked. Use /link <email> <password> first."
            )
            return

        receipt = parts[1].strip()
        await bot.send_message(
            chat_id=chat_id,
            text=f"🔍 Verifying receipt {receipt}... Please wait."
        )

        result = await verify_receipt(receipt)
        if not result["valid"]:
            await bot.send_message(
                chat_id=chat_id,
                text=f"❌ Verification failed: {result.get('error', 'Unknown error')}"
            )
            return

        details = result["details"]
        from decimal import Decimal
        amount = details.get("settled_amount_num", Decimal("0"))

        db = SessionLocal()
        try:
            txn = Transaction(
                user_id=user.id,
                type="deposit",
                receipt_no=receipt,
                amount=amount,
                payer_name=details.get("payer_name"),
                payer_phone=details.get("payer_phone"),
                receiver_name=details.get("receiver_name"),
                receiver_phone=details.get("receiver_phone"),
                status="pending",
            )
            db.add(txn)
            db.commit()
            db.refresh(txn)
            log_action(user.id, "deposit.request", {
                "transaction_id": txn.id,
                "receipt_no": receipt,
                "amount": str(amount),
                "source": "telegram",
            })
        finally:
            db.close()

        msg = (
            f"✅ *Deposit Request Submitted!*\n\n"
            f"Receipt: {receipt}\n"
            f"Amount: {_format_amount(amount)}\n"
            f"Payer: {details.get('payer_name', 'N/A')}\n"
            f"Status: ⏳ Pending Approval\n\n"
            f"Track: {BASE_URL}/status/{txn.id}"
        )
        await bot.send_message(chat_id=chat_id, text=msg, parse_mode="Markdown")
    elif text.startswith("/status"):
        user = get_user_by_chat_id(str(chat_id))
        if not user:
            await bot.send_message(
                chat_id=chat_id,
                text="Your Telegram is not linked. Use /link <email> <password> first."
            )
            return

        parts = text.split(maxsplit=1)
        db = SessionLocal()
        try:
            if len(parts) >= 2:
                txn_id = parts[1].strip()
                txn = db.query(Transaction).filter(
                    Transaction.id == txn_id,
                    Transaction.user_id == user.id,
                ).first()
                if not txn:
                    await bot.send_message(chat_id=chat_id, text="Transaction not found.")
                    return
                msg = (
                    f"📋 *Transaction #{txn.id}*\n\n"
                    f"Type: {txn.type.capitalize()}\n"
                    f"Amount: {_format_amount(txn.amount)}\n"
                    f"Status: {txn.status.upper()}\n"
                    f"Date: {txn.created_at.strftime('%b %d, %Y %H:%M') if txn.created_at else 'N/A'}\n"
                    f"Receipt: {txn.receipt_no or 'N/A'}\n"
                    f"Details: {BASE_URL}/status/{txn.id}"
                )
            else:
                txns = (
                    db.query(Transaction)
                    .filter(Transaction.user_id == user.id)
                    .order_by(Transaction.created_at.desc())
                    .limit(5)
                    .all()
                )
                if not txns:
                    await bot.send_message(chat_id=chat_id, text="No transactions found.")
                    return
                lines = ["📋 *Recent Transactions*\n"]
                for t in txns:
                    lines.append(
                        f"#{t.id} {t.type.capitalize()} - {_format_amount(t.amount)} - {t.status.upper()}"
                    )
                lines.append(f"\nFull history: {BASE_URL}/status")
                msg = "\n".join(lines)
        finally:
            db.close()
        await bot.send_message(chat_id=chat_id, text=msg, parse_mode="Markdown")
    elif text.startswith("/admin_pending") and _is_admin_chat(str(chat_id)):
        db = SessionLocal()
        try:
            deposits = db.query(Transaction).filter(
                Transaction.type == "deposit", Transaction.status == "pending"
            ).count()
            withdrawals = db.query(Transaction).filter(
                Transaction.type == "withdrawal", Transaction.status == "pending"
            ).count()
        finally:
            db.close()
        await bot.send_message(
            chat_id=chat_id,
            text=f"📊 *Admin Queue*\n\nPending Deposits: {deposits}\nPending Withdrawals: {withdrawals}\n\nManage: {BASE_URL}/admin",
            parse_mode="Markdown"
        )
    elif text.startswith("/admin_approve") and _is_admin_chat(str(chat_id)):
        parts = text.split(maxsplit=1)
        if len(parts) < 2:
            await bot.send_message(chat_id=chat_id, text="Usage: /admin_approve <transaction_id>")
            return
        db = SessionLocal()
        try:
            txn = db.query(Transaction).filter(Transaction.id == int(parts[1])).first()
            if txn and txn.type == "deposit" and txn.status == "pending":
                from decimal import Decimal
                from models import AdminSettings, Wallet
                import datetime
                settings = db.query(AdminSettings).first()
                fee_percent = settings.service_fee_percent if settings else Decimal("0.00")
                service_fee = Decimal("0.00")
                if fee_percent > 0 and txn.amount:
                    service_fee = (txn.amount * fee_percent) / Decimal("100")
                txn.service_fee = service_fee
                txn.status = "approved"
                txn.updated_at = datetime.datetime.utcnow()
                wallet = db.query(Wallet).filter(Wallet.user_id == txn.user_id).first()
                if wallet:
                    wallet.balance += (txn.amount - service_fee)
                db.commit()
                await bot.send_message(
                    chat_id=chat_id,
                    text=f"✅ Deposit #{txn.id} approved. Credited {float(txn.amount - service_fee):.2f} ETB."
                )
            else:
                await bot.send_message(chat_id=chat_id, text="Transaction not found or not pending.")
        finally:
            db.close()
    elif text.startswith("/admin_reject") and _is_admin_chat(str(chat_id)):
        parts = text.split(maxsplit=2)
        if len(parts) < 2:
            await bot.send_message(chat_id=chat_id, text="Usage: /admin_reject <transaction_id> [reason]")
            return
        db = SessionLocal()
        try:
            txn = db.query(Transaction).filter(Transaction.id == int(parts[1])).first()
            if txn and txn.status == "pending":
                txn.status = "rejected"
                txn.admin_note = parts[2].strip() if len(parts) > 2 else "Rejected via bot"
                txn.updated_at = __import__('datetime').datetime.utcnow()
                if txn.type == "withdrawal":
                    from models import Wallet
                    wallet = db.query(Wallet).filter(Wallet.user_id == txn.user_id).first()
                    if wallet:
                        wallet.balance += txn.amount
                db.commit()
                await bot.send_message(
                    chat_id=chat_id,
                    text=f"❌ Transaction #{txn.id} rejected."
                )
            else:
                await bot.send_message(chat_id=chat_id, text="Transaction not found or not pending.")
        finally:
            db.close()
    else:
        await bot.send_message(
            chat_id=chat_id,
            text="Unknown command. Use /help to see available commands."
        )
