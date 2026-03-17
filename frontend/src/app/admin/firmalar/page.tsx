'use client'

import { useEffect, useState } from 'react'
import { useRouter } from 'next/navigation'
import { adminApi } from '@/lib/api'

interface Firma {
  id: number
  ad: string
  sektor: string
  paket_ad: string
  durum: string
  email: string
  telefon: string
  created_at: string
  bu_ay_cagri: number
}

export default function FirmalarPage() {
  const router = useRouter()
  const [firmalar, setFirmalar] = useState<Firma[]>([])
  const [loading, setLoading] = useState(true)
  const [showModal, setShowModal] = useState(false)
  const [form, setForm] = useState({
    ad: '', sektor: 'otel', paket_id: 1, email: '', telefon: '',
    admin_email: '', admin_ad: '', admin_sifre: ''
  })

  const loadFirmalar = () => {
    adminApi.firmalar()
      .then(res => setFirmalar(res.data))
      .catch(() => router.push('/admin/login'))
      .finally(() => setLoading(false))
  }

  useEffect(() => {
    if (!localStorage.getItem('access_token')) { router.push('/admin/login'); return }
    loadFirmalar()
  }, [])

  const handleDurdur = async (id: number) => {
    if (!confirm('Firmayı durdurmak istediğinize emin misiniz?')) return
    await adminApi.firmaDurdur(id)
    loadFirmalar()
  }

  const handleAktif = async (id: number) => {
    await adminApi.firmaAktif(id)
    loadFirmalar()
  }

  const handleOlustur = async (e: React.FormEvent) => {
    e.preventDefault()
    try {
      await adminApi.firmaOlustur(form)
      setShowModal(false)
      loadFirmalar()
    } catch (err: unknown) {
      const e = err as { response?: { data?: { detail?: string } } }
      alert(e?.response?.data?.detail || 'Hata oluştu')
    }
  }

  const durumRenk = (durum: string) => {
    if (durum === 'aktif') return 'bg-green-100 text-green-700'
    if (durum === 'durduruldu') return 'bg-red-100 text-red-700'
    return 'bg-yellow-100 text-yellow-700'
  }

  return (
    <div className="min-h-screen bg-gray-50">
      <header className="bg-white border-b px-6 py-4 flex items-center justify-between">
        <div className="flex items-center gap-3">
          <a href="/admin/dashboard" className="text-gray-500 hover:text-gray-700">← Dashboard</a>
          <h1 className="font-bold text-gray-900">Firma Yönetimi</h1>
        </div>
        <button
          onClick={() => setShowModal(true)}
          className="bg-blue-600 text-white px-4 py-2 rounded-lg text-sm font-medium hover:bg-blue-700"
        >
          + Yeni Firma
        </button>
      </header>

      <main className="max-w-7xl mx-auto px-6 py-8">
        {loading ? (
          <div className="text-center text-gray-500 py-12">Yükleniyor...</div>
        ) : (
          <div className="bg-white rounded-xl border border-gray-200 overflow-hidden">
            <table className="w-full text-sm">
              <thead className="bg-gray-50 border-b">
                <tr>
                  <th className="text-left px-4 py-3 text-gray-600 font-medium">Firma</th>
                  <th className="text-left px-4 py-3 text-gray-600 font-medium">Sektör</th>
                  <th className="text-left px-4 py-3 text-gray-600 font-medium">Paket</th>
                  <th className="text-left px-4 py-3 text-gray-600 font-medium">Durum</th>
                  <th className="text-left px-4 py-3 text-gray-600 font-medium">Bu Ay Çağrı</th>
                  <th className="text-left px-4 py-3 text-gray-600 font-medium">İşlemler</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-gray-100">
                {firmalar.map(firma => (
                  <tr key={firma.id} className="hover:bg-gray-50">
                    <td className="px-4 py-3">
                      <div className="font-medium text-gray-900">{firma.ad}</div>
                      <div className="text-xs text-gray-500">{firma.email}</div>
                    </td>
                    <td className="px-4 py-3 text-gray-600">{firma.sektor}</td>
                    <td className="px-4 py-3 text-gray-600">{firma.paket_ad}</td>
                    <td className="px-4 py-3">
                      <span className={`px-2 py-1 rounded-full text-xs font-medium ${durumRenk(firma.durum)}`}>
                        {firma.durum}
                      </span>
                    </td>
                    <td className="px-4 py-3 text-gray-600">{firma.bu_ay_cagri}</td>
                    <td className="px-4 py-3">
                      <div className="flex gap-2">
                        {firma.durum === 'aktif' ? (
                          <button
                            onClick={() => handleDurdur(firma.id)}
                            className="text-xs bg-red-50 text-red-600 px-2 py-1 rounded hover:bg-red-100"
                          >
                            Durdur
                          </button>
                        ) : (
                          <button
                            onClick={() => handleAktif(firma.id)}
                            className="text-xs bg-green-50 text-green-600 px-2 py-1 rounded hover:bg-green-100"
                          >
                            Aktif Et
                          </button>
                        )}
                      </div>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
            {firmalar.length === 0 && (
              <div className="text-center text-gray-500 py-12">Henüz firma yok</div>
            )}
          </div>
        )}
      </main>

      {/* Yeni Firma Modal */}
      {showModal && (
        <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50 p-4">
          <div className="bg-white rounded-2xl w-full max-w-lg p-6">
            <h2 className="text-lg font-bold text-gray-900 mb-4">Yeni Firma Ekle</h2>
            <form onSubmit={handleOlustur} className="space-y-3">
              <input required placeholder="Firma Adı" value={form.ad}
                onChange={e => setForm({...form, ad: e.target.value})}
                className="w-full border rounded-lg px-3 py-2 text-sm" />
              <select value={form.sektor} onChange={e => setForm({...form, sektor: e.target.value})}
                className="w-full border rounded-lg px-3 py-2 text-sm">
                <option value="otel">Otel</option>
                <option value="klinik_poliklinik">Klinik</option>
                <option value="hali_yikama">Halı Yıkama</option>
                <option value="su_bayii">Su Bayii</option>
                <option value="kuafor_berber">Kuaför/Berber</option>
                <option value="restoran">Restoran</option>
              </select>
              <input required type="email" placeholder="Firma Email" value={form.email}
                onChange={e => setForm({...form, email: e.target.value})}
                className="w-full border rounded-lg px-3 py-2 text-sm" />
              <input placeholder="Telefon" value={form.telefon}
                onChange={e => setForm({...form, telefon: e.target.value})}
                className="w-full border rounded-lg px-3 py-2 text-sm" />
              <hr />
              <p className="text-xs text-gray-500 font-medium">Admin Kullanıcı</p>
              <input required placeholder="Admin Adı" value={form.admin_ad}
                onChange={e => setForm({...form, admin_ad: e.target.value})}
                className="w-full border rounded-lg px-3 py-2 text-sm" />
              <input required type="email" placeholder="Admin Email" value={form.admin_email}
                onChange={e => setForm({...form, admin_email: e.target.value})}
                className="w-full border rounded-lg px-3 py-2 text-sm" />
              <input required type="password" placeholder="Admin Şifre" value={form.admin_sifre}
                onChange={e => setForm({...form, admin_sifre: e.target.value})}
                className="w-full border rounded-lg px-3 py-2 text-sm" />
              <div className="flex gap-3 pt-2">
                <button type="button" onClick={() => setShowModal(false)}
                  className="flex-1 border border-gray-300 text-gray-700 py-2 rounded-lg text-sm">
                  İptal
                </button>
                <button type="submit"
                  className="flex-1 bg-blue-600 text-white py-2 rounded-lg text-sm font-medium">
                  Oluştur
                </button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  )
}
