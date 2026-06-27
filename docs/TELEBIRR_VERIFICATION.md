# Telebirr Receipt Verification

## Overview

When a user submits a Telebirr receipt number, the system fetches the official receipt page from `https://transactioninfo.ethiotelecom.et/receipt/{receipt_no}` and runs it through four verification layers before accepting the deposit.

## Verification Layers

### Layer 1: Regex Structure Check

**File**: `api/telebirr.py` → `verify_structure()`

Checks for **53 critical regex patterns** in the HTML, covering:

| Category | Items Checked |
|----------|---------------|
| Document | `<!DOCTYPE html>`, `<html lang="en">` |
| Meta | charset, script/link tags |
| CSS Classes | `.receipttableTd`, `.buttonStyle`, etc. |
| Amharic Labels | የከፋይ ስም/Payer Name, የክፍያ ሁኔታ/transaction status, etc. |
| Company Info | "Ethio telecom Share Company", TIN, VAT, P.O.Box, Tel |
| Social Media | facebook.com/telebirr, twitter.com/telebirr, t.me/telebirr, email |
| QR Code | `data:image/png;base64,` |
| JavaScript | `html2pdf`, CSS selectors in inline styles |

Returns `(False, [missing_patterns])` if any pattern is absent.

### Layer 2: Structural Fingerprint Check

**File**: `api/structure.py` → `verify_telebirr_structure()`

A **19-point DOM fingerprint comparison** against the reference `example.html`. Only truly dynamic values (names, phones, amounts, dates, invoice numbers, QR base64 data) may differ.

| # | Check | What It Verifies |
|---|-------|------------------|
| 1 | DOCTYPE | `<!DOCTYPE html>` present |
| 2 | Static Text | Company name, TIN, VAT, address, phone (11 items) |
| 3 | Labels | All 16 Amharic/English bilingual labels |
| 4 | Links | Facebook, X.com, Telegram, email (4 items) |
| 5 | Instructions | QR scan text, Download PDF, html2pdf |
| 6 | Attributes | `lang="en"`, `charset=utf-8`, `id="button"` |
| 7 | JS Fragments | `html2pdf`, `document.getElementById`, `addEventListener`, `html2canvas`, `useCORS`, `referencenumber`, `paid_reference_number`, `telebirr_Send Money to Registered Customer` (10 items) |
| 8 | QR Presence | `data:image/png;base64,` in HTML |
| 9 | CSS Selectors | All selectors from `<style>` blocks match reference |
| 10 | CSS Properties | All property:value pairs match reference |
| 11 | Script Sources | CDN script URLs match |
| 12 | Link HREFs | External CSS links match |
| 13 | URLs | Social media URLs match |
| 14 | CSS Classes | All class attributes match reference |
| 15 | Element IDs | All `id` attributes match reference |
| 16 | Tag Counts | Exactly 5 `<script>`, 1 `<meta>`, 1 `<link>` |
| 17 | Total Tags | Opening tag count within 5% of reference |
| 18 | Image Sources | All non-QR image paths match |
| 19 | Inline Style | `border-collapse: collapse` present |

**Sensitivity**: All 18 alteration tests pass (100% detection rate).

### Layer 3: Field Extraction

**File**: `api/telebirr.py` → `extract_details()`

Parses **15 fields** from the receipt HTML:

| Field | Description | Type |
|-------|-------------|------|
| `payer_name` | Sender's full name | string |
| `payer_phone` | Sender's masked phone number | string |
| `receiver_name` | Receiver's full name | string |
| `receiver_phone` | Receiver's masked phone number | string |
| `invoice_no` | Transaction invoice number | string |
| `payment_date` | Date and time of payment | string |
| `settled_amount` | Transaction amount with currency | string |
| `service_fee` | Telebirr service fee | string |
| `service_fee_vat` | VAT on service fee | string |
| `total_paid` | Total amount paid | string |
| `transaction_status` | Status (must be "Completed") | string |
| `payment_mode` | Payment method | string |
| `payment_reason` | Purpose of payment | string |
| `payment_channel` | Transaction channel | string |
| `settled_amount_num` | Numeric settled amount | Decimal |
| `total_paid_num` | Numeric total paid | Decimal |
| `service_fee_num` | Numeric service fee | Decimal |

### Layer 4: Status Validation

**File**: `api/telebirr.py` → `verify_receipt()`

After extraction, checks that `transaction_status` is `"Completed"` (case-insensitive).

## Orchestration

```python
async def verify_receipt(receipt_number: str) -> dict:
    html = await fetch_receipt(receipt_number)
    # Layer 1
    struct_valid, missing = verify_structure(html)
    # Layer 2
    fingerprint_valid, errors = verify_telebirr_structure(html)
    # Layer 3
    details = extract_details(html)
    # Layer 4
    if details.get("transaction_status", "").lower() != "completed":
        return error("Transaction not completed")
    return {"valid": True, "details": details, "error": None}
```

## Reference File

`example.html` (in project root) is the ground-truth Telebirr receipt page. It is used as the structural fingerprint source and should be kept up-to-date with any changes to Telebirr's receipt page format.

**Security**: `example.html` is excluded from version control via `.gitignore` and should be treated as sensitive data.
