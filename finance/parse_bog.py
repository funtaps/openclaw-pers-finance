#!/usr/bin/env python3
"""BoG (Bank of Georgia) CSV export parser.

Commands:
    python3 finance/parse_bog.py <file.csv>              # Parse an export
    python3 finance/parse_bog.py flagged                 # Show flagged items
    python3 finance/parse_bog.py approve 1=Food 2=skip   # Approve flagged items

Categories: Food, Transport, Utilities, Entertainment, Health, Kid, Pets, Clothes, Home, Other, Rent, Cash
"""

import csv, json, re, sys, hashlib
from pathlib import Path
from datetime import datetime

# ─── Paths ───────────────────────────────────────────────────────────────────
SCRIPT_DIR    = Path(__file__).parent
EXPENSES_PATH = SCRIPT_DIR / "expenses.csv"
FLAGGED_PATH  = SCRIPT_DIR / "flagged.json"
MERCHANT_MAP  = SCRIPT_DIR / "merchant_map.json"
DEDUP_PATH    = SCRIPT_DIR / ".dedup_keys"

VALID_CATEGORIES = [
    "Food","Transport","Utilities","Entertainment",
    "Health","Kid","Pets","Clothes","Home","Other","Rent","Cash",
]

# ─── Category mappings ───────────────────────────────────────────────────────
# MCC → category
MCC_CAT = {
    # Food & grocery
    "5411":"Food", "5441":"Food", "5499":"Food", "5461":"Food",
    "5812":"Food", "5814":"Food",
    "4215":"Food",   # delivery apps (Wolt, Glovo)
    # Transport
    "4121":"Transport", "5541":"Transport",
    "7523":"Transport", "9399":"Transport",
    # Utilities
    "4814":"Utilities",
    # Entertainment / subs / travel
    "5734":"Entertainment", "5816":"Entertainment", "5818":"Entertainment",
    "7841":"Entertainment", "7996":"Entertainment", "7922":"Entertainment",
    "7011":"Entertainment", "4722":"Entertainment", "7298":"Entertainment",
    "5732":"Entertainment",
    # Clothes
    "5691":"Clothes", "5651":"Clothes", "5661":"Clothes",
    # Home
    "5719":"Home", "5211":"Home", "5013":"Home",
    # Pets
    "5995":"Pets", "5996":"Pets",
    # Kid
    "5945":"Kid",
    # Health
    "5912":"Health",
    # Other
    "5311":"Other", "5262":"Other", "5192":"Other", "5947":"Other",
    "5169":"Other", "5993":"Other", "5992":"Other",
    "6300":"Other", "6012":"Other",
}

# Merchant name keywords → category
MERCHANT_KW = {
    "Food": [
        "nikora", "spar", "marketi", "europroduct", "clean house",
        "mcdon", "kfc", "subway", "pizzeria", "kafe", "cafe ",
        "wrap master", "wendys", "baho", "dunkin", "ori nabiji",
        "jambo coffee", "shukura", "anna smaragdina",
        "veriko tabidze", "giorgi phochkhua", "two dzma", "magniti",
    ],
    "Transport": [
        "yandex.go", "bolt taxi", "lukoil", "portal",
        "tbilisi bus", "scooter",
    ],
    "Pets":          ["zoomart", "animal planet"],
    "Utilities":     ["magticom", "silknet"],
    "Entertainment": [
        "steam", "google", "github", "cursor", "chatgpt", "openai",
        "youtube", "kindle", "gfn.am", "microsoft", "netflix",
        "biletebi", "gulo", "zoommer", "pulman", "pebblehost",
    ],
    "Kid":  ["robolaboratoria", "top toys", "tbilisi parki"],
    "Home": ["jysk", "amboli"],
    "Other": ["temu", "ozon", "vape room"],
}

# Known transfer beneficiaries → auto-category
KNOWN_BENEFICIARIES = {
    "dalakishvili ana": "Rent",
}

# ─── Helpers ─────────────────────────────────────────────────────────────────
def parse_eu_amount(s):
    """European format: '1 234,5' → 1234.5"""
    if not s or not s.strip():
        return 0.0
    return float(s.strip().replace(" ", "").replace("\xa0", "").replace(",", "."))

def dedup_key(date_str, details):
    return hashlib.md5(f"{date_str}|{details}".encode()).hexdigest()[:14]

def load_json(path, default=None):
    try:
        return json.loads(path.read_text())
    except:
        return default if default is not None else {}

def save_json(path, data):
    path.write_text(json.dumps(data, indent=2, ensure_ascii=False))

def load_dedup():
    try:
        return set(line for line in DEDUP_PATH.read_text().strip().split("\n") if line)
    except:
        return set()

def save_dedup(keys):
    DEDUP_PATH.write_text("\n".join(sorted(keys)))

