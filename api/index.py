import os
import sys
import json
import datetime
from decimal import Decimal

sys.path.insert(0, os.path.join(os.path.dirname(__file__)))

from fastapi import FastAPI, Request, Form, Cookie, UploadFile, File
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from fastapi.middleware.trustedhost import TrustedHostMiddleware
from starlette.middleware.base import BaseHTTPMiddleware
from telegram import Update, Bot

TOKEN = os.environ.get("TOKEN")
app = FastAPI()

# Security headers middleware
class SecurityHeadersMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        resp = await call_next(request)
        resp.headers["X-Content-Type-Options"] = "nosniff"
        resp.headers["X-Frame-Options"] = "DENY"
        resp.headers["X-XSS-Protection"] = "1; mode=block"
        resp.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
        csp = (
            "default-src 'self'; "
            "script-src 'self' https://cdn.tailwindcss.com https://unpkg.com https://cdnjs.cloudflare.com 'unsafe-inline'; "
            "style-src 'self' https://fonts.googleapis.com https://cdn.tailwindcss.com https://unpkg.com 'unsafe-inline'; "
            "font-src 'self' https://fonts.gstatic.com; "
            "img-src 'self' data:; "
            "connect-src 'self' https://api.telegram.org; "
            "frame-ancestors 'none'"
        )
        resp.headers["Content-Security-Policy"] = csp
        return resp

app.add_middleware(SecurityHeadersMiddleware)

from features import handle_update

from database import init_db
from auth import (
    create_user, authenticate_user, create_session_token,
    get_user_by_token, delete_session, get_wallet, is_admin, require_admin
)
from models import User, Transaction, AdminSettings, ActivityLog, UserRestriction, Wallet
from database import SessionLocal
from telebirr import verify_receipt
from logger import log_action

templates = Jinja2Templates(directory=os.path.join(os.path.dirname(__file__), "templates"))
static_dir = os.path.join(os.path.dirname(__file__), "static")
if os.path.isdir(static_dir):
    app.mount("/static", StaticFiles(directory=static_dir), name="static")


@app.on_event("startup")
def on_startup():
    init_db()
    _ensure_admin_settings()
    _seed_admin_from_file()


def _ensure_admin_settings():
    db = SessionLocal()
    try:
        settings = db.query(AdminSettings).first()
        if not settings:
            settings = AdminSettings(service_fee_percent=0.00, base_phone_number="")
            db.add(settings)
            db.commit()
    finally:
        db.close()


def _seed_admin_from_file():
    seed_dir = os.path.dirname(__file__)
    admin_path = os.path.join(seed_dir, "admin.txt")
    seed_py = os.path.join(seed_dir, "seed.py")

    if not os.path.exists(admin_path):
        return

    with open(admin_path) as f:
        creds = f.read().strip()

    if ":" not in creds:
        return

    email, password = creds.split(":", 1)

    from auth import hash_password, get_user_by_email
    from models import User, Wallet
    from database import SessionLocal

    existing = get_user_by_email(email)
    if existing:
        os.remove(admin_path)
        print(f"Admin {email} already exists — cleaned up admin.txt.")
    else:
        db = SessionLocal()
        try:
            user = User(
                full_name="Admin",
                email=email,
                phone="0000000000",
                password_hash=hash_password(password),
                role="admin",
            )
            db.add(user)
            db.flush()
            wallet = Wallet(user_id=user.id, balance=0.00)
            db.add(wallet)
            db.commit()
            db.refresh(user)
            print(f"Admin {email} created (id={user.id}).")
        finally:
            db.close()
        os.remove(admin_path)
        print("admin.txt deleted after seeding.")

    if os.path.exists(seed_py):
        os.remove(seed_py)
        print("seed.py deleted after seeding.")


def _get_user_from_cookie(request: Request) -> User | None:
    session_token = request.cookies.get("session")
    if not session_token:
        return None
    return get_user_by_token(session_token)


def _get_admin_or_redirect(request: Request):
    user = _get_user_from_cookie(request)
    if not user:
        return None, RedirectResponse(url="/login")
    if not is_admin(user):
        return None, RedirectResponse(url="/dashboard")
    return user, None


def _get_settings():
    db = SessionLocal()
    try:
        return db.query(AdminSettings).first()
    finally:
        db.close()


