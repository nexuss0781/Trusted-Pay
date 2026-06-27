# API Reference

## Public Routes

### `GET /`
Landing page with hero section and feature cards.

### `GET /signup`
Registration form page.

### `POST /signup`
Create a new user account.

| Field | Type | Required |
|-------|------|----------|
| `full_name` | string | Yes |
| `email` | string | Yes |
| `phone` | string | Yes |
| `password` | string | Yes (min 6 chars) |

**Response**: Redirect to `/dashboard` with session cookie, or re-render signup with error.

### `GET /login`
Login form page.

### `POST /login`
Authenticate user and create session.

| Field | Type | Required |
|-------|------|----------|
| `email` | string | Yes |
| `password` | string | Yes |

**Response**: Redirect to `/dashboard` with session cookie, or re-render login with error.

---

## User Routes (Session Required)

### `GET /dashboard`
User dashboard with wallet balance, latest 5 transactions, Telegram connection status.

**Query Parameters**: None

**Cookies**: `session` (required)

### `GET /logout`
Clear session and redirect to `/`.

### `GET /deposit`
Deposit form with instructions.

### `POST /deposit`
Submit a deposit request.

| Field | Type | Required |
|-------|------|----------|
| `receipt_number` | string | Yes (alphanumeric) |

**Process**:
1. Fetches receipt HTML from Telebirr API
2. Verifies structure (regex + fingerprint)
3. Extracts details (payer, amount, etc.)
4. Checks transaction status is "Completed"
5. Creates pending Transaction record

**Response**: Re-renders deposit page with success/error message.

### `POST /withdraw`
Submit a withdrawal request.

| Field | Type | Required |
|-------|------|----------|
| `amount` | string (decimal) | Yes |
| `reason` | string | No |

**Process**:
1. Validates amount > 0
2. Checks user is not frozen
3. Verifies sufficient balance
4. Checks for existing pending withdrawals (double-shield)
5. Deducts balance immediately
6. Creates pending Transaction

**Response**: Redirect to `/status/{txn_id}`.

### `GET /status`
Paginated transaction history.

| Query Param | Type | Default | Description |
|-------------|------|---------|-------------|
| `page` | int | 1 | Page number (10 per page) |

### `GET /status/{txn_id}`
Single transaction detail view.

### `POST /status/{txn_id}/dispute`
Submit a dispute for a rejected transaction.

| Field | Type | Required |
|-------|------|----------|
| `description` | string | Yes |
| `dispute_txn_number` | string | No |
| `attachment` | file | No (max 5MB) |

**Process**:
1. Validates transaction exists and status is "rejected"
2. Sets status to "disputed"
3. Saves dispute reason and optional attachment

---

## Admin Routes (Admin Role Required)

### `GET /admin`
Admin dashboard with aggregate statistics and recent disputes.

### `GET /admin/deposits`
Deposit queue showing pending and disputed deposits.

### `POST /admin/deposits/{txn_id}/approve`
Approve a pending deposit.

**Process**:
1. Calculates service fee (amount × fee_percent / 100)
2. Credits wallet with (amount - fee)
3. Sets status to "approved"

### `POST /admin/deposits/{txn_id}/reject`
Reject a pending deposit.

| Field | Type | Required |
|-------|------|----------|
| `reason` | string | No |

### `GET /admin/withdrawals`
Pending withdrawal queue.

### `POST /admin/withdrawals/{txn_id}/complete`
Complete a withdrawal.

| Field | Type | Required |
|-------|------|----------|
| `transaction_number` | string | Yes |

### `POST /admin/withdrawals/{txn_id}/reject`
Reject a withdrawal and refund.

| Field | Type | Required |
|-------|------|----------|
| `reason` | string | No |

### `GET /admin/users`
User management page with searchable table.

### `POST /admin/users/{user_id}/restrict`
Apply restriction to a user.

| Field | Type | Description |
|-------|------|-------------|
| `action` | string | `ban`, `freeze`, `restrict`, or `unban` |
| `reason` | string | Reason for restriction |
| `expires_at` | string | ISO datetime for timed restrictions |
| `permissions` | list | Permission checkboxes for restrict action |

### `POST /admin/users/{user_id}/scan`
Live scan of user's pending deposits against Telebirr API.

### `GET /admin/settings`
Settings page with activity log viewer.

### `POST /admin/settings`
Update system settings.

| Field | Type | Description |
|-------|------|-------------|
| `service_fee_percent` | string (decimal) | Fee percentage (0-100) |
| `base_phone_number` | string | Telebirr base account number |

### `POST /admin/disputes/{txn_id}/close`
Close a disputed transaction (resolve in user's favor).

| Field | Type | Required |
|-------|------|----------|
| `note` | string | No |

### `POST /admin/disputes/{txn_id}/reject-again`
Reject a dispute (uphold original rejection).

| Field | Type | Required |
|-------|------|----------|
| `reason` | string | No |

---

## Diagnostic Routes

### `POST /api/test-webhook`
Test Telegram bot connectivity.

**Response**:
```json
{
  "status": "ok",
  "bot": "MyBot",
  "webhook": "https://example.com/webhook",
  "pending": 0
}
```

### `GET /api/trace`
Debug endpoint to check deployed code version.

### `POST /webhook`
Telegram bot webhook receiver. Accepts Telegram Update JSON.
