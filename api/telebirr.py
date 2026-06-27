import re
import httpx
from decimal import Decimal, InvalidOperation

from structure import verify_telebirr_structure

TELEBIRR_RECEIPT_URL = "https://transactioninfo.ethiotelecom.et/receipt/{receipt_no}"

REQUIRED_STRUCTURES = [
    r'<!DOCTYPE html>',
    r'<html lang="en">',
    r'<meta http-equiv="Content-Type" content="text/html; charset=utf-8">',
    r'src="https://cdnjs.cloudflare.com/ajax/libs/html2pdf.js/0\.10\.1/html2pdf\.bundle\.min\.js"',
    r'<title>telebirr receipt </title>',
    r'\.receipttableTd\s*\{',
    r'\.buttonStyle\s*\{',
    r'telebirr Transaction information',
    r'የከፋይ ስም/Payer Name',
    r'የከፋይ ቴሌብር ቁ\./Payer telebirr no\.',
    r'የገንዘብ ተቀባይ ስም/Credited Party name',
    r'የገንዘብ ተቀባይ ቴሌብር ቁ\./Credited party account no',
    r'የክፍያው ሁኔታ/transaction status',
    r'የክፍያ ዝርዝር/ Invoice details',
    r'የክፍያ ቁጥር/Invoice No\.',
    r'የክፍያ ቀን/Payment date',
    r'የተከፈለው መጠን/Settled Amount',
    r'የአገልግሎት ክፍያ/Service fee',
    r'የአገልግሎት ክፍያ ተ\.እ\.ታ/Service fee VAT',
    r'ጠቅላላ የተከፈለ/Total Paid Amount',
    r'የገንዘቡ ልክ በፊደል/Total Amount in word',
    r'የክፍያ ዘዴ/Payment Mode',
    r'የክፍያ ምክንያት/Payment Reason',
    r'የክፍያ መንገድ/Payment channel',
    r'data:image/png;base64,',
    r'Scan the QR using telebirr SuperApp',
    r'www\.facebook\.com/telebirr',
    r'twitter\.com/telebirr',
    r't\.me/telebirr',
    r'telebirr@ethionet\.et',
    r'Download PDF',
    r'Ethio telecom Share Company',
    r'TIN No\.',
    r'0000030603',
    r'VAT Reg\. No\.',
    r'012700',
    r'P\.O\.Box',
    r'1047 Addis Ababa, Ethiopia',
    r'Tel \.',
    r'251\(0\) 115 505 678',
    r'Thank you for using telebirr',
    r'html2pdf\(\)\.from\(element\)\.set\(opt\)\.save',
]


async def fetch_receipt(receipt_number: str) -> str | None:
    if not receipt_number or not re.match(r'^[A-Za-z0-9]+$', receipt_number):
        return None
    url = TELEBIRR_RECEIPT_URL.format(receipt_no=receipt_number)
    try:
        async with httpx.AsyncClient(timeout=15.0, follow_redirects=True) as client:
            resp = await client.get(
                url,
                headers={"User-Agent": "Mozilla/5.0 (compatible; TrustedBot/1.0)"},
            )
            if resp.status_code == 200:
                return resp.text
            return None
    except (httpx.TimeoutException, httpx.RequestError):
        return None


def verify_structure(html: str) -> tuple[bool, list[str]]:
    if not html:
        return False, ["Empty HTML response"]
    missing = []
    for pattern in REQUIRED_STRUCTURES:
        if not re.search(pattern, html, re.IGNORECASE | re.DOTALL):
            missing.append(pattern[:60])
    if missing:
        return False, missing
    return True, []


def _extract_field(pattern: str, html: str, group: int = 1) -> str | None:
    m = re.search(pattern, html)
    if m:
        return m.group(group).strip()
    return None


def _parse_amount(text: str | None) -> Decimal | None:
    if not text:
        return None
    cleaned = re.sub(r'[^\d.,]', '', text)
    cleaned = cleaned.replace(',', '')
    try:
        return Decimal(cleaned)
    except (InvalidOperation, ValueError):
        return None


def _extract_value_after_header(pattern: str, html: str) -> str | None:
    m = re.search(pattern, html, re.DOTALL)
    if m:
        return m.group(1).strip()
    return None


