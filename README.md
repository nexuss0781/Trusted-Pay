# Telegram Bot Boilerplate

A production-ready Telegram bot boilerplate for **Vercel** (serverless, webhook) with built-in **web authentication** — sign up, log in, Telegram linking, and a polished UI.

Drop it in, swap the logic, add your features. Reusable for any Telegram bot project.

## What's Inside

### Bot (Telegram)
- `/start` — welcome message
- `/help` — available commands
- `/login` — get web login URL
- `/link <email> <password>` — link Telegram to your web account
- `/logoff` — disconnect Telegram from your account

### Web (FastAPI)
- **Landing page** — professional glassmorphism design with dark/light mode
- **Sign up** — full name, email, phone, password
- **Log in** — email + password
- **Dashboard** — account details + Telegram connection status
- **Log out** — session cleanup

### Stack
- **Backend**: FastAPI + python-telegram-bot + SQLAlchemy + SQLite
- **Frontend**: TailwindCSS + Lucide icons + glassmorphism
- **Deploy**: Vercel (serverless, webhook)
- **Database**: SQLite (`/tmp/trusted.db`, configurable via `DB_PATH` env var)

### Color Palette
`#1B325F` `#5E9FA3` `#DCD1B4` `#FAB87F` `#F87E7B` `#B05574`

## Quick Start

1. Fork, push to GitHub, import into Vercel
2. Set environment variables in Vercel:
   - `TOKEN` — from [@BotFather](https://t.me/botfather)
   - `BASE_URL` — your Vercel deployment URL
3. Deploy, then register webhook:
```bash
curl -X POST "https://api.telegram.org/bot<TOKEN>/setWebhook?url=https://<VERCEL_URL>/webhook"
```
4. Visit your Vercel URL — landing page is live

## Local Dev

```bash
git clone <repo>
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt uvicorn
export TOKEN=<token>
export BASE_URL=http://localhost:8000
uvicorn api.index:app --reload --port 8000
```

## Project Structure

```
├── api/
│   ├── index.py              # FastAPI app + routes
│   ├── database.py           # SQLAlchemy engine
│   ├── models.py             # User + Session models
│   ├── auth.py               # Password hashing, sessions, Telegram link
│   ├── features/
│   │   ├── __init__.py       # Re-exports handle_update
│   │   └── commands.py       # Bot command handlers
│   └── web/
│       ├── __init__.py
│       └── templates.py      # HTML templates (Tailwind + Lucide)
├── vercel.json
└── requirements.txt
```
