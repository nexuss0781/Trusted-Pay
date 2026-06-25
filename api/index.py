import os, sys
sys.path.insert(0, os.path.dirname(__file__))
from fastapi import FastAPI, Request, Form, Cookie
from fastapi.responses import HTMLResponse, RedirectResponse
from telegram import Update, Bot

TOKEN = os.environ.get("TOKEN")
app = FastAPI()

# ──────────────────────────────────────────────
# EXTEND HERE — add features in api/features/
#   features/commands.py  →  handle_update()
# ──────────────────────────────────────────────
from features import handle_update

# App modules
from database import init_db
from auth import create_user, authenticate_user, create_session_token, get_user_by_token, delete_session
from web.templates import landing_page, signup_page, login_page, dashboard_page


@app.on_event("startup")
def on_startup():
    init_db()


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
def index():
    return landing_page()


@app.get("/signup", response_class=HTMLResponse)
def signup_get():
    return signup_page()


@app.post("/signup")
async def signup_post(
    full_name: str = Form(...),
    email: str = Form(...),
    phone: str = Form(...),
    password: str = Form(...),
):
    user = create_user(full_name, email, phone, password)
    if not user:
        return signup_page(error="An account with this email already exists.")
    token = create_session_token(user.id)
    resp = RedirectResponse(url="/dashboard", status_code=303)
    resp.set_cookie(key="session", value=token, httponly=True, max_age=86400 * 7)
    return resp


@app.get("/login", response_class=HTMLResponse)
def login_get():
    return login_page()


@app.post("/login")
async def login_post(
    email: str = Form(...),
    password: str = Form(...),
):
    user = authenticate_user(email, password)
    if not user:
        return login_page(error="Invalid email or password.")
    token = create_session_token(user.id)
    resp = RedirectResponse(url="/dashboard", status_code=303)
    resp.set_cookie(key="session", value=token, httponly=True, max_age=86400 * 7)
    return resp


@app.get("/dashboard", response_class=HTMLResponse)
def dashboard(session: str = Cookie(default=None)):
    if not session:
        return RedirectResponse(url="/login")
    user = get_user_by_token(session)
    if not user:
        return RedirectResponse(url="/login")
    return dashboard_page(user)


@app.get("/logout")
def logout(session: str = Cookie(default=None)):
    if session:
        delete_session(session)
    resp = RedirectResponse(url="/")
    resp.delete_cookie("session")
    return resp


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
    except:
        return {"using_old_code": None}


@app.get("/bot-dashboard", response_class=HTMLResponse)
async def bot_dashboard():
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

    html = f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>Bot Dashboard</title>
<style>
* {{ box-sizing: border-box; }}
body {{ font-family: system-ui, sans-serif; max-width: 720px; margin: 40px auto; padding: 0 20px; background: #0f172a; color: #e2e8f0; }}
h1 {{ color: #f8fafc; font-size: 1.5rem; }}
.card {{ background: #1e293b; border-radius: 10px; padding: 20px; margin: 16px 0; border: 1px solid #334155; }}
.item {{ display: flex; justify-content: space-between; padding: 10px 0; border-bottom: 1px solid #334155; font-size: 0.95rem; }}
.item:last-child {{ border: none; }}
.label {{ color: #94a3b8; }}
.value {{ font-weight: 600; color: #e2e8f0; }}
.badge {{ display: inline-block; padding: 2px 10px; border-radius: 99px; font-size: 0.8rem; font-weight: 600; }}
.badge.ok {{ background: #064e3b; color: #6ee7b7; }}
.badge.err {{ background: #450a0a; color: #fca5a5; }}
.badge.warn {{ background: #451a03; color: #fdba74; }}
.btn {{ background: #3b82f6; color: #fff; border: none; padding: 10px 20px; border-radius: 8px; cursor: pointer; font-size: 0.9rem; }}
.btn:hover {{ background: #2563eb; }}
pre {{ background: #0f172a; padding: 12px; border-radius: 6px; font-size: 0.8rem; overflow-x: auto; margin: 8px 0; }}
#result {{ margin-top: 12px; }}
</style>
</head>
<body>
<h1>Bot Dashboard</h1>
<div class="card">
<div class="item"><span class="label">Token</span><span class="value"><span class="badge {'ok' if TOKEN else 'err'}">{token_status}</span></span></div>
<div class="item"><span class="label">Bot Name</span><span class="value">{bot_name}</span></div>
<div class="item"><span class="label">Username</span><span class="value">{bot_username}</span></div>
</div>
<div class="card">
<div class="item"><span class="label">Webhook URL</span><span class="value">{webhook_url}</span></div>
<div class="item"><span class="label">Pending Updates</span><span class="value">{pending}</span></div>
<div class="item"><span class="label">Last Error</span><span class="value">{last_err}</span></div>
</div>
{"".join(f"<div class='card' style='border-left:4px solid #ef4444'><b>Error:</b> {e}</div>" for e in errors) if errors else "<div class='card' style='border-left:4px solid #22c55e'><b>All checks passed</b></div>"}
<div class="card">
<b>End-to-End Test</b>
<button class="btn" onclick="testBot()">Test Webhook</button>
<div id="result"></div>
</div>
<script>
async function testBot() {{
const btn = document.querySelector('.btn');
btn.disabled = true; btn.textContent = 'Testing...';
try {{
const r = await fetch('/api/test-webhook', {{method:'POST'}});
const d = await r.json();
document.getElementById('result').innerHTML =
'<pre>' + JSON.stringify(d, null, 2) + '</pre>';
}} catch(e) {{
document.getElementById('result').innerHTML = '<pre style="color:#ef4444">' + e + '</pre>';
}}
btn.disabled = false; btn.textContent = 'Test Webhook';
}}
</script>
</body>
</html>"""
    return HTMLResponse(content=html)
