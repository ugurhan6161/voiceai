'use client'

import { useEffect, useState } from 'react'
import { useRouter } from 'next/navigation'
import { firmaApi } from '@/lib/api'

export default function FirmaDashboardPage() {
  const router = useRouter()
  const [data, setData] = useState<Record<string, unknown> | null>(null)
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    if (!localStorage.getItem('access_token')) { router.push('/firma/login'); return }
    firmaApi.dashboard()
      .then(res => setData(res.data))
      .catch(() => router.push('/firma/login'))
      .finally(() => setLoading(false))
  }, [router])

  const logout = () => { localStorage.clear(); router.push('/firma/login') }

  if (loading) return <div className="min-h-screen flex items-center justify-center text-gray-500">Yükleniyor...</div>

  const firma = data?.firma as Record<string, unknown> | undefined

  return (
    <div className="min-h-screen bg-gray-50">
      <header className="bg-white border-b px-6 py-4 flex items-center justify-between">
        <div className="flex items-center gap-3">
          <span className="text-2xl">🎙️</span>
          <div>
            <h1 className="font-bold text-gray-900">{firma?.ad as string || 'Firma Paneli'}</h1>
            <p className="text-xs text-gray-500">{firma?.sektor as string}</p>
          </div>
        </div>
        <nav className="flex items-center gap-4">
          <a href="/firma/ajan" className="text-sm text-gray-600 hover:text-indigo-600">Ajan</a>
          <a href="/firma/cagrilar" className="text-sm text-gray-600 hover:text-indigo-600">Çağrılar</a>
          <a href="/firma/fatura" className="text-sm text-gray-600 hover:text-indigo-600">Fatura</a>
          <button onClick={logout} className="text-sm text-red-600">Çıkış</button>
        </nav>
      </header>

      <main className="max-w-6xl mx-auto px-6 py-8">
        <div className="grid grid-cols-1 md:grid-cols-3 gap-6 mb-8">
          <div className="bg-white rounded-xl border p-6">
            <div className="text-2xl mb-2">📞</div>
            <div className="text-2xl font-bold text-gray-900">{data?.bugun_cagri as number || 0}</div>
            <div className="text-sm text-gray-500">Bugün Çağrı</div>
          </div>
          <div className="bg-white rounded-xl border p-6">
            <div className="text-2xl mb-2">📊</div>
            <div className="text-2xl font-bold text-gray-900">{data?.bu_ay_cagri as number || 0}</div>
            <div className="text-sm text-gray-500">Bu Ay Çağrı</div>
          </div>
          <div className="bg-white rounded-xl border p-6">
            <div className="text-2xl mb-2">💬</div>
            <div className="text-2xl font-bold text-gray-900">{data?.bu_ay_sms as number || 0}</div>
            <div className="text-sm text-gray-500">Bu Ay SMS</div>
          </div>
        </div>

        {/* Son Çağrılar */}
        <div className="bg-white rounded-xl border p-6">
          <h3 className="font-semibold text-gray-900 mb-4">Son Çağrılar</h3>
          {(data?.son_cagrilar as unknown[])?.length ? (
            <div className="space-y-3">
              {(data?.son_cagrilar as Record<string, unknown>[]).map((c, i) => (
                <div key={i} className="flex items-center justify-between py-2 border-b last:border-0">
                  <div>
                    <div className="font-medium text-sm text-gray-900">{c.telefon as string}</div>
                    <div className="text-xs text-gray-500">{c.ai_ozet as string || 'Özet yok'}</div>
                  </div>
                  <div className="text-right">
                    <div className="text-xs text-gray-500">{c.sure_saniye as number}sn</div>
                    <span className={`text-xs px-2 py-0.5 rounded-full ${c.sonuc === 'rezervasyon' ? 'bg-green-100 text-green-700' : 'bg-gray-100 text-gray-600'}`}>
                      {c.sonuc as string || 'bilgi'}
                    </span>
                  </div>
                </div>
              ))}
            </div>
          ) : (
            <p className="text-gray-500 text-sm">Henüz çağrı yok</p>
          )}
        </div>
      </main>
    </div>
  )
}
