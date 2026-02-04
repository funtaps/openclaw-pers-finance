# Household Finance Tracker

## Quick Start

Run report:
```bash
python3 calc.py
```

## Files

| File | Purpose | How to update |
|------|---------|---------------|
| `accounts.json` | Bank balances, assets, exchange rates | Edit balances monthly |
| `income.json` | Monthly income & fixed expenses | Edit when income changes |
| `expenses.csv` | Daily expense log | Append new lines |
| `calc.py` | Calculator script | Don't edit (unless adding features) |

## Tracking Expenses

Add a line to `expenses.csv`:
```
2026-02-03,Groceries at Carrefour,85,GEL,Food
2026-02-03,Taxi to work,15,GEL,Transport
```

Format: `date,description,amount,currency,category`

### Categories
- Food
- Transport
- Utilities
- Entertainment
- Health
- Kid
- Pets
- Clothes
- Home
- Other

## Updating Balances

Edit `accounts.json`:
1. Update `"updated"` date
2. Update `"rates"` if exchange rates changed significantly
3. Update account `"balance"` values

## Adding Sasha's Data

After finance talk:
1. Add her accounts to `accounts.json` → `"accounts"` array
2. Update her salary in `income.json` → `"monthly_income"`

## Tips

- Update exchange rates monthly (or when they move >5%)
- Update bank balances monthly (before net worth review)
- Log expenses >50 GEL daily
- Run `python3 calc.py` anytime to see current status
