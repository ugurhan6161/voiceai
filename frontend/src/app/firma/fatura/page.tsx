'use client'

import { useEffect, useState } from 'react'
import { useRouter } from 'next/navigation'
import { firmaApi } from '@/lib/api'

export default function FaturaPage() {
  const router = useRouter()
  const [faturalar, setFaturalar] = useState<Record<string, unknown>[]>([])
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    if (!localStorage.getItem('access_token')) { router.push('/firma/login'); return }
    firmaApi.faturalar()
      .then(res => setFaturalar(res.data.faturalar || []))
      .catch(() => router.push('/firma/login'))
      .finally(() => setLoading(false))
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
        <a href="/firma/dashboard" className="text-gray-500 hover:text-gray-700">← Dashboard</a>
        <h1 className="font-bold text-gray-900">Faturalarım</h1>
      </header>
      <main className="max-w-4xl mx-auto px-6 py-8">
        <div className="bg-white rounded-xl border overflow-hidden">
          <table className="w-full text-sm">
            <thead className="bg-gray-50 border-b">
              <tr>
                <th className="text-left px-4 py-3 text-gray-600 font-medium">Fatura No</th>
                <th className="text-left px-4 py-3 text-gray-600 font-medium">Dönem</th>
                <th className="text-left px-4 py-3 text-gray-600 font-medium">Tutar</th>
                <th className="text-left px-4 py-3 text-gray-600 font-medium">Vade</th>
                <th className="text-left px-4 py-3 text-gray-600 font-medium">Durum</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-gray-100">
              {faturalar.map((f, i) => (
                <tr key={i} className="hover:bg-gray-50">
                  <td className="px-4 py-3 font-medium text-gray-900">{f.fatura_no as string}</td>
                  <td className="px-4 py-3 text-gray-600">{f.ay as number}/{f.yil as number}</td>
                  <td className="px-4 py-3 text-gray-900 font-medium">{(f.genel_toplam as number)?.toLocaleString('tr-TR')} ₺</td>
                  <td className="px-4 py-3 text-gray-600 text-xs">{f.vade_tarihi as string}</td>
                  <td className="px-4 py-3">
                    <span className={`px-2 py-0.5 rounded-full text-xs font-medium ${durumRenk(f.durum as string)}`}>
                      {f.durum as string}
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