# ─── Extraction ──────────────────────────────────────────────────────────────
def extract_charged(details):
    """'Payment transaction amount and currency: 24.12 GEL' → (24.12, 'GEL')"""
    m = re.search(r"Payment transaction amount and currency:\s*([\d.,]+)\s*([A-Z]{3})", details)
    if m:
        return float(m.group(1).replace(",", "")), m.group(2)
    return None, None

def extract_leading(details):
    """'Amount: GEL59.49' or 'Amount GEL59.49' → (59.49, 'GEL')"""
    m = re.search(r"Amount:?\s*([A-Z]{3})\s*([\d.,]+)", details)
    if m:
        return float(m.group(2).replace(",", "")), m.group(1)
    return None, None

def extract_merchant_mcc_date(details):
    merchant = mcc = actual_date = None
    m = re.search(r"Merchant:\s*([^;]+)", details)
    if m: merchant = m.group(1).strip()
    m = re.search(r"MCC:(\d+)", details)
    if m: mcc = m.group(1)
    m = re.search(r"Date:\s*(\d{2}/\d{2}/\d{4})", details)
    if m: actual_date = m.group(1)
    return merchant, mcc, actual_date

def extract_atm(details):
    m = re.search(r"ATM:\s*([^;]+)", details)
    return m.group(1).strip() if m else "ATM"

def extract_beneficiary(details):
    m = re.search(r"Beneficiary:\s*([^;]+)", details)
    return m.group(1).strip() if m else "?"

def extract_transfer_note(details):
    m = re.search(r"Details:\s*(.+)", details)
    return m.group(1).strip() if m else ""

# ─── Categorization ──────────────────────────────────────────────────────────
def categorize(merchant, mcc, details, learned_map):
    """Returns (category, is_auto)."""
    # 1. Learned map (from previous approvals)
    if merchant and merchant.lower() in learned_map:
        return learned_map[merchant.lower()], True

    # 2. Special detail patterns
    dl = details.lower()
    if "traffic penalty" in dl:        return "Other", True
    if "tbilisienergy" in dl:          return "Utilities", True
    if "ep georgia supply" in dl:      return "Utilities", True
    if "tbilisi bus" in dl:            return "Transport", True

    # 3. Merchant keyword match
    if merchant:
        ml = merchant.lower()
        for cat, kws in MERCHANT_KW.items():
            if any(kw in ml for kw in kws):
                return cat, True

    # 4. MCC code
    if mcc and mcc in MCC_CAT:
        return MCC_CAT[mcc], True

    return None, False

def fix_description(desc, details):
    """Clean up description for known service patterns."""
    dl = details.lower()
    if "traffic penalty" in dl:        return "Traffic Penalty"
    if "tbilisienergy" in dl:          return "TbilisiEnergy (electricity)"
    if "ep georgia supply" in dl:      return "EP Georgia Supply (utilities)"
    if "tbilisi bus" in dl:            return "Tbilisi Bus"
    return desc

# ─── Core parser ─────────────────────────────────────────────────────────────
def should_skip(details):
    """Internal / non-expense rows to ignore entirely."""
    dl = details.lower()
    return any(tag in dl for tag in [
        "automatic conversion", "zolotayakorona",
        "interest payment", "points exchange", "point redemption",
        "foreign exchange", "incoming transfer", "credit funds",
    ])

