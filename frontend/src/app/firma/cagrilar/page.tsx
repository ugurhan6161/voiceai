'use client'

import { useEffect, useState } from 'react'
import { useRouter } from 'next/navigation'
import { firmaApi } from '@/lib/api'

export default function CagrilarPage() {
  const router = useRouter()
  const [data, setData] = useState<Record<string, unknown> | null>(null)
  const [loading, setLoading] = useState(true)
  const [seciliCagri, setSeciliCagri] = useState<Record<string, unknown> | null>(null)

  useEffect(() => {
    if (!localStorage.getItem('access_token')) { router.push('/firma/login'); return }
    firmaApi.cagrilar({ sayfa: 1, limit: 50 })
      .then(res => setData(res.data))
      .catch(() => router.push('/firma/login'))
      .finally(() => setLoading(false))
  }, [router])

  const sonucRenk = (sonuc: string) => {
    if (sonuc === 'rezervasyon') return 'bg-green-100 text-green-700'
    if (sonuc === 'aktarim') return 'bg-blue-100 text-blue-700'
    if (sonuc === 'basarisiz') return 'bg-red-100 text-red-700'
    return 'bg-gray-100 text-gray-600'
  }

  if (loading) return <div className="min-h-screen flex items-center justify-center text-gray-500">Yükleniyor...</div>

  const cagrilar = (data?.cagrilar as Record<string, unknown>[]) || []

  return (
    <div className="min-h-screen bg-gray-50">
      <header className="bg-white border-b px-6 py-4 flex items-center gap-3">
        <a href="/firma/dashboard" className="text-gray-500 hover:text-gray-700">← Dashboard</a>
        <h1 className="font-bold text-gray-900">Çağrı Geçmişi</h1>
        <span className="text-sm text-gray-500">({data?.toplam as number || 0} çağrı)</span>
      </header>

      <main className="max-w-6xl mx-auto px-6 py-8">
        <div className="bg-white rounded-xl border overflow-hidden">
          <table className="w-full text-sm">
            <thead className="bg-gray-50 border-b">
              <tr>
                <th className="text-left px-4 py-3 text-gray-600 font-medium">Telefon</th>
                <th className="text-left px-4 py-3 text-gray-600 font-medium">Tarih</th>
                <th className="text-left px-4 py-3 text-gray-600 font-medium">Süre</th>
                <th className="text-left px-4 py-3 text-gray-600 font-medium">Sonuç</th>
                <th className="text-left px-4 py-3 text-gray-600 font-medium">Özet</th>
                <th className="text-left px-4 py-3 text-gray-600 font-medium">Detay</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-gray-100">
              {cagrilar.map((c, i) => (
                <tr key={i} className="hover:bg-gray-50">
                  <td className="px-4 py-3 font-medium text-gray-900">{c.telefon as string}</td>
                  <td className="px-4 py-3 text-gray-600 text-xs">{new Date(c.baslangic as string).toLocaleString('tr-TR')}</td>
                  <td className="px-4 py-3 text-gray-600">{c.sure_saniye as number}sn</td>
                  <td className="px-4 py-3">
                    <span className={`px-2 py-0.5 rounded-full text-xs font-medium ${sonucRenk(c.sonuc as string)}`}>
                      {c.sonuc as string || 'bilgi'}
                    </span>
                  </td>
                  <td className="px-4 py-3 text-gray-500 text-xs max-w-xs truncate">{c.ai_ozet as string || '-'}</td>
                  <td className="px-4 py-3">
                    <button onClick={() => setSeciliCagri(c)}
                      className="text-xs text-blue-600 hover:text-blue-700">Görüntüle</button>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
          {cagrilar.length === 0 && <div className="text-center text-gray-500 py-12">Henüz çağrı yok</div>}
        </div>
      </main>

      {/* Detay Modal */}
      {seciliCagri && (
        <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50 p-4">
          <div className="bg-white rounded-2xl w-full max-w-lg p-6">
            <div className="flex items-center justify-between mb-4">
              <h2 className="font-bold text-gray-900">Çağrı Detayı</h2>
              <button onClick={() => setSeciliCagri(null)} className="text-gray-400 hover:text-gray-600">✕</button>
            </div>
            <div className="space-y-3 text-sm">
              <div><span className="text-gray-500">Telefon:</span> <span className="font-medium">{seciliCagri.telefon as string}</span></div>
              <div><span className="text-gray-500">Tarih:</span> <span>{new Date(seciliCagri.baslangic as string).toLocaleString('tr-TR')}</span></div>
              <div><span className="text-gray-500">Süre:</span> <span>{seciliCagri.sure_saniye as number} saniye</span></div>
              <div><span className="text-gray-500">Sonuç:</span> <span>{seciliCagri.sonuc as string}</span></div>
              <div>
                <span className="text-gray-500">AI Özeti:</span>
                <p className="mt-1 bg-gray-50 rounded-lg p-3 text-gray-700">{seciliCagri.ai_ozet as string || 'Özet yok'}</p>
              </div>
            </div>
          </div>
        </div>
      )}
    </div>
  )
}
