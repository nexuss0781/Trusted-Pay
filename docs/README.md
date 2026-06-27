# Trusted Pay

A secure wallet and account management platform with Telebirr integration. Users deposit money via Telebirr receipts, admin verifies and approves transactions, and funds are credited to user wallets. The system supports deposits, withdrawals, disputes, user restrictions, and full activity logging.

## Features

- **Wallet System** — Users have wallets with real-time balance tracking
- **Telebirr Receipt Verification** — 4-layer verification (regex patterns, DOM fingerprint, field extraction, status check)
- **Deposit Flow** — Submit Telebirr receipt numbers, verified against the official Telebirr receipt API
- **Withdrawal Flow** — Request withdrawals, deducted immediately, admin completes with transaction number
- **Dispute Resolution** — Users can dispute rejected transactions, admin can close or reject-again
- **Admin Dashboard** — Full admin panel for managing deposits, withdrawals, users, and settings
- **Telegram Bot** — Bot commands for deposits, balance checks, and admin operations
- **User Restrictions** — Ban, freeze (with expiry), or restrict permissions
- **Activity Logging** — Every action logged with timestamp and details
- **Security Headers** — CSP, X-Frame-Options, XSS protection, Referrer-Policy

## Tech Stack

| Component | Technology |
|-----------|------------|
| Framework | FastAPI (Python) |
| Database | SQLite via SQLAlchemy ORM |
| Templates | Jinja2 with Tailwind CSS |
| Telegram | python-telegram-bot (v20.x) |
| HTTP | httpx (for Telebirr API calls) |
| Deployment | Vercel (serverless) |

## Quick Start

```bash
# Install dependencies
pip install -r requirements.txt

# Set environment variables
export TOKEN="your_telegram_bot_token"
export BASE_URL="http://localhost:8000"

# Run
uvicorn api.index:app --reload
```

## Documentation

| Document | Description |
|----------|-------------|
| [Getting Started](GETTING_STARTED.md) | Setup, configuration, and deployment guide |
| [Architecture](ARCHITECTURE.md) | System architecture and component overview |
| [API Reference](API_REFERENCE.md) | Complete API routes documentation |
| [Database Schema](DATABASE.md) | Database models, fields, and relationships |
| [Telebirr Verification](TELEBIRR_VERIFICATION.md) | Receipt verification system details |
| [Bot Commands](BOT_COMMANDS.md) | Telegram bot commands reference |
| [Admin Guide](ADMIN_GUIDE.md) | Admin operations and workflows |
| [Workflows](WORKFLOWS.md) | Deposit, withdrawal, and dispute flows |
| [Security](SECURITY.md) | Security features and recommendations |

## Environment Variables

| Variable | Required | Default | Description |
|----------|----------|---------|-------------|
| `TOKEN` | Yes | — | Telegram Bot API token |
| `BASE_URL` | No | `https://trusted.vercel.app` | Base URL for link generation |
| `ADMIN_CHAT_IDS` | No | `""` | Comma-separated Telegram chat IDs with admin bot access |
| `DB_PATH` | No | `/tmp/trusted.db` | SQLite database file path |

## Project Structure

```
├── api/
│   ├── index.py              # FastAPI app, routes, middleware
│   ├── auth.py               # User authentication, sessions, wallet
│   ├── database.py           # SQLAlchemy engine and session setup
│   ├── models.py             # All database models
│   ├── telebirr.py           # Telebirr receipt verification
│   ├── structure.py          # Structural fingerprint verification
│   ├── logger.py             # Activity logging and snapshots
│   ├── features/
│   │   ├── __init__.py       # Bot update dispatcher
│   │   └── commands.py       # Bot command handlers
│   ├── templates/            # Jinja2 HTML templates
│   └── static/               # Static assets (CSS)
├── docs/                     # Documentation
├── requirements.txt          # Python dependencies
├── vercel.json               # Vercel deployment config
└── example.html              # Reference Telebirr receipt HTML
```