@app.post("/webhook")
async def webhook(request: Request):
    if not TOKEN:
        return {"error": "TOKEN not configured"}
    data = await request.json()
    bot = Bot(token=TOKEN)
    update = Update.de_json(data, bot)
    if update.message and update.message.text:
        await handle_update(update, bot)
    return {"message": "ok"}


@app.get("/", response_class=HTMLResponse)
def index(request: Request):
    return templates.TemplateResponse(request, "landing.html")


@app.get("/signup", response_class=HTMLResponse)
def signup_get(request: Request):
    return templates.TemplateResponse(request, "signup.html")


@app.post("/signup")
async def signup_post(
    request: Request,
    full_name: str = Form(...),
    email: str = Form(...),
    phone: str = Form(...),
    password: str = Form(...),
):
    full_name = full_name.strip()
    email = email.strip().lower()
    phone = phone.strip()
    if len(full_name) < 2 or len(password) < 6:
        return templates.TemplateResponse(request, "signup.html", {"error": "Name too short or password too weak."})
    user = create_user(full_name, email, phone, password)
    if not user:
        return templates.TemplateResponse(request, "signup.html", {"error": "An account with this email already exists."})
    token = create_session_token(user.id)
    log_action(user.id, "user.signup", {"email": email})
    resp = RedirectResponse(url="/dashboard", status_code=303)
    resp.set_cookie(key="session", value=token, httponly=True, max_age=86400 * 7, samesite="lax")
    return resp


@app.get("/login", response_class=HTMLResponse)
def login_get(request: Request):
    return templates.TemplateResponse(request, "login.html")


@app.post("/login")
async def login_post(
    request: Request,
    email: str = Form(...),
    password: str = Form(...),
):
    email = email.strip().lower()
    user = authenticate_user(email, password)
    if not user:
        return templates.TemplateResponse(request, "login.html", {"error": "Invalid email or password."})
    token = create_session_token(user.id)
    log_action(user.id, "user.login", {"email": email})
    resp = RedirectResponse(url="/dashboard", status_code=303)
    resp.set_cookie(key="session", value=token, httponly=True, max_age=86400 * 7, samesite="lax")
    return resp


@app.get("/dashboard", response_class=HTMLResponse)
def dashboard(request: Request):
    user = _get_user_from_cookie(request)
    if not user:
        return RedirectResponse(url="/login")
    if not user.is_active:
        resp = RedirectResponse(url="/logout")
        return resp
    wallet = get_wallet(user.id)
    db = SessionLocal()
    try:
        transactions = (
            db.query(Transaction)
            .filter(Transaction.user_id == user.id, Transaction.status != "closed")
            .order_by(Transaction.created_at.desc())
            .limit(5)
            .all()
        )
    finally:
        db.close()
    return templates.TemplateResponse(request, "dashboard.html", {
        "user": user,
        "wallet": wallet,
        "transactions": transactions,
        "telegram_link_msg": "",
    })


@app.get("/logout")
def logout(request: Request):
    session_token = request.cookies.get("session")
    if session_token:
        user = get_user_by_token(session_token)
        if user:
            log_action(user.id, "user.logout")
        delete_session(session_token)
    resp = RedirectResponse(url="/")
    resp.delete_cookie("session")
    return resp


# --- Deposit Routes ---

@app.get("/deposit", response_class=HTMLResponse)
def deposit_get(request: Request):
    user = _get_user_from_cookie(request)
    if not user:
        return RedirectResponse(url="/login")
    settings = _get_settings()
    return templates.TemplateResponse(request, "deposit.html", {
        "user": user,
        "base_phone": settings.base_phone_number if settings else "",
    })


