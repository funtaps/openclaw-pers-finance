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

// ─── State ───────────────────────────────────────────────────────────────────
let allExpenses: Expense[] = []
let activeCategories = new Set<string>()
let activeTypes       = new Set<string>(['monthly', 'yearly', 'oneoff'])
let dateFrom = ''
let dateTo   = ''

// ─── Helpers ─────────────────────────────────────────────────────────────────
function esc(s: string) {
  return s.replace(/&/g,'&amp;').replace(/</g,'&lt;').replace(/>/g,'&gt;').replace(/"/g,'&quot;')
}

function filtered(): Expense[] {
  return allExpenses.filter(e =>
    activeCategories.has(e.category) &&
    activeTypes.has(e.type) &&
    e.date >= dateFrom &&
    e.date <= dateTo
  )
}

// ─── Render pieces ───────────────────────────────────────────────────────────
function renderRows(expenses: Expense[]): string {
  if (expenses.length === 0) {
    return '<tr><td colspan="6" class="empty">No expenses match the filters</td></tr>'
  }
  return [...expenses]
    .sort((a, b) => b.date.localeCompare(a.date))
    .map(exp => {
      const color = CATEGORY_COLORS[exp.category] || '#6b7280'
      return `<tr>
        <td class="col-date">${exp.date}</td>
        <td class="col-desc" title="${esc(exp.description)}">${esc(exp.description)}</td>
        <td class="col-amount">${exp.amount.toFixed(2)}</td>
        <td class="col-currency">${exp.currency}</td>
        <td class="col-cat"><span class="badge" style="background:${color}18;color:${color};border-color:${color}40">${exp.category}</span></td>
        <td class="col-type"><span class="badge type">${TYPE_LABELS[exp.type] || exp.type}</span></td>
      </tr>`
    })
    .join('\n')
}

function renderTotals(expenses: Expense[]): string {
  const totals: Record<string, number> = {}
  expenses.forEach(e => { totals[e.currency] = (totals[e.currency] || 0) + e.amount })
  const parts = Object.entries(totals)
    .sort((a, b) => b[1] - a[1])
    .map(([cur, amt]) => `<span class="total-item">${amt.toFixed(2)} <strong>${cur}</strong></span>`)
    .join('')
  return parts
}

// ─── Full render ─────────────────────────────────────────────────────────────
export function renderTable(expenses: Expense[]): string {
  allExpenses = expenses
  activeCategories = new Set(expenses.map(e => e.category))

  const dates = expenses.map(e => e.date).sort()
  dateFrom = dates[0]
  dateTo   = dates[dates.length - 1]

  const categories = [...new Set(expenses.map(e => e.category))].sort()
  const catPills = categories.map(c => {
    const color = CATEGORY_COLORS[c] || '#6b7280'
    return `<button class="pill active" data-filter="category" data-value="${c}" style="--pill-color:${color}">${c}</button>`
  }).join('')

  const typePills = ['monthly','yearly','oneoff'].map(t =>
    `<button class="pill active" data-filter="type" data-value="${t}">${TYPE_LABELS[t]}</button>`
  ).join('')

  const currentFiltered = filtered()

  return `
    <div class="filters">
      <div class="filter-group">
        <label>Category</label>
        <div class="pills">${catPills}</div>
      </div>
      <div class="filter-group">
        <label>Type</label>
        <div class="pills">${typePills}</div>
      </div>
      <div class="filter-group">
        <label>Date</label>
        <div class="date-range">
          <input type="date" id="date-from" value="${dateFrom}" />
          <span>–</span>
          <input type="date" id="date-to" value="${dateTo}" />
        </div>
      </div>
      <button class="btn-reset" id="reset-filters">Reset</button>
    </div>

    <div class="card">
      <div class="table-header">
        <h2>📋 Expenses</h2>
        <div class="table-meta">
          <span class="table-totals" id="table-totals">${renderTotals(currentFiltered)}</span>
          <span class="table-count" id="table-count">${currentFiltered.length} items</span>
        </div>
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
          <tbody id="table-body">${renderRows(currentFiltered)}</tbody>
        </table>
      </div>
    </div>
  `
}

// ─── Init filters ────────────────────────────────────────────────────────────
export function initFilters() {
  const pills      = document.querySelectorAll<HTMLButtonElement>('.pill')
  const fromInput  = document.getElementById('date-from') as HTMLInputElement
  const toInput    = document.getElementById('date-to')   as HTMLInputElement
  const resetBtn   = document.getElementById('reset-filters')!
  const tbody      = document.getElementById('table-body')!
  const countEl    = document.getElementById('table-count')!
  const totalsEl   = document.getElementById('table-totals')!

  function update() {
    const result = filtered()
    tbody.innerHTML   = renderRows(result)
    countEl.textContent = `${result.length} items`
    totalsEl.innerHTML  = renderTotals(result)
  }

  // Pill toggles
  pills.forEach(pill => {
    pill.addEventListener('click', () => {
      const filterName = pill.dataset.filter!
      const value      = pill.dataset.value!
      const set        = filterName === 'category' ? activeCategories : activeTypes

      if (set.has(value)) { set.delete(value); pill.classList.remove('active') }
      else                { set.add(value);    pill.classList.add('active')    }
      update()
    })
  })

  // Date inputs
  fromInput.addEventListener('input', () => { dateFrom = fromInput.value; update() })
  toInput.addEventListener('input',   () => { dateTo   = toInput.value;   update() })

  // Reset
  resetBtn.addEventListener('click', () => {
    activeCategories = new Set(allExpenses.map(e => e.category))
    activeTypes      = new Set(['monthly', 'yearly', 'oneoff'])
    const dates      = allExpenses.map(e => e.date).sort()
    dateFrom = dates[0]; dateTo = dates[dates.length - 1]
    fromInput.value = dateFrom; toInput.value = dateTo
    pills.forEach(p => p.classList.add('active'))
    update()
  })
}