def parse_bog(filepath):
    """Parse BoG CSV → list of transaction dicts."""
    txs = []
    lines = Path(filepath).read_text(encoding="utf-8-sig").strip().split("\n")

    for line in lines[1:]:  # skip header
        if not line.strip():
            continue
        row = next(csv.reader([line]), None)
        if not row or len(row) < 2:
            continue

        date_raw = row[0].strip()
        details  = row[1].strip()

        # Skip non-date rows (Balance, empty, etc.)
        if not re.match(r"\d{2}/\d{2}/\d{4}", date_raw):
            continue
        # Skip internal transactions
        if should_skip(details):
            continue

        # Column amounts (European format)
        gel = parse_eu_amount(row[3]) if len(row) > 3 else 0
        usd = parse_eu_amount(row[4]) if len(row) > 4 else 0
        eur = parse_eu_amount(row[5]) if len(row) > 5 else 0
        gbp = parse_eu_amount(row[6]) if len(row) > 6 else 0

        date_obj = datetime.strptime(date_raw, "%d/%m/%Y")
        dk = dedup_key(date_raw, details)

        # ── ATM Withdrawal → flag as cash ────────────────────────────────────
        if details.startswith("Withdrawal"):
            amt, cur = extract_charged(details)
            if not amt:
                amt, cur = extract_leading(details)
            if not amt:
                amt, cur = (abs(gel), "GEL") if gel < 0 else (0, "GEL")
            _, _, act_date = extract_merchant_mcc_date(details)
            if act_date:
                date_obj = datetime.strptime(act_date, "%d/%m/%Y")

            txs.append(dict(
                date=date_obj.strftime("%Y-%m-%d"),
                description=f"Cash (ATM: {extract_atm(details)})",
                amount=amt, currency=cur,
                category=None, flag="cash", dk=dk,
            ))
            continue

        # ── Outgoing Transfer → flag unless known ────────────────────────────
        if details.startswith("Outgoing Transfer"):
            beneficiary = extract_beneficiary(details)
            note        = extract_transfer_note(details)
            amt, cur    = extract_leading(details)
            if not amt:
                if   usd < 0: amt, cur = abs(usd), "USD"
                elif gel < 0: amt, cur = abs(gel), "GEL"
                elif eur < 0: amt, cur = abs(eur), "EUR"
                else: continue

            cat, flag = None, "transfer"
            for known, known_cat in KNOWN_BENEFICIARIES.items():
                if known in beneficiary.lower():
                    cat, flag = known_cat, None
                    break

            txs.append(dict(
                date=date_obj.strftime("%Y-%m-%d"),
                description=f"→ {beneficiary}" + (f" ({note})" if note else ""),
                amount=amt, currency=cur,
                category=cat, flag=flag, dk=dk,
                merchant=None,
            ))
            continue

        # ── Regular Payment ──────────────────────────────────────────────────
        if details.startswith("Payment"):
            # Amount: prefer exact "Payment transaction amount and currency"
            amt, cur = extract_charged(details)
            if not amt:
                amt, cur = extract_leading(details)
            if not amt:
                if   gel < 0: amt, cur = abs(gel), "GEL"
                elif usd < 0: amt, cur = abs(usd), "USD"
                elif eur < 0: amt, cur = abs(eur), "EUR"
                elif gbp < 0: amt, cur = abs(gbp), "GBP"
                else: continue

            merchant, mcc, act_date = extract_merchant_mcc_date(details)
            if act_date:
                date_obj = datetime.strptime(act_date, "%d/%m/%Y")

            description = merchant if merchant else details[:60]
            description = fix_description(description, details)

            txs.append(dict(
                date=date_obj.strftime("%Y-%m-%d"),
                description=description,
                amount=amt, currency=cur,
                category=None, flag=None, dk=dk,
                merchant=merchant, mcc=mcc,
            ))
            continue

    return txs

# ─── Commands ────────────────────────────────────────────────────────────────
def cmd_parse(filepath):
    learned   = load_json(MERCHANT_MAP, {})
    known_dks = load_dedup()

    print(f"📂 Parsing {filepath}…")
    txs = parse_bog(filepath)
    print(f"   {len(txs)} transactions found")

    # Dedup
    new_txs, dupes = [], 0
    for t in txs:
        if t["dk"] in known_dks:
            dupes += 1
        else:
            new_txs.append(t)
    if dupes:
        print(f"   ⏭️  {dupes} duplicate(s) skipped")
    txs = new_txs

    if not txs:
        print("   Nothing new.")
        return

    # Categorize payments
    for t in txs:
        if t.get("flag") in ("cash", "transfer"):
            continue  # already typed — will be flagged
        if t.get("category") is not None:
            continue  # already categorized (e.g. known beneficiary)
        cat, is_auto = categorize(
            t.get("merchant"), t.get("mcc"),
            t.get("description", ""), learned
        )
        t["category"] = cat
        t["flag"]     = None if is_auto else "unknown"

    # Split
    auto    = [t for t in txs if not t.get("flag")]
    flagged = [t for t in txs if  t.get("flag")]

    # ── Print summary ────────────────────────────────────────────────────────
    print(f"\n✅ Auto-categorized: {len(auto)}")
    if auto:
        totals = {}
        for t in auto:
            k = (t["category"], t["currency"])
            totals[k] = totals.get(k, 0) + t["amount"]
        for (cat, cur), total in sorted(totals.items()):
            print(f"     {cat:16s} {total:>10.2f} {cur}")

    # Load existing flagged, merge new ones
    existing_flagged = load_json(FLAGGED_PATH, [])
    if not isinstance(existing_flagged, list):
        existing_flagged = []
    existing_dks = {item["dk"] for item in existing_flagged}
    for t in flagged:
        if t["dk"] not in existing_dks:
            existing_flagged.append(dict(
                dk=t["dk"], date=t["date"], description=t["description"],
                amount=t["amount"], currency=t["currency"],
                flag=t["flag"], merchant=t.get("merchant"),
            ))

    print(f"\n❓ Flagged for review: {len(existing_flagged)}")
    if existing_flagged:
        for i, item in enumerate(existing_flagged, 1):
            print(f"   [{i:2d}] {item['date']} | {item['amount']:>8.2f} {item['currency']} | "
                  f"[{item['flag']}] {item['description']}")

    # ── Save auto → expenses.csv ─────────────────────────────────────────────
    if auto:
        # If file only has example data, reset it
        if EXPENSES_PATH.exists():
            existing_lines = EXPENSES_PATH.read_text().strip().split("\n")
            if len(existing_lines) <= 2 and any("Example" in l for l in existing_lines):
                EXPENSES_PATH.write_text("date,description,amount,currency,category\n")
        else:
            EXPENSES_PATH.write_text("date,description,amount,currency,category\n")

        with open(EXPENSES_PATH, "a", newline="") as f:
            w = csv.writer(f)
            for t in sorted(auto, key=lambda x: x["date"]):
                w.writerow([t["date"], t["description"],
                            round(t["amount"], 2), t["currency"], t["category"]])
        print(f"\n💾 {len(auto)} expenses saved")

    # ── Save flagged ─────────────────────────────────────────────────────────
    save_json(FLAGGED_PATH, existing_flagged)
    if flagged:
        print(f"💾 {len(flagged)} new item(s) flagged")

    # ── Update dedup keys ────────────────────────────────────────────────────
    for t in txs:
        known_dks.add(t["dk"])
    save_dedup(known_dks)

    print(f"\n💡 To approve flagged: python3 finance/parse_bog.py approve 1=Food 2=skip …")


