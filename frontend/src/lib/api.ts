/**
 * VoiceAI Platform — API Client
 * Tüm backend API çağrıları bu modül üzerinden yapılır.
 */
import axios from 'axios'

const API_URL = process.env.NEXT_PUBLIC_API_URL || '/api'

export const api = axios.create({
  baseURL: API_URL,
  headers: { 'Content-Type': 'application/json' },
})

// Request interceptor: JWT token ekle
api.interceptors.request.use((config) => {
  if (typeof window !== 'undefined') {
    const token = localStorage.getItem('access_token')
    if (token) {
      config.headers.Authorization = `Bearer ${token}`
    }
  }
  return config
})

// Response interceptor: 401 → login'e yönlendir
api.interceptors.response.use(
  (response) => response,
  async (error) => {
    if (error.response?.status === 401 && typeof window !== 'undefined') {
      localStorage.removeItem('access_token')
      localStorage.removeItem('refresh_token')
      localStorage.removeItem('user')
      window.location.href = '/admin/login'
    }
    return Promise.reject(error)
  }
)

// ── Auth ──────────────────────────────────────────────────────
export const authApi = {
  login: (email: string, password: string) =>
    api.post('/auth/login', new URLSearchParams({ username: email, password }), {
      headers: { 'Content-Type': 'application/x-www-form-urlencoded' },
    }),
  me: () => api.get('/auth/me'),
  refresh: (token: string) => api.post('/auth/refresh', { refresh_token: token }),
}

// ── Admin ─────────────────────────────────────────────────────
export const adminApi = {
  dashboard: () => api.get('/admin/dashboard'),
  firmalar: (params?: { durum?: string; sektor?: string }) =>
    api.get('/admin/firmalar', { params }),
  firmaOlustur: (data: Record<string, unknown>) => api.post('/admin/firmalar', data),
  firmaDurdur: (id: number) => api.put(`/admin/firmalar/${id}/durdur`),
  firmaAktif: (id: number) => api.put(`/admin/firmalar/${id}/aktif`),
  firmaSil: (id: number) => api.delete(`/admin/firmalar/${id}`),
  firmaDetay: (id: number) => api.get(`/admin/firmalar/${id}`),
  gelirRaporu: () => api.get('/admin/raporlar/gelir'),
  cagriRaporu: () => api.get('/admin/raporlar/cagrilar'),
}

// ── Firma Panel ───────────────────────────────────────────────
export const firmaApi = {
  dashboard: () => api.get('/firma/dashboard'),
  ajanGetir: () => api.get('/firma/ajan'),
  ajanGuncelle: (data: Record<string, unknown>) => api.put('/firma/ajan', data),
  hizmetler: () => api.get('/firma/hizmetler'),
  cagrilar: (params?: { sayfa?: number; limit?: number }) =>
    api.get('/firma/cagrilar', { params }),
  faturalar: () => api.get('/firma/faturalar'),
  entegrasyonGetir: () => api.get('/firma/entegrasyon'),
  entegrasyonGuncelle: (data: Record<string, unknown>) => api.put('/firma/entegrasyon', data),
}

// ── Ayarlar ───────────────────────────────────────────────────
export const ayarlarApi = {
  sipGetir: (saglayici: string) => api.get(`/api/ayarlar/sistem/sip_${saglayici}`),
  sipKaydet: (saglayici: string, data: Record<string, unknown>) =>
    api.put(`/api/ayarlar/sistem/sip/${saglayici}`, data),
  smsKaydet: (data: Record<string, unknown>) => api.put('/api/ayarlar/sistem/sms/netgsm', data),
  iyzicoKaydet: (data: Record<string, unknown>) => api.put('/api/ayarlar/sistem/iyzico', data),
  smtpKaydet: (data: Record<string, unknown>) => api.put('/api/ayarlar/sistem/smtp', data),
  test: (tur: string, ayarlar: Record<string, unknown>) =>
    api.post('/api/ayarlar/test', { tur, ayarlar }),
}

// ── Şablonlar ─────────────────────────────────────────────────
export const sablonApi = {
  liste: () => api.get('/api/sablonlar/'),
  detay: (kod: string) => api.get(`/api/sablonlar/${kod}`),
  ata: (firma_id: number, sablon_kodu: string) =>
    api.post('/api/sablonlar/ata', { firma_id, sablon_kodu }),
}
