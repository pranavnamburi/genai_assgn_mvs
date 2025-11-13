import axios from 'axios';

const API_BASE_URL = 'http://localhost:8000';

// Create axios instance with default config
const api = axios.create({
  baseURL: API_BASE_URL,
  headers: {
    'Content-Type': 'application/json',
  },
});

// API Services
export const apiService = {
  // Get all stops
  getStops: async () => {
    const response = await api.get('/api/stops');
    return response.data;
  },

  // Get all paths
  getPaths: async () => {
    const response = await api.get('/api/paths');
    return response.data;
  },

  // Get all routes
  getRoutes: async () => {
    const response = await api.get('/api/routes');
    return response.data;
  },

  // Get all vehicles
  getVehicles: async () => {
    const response = await api.get('/api/vehicles');
    return response.data;
  },

  // Get all drivers
  getDrivers: async () => {
    const response = await api.get('/api/drivers');
    return response.data;
  },

  // Get all trips with deployment info
  getTrips: async () => {
    const response = await api.get('/api/trips');
    return response.data;
  },

  // Chat endpoint (already exists in MoviChat)
  sendChatMessage: async (formData) => {
    const response = await api.post('/api/chat', formData, {
      headers: {
        'Content-Type': 'multipart/form-data',
      },
    });
    return response.data;
  },
};

export default api;

