/**
 * Reads finance/*.csv + *.json → outputs src/data.json for the dashboard.
 * Run: tsx scripts/prepare-data.ts
 */
import { readFileSync, writeFileSync } from 'node:fs'
import { resolve, dirname } from 'node:path'
import { fileURLToPath } from 'node:url'

const __dirname   = dirname(fileURLToPath(import.meta.url))
const FINANCE_DIR = resolve(__dirname, '..', '..', 'finance')
const OUTPUT      = resolve(__dirname, '..', 'src', 'data.json')

// ─── CSV Parser ──────────────────────────────────────────────────────────────
function parseLine(line: string): string[] {
  const fields: string[] = []
  let current = ''
  let inQuotes = false

  for (const char of line) {
    if (char === '"')           { inQuotes = !inQuotes; continue }
    if (char === ',' && !inQuotes) { fields.push(current); current = ''; continue }
    current += char
  }
  fields.push(current)
  return fields
}

function parseCSV(content: string) {
  const lines   = content.trim().split('\n')
  const headers = parseLine(lines[0]).map(h => h.trim())

  return lines.slice(1).filter(l => l.trim()).map(line => {
    const values = parseLine(line)
    const obj: Record<string, string> = {}
    headers.forEach((h, i) => { obj[h] = (values[i] || '').trim() })
    return obj
  })
}

// ─── Read & transform ────────────────────────────────────────────────────────
const expensesRaw = parseCSV(
  readFileSync(resolve(FINANCE_DIR, 'expenses.csv'), 'utf-8')
)

const expenses = expensesRaw.map(row => ({
  date:        row.date,
  description: row.description,
  amount:      parseFloat(row.amount),
  currency:    row.currency,
  category:    row.category,
  type:        row.type || 'monthly',
}))

const accounts = JSON.parse(
  readFileSync(resolve(FINANCE_DIR, 'accounts.json'), 'utf-8')
)
const income = JSON.parse(
  readFileSync(resolve(FINANCE_DIR, 'income.json'), 'utf-8')
)

// ─── Output ──────────────────────────────────────────────────────────────────
const data = { expenses, accounts, income }
writeFileSync(OUTPUT, JSON.stringify(data, null, 2))

console.log(`✓ data.json — ${expenses.length} expenses, ${accounts.accounts.length} accounts`)
