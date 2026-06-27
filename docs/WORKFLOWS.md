# Workflows

## Deposit Flow

```
┌─────────────────────────────────────────────────────────────────┐
│                            USER                                  │
│  1. Opens Telebirr app                                           │
│  2. Sends money to the base Telebirr account                     │
│  3. Copies the receipt number from the Telebirr confirmation     │
│  4. Opens Trusted → clicks "Deposit" → enters receipt number     │
└──────────────────────────┬──────────────────────────────────────┘
                           │
                           ▼
┌─────────────────────────────────────────────────────────────────┐
│                      VERIFICATION SYSTEM                         │
│  5. Fetches receipt HTML from Telebirr API                       │
│  6. verify_structure() — 52 regex checks                        │
│  7. verify_telebirr_structure() — 19-point DOM fingerprint      │
│  8. extract_details() — parses 15 fields                        │
│  9. Checks transaction_status == "Completed"                    │
│ 10. Creates Transaction(status="pending")                       │
└──────────────────────────┬──────────────────────────────────────┘
                           │
                           ▼
┌─────────────────────────────────────────────────────────────────┐
│                         ADMIN                                    │
│ 11. Sees new deposit in /admin/deposits queue                    │
│ 12. Verifies amount received in base Telebirr account            │
│ 13. Clicks "Approve"                                             │
│     → System deducts service fee (if configured)                 │
│     → Credits wallet with (amount - fee)                         │
│     → Status set to "approved"                                   │
│     — OR —                                                       │
│ 13. Clicks "Reject" with reason                                  │
│     → Status set to "rejected"                                   │
└──────────────────────────┬──────────────────────────────────────┘
                           │
                           ▼
┌─────────────────────────────────────────────────────────────────┐
│                         USER                                     │
│ 14. Sees updated status on dashboard / status page               │
│ 15. If rejected → can submit dispute                             │
└─────────────────────────────────────────────────────────────────┘
```

### Deposit Rules

| Condition | Behavior |
|-----------|----------|
| Receipt number invalid | Error: "Could not fetch receipt" |
| Structure verification fails | Error: "Receipt structure verification failed" |
| Fingerprint verification fails | Error: "Receipt structure verification failed (fingerprint)" |
| Status not "Completed" | Error with current status shown |
| Receipt valid | Transaction created (pending) |
| User frozen | Error: "Account is frozen" |
| Admin approves | Wallet credited, status = approved |
| Admin rejects | Status = rejected, reason stored |

## Withdrawal Flow

```
┌─────────────────────────────────────────────────────────────────┐
│                            USER                                  │
│  1. Opens dashboard → clicks "Withdraw"                          │
│  2. Modal opens → enters amount (required) + reason (optional)   │
│  3. Submits form                                                 │
└──────────────────────────┬──────────────────────────────────────┘
                           │
                           ▼
┌─────────────────────────────────────────────────────────────────┐
│                     SYSTEM CHECKS                                │
│  4. Validates amount > 0                                         │
│  5. Checks user is not frozen                                    │
│  6. Verifies wallet.balance >= amount                            │
│  7. Checks for existing pending withdrawals (double-shield)      │
│  8. Deducts amount from wallet immediately                       │
│  9. Creates Transaction(status="pending")                        │
└──────────────────────────┬──────────────────────────────────────┘
                           │
                           ▼
┌─────────────────────────────────────────────────────────────────┐
│                         ADMIN                                    │
│ 10. Sees new withdrawal in /admin/withdrawals queue              │
│ 11. Sends amount to user's Telebirr account                     │
│ 12. Enters Telebirr transaction number → clicks "Complete"       │
│     → Status set to "completed"                                  │
│     — OR —                                                       │
│ 12. Clicks "Reject" with reason                                  │
│     → Amount refunded to wallet                                  │
│     → Status set to "rejected"                                   │
└──────────────────────────┬──────────────────────────────────────┘
                           │
                           ▼
┌─────────────────────────────────────────────────────────────────┐
│                         USER                                     │
│ 13. Sees updated status on dashboard / status page               │
└─────────────────────────────────────────────────────────────────┘
```

### Withdrawal Rules

| Condition | Behavior |
|-----------|----------|
| Amount ≤ 0 | Redirect to dashboard (no error shown) |
| User frozen | Redirect to dashboard (no error shown) |
| Insufficient balance | Redirect to dashboard (no error shown) |
| Existing pending withdrawal | Balance deducted, but admin reviews |
| Admin completes | Status = completed, receipt_no saved |
| Admin rejects | Amount refunded, status = rejected |

