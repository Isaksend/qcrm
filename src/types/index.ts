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
  sellerId: string
}

export interface Seller {
  id: string
  name: string
  email: string
  avatar: string
  role: string
  dealsWon: number
  dealsClosed: number
  revenue: number
  conversionRate: number
  activeLeads: number
}

export interface Activity {
  id: string
  type: 'call' | 'email' | 'meeting' | 'deal_won' | 'deal_lost' | 'lead_created' | 'note'
  entityType: 'contact' | 'lead' | 'deal' | 'seller'
  entityId: string
  description: string
  timestamp: string
}

export interface AIInsight {
  id: string
  entityType: 'contact' | 'lead' | 'deal' | 'seller' | 'general'
  entityId: string | null
  category: 'risk' | 'opportunity' | 'coaching' | 'prediction' | 'analysis'
  title: string
  content: string
  confidence: number
  suggestions: string[]
}

export type AIMode = 'demo' | 'live'
