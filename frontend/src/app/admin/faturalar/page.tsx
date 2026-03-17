'use client'

import { useEffect, useState } from 'react'
import { useRouter } from 'next/navigation'
import { api } from '@/lib/api'

export default function AdminFaturalarPage() {
  const router = useRouter()
  const [faturalar, setFaturalar] = useState<Record<string, unknown>[]>([])
  const [loading, setLoading] = useState(true)
  const [ozet, setOzet] = useState({ toplam: 0, odenen: 0, bekleyen: 0, geciken: 0 })

  useEffect(() => {
    if (!localStorage.getItem('access_token')) { router.push('/admin/login'); return }
    api.get('/admin/raporlar/gelir').then(res => {
      const data = res.data
      setFaturalar(data.faturalar || [])
      setOzet({
        toplam: data.toplam_gelir || 0,
        odenen: data.odenen_fatura || 0,
        bekleyen: data.bekleyen_fatura || 0,
        geciken: data.geciken_fatura || 0,
      })
    }).catch(() => {
      // Gelir raporu endpoint yoksa direkt fatura listesi dene
      api.get('/admin/firmalar').then(res => {
        setFaturalar(res.data || [])
      }).catch(() => router.push('/admin/login'))
    }).finally(() => setLoading(false))
  }, [router])

  const durumRenk = (durum: string) => {
    if (durum === 'odendi') return 'bg-green-100 text-green-700'
    if (durum === 'gecikti') return 'bg-red-100 text-red-700'
    return 'bg-yellow-100 text-yellow-700'
  }

  if (loading) return <div className="min-h-screen flex items-center justify-center text-gray-500">Yükleniyor...</div>

  return (
    <div className="min-h-screen bg-gray-50">
      <header className="bg-white border-b px-6 py-4 flex items-center gap-3">
        <a href="/admin/dashboard" className="text-gray-500 hover:text-gray-700">← Dashboard</a>
        <h1 className="font-bold text-gray-900">Fatura Yönetimi</h1>
      </header>

      <main className="max-w-7xl mx-auto px-6 py-8">
        {/* Özet Kartlar */}
        <div className="grid grid-cols-2 md:grid-cols-4 gap-4 mb-8">
          <div className="bg-white rounded-xl border p-4">
            <div className="text-sm text-gray-500">Toplam Gelir</div>
            <div className="text-xl font-bold text-gray-900">{ozet.toplam.toLocaleString('tr-TR')} ₺</div>
          </div>
          <div className="bg-green-50 rounded-xl border border-green-200 p-4">
            <div className="text-sm text-green-600">Ödenen</div>
            <div className="text-xl font-bold text-green-700">{ozet.odenen}</div>
          </div>
          <div className="bg-yellow-50 rounded-xl border border-yellow-200 p-4">
            <div className="text-sm text-yellow-600">Bekleyen</div>
            <div className="text-xl font-bold text-yellow-700">{ozet.bekleyen}</div>
          </div>
          <div className="bg-red-50 rounded-xl border border-red-200 p-4">
            <div className="text-sm text-red-600">Geciken</div>
            <div className="text-xl font-bold text-red-700">{ozet.geciken}</div>
          </div>
        </div>

        {/* Fatura Tablosu */}
        <div className="bg-white rounded-xl border overflow-hidden">
          <div className="px-6 py-4 border-b">
            <h2 className="font-semibold text-gray-900">Tüm Faturalar</h2>
          </div>
          <table className="w-full text-sm">
            <thead className="bg-gray-50 border-b">
              <tr>
                <th className="text-left px-4 py-3 text-gray-600 font-medium">Fatura No</th>
                <th className="text-left px-4 py-3 text-gray-600 font-medium">Firma</th>
                <th className="text-left px-4 py-3 text-gray-600 font-medium">Dönem</th>
                <th className="text-left px-4 py-3 text-gray-600 font-medium">Tutar</th>
                <th className="text-left px-4 py-3 text-gray-600 font-medium">Vade</th>
                <th className="text-left px-4 py-3 text-gray-600 font-medium">Durum</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-gray-100">
              {faturalar.map((f, i) => (
                <tr key={i} className="hover:bg-gray-50">
                  <td className="px-4 py-3 font-medium text-gray-900">{f.fatura_no as string || '-'}</td>
                  <td className="px-4 py-3 text-gray-600">{f.firma_adi as string || f.ad as string || '-'}</td>
                  <td className="px-4 py-3 text-gray-600">{f.ay as number}/{f.yil as number}</td>
                  <td className="px-4 py-3 font-medium">{(f.genel_toplam as number || 0).toLocaleString('tr-TR')} ₺</td>
                  <td className="px-4 py-3 text-gray-600 text-xs">{f.vade_tarihi as string || '-'}</td>
                  <td className="px-4 py-3">
                    <span className={`px-2 py-0.5 rounded-full text-xs font-medium ${durumRenk(f.durum as string || 'bekliyor')}`}>
                      {f.durum as string || 'bekliyor'}
                    </span>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
          {faturalar.length === 0 && <div className="text-center text-gray-500 py-12">Henüz fatura yok</div>}
        </div>
      </main>
    </div>
  )
}
