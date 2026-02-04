#!/usr/bin/env python3
"""
Household Finance Calculator
Run: python calc.py [--update-rates]
"""

import json
import csv
import sys
from datetime import datetime
from pathlib import Path

SCRIPT_DIR = Path(__file__).parent

def load_json(filename):
    with open(SCRIPT_DIR / filename) as f:
        return json.load(f)

def load_expenses():
    expenses = []
    csv_path = SCRIPT_DIR / "expenses.csv"
    if csv_path.exists():
        with open(csv_path) as f:
            reader = csv.DictReader(f)
            for row in reader:
                row['amount'] = float(row['amount'])
                expenses.append(row)
    return expenses

def to_usd(amount, currency, rates):
    if currency == "USD":
        return amount
    elif currency == "RUB":
        return amount / rates["RUB_USD"]
    elif currency == "GEL":
        return amount / rates["GEL_USD"]
    elif currency == "EUR":
        return amount * rates.get("EUR_USD", 1.08)
    elif currency == "GBP":
        return amount * rates.get("GBP_USD", 1.27)
    else:
        raise ValueError(f"Unknown currency: {currency}")

def fmt_usd(amount):
    return f"${amount:,.0f}"

def fmt_num(amount):
    return f"{amount:,.0f}"

def print_section(title):
    print(f"\n{'='*50}")
    print(f" {title}")
    print('='*50)

