"""
HTML structure fingerprinting for Telebirr receipt validation.

The reference example.html defines the exact structural and textual
fingerprint. Every tag, attribute, CSS rule, URL, JS snippet, and
static text fragment is verified. Only values that are truly dynamic
(payer name, phone, amounts, dates, invoice number, QR data) may
differ between receipts.
"""

import re
import os


def _load_example() -> str:
    path = os.path.join(os.path.dirname(__file__), "..", "example.html")
    with open(path, "r", encoding="utf-8") as f:
        return f.read()


EXAMPLE_HTML = _load_example()

# ── Static textual fragments that must appear verbatim ──────────
CRITICAL_TEXT = [
    "Ethio telecom Share Company",
    "telebirr Transaction information",
    "TIN No.",
    "0000030603",
    "VAT Reg. No.",
    "012700",
    "P.O.Box",
    "1047 Addis Ababa, Ethiopia",
    "Tel .",
    "251(0) 115 505 678",
    "Thank you for using telebirr",
]

CRITICAL_LABELS = [
    "Payer Name",
    "Payer telebirr no",
    "Credited Party name",
    "Credited party account no",
    "transaction status",
    "Invoice details",
    "Invoice No",
    "Payment date",
    "Settled Amount",
    "Service fee",
    "Service fee VAT",
    "Total Paid Amount",
    "Total Amount in word",
    "Payment Mode",
    "Payment Reason",
    "Payment channel",
]

CRITICAL_LINKS = [
    "www.facebook.com/telebirr",
    "x.com/telebirr",
    "t.me/telebirr",
    "telebirr@ethionet.et",
]

CRITICAL_INSTRUCTIONS = [
    "Scan the QR using telebirr SuperApp",
    "Download PDF",
    "html2pdf",
]

# ── Attribute values that must be exact ─────────────────────────
CRITICAL_ATTR_VALUES = {
    # meta charset
    "utf-8",
    # html lang
    "en",
    # button id
    "button",
    # download link attributes (exact contents vary by receipt)
}

# ── JS code fragments that must be present ──────────────────────
CRITICAL_JS_FRAGMENTS = [
    "html2pdf",
    "document.getElementById(\"button\")",
    "addEventListener",
    "html2canvas",
    "useCORS",
    "referencenumber",
    "paid_reference_number",
    "telebirr_Send Money to Registered Customer",
]


def _check_doctype(html: str) -> list[str]:
    if not re.search(r'<!DOCTYPE html>', html, re.IGNORECASE):
        return ["Missing DOCTYPE declaration"]
    return []


def _check_critical_text(html: str) -> list[str]:
    missing = []
    for s in CRITICAL_TEXT:
        if s not in html:
            missing.append(repr(s))
    return missing


def _check_labels(html: str) -> list[str]:
    missing = []
    for s in CRITICAL_LABELS:
        if s not in html:
            missing.append(repr(s))
    return missing


def _check_links(html: str) -> list[str]:
    missing = []
    for link in CRITICAL_LINKS:
        if link not in html:
            missing.append(link)
    return missing


def _check_instructions(html: str) -> list[str]:
    missing = []
    for s in CRITICAL_INSTRUCTIONS:
        if s not in html:
            missing.append(repr(s))
    return missing


def _check_critical_attrs(html: str) -> list[str]:
    errors = []
    # lang on <html>
    if not re.search(r'<html\s+lang="en"', html):
        errors.append("html lang is not 'en'")
    # charset (inside content attribute value)
    if 'charset=utf-8' not in html:
        errors.append("charset is not utf-8")
    # button id
    if 'id="button"' not in html:
        errors.append("Missing id='button'")
    return errors


def _check_js_fragments(html: str) -> list[str]:
    missing = []
    for frag in CRITICAL_JS_FRAGMENTS:
        if frag not in html:
            missing.append(repr(frag))
    return missing


def _extract_css_selectors(html: str) -> set[str]:
    selectors = set()
    for m in re.finditer(r'<style[^>]*>(.*?)</style>', html, re.DOTALL):
        for sel in re.finditer(r'([.#]?\w[\w-]*)\s*\{', m.group(1)):
            selectors.add(sel.group(1))
    return selectors


def _extract_css_properties(html: str) -> set[str]:
    props = set()
    for m in re.finditer(r'<style[^>]*>(.*?)</style>', html, re.DOTALL):
        for p in re.finditer(r'([\w-]+)\s*:\s*([^;]+);', m.group(1)):
            props.add(f"{p.group(1).strip()}:{p.group(2).strip()}")
    return props


def _extract_classes(html: str) -> set[str]:
    classes = set()
    for m in re.finditer(r'class\s*=\s*"([^"]*)"', html):
        for cls in m.group(1).split():
            classes.add(cls)
    return classes


