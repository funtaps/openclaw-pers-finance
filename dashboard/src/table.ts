import type { Expense } from './types'

// ─── Config ──────────────────────────────────────────────────────────────────
const CATEGORY_COLORS: Record<string, string> = {
  Food:          '#22c55e',
  Transport:     '#3b82f6',
  Utilities:     '#f59e0b',
  Entertainment: '#8b5cf6',
  Health:        '#ec4899',
  Kid:           '#06b6d4',
  Pets:          '#f97316',
  Clothes:       '#84cc16',
  Home:          '#14b8a6',
  Other:         '#6b7280',
  Rent:          '#ef4444',
  Cash:          '#9ca3af',
}

const TYPE_LABELS: Record<string, string> = {
  monthly: '🔄 monthly',
  yearly:  '📅 yearly',
  oneoff:  '🎄 one-off',
}

// ─── Render ──────────────────────────────────────────────────────────────────
export function renderTable(expenses: Expense[]): string {
  const sorted = [...expenses].sort((a, b) => b.date.localeCompare(a.date))

  const rows = sorted.map(exp => {
    const color = CATEGORY_COLORS[exp.category] || '#6b7280'
    return `<tr>
      <td class="col-date">${exp.date}</td>
      <td class="col-desc" title="${esc(exp.description)}">${esc(exp.description)}</td>
      <td class="col-amount">${exp.amount.toFixed(2)}</td>
      <td class="col-currency">${exp.currency}</td>
      <td class="col-cat"><span class="badge" style="background:${color}18;color:${color};border-color:${color}40">${exp.category}</span></td>
      <td class="col-type"><span class="badge type">${TYPE_LABELS[exp.type] || exp.type}</span></td>
    </tr>`
  }).join('\n')

  return `<div class="card">
    <div class="table-header">
      <h2>📋 Expenses</h2>
      <span class="table-count">${expenses.length} items</span>
    </div>
    <div class="table-wrap">
      <table>
        <thead>
          <tr>
            <th>Date</th>
            <th>Description</th>
            <th class="right">Amount</th>
            <th>Currency</th>
            <th>Category</th>
            <th>Type</th>
          </tr>
        </thead>
        <tbody>${rows}</tbody>
      </table>
    </div>
  </div>`
}

function esc(s: string) {
  return s.replace(/&/g,'&amp;').replace(/</g,'&lt;').replace(/>/g,'&gt;').replace(/"/g,'&quot;')
}
