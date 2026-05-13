import axios from 'axios';
import type { AIInputData, AIPredictionResponse } from '../types/ai';
import { apiUrl } from '../lib/api';

const aiBase = () => `${apiUrl('/api/v1')}/ai`;

// Get token from localStorage (assuming this is where it's stored based on common patterns)
const getAuthHeader = () => {
  const token = localStorage.getItem('token');
  return token ? { Authorization: `Bearer ${token}` } : {};
};

export const aiService = {
  async scoreLead(data: AIInputData): Promise<AIPredictionResponse> {
    const response = await axios.post(`${aiBase()}/score-lead`, data, {
      headers: getAuthHeader()
    });
    return response.data;
  },

  async predictChurn(data: AIInputData): Promise<AIPredictionResponse> {
    const response = await axios.post(`${aiBase()}/predict-churn`, data, {
      headers: getAuthHeader()
    });
    return response.data;
  },

  async analyzeContact(contactId: string): Promise<any> {
    const response = await axios.get(`${aiBase()}/analyze-contact/${contactId}`, {
      headers: getAuthHeader()
    });
    return response.data;
  }
};
