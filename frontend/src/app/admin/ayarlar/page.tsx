'use client'

import { useState } from 'react'
import { ayarlarApi } from '@/lib/api'

export default function AyarlarPage() {
  const [aktifTab, setAktifTab] = useState('sip')
  const [mesaj, setMesaj] = useState('')
  const [hata, setHata] = useState('')

  const [sipForm, setSipForm] = useState({ host: '', kullanici: '', sifre: '', aktif: true })
  const [smsForm, setSmsForm] = useState({ kullanici: '', sifre: '', baslik: 'VOICEAI', aktif: true })
  const [iyzicoForm, setIyzicoForm] = useState({ api_key: '', secret_key: '', mod: 'sandbox' })
  const [smtpForm, setSmtpForm] = useState({ host: '', port: 587, kullanici: '', sifre: '', gonderen_ad: '' })

  const kaydet = async (tur: string) => {
    setMesaj(''); setHata('')
    try {
      if (tur === 'sip') await ayarlarApi.sipKaydet('netgsm', sipForm)
      else if (tur === 'sms') await ayarlarApi.smsKaydet(smsForm)
      else if (tur === 'iyzico') await ayarlarApi.iyzicoKaydet(iyzicoForm)
      else if (tur === 'smtp') await ayarlarApi.smtpKaydet(smtpForm)
      setMesaj('✅ Ayarlar kaydedildi')
    } catch {
      setHata('❌ Kaydetme başarısız')
    }
  }

  const test = async (tur: string) => {
    setMesaj(''); setHata('')
    try {
      const ayarlar = tur === 'sip' ? sipForm : tur === 'sms' ? smsForm : tur === 'iyzico' ? iyzicoForm : smtpForm
      const res = await ayarlarApi.test(tur === 'sip' ? 'sip_netgsm' : tur === 'sms' ? 'sms_netgsm' : tur, ayarlar)
      setMesaj(res.data.mesaj || '✅ Bağlantı başarılı')
    } catch {
      setHata('❌ Bağlantı testi başarısız')
    }
  }

  const tabs = [
    { id: 'sip', label: '📞 SIP' },
    { id: 'sms', label: '💬 SMS' },
    { id: 'iyzico', label: '💳 iyzico' },
    { id: 'smtp', label: '📧 SMTP' },
  ]

  return (
    <div className="min-h-screen bg-gray-50">
      <header className="bg-white border-b px-6 py-4 flex items-center gap-3">
        <a href="/admin/dashboard" className="text-gray-500 hover:text-gray-700">← Dashboard</a>
        <h1 className="font-bold text-gray-900">Sistem Ayarları</h1>
      </header>

      <main className="max-w-3xl mx-auto px-6 py-8">
        {/* Tabs */}
        <div className="flex gap-2 mb-6">
          {tabs.map(tab => (
            <button key={tab.id} onClick={() => setAktifTab(tab.id)}
              className={`px-4 py-2 rounded-lg text-sm font-medium transition ${
                aktifTab === tab.id ? 'bg-blue-600 text-white' : 'bg-white border text-gray-600 hover:bg-gray-50'
              }`}>
              {tab.label}
            </button>
          ))}
        </div>

        {mesaj && <div className="bg-green-50 border border-green-200 text-green-700 px-4 py-3 rounded-lg mb-4 text-sm">{mesaj}</div>}
        {hata && <div className="bg-red-50 border border-red-200 text-red-700 px-4 py-3 rounded-lg mb-4 text-sm">{hata}</div>}

        <div className="bg-white rounded-xl border border-gray-200 p-6">
          {/* SIP */}
          {aktifTab === 'sip' && (
            <div className="space-y-4">
              <h2 className="font-semibold text-gray-900">Netgsm SIP Ayarları</h2>
              <input placeholder="SIP Host (sip.netgsm.com.tr)" value={sipForm.host}
                onChange={e => setSipForm({...sipForm, host: e.target.value})}
                className="w-full border rounded-lg px-3 py-2 text-sm" />
              <input placeholder="Kullanıcı Adı" value={sipForm.kullanici}
                onChange={e => setSipForm({...sipForm, kullanici: e.target.value})}
                className="w-full border rounded-lg px-3 py-2 text-sm" />
              <input type="password" placeholder="Şifre (boş bırakılırsa değişmez)" value={sipForm.sifre}
                onChange={e => setSipForm({...sipForm, sifre: e.target.value})}
                className="w-full border rounded-lg px-3 py-2 text-sm" />
              <div className="flex gap-3">
                <button onClick={() => test('sip')} className="flex-1 border border-blue-300 text-blue-600 py-2 rounded-lg text-sm">Test Et</button>
                <button onClick={() => kaydet('sip')} className="flex-1 bg-blue-600 text-white py-2 rounded-lg text-sm font-medium">Kaydet</button>
              </div>
            </div>
          )}

          {/* SMS */}
          {aktifTab === 'sms' && (
            <div className="space-y-4">
              <h2 className="font-semibold text-gray-900">Netgsm SMS Ayarları</h2>
              <input placeholder="Kullanıcı Adı" value={smsForm.kullanici}
                onChange={e => setSmsForm({...smsForm, kullanici: e.target.value})}
                className="w-full border rounded-lg px-3 py-2 text-sm" />
              <input type="password" placeholder="Şifre" value={smsForm.sifre}
                onChange={e => setSmsForm({...smsForm, sifre: e.target.value})}
                className="w-full border rounded-lg px-3 py-2 text-sm" />
              <input placeholder="SMS Başlığı (VOICEAI)" value={smsForm.baslik}
                onChange={e => setSmsForm({...smsForm, baslik: e.target.value})}
                className="w-full border rounded-lg px-3 py-2 text-sm" />
              <div className="flex gap-3">
                <button onClick={() => test('sms')} className="flex-1 border border-blue-300 text-blue-600 py-2 rounded-lg text-sm">Test Et</button>
                <button onClick={() => kaydet('sms')} className="flex-1 bg-blue-600 text-white py-2 rounded-lg text-sm font-medium">Kaydet</button>
              </div>
            </div>
          )}

          {/* iyzico */}
          {aktifTab === 'iyzico' && (
            <div className="space-y-4">
              <h2 className="font-semibold text-gray-900">iyzico Ödeme Ayarları</h2>
              <select value={iyzicoForm.mod} onChange={e => setIyzicoForm({...iyzicoForm, mod: e.target.value})}
                className="w-full border rounded-lg px-3 py-2 text-sm">
                <option value="sandbox">Sandbox (Test)</option>
                <option value="production">Production (Canlı)</option>
              </select>
              <input type="password" placeholder="API Key" value={iyzicoForm.api_key}
                onChange={e => setIyzicoForm({...iyzicoForm, api_key: e.target.value})}
                className="w-full border rounded-lg px-3 py-2 text-sm" />
              <input type="password" placeholder="Secret Key" value={iyzicoForm.secret_key}
                onChange={e => setIyzicoForm({...iyzicoForm, secret_key: e.target.value})}
                className="w-full border rounded-lg px-3 py-2 text-sm" />
              <div className="flex gap-3">
                <button onClick={() => test('iyzico')} className="flex-1 border border-blue-300 text-blue-600 py-2 rounded-lg text-sm">Test Et</button>
                <button onClick={() => kaydet('iyzico')} className="flex-1 bg-blue-600 text-white py-2 rounded-lg text-sm font-medium">Kaydet</button>
              </div>
            </div>
          )}

          {/* SMTP */}
          {aktifTab === 'smtp' && (
            <div className="space-y-4">
              <h2 className="font-semibold text-gray-900">SMTP E-posta Ayarları</h2>
              <input placeholder="SMTP Host (smtp.gmail.com)" value={smtpForm.host}
                onChange={e => setSmtpForm({...smtpForm, host: e.target.value})}
                className="w-full border rounded-lg px-3 py-2 text-sm" />
              <input type="number" placeholder="Port (587)" value={smtpForm.port}
                onChange={e => setSmtpForm({...smtpForm, port: parseInt(e.target.value)})}
                className="w-full border rounded-lg px-3 py-2 text-sm" />
              <input placeholder="Kullanıcı Adı (email)" value={smtpForm.kullanici}
                onChange={e => setSmtpForm({...smtpForm, kullanici: e.target.value})}
                className="w-full border rounded-lg px-3 py-2 text-sm" />
              <input type="password" placeholder="Şifre" value={smtpForm.sifre}
                onChange={e => setSmtpForm({...smtpForm, sifre: e.target.value})}
                className="w-full border rounded-lg px-3 py-2 text-sm" />
              <input placeholder="Gönderen Adı (VoiceAI)" value={smtpForm.gonderen_ad}
                onChange={e => setSmtpForm({...smtpForm, gonderen_ad: e.target.value})}
                className="w-full border rounded-lg px-3 py-2 text-sm" />
              <div className="flex gap-3">
                <button onClick={() => test('smtp')} className="flex-1 border border-blue-300 text-blue-600 py-2 rounded-lg text-sm">Test Et</button>
                <button onClick={() => kaydet('smtp')} className="flex-1 bg-blue-600 text-white py-2 rounded-lg text-sm font-medium">Kaydet</button>
              </div>
            </div>
          )}
        </div>
      </main>
    </div>
  )
}