@app.post("/deposit")
async def deposit_post(request: Request, receipt_number: str = Form(...)):
    user = _get_user_from_cookie(request)
    if not user:
        return RedirectResponse(url="/login")
    if user.is_frozen:
        return templates.TemplateResponse(request, "deposit.html", {
            "user": user,
            "success": False, "message": "Your account is frozen. Cannot process deposits.",
        })

    receipt_number = receipt_number.strip()
    if not receipt_number:
        return templates.TemplateResponse(request, "deposit.html", {
                "user": user,
            "success": False,
            "message": "Receipt number is required.",
        })

    result = await verify_receipt(receipt_number)
    if not result["valid"]:
        return templates.TemplateResponse(request, "deposit.html", {
                "user": user,
            "success": False,
            "message": result.get("error", "Receipt verification failed."),
        })

    details = result["details"]
    amount = details.get("settled_amount_num", 0)
    total_paid = details.get("total_paid_num")

    settings = _get_settings()
    fee_percent = settings.service_fee_percent if settings else Decimal("0.00")
    service_fee = Decimal("0.00")
    if fee_percent > 0 and amount:
        service_fee = (amount * fee_percent) / Decimal("100")

    db = SessionLocal()
    try:
        txn = Transaction(
            user_id=user.id,
            type="deposit",
            receipt_no=receipt_number,
            amount=amount,
            service_fee=service_fee,
            total_paid=total_paid,
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
            "receipt_no": receipt_number,
            "amount": str(amount),
        })
        return templates.TemplateResponse(request, "deposit.html", {
                "user": user,
            "success": True,
            "message": "Deposit request submitted successfully!",
            "txn": txn,
        })
    finally:
        db.close()


# --- Withdrawal Routes ---

@app.post("/withdraw")
async def withdraw_post(
    request: Request,
    amount: str = Form(...),
    reason: str = Form(""),
):
    user = _get_user_from_cookie(request)
    if not user:
        return RedirectResponse(url="/login")
    if user.is_frozen:
        return RedirectResponse(url="/dashboard", status_code=303)

    try:
        amount_dec = Decimal(amount)
        if amount_dec <= 0:
            return RedirectResponse(url="/dashboard", status_code=303)
    except Exception:
        return RedirectResponse(url="/dashboard", status_code=303)

    db = SessionLocal()
    try:
        wallet = db.query(Wallet).filter(Wallet.user_id == user.id).first()
        if not wallet or wallet.balance < amount_dec:
            return RedirectResponse(url="/dashboard", status_code=303)

        # double-shield: check for duplicate pending withdrawal patterns
        existing_pending = (
            db.query(Transaction)
            .filter(
                Transaction.user_id == user.id,
                Transaction.type == "withdrawal",
                Transaction.status.in_(["pending"]),
            )
            .all()
        )

        wallet.balance -= amount_dec
        txn = Transaction(
            user_id=user.id,
            type="withdrawal",
            amount=amount_dec,
            reason=reason.strip() if reason else None,
            status="pending",
        )
        db.add(txn)
        db.commit()
        db.refresh(txn)
        log_action(user.id, "withdrawal.request", {
            "transaction_id": txn.id,
            "amount": str(amount_dec),
        })
    finally:
        db.close()

    return RedirectResponse(url="/status/" + str(txn.id), status_code=303)


# --- Status Routes ---

