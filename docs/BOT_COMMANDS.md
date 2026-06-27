# Telegram Bot Commands

## Setup

1. Create a bot via [@BotFather](https://t.me/BotFather)
2. Set webhook to `https://your-domain.com/webhook`
3. Set `TOKEN` and `ADMIN_CHAT_IDS` environment variables

## User Commands

Available to all users with a linked Telegram account.

### `/start`
Welcome message listing all available commands.

### `/help`
Display help information with all commands.

### `/login`
Get the web application login URL.

### `/link <email> <password>`
Link your Telegram account to your Trusted account.

**Usage**: `/link user@example.com mypassword`

Authenticates via email/password and stores the chat ID for future commands.

### `/logoff`
Unlink your Telegram account from Trusted.

### `/balance`
Check your wallet balance.

**Response**:
```
💰 Your Wallet Balance
━━━━━━━━━━━━━━━━━━━
Balance: 1,250.00 ETB
━━━━━━━━━━━━━━━━━━━
```

### `/deposit <receipt_number>`
Submit a deposit using a Telebirr receipt number.

**Usage**: `/deposit ABC123XYZ`

**Process**:
1. Verifies receipt against Telebirr API
2. Creates pending transaction
3. Notifies admin for approval

**Response** (success):
```
✅ Deposit Submitted
━━━━━━━━━━━━━━━━━━━
Transaction ID: 42
Amount: 1,000.00 Birr
Status: Pending
━━━━━━━━━━━━━━━━━━━
```

**Response** (error):
```
❌ Verification Failed
━━━━━━━━━━━━━━━━━━━
Receipt structure verification failed.
━━━━━━━━━━━━━━━━━━━
```

### `/status [transaction_id]`
Check transaction status.

**Without ID**: Shows last 5 transactions.

**With ID**: Shows detailed transaction information.

**Response** (with ID):
```
📋 Transaction #42
━━━━━━━━━━━━━━━━━━━
Type: Deposit
Amount: 1,000.00 Birr
Status: ✅ Approved
Receipt: ABC123XYZ
Payer: John Doe
Date: 27-06-2026 15:02:32
━━━━━━━━━━━━━━━━━━━
```

## Admin Bot Commands

Require the sender's chat ID to be in the `ADMIN_CHAT_IDS` environment variable (comma-separated list).

### `/admin_pending`
Show count of pending deposits and withdrawals.

**Response**:
```
📊 Pending Queue
━━━━━━━━━━━━━━━━━━━
Deposits: 3 pending
Withdrawals: 1 pending
━━━━━━━━━━━━━━━━━━━
```

### `/admin_approve <transaction_id>`
Approve a pending deposit transaction.

**Usage**: `/admin_approve 42`

**Process**:
1. Calculates service fee (if configured)
2. Credits user's wallet
3. Logs the action

**Response**:
```
✅ Deposit #42 Approved
━━━━━━━━━━━━━━━━━━━
User: John Doe
Amount: 1,000.00 Birr
Fee: 0.00 Birr
Credited: 1,000.00 Birr
━━━━━━━━━━━━━━━━━━━
```

### `/admin_reject <transaction_id> [reason]`
Reject a pending deposit or withdrawal.

**Usage**: `/admin_reject 42 Suspicious activity`

For withdrawal rejections, the amount is automatically refunded to the user's wallet.

## Implementation Details

**File**: `api/features/commands.py`

The command handler uses an `if/elif` chain on `update.message.text`:

```python
text = update.message.text.strip()
if text.startswith("/start") or text.startswith("/help"):
    # show welcome/help
elif text.startswith("/link"):
    # parse email and password, link account
elif text.startswith("/admin_"):
    # check admin chat ID, execute admin command
# ...
```

**File**: `api/features/__init__.py`

The `handle_update()` function dispatches incoming updates:

```python
async def handle_update(update: Update, bot: Bot):
    if update.message and update.message.text:
        await handle_command(update, bot)
```

**Error Handling**: All commands are wrapped in try/except blocks. Errors are returned as user-friendly messages with Markdown formatting.
