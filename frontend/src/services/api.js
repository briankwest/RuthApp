import axios from 'axios';

const api = axios.create({
  baseURL: import.meta.env.VITE_API_URL || '',
  headers: {
    'Content-Type': 'application/json',
  },
});

// Add auth token to requests
api.interceptors.request.use((config) => {
  const token = localStorage.getItem('access_token');
  if (token) {
    config.headers.Authorization = `Bearer ${token}`;
  }
  return config;
});

// Handle token refresh on 401
api.interceptors.response.use(
  (response) => response,
  async (error) => {
    const originalRequest = error.config;

    if (error.response?.status === 401 && !originalRequest._retry) {
      originalRequest._retry = true;

      try {
        const refreshToken = localStorage.getItem('refresh_token');
        const response = await axios.post(
          `${import.meta.env.VITE_API_URL || ''}/api/auth/refresh`,
          { refresh_token: refreshToken }
        );

        const { access_token, refresh_token: new_refresh_token } = response.data;
        localStorage.setItem('access_token', access_token);
        if (new_refresh_token) {
          localStorage.setItem('refresh_token', new_refresh_token);
        }

        originalRequest.headers.Authorization = `Bearer ${access_token}`;
        return api(originalRequest);
      } catch (refreshError) {
        localStorage.removeItem('access_token');
        localStorage.removeItem('refresh_token');
        window.location.href = '/login';
        return Promise.reject(refreshError);
      }
    }

    return Promise.reject(error);
  }
);

export default api;

// Auth API
export const authAPI = {
  login: (email, password) => api.post('/api/auth/login', { email, password }),
  register: (data) => api.post('/api/auth/register', data),
  logout: () => api.post('/api/auth/logout'),
  getProfile: () => api.get('/api/auth/me'),
  updateProfile: (data) => api.put('/api/auth/profile', data),
};

// Representatives API
export const repsAPI = {
  lookupByAddress: (address) => api.post('/api/representatives/lookup', address),
  getRepresentatives: () => api.get('/api/representatives'),
  getRepresentative: (id) => api.get(`/api/representatives/${id}`),
  saveRepresentative: (repData) => api.post('/api/representatives/save', repData),
  getSavedRepresentatives: () => api.get('/api/representatives/saved'),
  removeSavedRepresentative: (repId) => api.delete(`/api/representatives/saved/${repId}`),
  saveAddress: (addressData) => api.post('/api/representatives/save-address', addressData),
  getUserAddresses: () => api.get('/api/representatives/user-addresses'),
  deleteAddress: (addressId) => api.delete(`/api/representatives/user-addresses/${addressId}`),
};

// Letters API
export const lettersAPI = {
  // Writing Profiles
  getWritingProfiles: () => api.get('/api/letters/writing-profiles'),
  createWritingProfile: (data) => api.post('/api/letters/writing-profiles', data),
  updateWritingProfile: (id, data) => api.put(`/api/letters/writing-profiles/${id}`, data),
  deleteWritingProfile: (id) => api.delete(`/api/letters/writing-profiles/${id}`),
  analyzeWriting: (samples) => api.post('/api/letters/writing-profiles/analyze', { writing_samples: samples }),
  generateDescription: (data) => api.post('/api/letters/writing-profiles/generate-description', data),
  previewWritingProfile: (id) => api.post(`/api/letters/writing-profiles/${id}/preview`),
  getPoliticalIssues: () => api.get('/api/letters/political-issues'),

  // Articles
  fetchArticles: (urls) => api.post('/api/letters/fetch-articles', { urls }),
  generateFocusOptions: (urls) => api.post('/api/letters/generate-focus-options', { article_urls: urls }),
  generateTopicSuggestions: (urls) => api.post('/api/letters/generate-topic-suggestions', { article_urls: urls }),

  // Letter Generation
  generateLetter: (data) => api.post('/api/letters/generate', data),
  getLetters: (params) => api.get('/api/letters/', { params }),
  getLetter: (id) => api.get(`/api/letters/${id}`),
  refineLetter: (id, feedback) => api.post(`/api/letters/${id}/refine`, { feedback }),
  updateRecipientContent: (letterId, recipientId, content) =>
    api.patch(`/api/letters/${letterId}/recipients/${recipientId}`, { content }),
  improveText: (text, improvementType, customPrompt = null) =>
    api.post('/api/letters/improve-text', {
      text,
      improvement_type: improvementType,
      custom_prompt: customPrompt
    }),
  finalizeLetter: (id) => api.put(`/api/letters/${id}/finalize`),
  updateLetterStatus: (id, status) => api.patch(`/api/letters/${id}/status`, { status }),
  deleteLetter: (id) => api.delete(`/api/letters/${id}`),

  // PDF Generation
  generatePDF: (letterId, recipientId, options = {}) =>
    api.post(`/api/letters/${letterId}/recipients/${recipientId}/generate-pdf`, {
      include_email: options.include_email || false,
      include_phone: options.include_phone || false
    }),
  generateAllPDFs: (letterId, options = {}) =>
    api.post(`/api/letters/${letterId}/generate-all-pdfs`, {
      include_email: options.include_email || false,
      include_phone: options.include_phone || false
    }),
};

// Delivery API
export const deliveryAPI = {
  getDeliveryOptions: (letterId) =>
    api.get(`/api/delivery/letters/${letterId}/delivery-options`),
  getRecipientDeliveryOptions: (letterId, recipientId) =>
    api.get(`/api/delivery/letters/${letterId}/recipients/${recipientId}/delivery-options`),

  sendFax: (letterId, recipientId, faxNumber) =>
    api.post(`/api/delivery/letters/${letterId}/recipients/${recipientId}/send-fax`, { fax_number: faxNumber }),
  sendEmail: (letterId, recipientId, emailAddress) =>
    api.post(`/api/delivery/letters/${letterId}/recipients/${recipientId}/send-email`, { email_address: emailAddress }),

  getFaxStatus: (faxSid) => api.get(`/api/delivery/fax/${faxSid}/status`),
  getDeliveryStatus: (letterId) => api.get(`/api/delivery/letters/${letterId}/delivery-status`),
  getRecipientDeliveryStatus: (letterId, recipientId) =>
    api.get(`/api/delivery/letters/${letterId}/recipients/${recipientId}/delivery-status`),
};
