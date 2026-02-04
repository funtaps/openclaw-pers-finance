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
    if len(expenses) > 1:  # More than just the example
        print_section("EXPENSE TRACKING")
        
        # Group by category
        by_category = {}
        total_tracked = 0
        for exp in expenses:
            if exp['description'].startswith('Example:'):
                continue
            cat = exp['category']
            usd_val = to_usd(exp['amount'], exp['currency'], rates)
            by_category[cat] = by_category.get(cat, 0) + usd_val
            total_tracked += usd_val
        
        if by_category:
            print("\n📋 Spending by Category:")
            for cat, amount in sorted(by_category.items(), key=lambda x: -x[1]):
                print(f"  {cat}: {fmt_usd(amount)}")
            print(f"  ─────────────────────────────")
            print(f"  Total Tracked: {fmt_usd(total_tracked)}")
    
    print("\n" + "="*50)

if __name__ == "__main__":
    main()
