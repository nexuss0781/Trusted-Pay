<div align="center">
  <img src="https://img.shields.io/badge/status-active-success.svg" alt="Status">
  <img src="https://img.shields.io/badge/python-3.10%2B-blue" alt="Python">
  <img src="https://img.shields.io/badge/framework-FastAPI-009688" alt="FastAPI">
  <img src="https://img.shields.io/badge/license-MIT-yellow" alt="License">
  <br/>
  <h1>Trusted Pay</h1>
  <p><strong>Secure Wallet & Account Management with Telebirr Integration</strong></p>
  <p>A production-ready platform for managing deposits, withdrawals, and disputes using Telebirr receipt verification. Features a Telegram bot, admin dashboard, and multi-layer security.</p>
</div>

---

## Features

<table>
<tr>
<td width="50%">

### 💰 Wallet System
- User wallets with real-time balance tracking
- Deposit via Telebirr receipt submission
- Withdrawal requests with admin approval
- Configurable service fee percentage

### 🔒 4-Layer Security
- 53-pattern regex structure verification
- 19-point DOM fingerprint comparison
- Field extraction with numeric validation
- Transaction status enforcement

### 🤖 Telegram Bot
- Link Telegram to your account
- Deposit via `/deposit` command
- Balance check and status tracking
- Admin commands for queue management

</td>
<td width="50%">

### 👨‍💼 Admin Panel
- Deposit approval/rejection queue
- Withdrawal processing with transaction numbers
- User management (ban, freeze, restrict)
- Dispute resolution system
- Activity log viewer
- Service fee configuration

### 📊 Full Audit Trail
- Every action logged with timestamps
- Automatic 2-hour platform snapshots
- Daily financial aggregations
- Admin scan for live verification

### 🚀 Production Ready
- Vercel serverless deployment
- SQLite + SQLAlchemy ORM
- Tailwind CSS glassmorphism UI
- Dark/light mode
- CSP security headers

</td>
</tr>
</table>

---

## Quick Start

```bash
# Clone and install
git clone https://github.com/nexuss0781/Trusted-Pay.git
cd Trusted-Pay
pip install -r requirements.txt

# Set env vars
export TOKEN="your_telegram_bot_token"
export BASE_URL="http://localhost:8000"
export ADMIN_CHAT_IDS="your_chat_id"

# Run
uvicorn api.index:app --reload --port 8000
```

[▶ Full setup guide →](docs/GETTING_STARTED.md)

---

## Screenshots

<div align="center">
<table>
<tr>
<td><em>Dashboard</em></td>
<td><em>Admin Panel</em></td>
<td><em>Deposit Flow</em></td>
</tr>
</table>
</div>

---

## Architecture

```
┌─────────┐     ┌───────────┐     ┌──────────────────┐
│  Users   │────▶│  FastAPI  │────▶│  Telebirr API    │
│ (Web)    │     │  App      │     │  (Verification)  │
└─────────┘     └─────┬─────┘     └──────────────────┘
                      │
┌─────────┐     ┌─────┴─────┐     ┌──────────────────┐
│ Telegram │────▶│ SQLAlchemy│────▶│  SQLite DB       │
│ Bot      │     │  ORM      │     │  8 tables        │
└─────────┘     └───────────┘     └──────────────────┘
```

[▶ Full architecture →](docs/ARCHITECTURE.md)

---

## Tech Stack

