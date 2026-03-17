'use client'

import { useEffect, useState } from 'react'
import { useRouter } from 'next/navigation'
import { firmaApi } from '@/lib/api'

export default function AjanPage() {
  const router = useRouter()
  const [data, setData] = useState<Record<string, unknown> | null>(null)
  const [mesaj, setMesaj] = useState('')
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    if (!localStorage.getItem('access_token')) { router.push('/firma/login'); return }
    firmaApi.ajanGetir()
      .then(res => setData(res.data))
      .catch(() => router.push('/firma/login'))
      .finally(() => setLoading(false))
  }, [router])

  const kaydet = async () => {
    try {
      await firmaApi.ajanGuncelle(data || {})
      setMesaj('✅ Ajan ayarları kaydedildi')
    } catch {
      setMesaj('❌ Kaydetme başarısız')
    }
  }

  if (loading) return <div className="min-h-screen flex items-center justify-center text-gray-500">Yükleniyor...</div>

  return (
    <div className="min-h-screen bg-gray-50">
      <header className="bg-white border-b px-6 py-4 flex items-center gap-3">
        <a href="/firma/dashboard" className="text-gray-500 hover:text-gray-700">← Dashboard</a>
        <h1 className="font-bold text-gray-900">Ajan Ayarları</h1>
      </header>
      <main className="max-w-2xl mx-auto px-6 py-8">
        {mesaj && <div className={`px-4 py-3 rounded-lg mb-4 text-sm ${mesaj.startsWith('✅') ? 'bg-green-50 text-green-700 border border-green-200' : 'bg-red-50 text-red-700 border border-red-200'}`}>{mesaj}</div>}
        <div className="bg-white rounded-xl border p-6 space-y-4">
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">Firma Adı</label>
            <input value={data?.firma_adi as string || ''} readOnly
              className="w-full border rounded-lg px-3 py-2 text-sm bg-gray-50" />
          </div>
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">Sektör / Şablon</label>
            <input value={data?.sektor as string || ''} readOnly
              className="w-full border rounded-lg px-3 py-2 text-sm bg-gray-50" />
          </div>
          <div className="pt-2">
            <p className="text-sm text-gray-500 mb-4">
              Ajan ayarları şablon tarafından yönetilmektedir. Karşılama metni ve ses ayarları için destek ekibiyle iletişime geçin.
            </p>
            <div className="bg-blue-50 border border-blue-200 rounded-lg p-4">
              <p className="text-sm text-blue-700">
                <strong>Aktif Şablon:</strong> {data?.sektor as string || 'Belirlenmemiş'}<br/>
                <strong>Schema:</strong> {data?.schema as string || '-'}
              </p>
            </div>
          </div>
          <button onClick={kaydet} className="w-full bg-indigo-600 text-white py-2 rounded-lg text-sm font-medium hover:bg-indigo-700">
            Kaydet
          </button>
        </div>
      </main>
    </div>
  )
}
