import axios from 'axios';
import { apiUrl } from '../lib/api';

const analyticsBase = () => `${apiUrl('/api/v1')}/analytics`;

const getAuthHeader = () => {
  const token = localStorage.getItem('token');
  return token ? { Authorization: `Bearer ${token}` } : {};
};

export const analyticsService = {
  async getSalesVelocity() {
    const response = await axios.get(`${analyticsBase()}/sales-velocity`, {
      headers: getAuthHeader()
    });
    return response.data;
  },

  async getCommunicationStats() {
    const response = await axios.get(`${analyticsBase()}/communication-stats`, {
      headers: getAuthHeader()
    });
    return response.data;
  },

  async getContactsByCountry() {
    const response = await axios.get(`${analyticsBase()}/contacts-by-country`, {
      headers: getAuthHeader()
    });
    return response.data;
  },

  async getContactsByCity() {
    const response = await axios.get(`${analyticsBase()}/contacts-by-city`, {
      headers: getAuthHeader()
    });
    return response.data;
  },

  async getFunnelConversions() {
    const response = await axios.get(`${analyticsBase()}/funnel-conversions`, {
      headers: getAuthHeader()
    });
    return response.data as { edges: { from_stage: string; to_stage: string; count: number; conversion_rate: number }[]; events: number };
  },

  async getChurnRiskDistribution(limit = 80) {
    const response = await axios.get(`${analyticsBase()}/churn-risk-distribution`, {
      headers: getAuthHeader(),
      params: { limit }
    });
    return response.data as { buckets: Record<string, number>; total_scored: number; model_loaded: boolean };
  }
};
