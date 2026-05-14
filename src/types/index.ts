export interface Contact {
  id: string
  name: string
  email: string
  phone: string
  company: string
  role: string
  status: 'Active' | 'Inactive' | 'Prospect'
  avatar: string
  revenue: number
  lastContact: string
  tags: string[]
  telegram_id?: string
  /** ISO 3166-1 alpha-2 */
  country_iso2?: string | null
  city?: string | null
}

export interface Lead {
  id: string
  contactId: string
  title: string
  value: number
  stage: 'New' | 'Qualified' | 'Proposal' | 'Negotiation' | 'Won' | 'Lost'
  probability: number
  source: string
  assignedTo: string
  createdAt: string
  notes: string
}

export interface Deal {
  id: string
  leadId: string
  contactId: string
  title: string
  value: number
  stage: 'New Request' | 'Qualified' | 'Discovery' | 'Proposal' | 'Negotiation' | 'Closed Won' | 'Closed Lost'
  closedAt: string | null
  userId: string | null
  /** Кто создал сделку (аудит); может совпадать с userId. */
  createdById?: string | null
  companyId: string | null
  notes?: string
}



export interface Activity {
  id: string
  type: 'call' | 'email' | 'meeting' | 'deal_won' | 'deal_lost' | 'lead_created' | 'note'
  entityType: 'contact' | 'lead' | 'deal' | 'user'
  entityId: string
  description: string
  timestamp: string
}

export interface Note {
  id: string
  dealId: string
  userId: string
  content: string
  createdAt: string
  /** Имя автора с бэкенда (если есть) */
  authorName?: string | null
}

/** Задача / напоминание по сделке */
export interface DealTask {
  id: string
  dealId: string
  title: string
  dueAt: string | null
  isDone: number
  createdBy: string | null
  createdAt: string
  /** Исполнитель (кому назначена задача) */
  assignedUserId?: string | null
}

/** Элемент списка «мои открытые задачи по сделкам» (GET /api/users/me/deal-tasks). */
export interface MyDealTaskItem {
  id: string
  dealId: string
  dealTitle: string
  title: string
  dueAt: string | null
  assignedUserId: string | null
  createdAt: string
}

export interface AIInsight {
  id: string
  entityType: 'contact' | 'lead' | 'deal' | 'user' | 'general'
  entityId: string | null
  category: 'risk' | 'opportunity' | 'coaching' | 'prediction' | 'analysis'
  title: string
  content: string
  confidence: number
  suggestions: string[]
}

export type AIMode = 'demo' | 'live'