def _extract_ids(html: str) -> set[str]:
    ids = set()
    for m in re.finditer(r'id\s*=\s*"([^"]*)"', html):
        ids.add(m.group(1))
    return ids


def _extract_urls(html: str) -> set[str]:
    urls = set()
    for m in re.finditer(r'(?:href|src)\s*=\s*"(https?://[^"]*)"', html):
        urls.add(m.group(1))
    return urls


def _extract_script_srcs(html: str) -> set[str]:
    srcs = set()
    for m in re.finditer(r'<script[^>]*src\s*=\s*"([^"]*)"', html):
        srcs.add(m.group(1))
    return srcs


def _extract_link_hrefs(html: str) -> set[str]:
    hrefs = set()
    for m in re.finditer(r'<link[^>]*href\s*=\s*"([^"]*)"', html):
        hrefs.add(m.group(1))
    return hrefs


def _count_tags(html: str) -> int:
    """Count opening tags (excluding self-closing meta/link/br/img/input/hr)."""
    count = 0
    VOID = {'meta', 'link', 'br', 'img', 'input', 'hr'}
    for m in re.finditer(r'<(\w+)(?:\s[^>]*)?>', html):
        tag = m.group(1)
        if tag not in VOID and not html[m.start():m.start()+2] == '</':
            count += 1
    return count


def _extract_img_srcs(html: str) -> set[str]:
    srcs = set()
    for m in re.finditer(r'<img[^>]*src\s*=\s*"([^"]*)"', html):
        srcs.add(m.group(1))
    return srcs


def verify_telebirr_structure(html: str) -> tuple[bool, list[str]]:
    """
    Verify that `html` matches the structural fingerprint of example.html.
    Returns (is_valid, list_of_errors).
    """
    if not html or len(html) < 500:
        return False, ["HTML too short or empty"]

    errors = []

    # 1. DOCTYPE
    errors.extend(_check_doctype(html))

    # 2. Static text (company info, TIN, VAT, address, phone)
    errors.extend(_check_critical_text(html))

    # 3. All Amharic/English labels
    errors.extend(_check_labels(html))

    # 4. Social media links and contact
    errors.extend(_check_links(html))

    # 5. Instructions (QR scan, download, PDF)
    errors.extend(_check_instructions(html))

    # 6. Critical attribute values (lang, charset, ids)
    errors.extend(_check_critical_attrs(html))

    # 7. JavaScript fragments
    errors.extend(_check_js_fragments(html))

    # 8. QR code presence
    if 'data:image/png;base64,' not in html:
        errors.append("Missing QR code data")

    # 9. CSS selectors
    ref_css = _extract_css_selectors(EXAMPLE_HTML)
    sub_css = _extract_css_selectors(html)
    missing_css = ref_css - sub_css
    if missing_css:
        errors.append(f"Missing CSS selectors ({len(missing_css)}): {', '.join(sorted(missing_css)[:6])}")

    # 10. CSS property:value pairs
    ref_props = _extract_css_properties(EXAMPLE_HTML)
    sub_props = _extract_css_properties(html)
    missing_props = ref_props - sub_props
    if missing_props:
        errors.append(f"Missing CSS props ({len(missing_props)}): {', '.join(sorted(missing_props)[:4])}")

    # 11. External script sources
    ref_scripts = _extract_script_srcs(EXAMPLE_HTML)
    sub_scripts = _extract_script_srcs(html)
    if ref_scripts and not ref_scripts.issubset(sub_scripts):
        errors.append(f"Missing script srcs: {ref_scripts - sub_scripts}")

    # 12. External link hrefs
    ref_links = _extract_link_hrefs(EXAMPLE_HTML)
    sub_links = _extract_link_hrefs(html)
    if ref_links and not ref_links.issubset(sub_links):
        errors.append(f"Missing link hrefs: {ref_links - sub_links}")

    # 13. URLs (social media etc.)
    ref_urls = _extract_urls(EXAMPLE_HTML)
    sub_urls = _extract_urls(html)
    if ref_urls and not ref_urls.issubset(sub_urls):
        errors.append(f"Missing URLs: {ref_urls - sub_urls}")

    # 14. CSS classes
    ref_classes = _extract_classes(EXAMPLE_HTML)
    sub_classes = _extract_classes(html)
    missing_classes = ref_classes - sub_classes
    if missing_classes:
        errors.append(f"Missing CSS classes ({len(missing_classes)}): {', '.join(sorted(missing_classes)[:6])}")

    # 15. Element ids
    ref_ids = _extract_ids(EXAMPLE_HTML)
    sub_ids = _extract_ids(html)
    missing_ids = ref_ids - sub_ids
    if missing_ids:
        errors.append(f"Missing IDs: {', '.join(sorted(missing_ids)[:5])}")

    # 16. Element count checks
    for tag, expected in [('script', 5), ('meta', 1), ('link', 1)]:
        actual = len(re.findall(rf'<{tag}[\s>]', html))
        if actual != expected:
            errors.append(f"Expected {expected} <{tag}> tags, got {actual}")
            break  # one error per category

    # 17. Tag count check (±5% tolerance)
    ref_count = _count_tags(EXAMPLE_HTML)
    sub_count = _count_tags(html)
    if sub_count < ref_count * 0.95:
        errors.append(f"Too few opening tags ({sub_count} vs {ref_count})")
    elif sub_count > ref_count * 1.05:
        errors.append(f"Too many opening tags ({sub_count} vs {ref_count})")

    # 17. Image sources (excluding QR code which is dynamic)
    ref_imgs = {s for s in _extract_img_srcs(EXAMPLE_HTML) if not s.startswith('data:')}
    sub_imgs = {s for s in _extract_img_srcs(html) if not s.startswith('data:')}
    if ref_imgs and not ref_imgs.issubset(sub_imgs):
        errors.append(f"Missing image sources: {ref_imgs - sub_imgs}")

    # 19. Check for known-static inline style values
    # (e.g., receipt table styling)
    if 'border-collapse: collapse' not in html:
        errors.append("Missing receipt table border-collapse style")

    if errors:
        return False, errors
    return True, []