| Component | Technology |
|-----------|------------|
| **Framework** | [FastAPI](https://fastapi.tiangolo.com/) — Python async web framework |
| **Database** | [SQLite](https://www.sqlite.org/) via [SQLAlchemy](https://www.sqlalchemy.org/) ORM |
| **Templates** | [Jinja2](https://jinja.palletsprojects.com/) with [Tailwind CSS](https://tailwindcss.com/) |
| **Icons** | [Lucide](https://lucide.dev/) — open-source icon library |
| **Bot** | [python-telegram-bot](https://python-telegram-bot.org/) v20.x |
| **HTTP** | [httpx](https://www.python-httpx.org/) — async HTTP client |
| **PDF** | [html2pdf.js](https://ekoopmans.github.io/html2pdf.js/) — receipt PDF download |
| **Deploy** | [Vercel](https://vercel.com/) — serverless functions |

---

## Environment Variables

| Variable | Required | Default | Description |
|----------|----------|---------|-------------|
| `TOKEN` | ✅ Yes | — | Telegram Bot API token from [@BotFather](https://t.me/botfather) |
| `BASE_URL` | ❌ No | `https://trusted.vercel.app` | Base URL for link generation |
| `ADMIN_CHAT_IDS` | ❌ No | `""` | Comma-separated Telegram chat IDs with admin bot access |
| `DB_PATH` | ❌ No | `/tmp/trusted.db` | SQLite database file path |

---

## Documentation

| Document | Description |
|----------|-------------|
| [📖 Getting Started](docs/GETTING_STARTED.md) | Setup, configuration, and deployment |
| [🏗️ Architecture](docs/ARCHITECTURE.md) | System architecture and component overview |
| [📡 API Reference](docs/API_REFERENCE.md) | Complete API routes documentation |
| [🗄️ Database Schema](docs/DATABASE.md) | All models, fields, and relationships |
| [🔐 Telebirr Verification](docs/TELEBIRR_VERIFICATION.md) | 4-layer receipt verification system |
| [🤖 Bot Commands](docs/BOT_COMMANDS.md) | Telegram bot commands reference |
| [👨‍💼 Admin Guide](docs/ADMIN_GUIDE.md) | Admin panel operations and workflows |
| [🔄 Workflows](docs/WORKFLOWS.md) | Deposit, withdrawal, and dispute flows |
| [🛡️ Security](docs/SECURITY.md) | Security features and recommendations |

---

## Verification Layers

The system verifies Telebirr receipts through **4 independent layers**:

```
Receipt Number
     │
     ▼
┌─────────────────────┐
│ Layer 1: Regex      │  53 patterns check HTML structure
│ Structure Check     │  (tags, classes, labels, links, QR)
└─────────┬───────────┘
          │
          ▼
┌─────────────────────┐
│ Layer 2: DOM        │  19-point fingerprint vs example.html
│ Fingerprint         │  (CSS, JS, attributes, counts, URLs)
└─────────┬───────────┘
          │
          ▼
┌─────────────────────┐
│ Layer 3: Field      │  Extract 15 fields (payer, amount, etc.)
│ Extraction          │  with numeric parsing
└─────────┬───────────┘
          │
          ▼
┌─────────────────────┐
│ Layer 4: Status     │  Verify transaction_status == "Completed"
│ Validation          │
└─────────┬───────────┘
          │
          ▼
    Pending Transaction → Admin Approval
```

The DOM fingerprint check is **100% sensitive** — every alteration to the receipt HTML structure is detected.

[▶ Full verification docs →](docs/TELEBIRR_VERIFICATION.md)

---

## Project Structure

```
trusted/
├── api/
│   ├── index.py              # FastAPI app, routes, middleware
│   ├── auth.py               # Authentication, sessions, wallet
│   ├── database.py           # SQLAlchemy engine & session factory
│   ├── models.py             # 8 database models
│   ├── telebirr.py           # Telebirr receipt verification
│   ├── structure.py          # DOM fingerprint verification
│   ├── logger.py             # Activity logging & snapshots
│   ├── features/
│   │   ├── __init__.py       # Bot update dispatcher
│   │   └── commands.py       # Bot command handlers
│   ├── templates/            # Jinja2 HTML templates (14 files)
│   └── static/               # CSS assets
├── docs/                     # Documentation (10 files)
├── requirements.txt          # Python dependencies
├── vercel.json               # Vercel deployment config
└── example.html              # Reference Telebirr receipt
```

---

## Deployment

### Deploy to Vercel in 3 Steps

```bash
# 1. Install Vercel CLI
npm i -g vercel

# 2. Deploy
vercel

# 3. Set webhook
curl -X POST "https://api.telegram.org/bot<TOKEN>/setWebhook?url=https://<YOUR_VERCEL_URL>/webhook"
```

[▶ Detailed deployment guide →](docs/GETTING_STARTED.md#deployment)

---

## Bot Commands

### User Commands

| Command | Description |
|---------|-------------|
| `/start` | Welcome message |
| `/help` | Show available commands |
| `/login` | Get web login link |
| `/link <email> <password>` | Link Telegram to your account |
| `/logoff` | Unlink Telegram |
| `/balance` | Check wallet balance |
| `/deposit <receipt_no>` | Submit a deposit |
| `/status [id]` | Check transaction status |

### Admin Commands

| Command | Description |
|---------|-------------|
| `/admin_pending` | Show pending queue counts |
| `/admin_approve <id>` | Approve a deposit |
| `/admin_reject <id> [reason]` | Reject a transaction |

[▶ Full bot docs →](docs/BOT_COMMANDS.md)

---

## License

This project is licensed under the MIT License.

---

<div align="center">
  <sub>Built with FastAPI, Tailwind CSS, and ❤️</sub>
  <br/>
  <sub>© 2026 Trusted Pay</sub>
</div>
