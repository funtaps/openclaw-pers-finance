/**
 * Reads finance/*.csv + *.json → outputs src/data.json for the dashboard.
 * Run: tsx scripts/prepare-data.ts
 */
import { readFileSync, writeFileSync } from 'node:fs'
import { resolve, dirname } from 'node:path'
import { fileURLToPath } from 'node:url'

const __dirname     = dirname(fileURLToPath(import.meta.url))
const FINANCE_DIR   = resolve(__dirname, '..', '..', 'finance')
const OUTPUT_PATH   = resolve(__dirname, '..', 'src', 'data.json')

// ─── Output stub for chunk 1 ─────────────────────────────────────────────────
const data = {
  expenses: [] as Record<string, string>[],
  accounts: {} as Record<string, unknown>,
  income:   {} as Record<string, unknown>,
}

writeFileSync(OUTPUT_PATH, JSON.stringify(data, null, 2))
console.log('✓ data.json generated')
