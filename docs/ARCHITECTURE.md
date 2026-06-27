# System Architecture

## Overview

Trusted is a FastAPI-based web application with Telegram bot integration, SQLite database, and a multi-layer Telebirr receipt verification system.

```
┌─────────────────────────────────────────────────────────┐
│                     Users (Web Browser)                  │
├─────────────────────────────────────────────────────────┤
│                        FastAPI                           │
│  ┌──────────┐ ┌──────────┐ ┌──────────┐ ┌───────────┐  │
│  │ Auth     │ │ Deposit  │ │ Withdraw │ │ Admin     │  │
│  │ Routes   │ │ Routes   │ │ Routes   │ │ Routes    │  │
│  └────┬─────┘ └────┬─────┘ └────┬─────┘ └─────┬─────┘  │
│       │            │            │              │        │
│  ┌────┴────────────┴────────────┴──────────────┴────┐   │
│  │              SQLAlchemy ORM                       │   │
│  │  ┌──────┐ ┌──────────┐ ┌──────┐ ┌────────────┐  │   │
│  │  │Users │ │Wallets   │ │Trans │ │ActivityLog │  │   │
│  │  └──────┘ └──────────┘ └──────┘ └────────────┘  │   │
│  └─────────────────────┬────────────────────────────┘   │
│                        │                                │
│              ┌─────────┴─────────┐                      │
│              │    SQLite DB      │                      │
│              └───────────────────┘                      │
├─────────────────────────────────────────────────────────┤
│                    Telegram Bot                          │
│  ┌────────────┐ ┌──────────┐ ┌───────────────────┐     │
│  │ User Cmds  │ │Admin Cmds│ │ Webhook Handler   │     │
│  └────────────┘ └──────────┘ └───────────────────┘     │
├─────────────────────────────────────────────────────────┤
│              Telebirr Receipt Verification               │
│  ┌──────────┐ ┌──────────────┐ ┌────────────────┐      │
│  │Regex     │ │Fingerprint   │ │Field Extraction│      │
│  │Verify    │ │Verify        │ │                │      │
│  └──────────┘ └──────────────┘ └────────────────┘      │
└─────────────────────────────────────────────────────────┘
```

## Components

### 1. FastAPI Application (`api/index.py`)

The main web server handling all HTTP routes. Includes:
- Session-based authentication (cookie-based)
- Security headers middleware (CSP, X-Frame-Options, etc.)
- Jinja2 template rendering
- Static file serving

### 2. Authentication System (`api/auth.py`)

- Password hashing with SHA-256 + 16-byte random salt
- Session tokens via `secrets.token_hex(32)`
- Role-based access control (`user` / `admin` roles)
- Telegram chat ID linking

### 3. Database Layer

- **Engine**: SQLite via SQLAlchemy
- **Tables**: `users`, `sessions`, `wallets`, `transactions`, `admin_settings`, `user_restrictions`, `activity_logs`, `snapshots`
- **Session Management**: `SessionLocal` factory with manual open/close

### 4. Telebirr Verification (`api/telebirr.py` + `api/structure.py`)

Four verification layers:

| Layer | File | Function | Description |
|-------|------|----------|-------------|
| 1 | `telebirr.py` | `verify_structure()` | Checks 52 regex patterns for structural elements |
| 2 | `structure.py` | `verify_telebirr_structure()` | 19-point DOM fingerprint against `example.html` |
| 3 | `telebirr.py` | `extract_details()` | Parses 15 fields from the receipt HTML |
| 4 | `telebirr.py` | `verify_receipt()` | Checks `transaction_status == "Completed"` |

### 5. Telegram Bot (`api/features/`)

- `__init__.py`: Dispatches incoming webhook updates to command handlers
- `commands.py`: All bot command implementations
- Admin commands gated by `ADMIN_CHAT_IDS` whitelist

### 6. Logging System (`api/logger.py`)

- `log_action()`: Records every significant action to `ActivityLog` table
- `create_snapshot()`: Captures platform-wide metrics for reporting
- `create_daily_aggregation()`: Daily financial aggregation

## Route Categories

| Category | Prefix | Auth | Description |
|----------|--------|------|-------------|
| Public | `/`, `/signup`, `/login` | None | Landing, registration, login |
| User | `/dashboard`, `/deposit`, `/withdraw`, `/status` | Session | User operations |
| Admin | `/admin/*` | Admin role | Admin panel |
| API | `/api/*`, `/webhook` | None/Token | Webhook, diagnostics |
| Bot | `/webhook` | None | Telegram bot updates |

## Data Flow: Deposit

```
User → submits receipt_no → verify_receipt()
  → fetch_receipt() (HTTP GET to Telebirr API)
  → verify_structure() (52 regex patterns)
  → verify_telebirr_structure() (19-point DOM fingerprint)
  → extract_details() (15 fields parsed)
  → status check (must be "Completed")
  → Transaction created (status: pending)
  → Admin approves → wallet credited
  → User sees updated status
```

## Data Flow: Withdrawal

```
User → submits amount + reason → balance deducted immediately
  → double-shield check (existing pending withdrawals)
  → Transaction created (status: pending, amount deducted)
  → Admin completes (with transaction number)
    OR Admin rejects (amount refunded)
```
