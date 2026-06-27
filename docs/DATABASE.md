# Database Schema

## Entity-Relationship Diagram

```
users (1) ────── (0..*) sessions
users (1) ────── (0..1) wallets
users (1) ────── (0..*) transactions (as user)
users (1) ────── (0..*) transactions (as admin)
users (1) ────── (0..*) user_restrictions (as subject)
users (1) ────── (0..*) user_restrictions (as creator)
users (1) ────── (0..*) activity_logs
admin_settings (1) — singleton table
snapshots — standalone table
```

## Models

### User (`users`)

| Column | Type | Constraints | Description |
|--------|------|-------------|-------------|
| `id` | Integer | PK, indexed | Auto-increment |
| `full_name` | String(100) | NOT NULL | Display name |
| `email` | String(100) | UNIQUE, NOT NULL, indexed | Login identifier |
| `phone` | String(20) | NOT NULL | Contact phone |
| `password_hash` | String(200) | NOT NULL | `salt:sha256_hex` format |
| `telegram_chat_id` | String(50) | NULLABLE, UNIQUE | Linked Telegram chat |
| `role` | String(20) | NOT NULL, default `"user"` | `"user"` or `"admin"` |
| `is_active` | Boolean | NOT NULL, default `True` | Account active |
| `is_frozen` | Boolean | NOT NULL, default `False` | Account frozen |
| `created_at` | DateTime | default `utcnow` | Registration timestamp |

**Relationships**:
- `sessions`: One-to-many with `Session` (cascade delete)
- `wallet`: One-to-one with `Wallet` (cascade delete)
- `transactions`: One-to-many with `Transaction` (via `user_id`)

### Session (`sessions`)

| Column | Type | Constraints | Description |
|--------|------|-------------|-------------|
| `id` | Integer | PK, indexed | Auto-increment |
| `user_id` | Integer | FK → `users.id`, NOT NULL | Owner |
| `token` | String(100) | UNIQUE, NOT NULL, indexed | Session token (64 hex chars) |
| `created_at` | DateTime | default `utcnow` | Creation time |

### Wallet (`wallets`)

| Column | Type | Constraints | Description |
|--------|------|-------------|-------------|
| `id` | Integer | PK, indexed | Auto-increment |
| `user_id` | Integer | FK → `users.id`, UNIQUE, NOT NULL | Wallet owner |
| `balance` | Numeric(12,2) | NOT NULL, default 0.00 | Current balance |
| `created_at` | DateTime | default `utcnow` | Creation time |
| `updated_at` | DateTime | default `utcnow`, onupdate | Last update |

### Transaction (`transactions`)

| Column | Type | Constraints | Description |
|--------|------|-------------|-------------|
| `id` | Integer | PK, indexed | Auto-increment |
| `user_id` | Integer | FK → `users.id`, NOT NULL, indexed | Transaction owner |
| `type` | String(20) | NOT NULL | `"deposit"` or `"withdrawal"` |
| `receipt_no` | String(50) | NULLABLE, indexed | Telebirr receipt/transaction number |
| `amount` | Numeric(12,2) | NOT NULL | Transaction amount |
| `service_fee` | Numeric(12,2) | NULLABLE, default 0.00 | Admin service fee |
| `total_paid` | Numeric(12,2) | NULLABLE | Total from Telebirr receipt |
| `payer_name` | String(100) | NULLABLE | From Telebirr receipt |
| `payer_phone` | String(20) | NULLABLE | From Telebirr receipt |
| `receiver_name` | String(100) | NULLABLE | From Telebirr receipt |
| `receiver_phone` | String(20) | NULLABLE | From Telebirr receipt |
| `status` | String(20) | NOT NULL, default `"pending"`, indexed | Current status |
| `admin_id` | Integer | FK → `users.id`, NULLABLE | Admin who processed |
| `admin_note` | Text | NULLABLE | Admin notes |
| `reason` | Text | NULLABLE | Withdrawal reason |
| `attachment_path` | String(255) | NULLABLE | Dispute attachment path |
| `dispute_reason` | Text | NULLABLE | User's dispute explanation |
| `resolved_at` | DateTime | NULLABLE | When dispute was resolved |
| `created_at` | DateTime | default `utcnow` | Creation time |
| `updated_at` | DateTime | default `utcnow`, onupdate | Last update |

**Status Lifecycle**:

```
deposit:  pending → approved
                   → rejected → disputed → closed
                                      → rejected (again)

withdrawal: pending → completed
                    → rejected (refund)
```

### AdminSettings (`admin_settings`)

Singleton table storing global platform settings.

| Column | Type | Constraints | Description |
|--------|------|-------------|-------------|
| `id` | Integer | PK, indexed | Always 1 (singleton) |
| `service_fee_percent` | Numeric(5,2) | NOT NULL, default 0.00 | Fee percentage |
| `base_phone_number` | String(20) | NULLABLE | Telebirr base account |
| `updated_at` | DateTime | default `utcnow`, onupdate | Last update |

### UserRestriction (`user_restrictions`)

| Column | Type | Constraints | Description |
|--------|------|-------------|-------------|
| `id` | Integer | PK, indexed | Auto-increment |
| `user_id` | Integer | FK → `users.id`, NOT NULL, indexed | Restricted user |
| `restriction_type` | String(20) | NOT NULL | `"freeze"`, `"restrict"`, `"ban"` |
| `permissions_json` | Text | NULLABLE | JSON permission list |
| `reason` | Text | NULLABLE | Admin's reason |
| `expires_at` | DateTime | NULLABLE | Auto-expiry |
| `created_by` | Integer | FK → `users.id`, NOT NULL | Admin who applied |
| `created_at` | DateTime | default `utcnow` | Creation time |

### ActivityLog (`activity_logs`)

| Column | Type | Constraints | Description |
|--------|------|-------------|-------------|
| `id` | Integer | PK, indexed | Auto-increment |
| `user_id` | Integer | FK → `users.id`, NULLABLE, indexed | Actor |
| `action` | String(100) | NOT NULL | Action identifier |
| `details_json` | Text | NULLABLE | JSON details payload |
| `ip_address` | String(45) | NULLABLE | Client IP |
| `created_at` | DateTime | default `utcnow` | Timestamp |

### Snapshot (`snapshots`)

| Column | Type | Constraints | Description |
|--------|------|-------------|-------------|
| `id` | Integer | PK, indexed | Auto-increment |
| `snapshot_type` | String(20) | NOT NULL | `"auto_2h"` or `"daily"` |
| `data_json` | Text | NOT NULL | Snapshot data payload |
| `created_at` | DateTime | default `utcnow` | Timestamp |