def main():
    accounts_data = load_json("accounts.json")
    income_data = load_json("income.json")
    expenses = load_expenses()
    
    rates = accounts_data["rates"]
    
    # ========== NET WORTH ==========
    print_section("NET WORTH")
    print(f"As of: {accounts_data['updated']}")
    print(f"Rates: 1 USD = {rates['RUB_USD']} RUB | {rates['GEL_USD']} GEL")
    
    # Bank accounts
    print("\n📊 Bank Accounts:")
    bank_total_usd = 0
    for acc in accounts_data["accounts"]:
        usd_val = to_usd(acc["balance"], acc["currency"], rates)
        bank_total_usd += usd_val
        if acc["balance"] > 0:
            print(f"  {acc['name']}: {fmt_num(acc['balance'])} {acc['currency']} ({fmt_usd(usd_val)})")
    print(f"  ─────────────────────────────")
    print(f"  Bank Total: {fmt_usd(bank_total_usd)}")
    
    # Assets
    print("\n🏠 Assets:")
    assets_total_usd = 0
    for asset in accounts_data["assets"]:
        usd_val = to_usd(asset["value"], asset["currency"], rates)
        assets_total_usd += usd_val
        note = f" ({asset.get('note', '')})" if asset.get('note') else ""
        print(f"  {asset['name']}: {fmt_num(asset['value'])} {asset['currency']} ({fmt_usd(usd_val)}){note}")
    print(f"  ─────────────────────────────")
    print(f"  Assets Total: {fmt_usd(assets_total_usd)}")
    
    # Passive income assets
    print("\n📈 Passive Income:")
    for item in accounts_data["passive_income"]:
        monthly_usd = to_usd(item["monthly"], item["currency"], rates)
        print(f"  {item['name']}: {fmt_num(item['monthly'])} {item['currency']}/mo ({fmt_usd(monthly_usd)}/mo)")
    
    # Total
    total_net_worth = bank_total_usd + assets_total_usd
    print(f"\n💰 TOTAL NET WORTH: {fmt_usd(total_net_worth)}")
    
    # ========== MONTHLY CASH FLOW ==========
    print_section("MONTHLY CASH FLOW")
    
    # Income
    print("\n📥 Income:")
    income_total_usd = 0
    for inc in income_data["monthly_income"]:
        usd_val = to_usd(inc["amount"], inc["currency"], rates)
        income_total_usd += usd_val
        if inc["amount"] > 0:
            print(f"  {inc['source']}: {fmt_num(inc['amount'])} {inc['currency']} ({fmt_usd(usd_val)})")
        else:
            note = inc.get('note', 'TBD')
            print(f"  {inc['source']}: {note}")
    print(f"  ─────────────────────────────")
    print(f"  Income Total: {fmt_usd(income_total_usd)}/month")
    
    # Fixed expenses
    print("\n📤 Fixed Expenses:")
    expenses_total_usd = 0
    for exp in income_data["fixed_expenses"]:
        usd_val = to_usd(exp["amount"], exp["currency"], rates)
        expenses_total_usd += usd_val
        print(f"  {exp['item']}: {fmt_num(exp['amount'])} {exp['currency']} ({fmt_usd(usd_val)})")
    print(f"  ─────────────────────────────")
    print(f"  Fixed Total: {fmt_usd(expenses_total_usd)}/month")
    
    # Available
    available_usd = income_total_usd - expenses_total_usd
    available_gel = available_usd * rates["GEL_USD"]
    print(f"\n💵 Available for Living:")
    print(f"  {fmt_usd(available_usd)}/month")
    print(f"  {fmt_num(available_gel)} GEL/month")
    
    # ========== EXPENSE TRACKING ==========
    if len(expenses) > 1:
        print_section("EXPENSE TRACKING")

        # Date range
        dates = [datetime.strptime(e['date'], '%Y-%m-%d') for e in expenses]
        start, end = min(dates), max(dates)
        weeks  = max((end - start).days / 7.0, 1)
        months = weeks / 4.33

        # Bucket expenses
        monthly_cat = {}   # category → total USD
        yearly_items = {}  # description → total USD
        oneoff_cat  = {}   # category → total USD

        for exp in expenses:
            usd_val = to_usd(exp['amount'], exp['currency'], rates)
            cat  = exp['category']
            typ  = exp.get('type', 'monthly')

            if typ == 'yearly':
                yearly_items[exp['description']] = yearly_items.get(exp['description'], 0) + usd_val
            elif typ == 'oneoff':
                oneoff_cat[cat] = oneoff_cat.get(cat, 0) + usd_val
            else:  # monthly
                monthly_cat[cat] = monthly_cat.get(cat, 0) + usd_val

        print(f"\nPeriod: {start.strftime('%b %d')} – {end.strftime('%b %d')} ({weeks:.1f} weeks)")

        # 🔄 Monthly baseline (normalized to per-month)
        monthly_total = sum(monthly_cat.values())
        monthly_per_mo = monthly_total / months
        print(f"\n🔄 MONTHLY (per month, normalized):")
        for cat, total in sorted(monthly_cat.items(), key=lambda x: -x[1]):
            print(f"  {cat:16s} {fmt_usd(total / months):>8s}/mo")
        print(f"  ─────────────────────────────")
        print(f"  {'Baseline':16s} {fmt_usd(monthly_per_mo):>8s}/mo")

        # 📅 Yearly (amortized /12)
        yearly_per_mo = 0
        if yearly_items:
            print(f"\n📅 YEARLY (amortized /12):")
            for desc, total in sorted(yearly_items.items(), key=lambda x: -x[1]):
                per_mo = total / 12
                yearly_per_mo += per_mo
                print(f"  {desc:30s} {fmt_usd(per_mo):>6s}/mo  (paid: {fmt_usd(total)})")
            print(f"  ─────────────────────────────")
            print(f"  {'Yearly total':30s} {fmt_usd(yearly_per_mo):>6s}/mo")

        # 🎄 One-off
        oneoff_total = sum(oneoff_cat.values())
        oneoff_per_mo = oneoff_total / months if months > 0 else 0
        if oneoff_cat:
            print(f"\n🎄 ONE-OFF (this period):")
            for cat, total in sorted(oneoff_cat.items(), key=lambda x: -x[1]):
                print(f"  {cat:16s} {fmt_usd(total)}")
            print(f"  ─────────────────────────────")
            print(f"  {'Total':16s} {fmt_usd(oneoff_total)}  (avg {fmt_usd(oneoff_per_mo)}/mo)")

        # 📊 Normalized monthly
        normalized = monthly_per_mo + yearly_per_mo + oneoff_per_mo
        print(f"\n📊 NORMALIZED MONTHLY: {fmt_usd(normalized)}/mo")
        print(f"   baseline {fmt_usd(monthly_per_mo)} + yearly {fmt_usd(yearly_per_mo)} + one-off avg {fmt_usd(oneoff_per_mo)}")
    
    print("\n" + "="*50)

if __name__ == "__main__":
    main()