def cmd_flagged():
    items = load_json(FLAGGED_PATH, [])
    if not isinstance(items, list) or not items:
        print("✅ No flagged items.")
        return
    print(f"❓ Flagged items ({len(items)}):\n")
    for i, item in enumerate(items, 1):
        print(f"  [{i:2d}] {item['date']} | {item['amount']:>8.2f} {item['currency']} | "
              f"[{item['flag']}] {item['description']}")
    print(f"\nCategories: {', '.join(VALID_CATEGORIES)}")
    print("Usage: python3 finance/parse_bog.py approve 1=Food 2=skip …")


def cmd_approve(args):
    """Approve flagged items. Args: ['1=Food', '3=skip', ...]"""
    items   = load_json(FLAGGED_PATH, [])
    learned = load_json(MERCHANT_MAP, {})
    if not isinstance(items, list) or not items:
        print("✅ No flagged items.")
        return

    approved, to_remove = [], set()

    for arg in args:
        if "=" not in arg:
            print(f"⚠️  Skip '{arg}' — use N=Category")
            continue
        idx_s, cat_s = arg.split("=", 1)
        try:
            idx = int(idx_s) - 1
        except ValueError:
            print(f"⚠️  Bad index '{idx_s}'")
            continue
        if idx < 0 or idx >= len(items):
            print(f"⚠️  Index {idx+1} out of range (1–{len(items)})")
            continue

        item = items[idx]
        cat  = cat_s.strip()

        if cat.lower() == "skip":
            to_remove.add(idx)
            print(f"  ⏭️  [{idx+1}] Skipped: {item['description']}")
            continue

        # Case-insensitive category match
        matched = next((c for c in VALID_CATEGORIES if c.lower() == cat.lower()), None)
        if not matched:
            print(f"⚠️  Unknown category '{cat}'. Valid: {', '.join(VALID_CATEGORIES)}")
            continue

        item["category"] = matched
        approved.append(item)
        to_remove.add(idx)

        # Learn merchant mapping
        if item.get("merchant"):
            learned[item["merchant"].lower()] = matched
            print(f"  ✅ [{idx+1}] {item['description']} → {matched}  (learned: {item['merchant']})")
        else:
            print(f"  ✅ [{idx+1}] {item['description']} → {matched}")

    # Save approved to expenses.csv
    if approved:
        with open(EXPENSES_PATH, "a", newline="") as f:
            w = csv.writer(f)
            for item in approved:
                w.writerow([item["date"], item["description"],
                            round(item["amount"], 2), item["currency"], item["category"]])
        print(f"\n💾 {len(approved)} expense(s) saved")

    # Update flagged + merchant map
    remaining = [item for i, item in enumerate(items) if i not in to_remove]
    save_json(FLAGGED_PATH, remaining)
    save_json(MERCHANT_MAP, learned)

    if remaining:
        print(f"\n❓ {len(remaining)} item(s) still flagged")
    else:
        print("\n✅ All items reviewed!")

# ─── CLI ─────────────────────────────────────────────────────────────────────
def main():
    if len(sys.argv) < 2:
        print(__doc__)
        sys.exit(1)

    cmd = sys.argv[1]
    if cmd == "flagged":
        cmd_flagged()
    elif cmd == "approve":
        cmd_approve(sys.argv[2:])
    elif cmd.endswith(".csv") or "/" in cmd or "." in cmd:
        cmd_parse(cmd)
    else:
        print(__doc__)

if __name__ == "__main__":
    main()
