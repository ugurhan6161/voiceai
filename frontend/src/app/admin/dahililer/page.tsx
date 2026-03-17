'use client'

import { useState, useEffect } from 'react'
import { api } from '@/lib/api'

interface Dahili {
  id: number
  firma_id: number
  firma_adi: string
  dahili_no: string
  kullanici_adi: string
  yonlendirme_turu: string
  aktif: boolean
  son_kayit: string | null
}

export default function DahililerPage() {
  const [dahililer, setDahililer] = useState<Dahili[]>([])
  const [loading, setLoading] = useState(true)
  const [silOnay, setSilOnay] = useState<number | null>(null)

  useEffect(() => {
    fetchDahililer()
  }, [])

  const fetchDahililer = async () => {
    try {
      const res = await api.get('/admin/dahililer')
      setDahililer(res.data)
    } catch {
      // Demo veri
      setDahililer([
        {
          id: 1, firma_id: 1, firma_adi: 'Test Otel',
          dahili_no: '101', kullanici_adi: 'firma_1_dahili',
          yonlendirme_turu: 'uygulama', aktif: true, son_kayit: null
        }
      ])
    } finally {
      setLoading(false)
    }
  }

  const dahiliSil = async (id: number) => {
    try {
      await api.delete(`/admin/dahililer/${id}`)
      setDahililer(dahililer.filter(d => d.id !== id))
      setSilOnay(null)
    } catch (err) {
      alert('Silme başarısız')
    }
  }

  if (loading) {
    return (
      <div className="flex items-center justify-center min-h-screen">
        <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600"></div>
      </div>
    )
  }

  return (
    <div className="p-6 max-w-6xl mx-auto">
      <div className="flex justify-between items-center mb-6">
        <div>
          <h1 className="text-2xl font-bold text-gray-900">📞 SIP Dahili Yönetimi</h1>
          <p className="text-gray-500 text-sm mt-1">Firma Zoiper/SIP bağlantı bilgileri</p>
        </div>
      </div>

      {/* Tablo */}
      <div className="bg-white rounded-xl shadow-sm border overflow-hidden">
        <table className="w-full">
          <thead className="bg-gray-50 border-b">
            <tr>
              <th className="text-left px-4 py-3 text-sm font-semibold text-gray-600">Firma</th>
              <th className="text-left px-4 py-3 text-sm font-semibold text-gray-600">Dahili No</th>
              <th className="text-left px-4 py-3 text-sm font-semibold text-gray-600">Kullanıcı Adı</th>
              <th className="text-left px-4 py-3 text-sm font-semibold text-gray-600">Yönlendirme</th>
              <th className="text-left px-4 py-3 text-sm font-semibold text-gray-600">Bağlantı</th>
              <th className="text-left px-4 py-3 text-sm font-semibold text-gray-600">Son Kayıt</th>
              <th className="text-left px-4 py-3 text-sm font-semibold text-gray-600">İşlem</th>
            </tr>
          </thead>
          <tbody className="divide-y">
            {dahililer.map((d) => (
              <tr key={d.id} className="hover:bg-gray-50">
                <td className="px-4 py-3">
                  <div className="font-medium text-gray-900">{d.firma_adi}</div>
                  <div className="text-xs text-gray-500">ID: {d.firma_id}</div>
                </td>
                <td className="px-4 py-3">
                  <span className="font-mono bg-gray-100 px-2 py-1 rounded text-sm">{d.dahili_no}</span>
                </td>
                <td className="px-4 py-3">
                  <span className="font-mono text-sm text-gray-700">{d.kullanici_adi}</span>
                </td>
                <td className="px-4 py-3">
                  <span className={`px-2 py-1 rounded-full text-xs font-medium ${
                    d.yonlendirme_turu === 'uygulama'
                      ? 'bg-blue-100 text-blue-700'
                      : 'bg-orange-100 text-orange-700'
                  }`}>
                    {d.yonlendirme_turu === 'uygulama' ? '📱 Uygulama' : '📞 Telefon'}
                  </span>
                </td>
                <td className="px-4 py-3">
                  <span className={`flex items-center gap-1 text-sm ${
                    d.son_kayit ? 'text-green-600' : 'text-gray-400'
                  }`}>
                    <span className={`w-2 h-2 rounded-full ${d.son_kayit ? 'bg-green-500' : 'bg-gray-300'}`}></span>
                    {d.son_kayit ? 'Bağlı' : 'Bağlı Değil'}
                  </span>
                </td>
                <td className="px-4 py-3 text-sm text-gray-500">
                  {d.son_kayit ? new Date(d.son_kayit).toLocaleString('tr-TR') : '—'}
                </td>
                <td className="px-4 py-3">
                  {silOnay === d.id ? (
                    <div className="flex gap-2">
                      <button
                        onClick={() => dahiliSil(d.id)}
                        className="px-2 py-1 bg-red-600 text-white rounded text-xs hover:bg-red-700"
                      >
                        Evet, Sil
                      </button>
                      <button
                        onClick={() => setSilOnay(null)}
                        className="px-2 py-1 bg-gray-200 text-gray-700 rounded text-xs"
                      >
                        İptal
                      </button>
                    </div>
                  ) : (
                    <button
                      onClick={() => setSilOnay(d.id)}
                      className="px-2 py-1 text-red-600 hover:bg-red-50 rounded text-xs"
                    >
                      Sil
                    </button>
                  )}
                </td>
              </tr>
            ))}
          </tbody>
        </table>

        {dahililer.length === 0 && (
          <div className="text-center py-12 text-gray-500">
            <div className="text-4xl mb-3">📞</div>
            <p>Henüz dahili hat yok</p>
            <p className="text-sm mt-1">Firma eklendiğinde otomatik oluşturulur</p>
          </div>
        )}
      </div>

      {/* Bilgi kartı */}
      <div className="mt-6 p-4 bg-blue-50 rounded-lg border border-blue-200">
        <h3 className="font-semibold text-blue-800 mb-2">ℹ️ Zoiper Bağlantı Bilgileri</h3>
        <div className="text-sm text-blue-700 space-y-1">
          <p>• <strong>Sunucu:</strong> 31.57.77.166</p>
          <p>• <strong>Port:</strong> 5060 (UDP/TCP)</p>
          <p>• <strong>Kullanıcı adı ve şifre</strong> firma panelinden görüntülenebilir</p>
          <p>• Yeni firma eklendiğinde dahili hat <strong>otomatik oluşturulur</strong></p>
        </div>
      </div>
    </div>
  )
}
