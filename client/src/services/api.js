import axios from 'axios';

const API_BASE_URL = 'http://localhost:8000/api';

const apiClient = axios.create({
  baseURL: API_BASE_URL,
  headers: {
    'Content-Type': 'application/json',
  },
  timeout: 90000, // 90 seconds timeout for repository cloning & analysis
});

export const analyzeRepository = async (githubUrl) => {
  try {
    const response = await apiClient.post('/analyze', { github_url: githubUrl });
    return response.data;
  } catch (error) {
    if (error.response && error.response.data && error.response.data.detail) {
      throw new Error(error.response.data.detail);
    }
    throw new Error(error.message || 'Failed to connect to CodeLens backend server.');
  }
};

export const checkHealth = async () => {
  try {
    const response = await apiClient.get('/health');
    return response.data;
  } catch (error) {
    return { status: 'error', message: error.message };
  }
};
