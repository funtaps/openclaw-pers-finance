export interface Expense {
  date: string
  description: string
  amount: number
  currency: string
  category: string
  type: 'monthly' | 'yearly' | 'oneoff'
}

export interface Account {
  name: string
  currency: string
  balance: number
  note?: string
}

export interface Asset {
  name: string
  currency: string
  value: number
  note?: string
}

export interface PassiveIncome {
  name: string
  currency: string
  monthly: number
  note?: string
}

export interface AccountsData {
  updated: string
  rates: Record<string, number>
  accounts: Account[]
  assets: Asset[]
  passive_income: PassiveIncome[]
}

export interface IncomeItem {
  source: string
  currency: string
  amount: number
  note?: string
}

export interface FixedExpense {
  item: string
  currency: string
  amount: number
}

export interface IncomeData {
  updated: string
  monthly_income: IncomeItem[]
  fixed_expenses: FixedExpense[]
}

export interface DashboardData {
  expenses: Expense[]
  accounts: AccountsData
  income: IncomeData
}