@app.get("/status", response_class=HTMLResponse)
def status_list(request: Request, page: int = 1):
    user = _get_user_from_cookie(request)
    if not user:
        return RedirectResponse(url="/login")
    per_page = 10
    db = SessionLocal()
    try:
        total = db.query(Transaction).filter(
            Transaction.user_id == user.id,
            Transaction.status != "closed",
        ).count()
        transactions = (
            db.query(Transaction)
            .filter(Transaction.user_id == user.id, Transaction.status != "closed")
            .order_by(Transaction.created_at.desc())
            .offset((page - 1) * per_page)
            .limit(per_page)
            .all()
        )
        total_pages = max(1, (total + per_page - 1) // per_page)
    finally:
        db.close()
    return templates.TemplateResponse(request, "status_list.html", {
        "user": user,
        "transactions": transactions,
        "page": page,
        "total_pages": total_pages,
    })


@app.get("/status/{txn_id}", response_class=HTMLResponse)
def status_detail(request: Request, txn_id: int):
    user = _get_user_from_cookie(request)
    if not user:
        return RedirectResponse(url="/login")
    db = SessionLocal()
    try:
        txn = (
            db.query(Transaction)
            .filter(Transaction.id == txn_id, Transaction.user_id == user.id)
            .first()
        )
        if not txn:
            return RedirectResponse(url="/status")
    finally:
        db.close()
    return templates.TemplateResponse(request, "status_detail.html", {
        "user": user,
        "txn": txn,
        "dispute_submitted": False,
    })


@app.post("/status/{txn_id}/dispute")
async def dispute_post(
    request: Request,
    txn_id: int,
    description: str = Form(...),
    dispute_txn_number: str = Form(""),
    attachment: UploadFile = File(None),
):
    user = _get_user_from_cookie(request)
    if not user:
        return RedirectResponse(url="/login")

    db = SessionLocal()
    try:
        txn = (
            db.query(Transaction)
            .filter(Transaction.id == txn_id, Transaction.user_id == user.id)
            .first()
        )
        if not txn or txn.status != "rejected":
            return RedirectResponse(url="/status")

        txn.dispute_reason = description.strip()
        txn.receipt_no = dispute_txn_number.strip() or txn.receipt_no
        txn.status = "disputed"
        if attachment and attachment.filename:
            import aiofiles
            upload_dir = "/tmp/disputes"
            os.makedirs(upload_dir, exist_ok=True)
            safe_name = f"{txn_id}_{datetime.datetime.utcnow().timestamp()}_{attachment.filename}"
            filepath = os.path.join(upload_dir, safe_name)
            content = await attachment.read()
            if len(content) < 5 * 1024 * 1024:
                async with aiofiles.open(filepath, "wb") as f:
                    await f.write(content)
                txn.attachment_path = filepath

        db.commit()
        log_action(user.id, "dispute.submit", {"transaction_id": txn_id})
    finally:
        db.close()

    return RedirectResponse(url=f"/status/{txn_id}", status_code=303)


@app.post("/admin/disputes/{txn_id}/close")
async def admin_close_dispute(request: Request, txn_id: int, note: str = Form("")):
    user, error = _get_admin_or_redirect(request)
    if error:
        return error
    db = SessionLocal()
    try:
        txn = db.query(Transaction).filter(Transaction.id == txn_id).first()
        if txn and txn.status == "disputed":
            txn.status = "closed"
            txn.admin_note = (txn.admin_note or "") + " | Closed: " + note.strip() if note.strip() else txn.admin_note
            txn.admin_id = user.id
            txn.resolved_at = datetime.datetime.utcnow()
            db.commit()
            log_action(user.id, "dispute.close", {"transaction_id": txn_id, "note": note.strip()})
    finally:
        db.close()
    return RedirectResponse(url="/admin/deposits", status_code=303)


@app.post("/admin/disputes/{txn_id}/reject-again")
async def admin_reject_dispute_again(request: Request, txn_id: int, reason: str = Form("")):
    user, error = _get_admin_or_redirect(request)
    if error:
        return error
    db = SessionLocal()
    try:
        txn = db.query(Transaction).filter(Transaction.id == txn_id).first()
        if txn and txn.status == "disputed":
            txn.status = "rejected"
            txn.admin_note = reason.strip() if reason.strip() else "Dispute rejected"
            txn.admin_id = user.id
            txn.updated_at = datetime.datetime.utcnow()
            db.commit()
            log_action(user.id, "dispute.reject", {"transaction_id": txn_id, "reason": reason.strip()})
    finally:
        db.close()
    return RedirectResponse(url="/admin/deposits", status_code=303)


# --- Admin Routes ---

@app.get("/admin", response_class=HTMLResponse)
def admin_dashboard(request: Request):
    user, error = _get_admin_or_redirect(request)
    if error:
        return error
    db = SessionLocal()
    try:
        pending_deposits = db.query(Transaction).filter(
            Transaction.type == "deposit", Transaction.status == "pending"
        ).count()
        pending_withdrawals = db.query(Transaction).filter(
            Transaction.type == "withdrawal", Transaction.status == "pending"
        ).count()
        total_users = db.query(User).count()
        total_wallets = db.query(Wallet).count()
        total_deposits = db.query(Transaction).filter(
            Transaction.type == "deposit", Transaction.status == "approved"
        ).count()
        total_withdrawals = db.query(Transaction).filter(
            Transaction.type == "withdrawal", Transaction.status == "completed"
        ).count()
        disputes = (
            db.query(Transaction)
            .filter(Transaction.status == "disputed")
            .order_by(Transaction.created_at.desc())
            .limit(10)
            .all()
        )
    finally:
        db.close()
    return templates.TemplateResponse(request, "admin_dashboard.html", {
        "user": user,
        "pending_deposits": pending_deposits,
        "pending_withdrawals": pending_withdrawals,
        "total_users": total_users,
        "total_wallets": total_wallets,
        "total_deposits": total_deposits,
        "total_withdrawals": total_withdrawals,
        "disputes": disputes,
    })


@app.get("/admin/deposits", response_class=HTMLResponse)
def admin_deposits(request: Request):
    user, error = _get_admin_or_redirect(request)
    if error:
        return error
    db = SessionLocal()
    try:
        pending = (
            db.query(Transaction)
            .filter(Transaction.type == "deposit", Transaction.status == "pending")
            .order_by(Transaction.created_at.desc())
            .all()
        )
        disputed = (
            db.query(Transaction)
            .filter(Transaction.type == "deposit", Transaction.status == "disputed")
            .order_by(Transaction.created_at.desc())
            .all()
        )
        settings = db.query(AdminSettings).first()
    finally:
        db.close()
    return templates.TemplateResponse(request, "admin_deposits.html", {
        "user": user,
        "pending_deposits": pending,
        "disputed_deposits": disputed,
        "service_fee_percent": settings.service_fee_percent if settings else 0,
    })


@app.post("/admin/deposits/{txn_id}/approve")
async def admin_approve_deposit(request: Request, txn_id: int):
    user, error = _get_admin_or_redirect(request)
    if error:
        return error
    db = SessionLocal()
    try:
        txn = db.query(Transaction).filter(Transaction.id == txn_id).first()
        if not txn or txn.type != "deposit" or txn.status != "pending":
            return RedirectResponse(url="/admin/deposits", status_code=303)

        settings = db.query(AdminSettings).first()
        fee_percent = settings.service_fee_percent if settings else Decimal("0.00")
        service_fee = Decimal("0.00")
        if fee_percent > 0 and txn.amount:
            service_fee = (txn.amount * fee_percent) / Decimal("100")

        txn.service_fee = service_fee
        txn.status = "approved"
        txn.admin_id = user.id
        txn.updated_at = datetime.datetime.utcnow()

        wallet = db.query(Wallet).filter(Wallet.user_id == txn.user_id).first()
        if wallet:
            wallet.balance += (txn.amount - service_fee)
            wallet.updated_at = datetime.datetime.utcnow()

        db.commit()
        log_action(user.id, "deposit.approve", {
            "transaction_id": txn_id,
            "amount": str(txn.amount),
            "fee": str(service_fee),
            "credited": str(txn.amount - service_fee),
            "user_id": txn.user_id,
        })
    finally:
        db.close()
    return RedirectResponse(url="/admin/deposits", status_code=303)


@app.post("/admin/deposits/{txn_id}/reject")
async def admin_reject_deposit(request: Request, txn_id: int, reason: str = Form("")):
    user, error = _get_admin_or_redirect(request)
    if error:
        return error
    db = SessionLocal()
    try:
        txn = db.query(Transaction).filter(Transaction.id == txn_id).first()
        if txn and txn.type == "deposit" and txn.status == "pending":
            txn.status = "rejected"
            txn.admin_note = reason.strip() if reason.strip() else "Rejected by admin"
            txn.admin_id = user.id
            txn.updated_at = datetime.datetime.utcnow()
            db.commit()
            log_action(user.id, "deposit.reject", {
                "transaction_id": txn_id,
                "reason": reason.strip(),
                "user_id": txn.user_id,
            })
    finally:
        db.close()
    return RedirectResponse(url="/admin/deposits", status_code=303)


@app.get("/admin/withdrawals", response_class=HTMLResponse)
def admin_withdrawals(request: Request):
    user, error = _get_admin_or_redirect(request)
    if error:
        return error
    db = SessionLocal()
    try:
        pending = (
            db.query(Transaction)
            .filter(Transaction.type == "withdrawal", Transaction.status == "pending")
            .order_by(Transaction.created_at.desc())
            .all()
        )
    finally:
        db.close()
    return templates.TemplateResponse(request, "admin_withdrawals.html", {
        "user": user,
        "pending_withdrawals": pending,
    })


@app.post("/admin/withdrawals/{txn_id}/complete")
async def admin_complete_withdrawal(
    request: Request, txn_id: int,
    transaction_number: str = Form(...),
):
    user, error = _get_admin_or_redirect(request)
    if error:
        return error
    db = SessionLocal()
    try:
        txn = db.query(Transaction).filter(Transaction.id == txn_id).first()
        if txn and txn.type == "withdrawal" and txn.status == "pending":
            txn.status = "completed"
            txn.receipt_no = transaction_number.strip()
            txn.admin_id = user.id
            txn.updated_at = datetime.datetime.utcnow()
            db.commit()
            log_action(user.id, "withdrawal.complete", {
                "transaction_id": txn_id,
                "txn_number": transaction_number.strip(),
                "user_id": txn.user_id,
            })
    finally:
        db.close()
    return RedirectResponse(url="/admin/withdrawals", status_code=303)


@app.post("/admin/withdrawals/{txn_id}/reject")
async def admin_reject_withdrawal(request: Request, txn_id: int, reason: str = Form("")):
    user, error = _get_admin_or_redirect(request)
    if error:
        return error
    db = SessionLocal()
    try:
        txn = db.query(Transaction).filter(Transaction.id == txn_id).first()
        if txn and txn.type == "withdrawal" and txn.status == "pending":
            txn.status = "rejected"
            txn.admin_note = reason.strip() if reason.strip() else "Rejected by admin"
            txn.admin_id = user.id
            txn.updated_at = datetime.datetime.utcnow()

            wallet = db.query(Wallet).filter(Wallet.user_id == txn.user_id).first()
            if wallet:
                wallet.balance += txn.amount
                wallet.updated_at = datetime.datetime.utcnow()

            db.commit()
            log_action(user.id, "withdrawal.reject", {
                "transaction_id": txn_id,
                "reason": reason.strip(),
                "user_id": txn.user_id,
                "refunded": str(txn.amount),
            })
    finally:
        db.close()
    return RedirectResponse(url="/admin/withdrawals", status_code=303)


@app.get("/admin/users", response_class=HTMLResponse)
def admin_users(request: Request):
    user, error = _get_admin_or_redirect(request)
    if error:
        return error
    db = SessionLocal()
    try:
        users = db.query(User).order_by(User.created_at.desc()).all()
        wallets = db.query(Wallet).all()
        user_wallets = {w.user_id: float(w.balance) for w in wallets}
    finally:
        db.close()
    return templates.TemplateResponse(request, "admin_users.html", {
        "user": user,
        "users": users,
        "user_wallets": user_wallets,
    })


@app.post("/admin/users/{user_id}/restrict")
async def admin_restrict_user(
    request: Request,
    user_id: int,
    action: str = Form(...),
    reason: str = Form(""),
    expires_at: str = Form(""),
    permissions: list[str] = Form([]),
):
    admin_user, error = _get_admin_or_redirect(request)
    if error:
        return error
    db = SessionLocal()
    try:
        target = db.query(User).filter(User.id == user_id).first()
        if not target:
            return RedirectResponse(url="/admin/users", status_code=303)

        if action == "ban":
            target.is_active = False
            target.is_frozen = False
            log_action(admin_user.id, "admin.ban", {
                "target_user_id": user_id, "reason": reason.strip()
            })
        elif action == "freeze":
            target.is_frozen = True
            exp = None
            if expires_at:
                try:
                    exp = datetime.datetime.fromisoformat(expires_at)
                except ValueError:
                    pass
            restriction = UserRestriction(
                user_id=user_id,
                restriction_type="freeze",
                reason=reason.strip() or None,
                expires_at=exp,
                created_by=admin_user.id,
            )
            db.add(restriction)
            log_action(admin_user.id, "admin.freeze", {
                "target_user_id": user_id, "reason": reason.strip(), "expires": expires_at
            })
        elif action == "restrict":
            restriction = UserRestriction(
                user_id=user_id,
                restriction_type="restrict",
                permissions_json=json.dumps(permissions),
                reason=reason.strip() or None,
                created_by=admin_user.id,
            )
            db.add(restriction)
            log_action(admin_user.id, "admin.restrict", {
                "target_user_id": user_id, "permissions": permissions, "reason": reason.strip()
            })
        elif action == "unban":
            target.is_active = True
            target.is_frozen = False
            db.query(UserRestriction).filter(
                UserRestriction.user_id == user_id
            ).delete()
            log_action(admin_user.id, "admin.unban", {"target_user_id": user_id})

        db.commit()
    finally:
        db.close()
    return RedirectResponse(url="/admin/users", status_code=303)


@app.post("/admin/users/{user_id}/scan")
async def admin_scan_user(request: Request, user_id: int):
    admin_user, error = _get_admin_or_redirect(request)
    if error:
        return error
    scan_results = []
    db = SessionLocal()
    try:
        pending_txns = (
            db.query(Transaction)
            .filter(
                Transaction.user_id == user_id,
                Transaction.status.in_(["pending", "disputed"]),
            )
            .all()
        )
        for txn in pending_txns:
            if txn.receipt_no and txn.type == "deposit":
                try:
                    result = await verify_receipt(txn.receipt_no)
                    scan_results.append({
                        "txn_id": txn.id,
                        "receipt": txn.receipt_no,
                        "valid": result["valid"],
                        "error": result.get("error"),
                    })
                except Exception as e:
                    scan_results.append({
                        "txn_id": txn.id, "receipt": txn.receipt_no,
                        "valid": False, "error": str(e),
                    })
        log_action(admin_user.id, "admin.scan", {
            "target_user_id": user_id,
            "pending_count": len(pending_txns),
            "results": scan_results,
        })
    finally:
        db.close()
    return RedirectResponse(url="/admin/users", status_code=303)


@app.get("/admin/settings", response_class=HTMLResponse)
def admin_settings_get(request: Request):
    user, error = _get_admin_or_redirect(request)
    if error:
        return error
    settings = _get_settings()
    db = SessionLocal()
    try:
        logs = (
            db.query(ActivityLog)
            .order_by(ActivityLog.created_at.desc())
            .limit(50)
            .all()
        )
    finally:
        db.close()
    return templates.TemplateResponse(request, "admin_settings.html", {
        "user": user,
        "settings": settings,
        "logs": logs,
    })


@app.post("/admin/settings")
async def admin_settings_post(
    request: Request,
    service_fee_percent: str = Form("0"),
    base_phone_number: str = Form(""),
):
    user, error = _get_admin_or_redirect(request)
    if error:
        return error
    db = SessionLocal()
    try:
        settings = db.query(AdminSettings).first()
        if not settings:
            settings = AdminSettings()
            db.add(settings)
        try:
            settings.service_fee_percent = Decimal(service_fee_percent)
        except Exception:
            settings.service_fee_percent = Decimal("0.00")
        settings.base_phone_number = base_phone_number.strip()
        settings.updated_at = datetime.datetime.utcnow()
        db.commit()
        log_action(user.id, "admin.settings.update", {
            "service_fee_percent": service_fee_percent,
            "base_phone_number": base_phone_number.strip(),
        })
    finally:
        db.close()
    return RedirectResponse(url="/admin/settings", status_code=303)


# --- Bot Dashboard ---

@app.post("/api/test-webhook")
async def test_webhook():
    if not TOKEN:
        return {"status": "error", "message": "TOKEN not configured"}
    try:
        bot = Bot(token=TOKEN)
        me = await bot.get_me()
        info = await bot.get_webhook_info()
        return {
            "status": "ok",
            "bot": me.username,
            "webhook": info.url,
            "pending": info.pending_update_count,
        }
    except Exception as e:
        return {"status": "error", "message": str(e)}


@app.get("/api/trace")
async def get_trace():
    try:
        with open("/var/task/api/index.py") as f:
            deployed = f.read()
        has_app_process = "application.process_update" in deployed
        return {"using_old_code": has_app_process}
    except Exception:
        return {"using_old_code": None}


@app.get("/bot-dashboard", response_class=HTMLResponse)
async def bot_dashboard(request: Request):
    errors = []
    me = None
    webhook_info = None

    if not TOKEN:
        errors.append("TOKEN environment variable is not set")
    else:
        bot = Bot(token=TOKEN)
        try:
            me = await bot.get_me()
        except Exception as e:
            errors.append(f"getMe failed: {e}")
        try:
            webhook_info = await bot.get_webhook_info()
        except Exception as e:
            errors.append(f"getWebhookInfo failed: {e}")

    token_status = "✅ Configured" if TOKEN else "❌ Not configured"
    bot_name = me.first_name if me else "-"
    bot_username = f"@{me.username}" if me else "-"
    wh = webhook_info
    webhook_url = wh.url if wh else "-"
    pending = wh.pending_update_count if wh else "-"
    last_err = wh.last_error_message or "None" if wh else "-"

    return templates.TemplateResponse(request, "bot_dashboard.html", {
        "token_status": token_status,
        "bot_name": bot_name,
        "bot_username": bot_username,
        "webhook_url": webhook_url,
        "pending": pending,
        "last_err": last_err,
        "errors": errors,
        "TOKEN": TOKEN,
    })