## Dispute Flow

```
┌─────────────────────────────────────────────────────────────────┐
│                            USER                                  │
│  1. Views rejected transaction on /status/{id}                   │
│  2. Sees dispute form:                                            │
│     - Telebirr transaction number (optional)                     │
│     - Explanation (required)                                     │
│     - File attachment (optional, <5MB)                           │
│  3. Submits dispute                                              │
└──────────────────────────┬──────────────────────────────────────┘
                           │
                           ▼
┌─────────────────────────────────────────────────────────────────┐
│                      SYSTEM                                      │
│  4. Sets status = "disputed"                                     │
│  5. Saves dispute_reason and optional attachment                 │
└──────────────────────────┬──────────────────────────────────────┘
                           │
                           ▼
┌─────────────────────────────────────────────────────────────────┐
│                         ADMIN                                    │
│  6. Sees dispute in /admin/deposits (Disputed section)           │
│  7. Reviews transaction + user's explanation                     │
│  8. Clicks "Close Dispute"                                       │
│     → Status = "closed"                                          │
│     → Card hidden from user's default list                       │
│     — OR —                                                       │
│  8. Clicks "Reject Again"                                        │
│     → Status = "rejected"                                        │
│     → User can dispute again if needed                           │
└─────────────────────────────────────────────────────────────────┘
```

### Dispute Rules

| Condition | Behavior |
|-----------|----------|
| Transaction status is not "rejected" | Redirect (cannot dispute) |
| Dispute submitted | Status changes to "disputed" |
| Admin closes dispute | Status changes to "closed" (resolved) |
| Admin rejects again | Status changes to "rejected" (user can retry) |
| Closed transactions | Filtered from user's default status list |
| File attachment | Saved to `/tmp/disputes/`, max 5MB |

## Admin Quick Scan Flow

```
┌─────────────────────────────────────────────────────────────────┐
│                         ADMIN                                    │
│  1. Opens /admin/users → clicks "Manage" on a user              │
│  2. Clicks "Quick Scan"                                         │
└──────────────────────────┬──────────────────────────────────────┘
                           │
                           ▼
┌─────────────────────────────────────────────────────────────────┐
│                      SYSTEM                                      │
│  3. Finds all user's pending and disputed transactions           │
│  4. For each with a receipt_no:                                  │
│     - Fetches receipt from Telebirr API                         │
│     - Runs verify_receipt()                                      │
│     - Records valid/invalid status                               │
│  5. Logs all scan results to ActivityLog                         │
└──────────────────────────┬──────────────────────────────────────┘
                           │
                           ▼
┌─────────────────────────────────────────────────────────────────┐
│                         ADMIN                                    │
│  6. Reviews scan results (logged, not displayed on UI)           │
│  7. Takes appropriate action (approve/reject based on scan)      │
└─────────────────────────────────────────────────────────────────┘
```

## User Restriction Flow

```
┌─────────────────────────────────────────────────────────────────┐
│                         ADMIN                                    │
│  1. Opens /admin/users → clicks "Manage"                        │
│  2. Selects action:                                             │
│                                                                  │
│  ┌─────── BAN ───────────────────────────────────────────────┐  │
│  │  Effect: User cannot log in (is_active = False)           │  │
│  │  Reversal: Admin clicks "Unban"                           │  │
│  └───────────────────────────────────────────────────────────┘  │
│                                                                  │
│  ┌─────── FREEZE ────────────────────────────────────────────┐  │
│  │  Effect: User cannot deposit or withdraw (is_frozen)      │  │
│  │  Can still log in and view status                         │  │
│  │  Optional: Set expiry datetime for auto-unfreeze          │  │
│  │  Record stored in UserRestriction table                   │  │
│  └───────────────────────────────────────────────────────────┘  │
│                                                                  │
│  ┌─────── RESTRICT ──────────────────────────────────────────┐  │
│  │  Effect: Selectively block permissions:                   │  │
│  │  - can_deposit                                            │  │
│  │  - can_withdraw                                           │  │
│  │  - can_view_status                                        │  │
│  │  Record stored in UserRestriction table                   │  │
│  └───────────────────────────────────────────────────────────┘  │
│                                                                  │
│  3. Submits form → action logged                                │
└─────────────────────────────────────────────────────────────────┘
```
