import './style.css'
import data from './data.json'
import type { DashboardData } from './types'

const { expenses } = data as DashboardData

const app = document.getElementById('app')!

app.innerHTML = `
  <h1>💰 Funtov Finance</h1>
  <p class="subtitle">${expenses.length} expenses loaded · ${new Set(expenses.map(e => e.category)).size} categories</p>
`