def sensitivity_test():
    """Run small alterations against example.html to verify sensitivity."""
    print("=" * 60)
    print("STRUCTURAL VERIFICATION SENSITIVITY TEST")
    print("=" * 60)

    tests = []

    def run_test(name: str, altered_html: str, expect_pass: bool):
        valid, errs = verify_telebirr_structure(altered_html)
        if expect_pass:
            ok = valid
            status = "✅ PASS" if valid else f"❌ FAIL ({errs[0][:60]})"
        else:
            ok = not valid
            status = "✅ CAUGHT" if not valid else "❌ MISSED"
        tests.append((name, expect_pass, ok))
        print(f"{'%02d' % (len(tests)+1)}. {status}  ({name})")

    # 1. Original must pass
    print(f" 1. {'✅ PASS' if verify_telebirr_structure(EXAMPLE_HTML)[0] else '❌ FAIL'}  (Original example.html)")
    tests.append(("Original", True, verify_telebirr_structure(EXAMPLE_HTML)[0]))

    # 2. Remove DOCTYPE
    altered = EXAMPLE_HTML.replace("<!DOCTYPE html>", "")
    valid, _ = verify_telebirr_structure(altered)
    ok = not valid
    print(f" 2. {'✅ CAUGHT' if ok else '❌ MISSED'}  (Remove DOCTYPE)"); tests.append(("Remove DOCTYPE", False, ok))

    # 3. Change CSS property
    altered = EXAMPLE_HTML.replace("background-color:#fff", "background-color:#000")
    valid, _ = verify_telebirr_structure(altered)
    ok = not valid
    print(f" 3. {'✅ CAUGHT' if ok else '❌ MISSED'}  (Change CSS background-color)"); tests.append(("Change CSS bg", False, ok))

    # 4. Rename a CSS class
    altered = EXAMPLE_HTML.replace("receipttableTd2", "fakeclass")
    valid, _ = verify_telebirr_structure(altered)
    ok = not valid
    print(f" 4. {'✅ CAUGHT' if ok else '❌ MISSED'}  (Rename CSS class receipttableTd2)"); tests.append(("Rename CSS class", False, ok))

    # 5. Alter Facebook URL
    altered = EXAMPLE_HTML.replace("https://www.facebook.com/telebirr", "https://www.facebook.com/fake")
    valid, _ = verify_telebirr_structure(altered)
    ok = not valid
    print(f" 5. {'✅ CAUGHT' if ok else '❌ MISSED'}  (Alter Facebook URL)"); tests.append(("Alter FB URL", False, ok))

    # 6. Alter telephone number
    altered = EXAMPLE_HTML.replace("251(0) 115 505 678", "251(0) 000 000 000")
    valid, _ = verify_telebirr_structure(altered)
    ok = not valid
    print(f" 6. {'✅ CAUGHT' if ok else '❌ MISSED'}  (Alter Tel number)"); tests.append(("Alter Tel", False, ok))

    # 7. Remove QR code
    altered = EXAMPLE_HTML.replace("data:image/png;base64,", "")
    valid, _ = verify_telebirr_structure(altered)
    ok = not valid
    print(f" 7. {'✅ CAUGHT' if ok else '❌ MISSED'}  (Remove QR code)"); tests.append(("Remove QR", False, ok))

    # 8. Remove JS code
    altered = EXAMPLE_HTML.replace('const btn = document.getElementById("button");', '')
    valid, _ = verify_telebirr_structure(altered)
    ok = not valid
    print(f" 8. {'✅ CAUGHT' if ok else '❌ MISSED'}  (Remove JS code)"); tests.append(("Remove JS", False, ok))

    # 9. Change company name
    altered = EXAMPLE_HTML.replace("Ethio telecom Share Company", "Fake Company")
    valid, _ = verify_telebirr_structure(altered)
    ok = not valid
    print(f" 9. {'✅ CAUGHT' if ok else '❌ MISSED'}  (Change company name)"); tests.append(("Change company", False, ok))

    # 10. Change TIN number
    altered = EXAMPLE_HTML.replace("0000030603", "0000000000")
    valid, _ = verify_telebirr_structure(altered)
    ok = not valid
    print(f"10. {'✅ CAUGHT' if ok else '❌ MISSED'}  (Alter TIN number)"); tests.append(("Alter TIN", False, ok))

    # 11. Remove VAT row
    altered = EXAMPLE_HTML.replace('<td style="text-align: left;">VAT Reg. No. </td>', '')
    valid, _ = verify_telebirr_structure(altered)
    ok = not valid
    print(f"11. {'✅ CAUGHT' if ok else '❌ MISSED'}  (Remove VAT row)"); tests.append(("Remove VAT row", False, ok))

    # 12. Change Download button text
    altered = EXAMPLE_HTML.replace("Download PDF", "Download")
    valid, _ = verify_telebirr_structure(altered)
    ok = not valid
    print(f"12. {'✅ CAUGHT' if ok else '❌ MISSED'}  (Alter Download button text)"); tests.append(("Alter Download", False, ok))

    # 13. Change html lang
    altered = EXAMPLE_HTML.replace('<html lang="en">', '<html lang="am">')
    valid, _ = verify_telebirr_structure(altered)
    ok = not valid
    print(f"13. {'✅ CAUGHT' if ok else '❌ MISSED'}  (Change html lang)"); tests.append(("Change lang", False, ok))

    # 14. Remove Facebook link element
    altered = EXAMPLE_HTML.replace('<a href="https://www.facebook.com/telebirr">https://www.facebook.com/telebirr</a>', '')
    valid, _ = verify_telebirr_structure(altered)
    ok = not valid
    print(f"14. {'✅ CAUGHT' if ok else '❌ MISSED'}  (Remove FB link element)"); tests.append(("Remove FB link", False, ok))

    # 15. Inject extra script
    altered = EXAMPLE_HTML.replace('</body>', '<script>alert("hack")</script></body>')
    valid, _ = verify_telebirr_structure(altered)
    ok = not valid
    print(f"15. {'✅ CAUGHT' if ok else '❌ MISSED'}  (Inject extra script)"); tests.append(("Inject script", False, ok))

    # 16. Change meta charset
    altered = EXAMPLE_HTML.replace(
        '<meta http-equiv="Content-Type" content="text/html; charset=utf-8">',
        '<meta http-equiv="Content-Type" content="text/html; charset=iso-8859-1">'
    )
    valid, _ = verify_telebirr_structure(altered)
    ok = not valid
    print(f"16. {'✅ CAUGHT' if ok else '❌ MISSED'}  (Change meta charset)"); tests.append(("Change charset", False, ok))

    # 17. Remove image source
    altered = EXAMPLE_HTML.replace('../image/telebirr.png', '../image/fake.png')
    valid, _ = verify_telebirr_structure(altered)
    ok = not valid
    print(f"17. {'✅ CAUGHT' if ok else '❌ MISSED'}  (Alter image source)"); tests.append(("Alter img src", False, ok))

    # 18. Change X (twitter) URL
    altered = EXAMPLE_HTML.replace("https://x.com/telebirr", "https://x.com/fake")
    valid, _ = verify_telebirr_structure(altered)
    ok = not valid
    print(f"18. {'✅ CAUGHT' if ok else '❌ MISSED'}  (Alter X.com URL)"); tests.append(("Alter X URL", False, ok))

    # Summary
    print(f"\n{'=' * 60}")
    total = len(tests)
    original_ok = tests[0][2]
    caught = sum(1 for i in range(1, total) if tests[i][2])
    print(f"Original example.html: {'✅ PASS' if original_ok else '❌ FAIL'}")
    print(f"Alterations detected: {caught}/{total-1}")
    if caught == total - 1:
        print("✅ ALL ALTERATIONS DETECTED — system is fully sensitive")
    else:
        print(f"❌ {total-1 - caught} alteration(s) were not detected")
    print(f"{'=' * 60}")
    return caught == total - 1
    all_ok = all(ok for _, _, ok in tests)
    if all_ok:
        print("✅ ALL TESTS PASS — system is fully sensitive")
    else:
        print("❌ Some tests failed")
    print(f"{'=' * 60}")

    return all_ok


if __name__ == "__main__":
    sensitivity_test()
