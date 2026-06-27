# Admin Guide

## Access

Navigate to `/admin` and log in with an admin account. Admin accounts have `role="admin"` in the database.

### Creating an Admin

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

## Admin Panel Sections

### Dashboard (`/admin`)

Overview page showing:
- **Pending Deposits** — Count of deposits awaiting approval
- **Pending Withdrawals** — Count of withdrawals awaiting processing
- **Total Users / Wallets** — Platform user metrics
- **Total Deposits / Withdrawals** — Lifetime transaction counts
- **Recent Disputes** — List of disputed transactions with dispute reasons

### Deposits (`/admin/deposits`)

Two sections:

**Pending Approvals**: Each card shows:
- User info (ID, name)
- Amount, service fee calculation
- Receipt number
- Payer name and phone (from Telebirr)
- Total paid amount
- **Approve** button — credits wallet after fee deduction
- **Reject** button — requires optional reason

**Disputed Transactions**: Each card shows:
- Original transaction details
- User's dispute reason
- **Close Dispute** button — resolves in user's favor, card hidden from user
- **Reject Again** button — upholds rejection with optional reason

### Withdrawals (`/admin/withdrawals`)

Each pending withdrawal shows:
- User info and amount
- Phone number
- Withdrawal reason (if provided)
- **Mark Completed** — requires entering the real Telebirr transaction number
- **Reject** — refunds amount to user's wallet with optional reason

### Users (`/admin/users`)

Searchable table of all users. Click "Manage" to open the user detail modal:

**User Info**: Email, Phone, Role, Telegram status, Wallet balance, Member since

**Actions**:

| Action | Effect |
|--------|--------|
| **Restrict** | Blocks specific permissions (can_deposit, can_withdraw, can_view_status) |
| **Freeze** | Temporarily halts all account activity (with optional expiry datetime) |
| **Ban** | Immediately deactivates account, prevents login |
| **Unban** | Removes all restrictions and reactivates |

**Quick Scan**: Re-verifies the user's pending deposits against the live Telebirr API. Useful for auditing before releasing funds.

### Settings (`/admin/settings`)

**General Settings**:

| Setting | Description |
|---------|-------------|
| Service Fee % | Percentage deducted from deposit amounts before wallet credit (0-100) |
| Base Phone Number | The Telebirr account number displayed to users for deposits |

**Activity Log**: Displays the last 50 logged actions with timestamp, action name, and JSON details.

## Workflows

### Approving a Deposit

1. Go to `/admin/deposits`
2. Review the receipt details (payer name, amount, etc.)
3. Verify the amount was actually received in the base Telebirr account
4. Click **Approve**
5. System deducts service fee (if configured) and credits the user's wallet

### Processing a Withdrawal

1. Go to `/admin/withdrawals`
2. Review the user's request and available balance
3. Send the amount to the user's Telebirr account
4. Enter the Telebirr transaction number and click **Mark Completed**
5. System logs the completion

### Handling a Dispute

1. Go to `/admin/deposits` (Disputed section)
2. Review the transaction and the user's dispute explanation
3. **Close** if the dispute is valid (resolves in user's favor, hides the card)
4. **Reject Again** if the original rejection was correct

### Banning/Freezing a User

1. Go to `/admin/users`
2. Find the user and click **Manage**
3. Select the action:
   - **Ban**: Immediate deactivation
   - **Freeze**: Temporary hold (set optional expiry)
   - **Restrict**: Permission-specific limitations
4. Add a reason (logged for audit trail)
5. Submit

## Telegram Bot Admin

Admin bot commands work via Telegram when the admin's chat ID is in `ADMIN_CHAT_IDS`:

| Command | Description |
|---------|-------------|
| `/admin_pending` | Check pending queue counts |
| `/admin_approve <id>` | Approve a deposit |
| `/admin_reject <id> [reason]` | Reject a transaction |
