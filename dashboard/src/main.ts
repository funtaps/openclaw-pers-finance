import './style.css'
import data from './data.json'
import type { DashboardData } from './types'
import { renderTable, initFilters } from './table'

const { expenses } = data as DashboardData

const app = document.getElementById('app')!

app.innerHTML = `
  <h1>💰 Funtov Finance</h1>
  <p class="subtitle">${expenses.length} expenses · ${new Set(expenses.map(e => e.category)).size} categories</p>
  ${renderTable(expenses)}
`

initFilters()
