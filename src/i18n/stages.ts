/** Ключи API/БД → ключи в dealStages.* */
export const DEAL_STAGE_TO_I18N: Record<string, string> = {
  'New Request': 'newRequest',
  Qualified: 'qualified',
  Discovery: 'discovery',
  Proposal: 'proposal',
  Negotiation: 'negotiation',
  'Closed Won': 'closedWon',
  'Closed Lost': 'closedLost',
}

export function dealStageLabel(t: (key: string) => string, stage: string): string {
  const key = DEAL_STAGE_TO_I18N[stage]
  return key ? String(t(`dealStages.${key}`)) : stage
}
