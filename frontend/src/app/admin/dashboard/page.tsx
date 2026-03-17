'use client'

import { useEffect, useState } from 'react'
import { useRouter } from 'next/navigation'
import { adminApi } from '@/lib/api'

interface DashboardStats {
  toplam_firma: number
  aktif_firma: number
  durdurulmus_firma: number
  toplam_kullanici: number
  bugun_cagri: number
  bu_ay_cagri: number
  sistem_saglik: string
}

export default function AdminDashboardPage() {
  const router = useRouter()
  const [stats, setStats] = useState<DashboardStats | null>(null)
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    const token = localStorage.getItem('access_token')
    if (!token) { router.push('/admin/login'); return }

    adminApi.dashboard()
      .then(res => setStats(res.data))
      .catch(() => router.push('/admin/login'))
      .finally(() => setLoading(false))
  }, [router])

  const logout = () => {
    localStorage.clear()
    router.push('/admin/login')
  }

  if (loading) return (
    <div className="min-h-screen bg-gray-50 flex items-center justify-center">
      <div className="text-gray-500">Yükleniyor...</div>
    </div>
  )

  return (
    <div className="min-h-screen bg-gray-50">
      {/* Header */}
      <header className="bg-white border-b border-gray-200 px-6 py-4 flex items-center justify-between">
        <div className="flex items-center gap-3">
          <span className="text-2xl">🎙️</span>
          <div>
            <h1 className="font-bold text-gray-900">VoiceAI Platform</h1>
            <p className="text-xs text-gray-500">Super Admin Paneli</p>
          </div>
        </div>
        <nav className="flex items-center gap-4">
          <a href="/admin/firmalar" className="text-sm text-gray-600 hover:text-blue-600">Firmalar</a>
          <a href="/admin/ayarlar" className="text-sm text-gray-600 hover:text-blue-600">Ayarlar</a>
          <a href="/admin/faturalar" className="text-sm text-gray-600 hover:text-blue-600">Faturalar</a>
          <button onClick={logout} className="text-sm text-red-600 hover:text-red-700">Çıkış</button>
        </nav>
      </header>

      <main className="max-w-7xl mx-auto px-6 py-8">
        <h2 className="text-xl font-bold text-gray-900 mb-6">Dashboard</h2>

        {/* İstatistik Kartları */}
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6 mb-8">
          <StatCard title="Toplam Firma" value={stats?.toplam_firma ?? 0} icon="🏢" color="blue" />
          <StatCard title="Aktif Firma" value={stats?.aktif_firma ?? 0} icon="✅" color="green" />
          <StatCard title="Bugün Çağrı" value={stats?.bugun_cagri ?? 0} icon="📞" color="purple" />
          <StatCard title="Bu Ay Çağrı" value={stats?.bu_ay_cagri ?? 0} icon="📊" color="orange" />
        </div>

        {/* Sistem Sağlığı */}
        <div className="bg-white rounded-xl border border-gray-200 p-6 mb-6">
          <h3 className="font-semibold text-gray-900 mb-4">Sistem Durumu</h3>
          <div className="flex items-center gap-3">
            <div className={`w-3 h-3 rounded-full ${stats?.sistem_saglik === 'healthy' ? 'bg-green-500' : 'bg-yellow-500'}`} />
            <span className="text-sm text-gray-700">
              {stats?.sistem_saglik === 'healthy' ? '✅ Sistem sağlıklı çalışıyor' : '⚠️ Dikkat gerektiren durumlar var'}
            </span>
          </div>
          <div className="mt-4 grid grid-cols-3 gap-4 text-sm">
            <div className="bg-gray-50 rounded-lg p-3">
              <div className="text-gray-500">Toplam Kullanıcı</div>
              <div className="font-bold text-gray-900 text-lg">{stats?.toplam_kullanici ?? 0}</div>
            </div>
            <div className="bg-gray-50 rounded-lg p-3">
              <div className="text-gray-500">Durdurulmuş Firma</div>
              <div className="font-bold text-red-600 text-lg">{stats?.durdurulmus_firma ?? 0}</div>
            </div>
            <div className="bg-gray-50 rounded-lg p-3">
              <div className="text-gray-500">Bu Ay Çağrı</div>
              <div className="font-bold text-gray-900 text-lg">{stats?.bu_ay_cagri ?? 0}</div>
            </div>
          </div>
        </div>

        {/* Hızlı Erişim */}
        <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
          <QuickLink href="/admin/firmalar" icon="🏢" title="Firma Yönetimi" desc="Firma ekle, düzenle, durdur" />
          <QuickLink href="/admin/ayarlar" icon="⚙️" title="Sistem Ayarları" desc="SIP, SMS, iyzico, SMTP" />
          <QuickLink href="/admin/faturalar" icon="💰" title="Faturalar" desc="Gelir raporları ve ödemeler" />
        </div>
      </main>
    </div>
  )
}

function StatCard({ title, value, icon, color }: { title: string; value: number; icon: string; color: string }) {
  const colors: Record<string, string> = {
    blue: 'bg-blue-50 border-blue-200',
    green: 'bg-green-50 border-green-200',
    purple: 'bg-purple-50 border-purple-200',
    orange: 'bg-orange-50 border-orange-200',
  }
  return (
    <div className={`rounded-xl border p-6 ${colors[color] || colors.blue}`}>
      <div className="text-2xl mb-2">{icon}</div>
      <div className="text-2xl font-bold text-gray-900">{value.toLocaleString('tr-TR')}</div>
      <div className="text-sm text-gray-600 mt-1">{title}</div>
    </div>
  )
}

function QuickLink({ href, icon, title, desc }: { href: string; icon: string; title: string; desc: string }) {
  return (
    <a href={href} className="bg-white rounded-xl border border-gray-200 p-5 hover:border-blue-300 hover:shadow-sm transition block">
      <div className="text-2xl mb-2">{icon}</div>
      <div className="font-semibold text-gray-900">{title}</div>
      <div className="text-sm text-gray-500 mt-1">{desc}</div>
    </a>
  )
}