def _extract_table_value(header_text: str, html: str, col: int = 0) -> str | None:
    header_row = re.search(
        r'<tr[^>]*>.*?' + re.escape(header_text) + r'.*?</tr>',
        html, re.DOTALL
    )
    if not header_row:
        return None
    rest = html[header_row.end():]
    value_row = re.search(r'<tr[^>]*>(.*?)</tr>', rest, re.DOTALL)
    if not value_row:
        return None
    tds = re.findall(r'<td[^>]*>\s*([^<]+)\s*</td>', value_row.group(1))
    if col < len(tds):
        return tds[col].strip()
    return None


def extract_details(html: str) -> dict | None:
    if not html:
        return None
    try:
        details = {
            "payer_name": _extract_value_after_header(
                r'የከፋይ ስም/Payer Name\s*</td>\s*<td[^>]*>\s*([^<]+)', html
            ),
            "payer_phone": _extract_value_after_header(
                r'የከፋይ ቴሌብር ቁ\./Payer telebirr no\.\s*</td>\s*<td[^>]*>\s*([^<]+)', html
            ),
            "receiver_name": _extract_value_after_header(
                r'የገንዘብ ተቀባይ ስም/Credited Party name\s*</td>\s*<td[^>]*>\s*([^<]+)', html
            ),
            "receiver_phone": _extract_value_after_header(
                r'የገንዘብ ተቀባይ ቴሌብር ቁ\./Credited party account no\s*</td>\s*<td[^>]*>\s*([^<]+)', html
            ),
            "invoice_no": _extract_table_value(
                "የክፍያ ቁጥር/Invoice No.", html, 0
            ),
            "payment_date": _extract_table_value(
                "የክፍያ ቁጥር/Invoice No.", html, 1
            ),
            "settled_amount": _extract_table_value(
                "የክፍያ ቁጥር/Invoice No.", html, 2
            ),
            "service_fee": _extract_value_after_header(
                r'የአገልግሎት ክፍያ/Service fee\s*(?:&nbsp;\s*)+\s*</td>\s*<td[^>]*>\s*([^<]+)\s*</td>', html
            ),
            "service_fee_vat": _extract_value_after_header(
                r'የአገልግሎት ክፍያ ተ\.እ\.ታ/Service fee VAT\s*(?:&nbsp;\s*)+\s*</td>\s*<td[^>]*>\s*([^<]+)\s*</td>', html
            ),
            "total_paid": _extract_value_after_header(
                r'ጠቅላላ የተከፈለ/Total Paid Amount\s*(?:&nbsp;\s*)+\s*</td>\s*<td[^>]*>\s*([^<]+)\s*</td>', html
            ),
            "transaction_status": _extract_value_after_header(
                r'የክፍያው ሁኔታ/transaction status\s*<td[^>]*>\s*([^<]+)', html
            ),
            "payment_mode": _extract_value_after_header(
                r'የክፍያ ዘዴ/Payment Mode\s*</td>\s*<td[^>]*>\s*([^<]+)', html
            ),
            "payment_reason": _extract_value_after_header(
                r'የክፍያ ምክንያት/Payment Reason\s*</td>\s*<td[^>]*>\s*([^<]+)', html
            ),
            "payment_channel": _extract_value_after_header(
                r'የክፍያ መንገድ/Payment channel\s*</td>\s*<td[^>]*>\s*([^<]+)', html
            ),
        }
        details["settled_amount_num"] = _parse_amount(details.get("settled_amount"))
        details["total_paid_num"] = _parse_amount(details.get("total_paid"))
        details["service_fee_num"] = _parse_amount(details.get("service_fee"))
        return details
    except Exception:
        return None


async def verify_receipt(receipt_number: str) -> dict:
    html = await fetch_receipt(receipt_number)
    if not html:
        return {"valid": False, "details": None, "error": "Could not fetch receipt. Check the receipt number and try again."}

    struct_valid, missing = verify_structure(html)
    if not struct_valid:
        return {"valid": False, "details": None, "error": f"Receipt structure verification failed (regex). Missing elements: {', '.join(missing[:5])}"}

    fingerprint_valid, fingerprint_errors = verify_telebirr_structure(html)
    if not fingerprint_valid:
        return {"valid": False, "details": None, "error": f"Receipt structure verification failed (fingerprint). Issues: {'; '.join(fingerprint_errors[:5])}"}

    details = extract_details(html)
    if not details:
        return {"valid": False, "details": None, "error": "Could not parse receipt details."}

    if details.get("transaction_status", "").lower() != "completed":
        return {"valid": False, "details": details, "error": f"Transaction status is '{details.get('transaction_status')}', expected 'Completed'."}

    return {"valid": True, "details": details, "error": None}
