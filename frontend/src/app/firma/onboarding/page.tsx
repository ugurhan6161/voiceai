'use client'

import { useState } from 'react'
import { useRouter } from 'next/navigation'
import { adminApi, sablonApi } from '@/lib/api'

const ADIMLAR = ['Firma Bilgileri', 'Sektör Seç', 'Telefon', 'Hizmetler', 'Test']

export default function OnboardingPage() {
  const router = useRouter()
  const [adim, setAdim] = useState(0)
  const [loading, setLoading] = useState(false)
  const [firmaId, setFirmaId] = useState<number | null>(null)
  const [form, setForm] = useState({
    ad: '', email: '', telefon: '', adres: '',
    sektor: 'otel', paket_id: 1,
    admin_email: '', admin_ad: '', admin_sifre: '',
    sip_numarasi: '',
  })

  const ileri = () => setAdim(a => Math.min(a + 1, ADIMLAR.length - 1))
  const geri = () => setAdim(a => Math.max(a - 1, 0))

  const firmaOlustur = async () => {
    setLoading(true)
    try {
      const res = await adminApi.firmaOlustur(form)
      setFirmaId(res.data.id)
      ileri()
    } catch (err: unknown) {
      const e = err as { response?: { data?: { detail?: string } } }
      alert(e?.response?.data?.detail || 'Hata oluştu')
    } finally {
      setLoading(false)
    }
  }

  const sablonAta = async () => {
    if (!firmaId) return
    setLoading(true)
    try {
      await sablonApi.ata(firmaId, form.sektor)
      ileri()
    } catch {
      alert('Şablon atama başarısız')
    } finally {
      setLoading(false)
    }
  }

  const tamamla = () => router.push('/firma/dashboard')

  const SEKTORLER = [
    { kod: 'otel', ad: 'Otel', ikon: '🏨' },
    { kod: 'klinik_poliklinik', ad: 'Klinik', ikon: '🏥' },
    { kod: 'hali_yikama', ad: 'Halı Yıkama', ikon: '🧺' },
    { kod: 'su_bayii', ad: 'Su Bayii', ikon: '💧' },
    { kod: 'kuafor_berber', ad: 'Kuaför/Berber', ikon: '💈' },
    { kod: 'restoran', ad: 'Restoran', ikon: '🍽️' },
    { kod: 'oto_servis', ad: 'Oto Servis', ikon: '🔩' },
    { kod: 'dis_klinigi', ad: 'Diş Kliniği', ikon: '🦷' },
    { kod: 'tup_gaz_bayii', ad: 'Tüp Gaz', ikon: '🔥' },
    { kod: 'spor_salonu', ad: 'Spor Salonu', ikon: '🏋️' },
  ]

  return (
    <div className="min-h-screen bg-gradient-to-br from-indigo-50 to-blue-50 flex items-center justify-center p-4">
      <div className="bg-white rounded-2xl shadow-xl w-full max-w-2xl p-8">
        {/* Progress */}
        <div className="flex items-center gap-2 mb-8">
          {ADIMLAR.map((a, i) => (
            <div key={i} className="flex items-center gap-2 flex-1">
              <div className={`w-8 h-8 rounded-full flex items-center justify-center text-sm font-bold ${
                i < adim ? 'bg-green-500 text-white' : i === adim ? 'bg-indigo-600 text-white' : 'bg-gray-200 text-gray-500'
              }`}>{i < adim ? '✓' : i + 1}</div>
              {i < ADIMLAR.length - 1 && <div className={`flex-1 h-1 rounded ${i < adim ? 'bg-green-500' : 'bg-gray-200'}`} />}
            </div>
          ))}
        </div>

        <h2 className="text-xl font-bold text-gray-900 mb-6">{ADIMLAR[adim]}</h2>

        {/* Adım 0: Firma Bilgileri */}
        {adim === 0 && (
          <div className="space-y-4">
            <input placeholder="Firma Adı *" value={form.ad} onChange={e => setForm({...form, ad: e.target.value})}
              className="w-full border rounded-lg px-3 py-2 text-sm" />
            <input type="email" placeholder="Firma Email *" value={form.email} onChange={e => setForm({...form, email: e.target.value})}
              className="w-full border rounded-lg px-3 py-2 text-sm" />
            <input placeholder="Telefon" value={form.telefon} onChange={e => setForm({...form, telefon: e.target.value})}
              className="w-full border rounded-lg px-3 py-2 text-sm" />
            <hr />
            <p className="text-xs text-gray-500 font-medium">Panel Giriş Bilgileri</p>
            <input placeholder="Admin Adı *" value={form.admin_ad} onChange={e => setForm({...form, admin_ad: e.target.value})}
              className="w-full border rounded-lg px-3 py-2 text-sm" />
            <input type="email" placeholder="Admin Email *" value={form.admin_email} onChange={e => setForm({...form, admin_email: e.target.value})}
              className="w-full border rounded-lg px-3 py-2 text-sm" />
            <input type="password" placeholder="Şifre *" value={form.admin_sifre} onChange={e => setForm({...form, admin_sifre: e.target.value})}
              className="w-full border rounded-lg px-3 py-2 text-sm" />
            <button onClick={firmaOlustur} disabled={loading || !form.ad || !form.email}
              className="w-full bg-indigo-600 text-white py-3 rounded-lg font-medium disabled:bg-indigo-300">
              {loading ? 'Oluşturuluyor...' : 'Devam Et →'}
            </button>
          </div>
        )}

        {/* Adım 1: Sektör */}
        {adim === 1 && (
          <div>
            <div className="grid grid-cols-2 gap-3 mb-6">
              {SEKTORLER.map(s => (
                <button key={s.kod} onClick={() => setForm({...form, sektor: s.kod})}
                  className={`p-4 rounded-xl border-2 text-left transition ${
                    form.sektor === s.kod ? 'border-indigo-500 bg-indigo-50' : 'border-gray-200 hover:border-gray-300'
                  }`}>
                  <div className="text-2xl mb-1">{s.ikon}</div>
                  <div className="text-sm font-medium text-gray-900">{s.ad}</div>
                </button>
              ))}
            </div>
            <div className="flex gap-3">
              <button onClick={geri} className="flex-1 border border-gray-300 text-gray-700 py-2 rounded-lg text-sm">← Geri</button>
              <button onClick={sablonAta} disabled={loading}
                className="flex-1 bg-indigo-600 text-white py-2 rounded-lg text-sm font-medium disabled:bg-indigo-300">
                {loading ? 'Atanıyor...' : 'Devam Et →'}
              </button>
            </div>
          </div>
        )}

        {/* Adım 2: Telefon */}
        {adim === 2 && (
          <div className="space-y-4">
            <p className="text-sm text-gray-600">Müşterilerinizin arayacağı telefon numarasını girin. Bu numara SIP trunk üzerinden yönlendirilecektir.</p>
            <input placeholder="Örn: 02121234567" value={form.sip_numarasi} onChange={e => setForm({...form, sip_numarasi: e.target.value})}
              className="w-full border rounded-lg px-3 py-2 text-sm" />
            <div className="bg-blue-50 border border-blue-200 rounded-lg p-4 text-sm text-blue-700">
              💡 Netgsm veya Verimor üzerinden DID numarası alarak bu alana girebilirsiniz.
            </div>
            <div className="flex gap-3">
              <button onClick={geri} className="flex-1 border border-gray-300 text-gray-700 py-2 rounded-lg text-sm">← Geri</button>
              <button onClick={ileri} className="flex-1 bg-indigo-600 text-white py-2 rounded-lg text-sm font-medium">Devam Et →</button>
            </div>
          </div>
        )}

        {/* Adım 3: Hizmetler */}
        {adim === 3 && (
          <div className="space-y-4">
            <p className="text-sm text-gray-600">Hizmetleriniz ve fiyatlarınız şablon tarafından otomatik yüklenmiştir. Panelden düzenleyebilirsiniz.</p>
            <div className="bg-green-50 border border-green-200 rounded-lg p-4 text-sm text-green-700">
              ✅ <strong>{form.sektor}</strong> şablonu başarıyla yüklendi. Hizmetler ve fiyatlar hazır.
            </div>
            <div className="flex gap-3">
              <button onClick={geri} className="flex-1 border border-gray-300 text-gray-700 py-2 rounded-lg text-sm">← Geri</button>
              <button onClick={ileri} className="flex-1 bg-indigo-600 text-white py-2 rounded-lg text-sm font-medium">Devam Et →</button>
            </div>
          </div>
        )}

        {/* Adım 4: Test */}
        {adim === 4 && (
          <div className="space-y-4 text-center">
            <div className="text-6xl mb-4">🎉</div>
            <h3 className="text-xl font-bold text-gray-900">Kurulum Tamamlandı!</h3>
            <p className="text-gray-600">AI asistanınız hazır. Şimdi test çağrısı yapabilirsiniz.</p>
            <div className="bg-gray-50 rounded-xl p-4 text-left text-sm space-y-2">
              <div>✅ Firma oluşturuldu</div>
              <div>✅ {form.sektor} şablonu atandı</div>
              <div>✅ Veritabanı hazırlandı</div>
              <div>✅ AI asistan aktif</div>
            </div>
            <button onClick={tamamla} className="w-full bg-indigo-600 text-white py-3 rounded-lg font-medium">
              Panele Git →
            </button>
          </div>
        )}
      </div>
    </div>
  )
}
