# Getting Started

## Prerequisites

- Python 3.10+
- Telegram Bot Token (from [@BotFather](https://t.me/BotFather))
- A Telebirr account for testing

## Local Development

### 1. Clone and Install

```bash
git clone <repo-url> trusted
cd trusted
pip install -r requirements.txt
```

### 2. Set Environment Variables

```bash
export TOKEN="your_telegram_bot_token"
export BASE_URL="http://localhost:8000"
export ADMIN_CHAT_IDS="your_telegram_chat_id"
```

### 3. Initialize the Database

The database is created automatically on first run. By default it uses `/tmp/trusted.db`. Override with:

```bash
export DB_PATH="./trusted.db"
```

### 4. Start the Server

```bash
uvicorn api.index:app --reload --port 8000
```

### 5. Set Telegram Webhook

```bash
curl -F "url=https://your-domain.com/webhook" \
     https://api.telegram.org/bot<YOUR_TOKEN>/setWebhook
```

For local testing, use a tunneling service like ngrok:

```bash
ngrok http 8000
# Then set webhook to https://<ngrok-id>.ngrok.io/webhook
```

### 6. Create an Admin Account

```bash
python3 -c "
import sys, os
sys.path.insert(0, 'api')
from database import init_db, SessionLocal
from auth import hash_password
from models import User, Wallet

init_db()
db = SessionLocal()
email = 'admin@example.com'
user = User(
    full_name='Admin',
    email=email,
    phone='',
    password_hash=hash_password('your_password'),
    role='admin',
)
db.add(user)
db.flush()
db.add(Wallet(user_id=user.id, balance=0.00))
db.commit()
db.close()
print(f'Admin created: {email}')
"
```

## Deployment

### Vercel

The project includes a `vercel.json` configured for Vercel serverless deployment:

```json
{
  "rewrites": [{ "source": "/(.*)", "destination": "/api/index" }]
}
```

1. Install Vercel CLI: `npm i -g vercel`
2. Deploy: `vercel`
3. Add environment variables in Vercel dashboard

### Environment Variables on Vercel

| Variable | Value |
|----------|-------|
| `TOKEN` | Your Telegram bot token |
| `BASE_URL` | `https://your-app.vercel.app` |
| `ADMIN_CHAT_IDS` | Comma-separated admin chat IDs |
| `DB_PATH` | `/tmp/trusted.db` |

## Configuration

### Admin Settings (via Web UI)

Navigate to `/admin/settings` to configure:

- **Service Fee %** — Percentage deducted from deposits before wallet credit (default: 0%)
- **Base Phone Number** — The Telebirr account number displayed to users for deposits

## Telegram Bot Setup

1. Create a bot via [@BotFather](https://t.me/BotFather)
2. Set the bot token as `TOKEN` environment variable
3. Set the webhook URL to `https://your-domain.com/webhook`
4. Users link their Telegram via `/link` command in the bot
5. Add admin chat IDs to `ADMIN_CHAT_IDS` for admin bot commands

### Bot Commands (set via BotFather)

```
start - Welcome message
help - Show help
login - Get web login link
link <email> <password> - Link Telegram to your account
logoff - Unlink Telegram
balance - Check wallet balance
deposit <receipt_number> - Submit a deposit
status [id] - Check transaction status
```
