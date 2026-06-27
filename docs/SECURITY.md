# Security

## Implemented Features

### Authentication & Session Management

- **Password Hashing**: SHA-256 with 16-byte random salt, stored as `salt:hash`
- **HTTP-Only Cookies**: Session cookie set with `httponly=True`, `samesite="lax"`, 7-day expiry
- **Session Tokens**: Generated via `secrets.token_hex(32)` (64 hex characters)
- **Role-Based Access**: Admin routes gated by `user.role == "admin"` check

### HTTP Security Headers

Applied via `SecurityHeadersMiddleware` to all responses:

| Header | Value |
|--------|-------|
| `X-Content-Type-Options` | `nosniff` |
| `X-Frame-Options` | `DENY` |
| `X-XSS-Protection` | `1; mode=block` |
| `Referrer-Policy` | `strict-origin-when-cross-origin` |
| `Content-Security-Policy` | Tightly scoped (scripts: self + CDNs, styles: self + fonts, images: self + data:, frame-ancestors: none) |

### Telebirr Receipt Verification (4 Layers)

1. **Regex Structure Check** — 53 patterns verify HTML structure
2. **DOM Fingerprint** — 19-point comparison against reference `example.html`
3. **Field Extraction** — Parses 15 fields with regex validation
4. **Status Validation** — Ensures transaction status is "Completed"

Structural fingerprint is **sensitive to any alteration** (100% test pass rate).

### Input Validation

- Receipt numbers: alphanumeric only (`^[A-Za-z0-9]+$`)
- Amounts: parsed as `Decimal`, validated > 0
- Session tokens: validated against database
- File uploads: max 5MB, safe filename generation with timestamp prefix

### Database Security

- SQLAlchemy ORM throughout (no raw SQL queries)
- Foreign key constraints enforce referential integrity
- Cascading deletes for user-related records

### Anti-Fraud

| Protection | Mechanism |
|------------|-----------|
| **Double-Shield Withdrawal** | Checks for existing pending withdrawals before allowing new ones |
| **Frozen Account Block** | Frozen users blocked from deposit and withdrawal |
| **Real-Time Admin Scan** | Admin can re-verify any user's pending deposits against live Telebirr API |
| **Activity Logging** | All significant actions recorded with timestamps and details |
| **Dispute System** | Users can escalate rejected transactions with evidence |
| **Admin Bot Gate** | Admin Telegram commands restricted to whitelisted chat IDs |

## Recommended Additions

The following security improvements are NOT yet implemented and are recommended for production deployment:

| Priority | Feature | Description |
|----------|---------|-------------|
| **High** | **CSRF Protection** | Add CSRF tokens to all POST forms to prevent cross-site request forgery |
| **High** | **Rate Limiting** | Limit login attempts, deposit submissions, and withdrawal requests per IP/user |
| **Medium** | **Duplicate Receipt Prevention** | Check if a receipt number has already been used before accepting a deposit |
| **Medium** | **Session Rotation** | Rotate session tokens on role elevation (e.g., when user becomes admin) |
| **Low** | **Permission Enforcement** | Implement the `UserRestriction.permissions_json` checks in route handlers |
| **Low** | **2FA** | Add two-factor authentication for admin accounts |
| **Low** | **IP Logging** | Capture and store IP addresses with activity logs (schema supports it) |

## Environment Variable Security

- `TOKEN` (Telegram Bot API token) — must be kept secret
- `ADMIN_CHAT_IDS` — controls admin bot access
- `DB_PATH` — file path for SQLite database

## Example HTML Security

`example.html` contains a real Telebirr receipt with identifiable information. It is excluded from version control via `.gitignore` and should be:
- Stored securely
- Kept up-to-date with Telebirr's receipt page format
- Never shared publicly
