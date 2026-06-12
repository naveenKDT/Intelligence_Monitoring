import axios from 'axios'

const API_BASE_URL = import.meta.env.VITE_API_URL || '/api/v1'

const api = axios.create({
  baseURL: API_BASE_URL,
  headers: {
    'Content-Type': 'application/json',
  },
})

// Request interceptor
api.interceptors.request.use(
  (config) => {
    // Add auth token if available
    const token = localStorage.getItem('auth_token')
    if (token) {
      config.headers.Authorization = `Bearer ${token}`
    }
    return config
  },
  (error) => {
    return Promise.reject(error)
  }
)

// Response interceptor
api.interceptors.response.use(
  (response) => response,
  (error) => {
    if (error.response?.status === 401) {
      localStorage.removeItem('auth_token')
      window.location.href = '/login'
    }
    return Promise.reject(error)
  }
)

// Companies API
export const companiesApi = {
  list: (params?: {
    page?: number
    page_size?: number
    search?: string
    industry?: string
    country?: string
    city?: string
    status?: string
    is_monitored?: boolean
  }) => api.get('/companies', { params }),

  get: (id: string) => api.get(`/companies/${id}`),

  create: (data: any) => api.post('/companies', data),

  update: (id: string, data: any) => api.put(`/companies/${id}`, data),

  delete: (id: string) => api.delete(`/companies/${id}`),

  getProducts: (id: string) => api.get(`/companies/${id}/products`),

  getServices: (id: string) => api.get(`/companies/${id}/services`),

  getLeadership: (id: string) => api.get(`/companies/${id}/leadership`),

  getLocations: (id: string) => api.get(`/companies/${id}/locations`),

  getNews: (id: string) => api.get(`/companies/${id}/news`),

  getDocuments: (id: string) => api.get(`/companies/${id}/documents`),

  getSnapshots: (id: string) => api.get(`/companies/${id}/snapshots`),

  getChanges: (id: string) => api.get(`/companies/${id}/changes`),

  createSnapshot: (id: string) => api.post(`/companies/${id}/snapshots`),

  getChatHistory: (id: string) => api.get(`/companies/${id}/chat`),
}

// Search API
export const searchApi = {
  search: (params: {
    q: string
    entity_type?: string
    industry?: string
    domain?: string
    country?: string
    city?: string
    limit?: number
    offset?: number
    use_semantic?: boolean
  }) => api.get('/search', { params }),

  searchCompanies: (params: {
    q: string
    industry?: string
    domain?: string
    country?: string
    city?: string
    technology?: string
    limit?: number
  }) => api.get('/search/companies', { params }),

  findSimilar: (id: string, limit?: number) =>
    api.get(`/search/similar/${id}`, { params: { limit } }),

  searchIndustries: (q: string) => api.get('/search/industries', { params: { q } }),

  searchDomains: (q: string) => api.get('/search/domains', { params: { q } }),

  searchTechnologies: (q: string) => api.get('/search/technologies', { params: { q } }),
}

// Intelligence API
export const intelligenceApi = {
  extract: (data: { content: string; content_type: string; company_id?: string }) =>
    api.post('/intelligence/extract', data),

  classify: (data: { company_id: string; classification_type: string }) =>
    api.post('/intelligence/classify', data),

  getSummary: (companyId: string) => api.get(`/intelligence/summary/${companyId}`),

  chat: (data: { message: string; company_id?: string }) => api.post('/chat', data),

  getChatHistory: (companyId: string) => api.get(`/chat/history/${companyId}`),
}

// Monitoring API
export const monitoringApi = {
  getMonitoredCompanies: (limit?: number) =>
    api.get('/monitoring/companies', { params: { limit } }),

  enableMonitoring: (companyId: string) =>
    api.post(`/monitoring/companies/${companyId}/enable`),

  disableMonitoring: (companyId: string) =>
    api.post(`/monitoring/companies/${companyId}/disable`),

  triggerScrape: (companyId?: string, url?: string) =>
    api.post('/monitoring/scrape', {}, { params: { company_id: companyId, url } }),

  getChanges: (params?: { limit?: number; severity?: string; change_type?: string; days?: number }) =>
    api.get('/monitoring/changes', { params }),

  getCompanyChanges: (companyId: string, limit?: number) =>
    api.get(`/monitoring/changes/company/${companyId}`, { params: { limit } }),

  checkCompanyChanges: (companyId: string) =>
    api.post(`/monitoring/check-changes/${companyId}`),
}

// Dashboard API
export const dashboardApi = {
  getExecutive: () => api.get('/dashboard/executive'),

  getIndustry: () => api.get('/dashboard/industry'),

  getCompany: (companyId: string) => api.get(`/dashboard/company/${companyId}`),
}

export default api