export interface SHAPFactor {
  feature: string;
  impact: number;
  description: string;
}

export interface AIPredictionResponse {
  probability: number;
  risk_category: 'Low' | 'Medium' | 'High';
  top_factors: SHAPFactor[];
}

export interface AIInputData {
  activity_count_30d: number;
  days_since_last_contact: number;
  total_deal_value: number;
  interaction_score: number;
}
