'use client'

import { useState, useEffect } from 'react'
import { api } from '@/lib/api'

interface SIPBilgi {
  sunucu: string
  port: string
  kullanici_adi: string
  sifre: string
  domain: string
  dahili_no: string
}

export default function ZoiperKurulumPage() {
  const [sipBilgi, setSipBilgi] = useState<SIPBilgi | null>(null)
  const [aktifAdim, setAktifAdim] = useState(1)
  const [kopyalandi, setKopyalandi] = useState<string | null>(null)
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    const fetchSIP = async () => {
      try {
        const res = await api.get('/firma/sip-bilgi')
        setSipBilgi(res.data)
      } catch {
        // Demo bilgi
        setSipBilgi({
          sunucu: '31.57.77.166',
          port: '5060',
          kullanici_adi: 'firma_1_dahili',
          sifre: 'DahiliSifre2026!',
          domain: '31.57.77.166',
          dahili_no: '101'
        })
      } finally {
        setLoading(false)
      }
    }
    fetchSIP()
  }, [])

  const kopyala = (deger: string, alan: string) => {
    navigator.clipboard.writeText(deger)
    setKopyalandi(alan)
    setTimeout(() => setKopyalandi(null), 2000)
  }

  const adimlar = [
    { no: 1, baslik: 'Zoiper İndir', ikon: '📱' },
    { no: 2, baslik: 'Hesap Oluştur', ikon: '👤' },
    { no: 3, baslik: 'SIP Ayarları', ikon: '⚙️' },
    { no: 4, baslik: 'Bağlan', ikon: '🔗' },
    { no: 5, baslik: 'Test Et', ikon: '✅' },
  ]

  if (loading) {
    return (
      <div className="flex items-center justify-center min-h-screen">
        <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600"></div>
      </div>
    )
  }

  return (
    <div className="min-h-screen bg-gray-50 py-8 px-4">
      <div className="max-w-3xl mx-auto">
        {/* Başlık */}
        <div className="text-center mb-8">
          <h1 className="text-3xl font-bold text-gray-900">📞 Zoiper Kurulum Rehberi</h1>
          <p className="text-gray-600 mt-2">
            AI asistanınız müşterileri size yönlendirdiğinde Zoiper uygulamanız çalacak.
          </p>
        </div>

        {/* Adım göstergesi */}
        <div className="flex justify-between mb-8">
          {adimlar.map((adim) => (
            <button
              key={adim.no}
              onClick={() => setAktifAdim(adim.no)}
              className={`flex flex-col items-center flex-1 ${
                aktifAdim === adim.no ? 'text-blue-600' : 'text-gray-400'
              }`}
            >
              <div className={`w-10 h-10 rounded-full flex items-center justify-center text-lg mb-1 ${
                aktifAdim >= adim.no ? 'bg-blue-600 text-white' : 'bg-gray-200'
              }`}>
                {aktifAdim > adim.no ? '✓' : adim.ikon}
              </div>
              <span className="text-xs font-medium hidden sm:block">{adim.baslik}</span>
            </button>
          ))}
        </div>

        {/* Adım içerikleri */}
        <div className="bg-white rounded-xl shadow-sm border p-6 mb-6">

          {/* Adım 1: İndir */}
          {aktifAdim === 1 && (
            <div>
              <h2 className="text-xl font-bold mb-4">📱 Zoiper'ı İndirin</h2>
              <p className="text-gray-600 mb-6">Cihazınıza uygun sürümü indirin:</p>
              <div className="grid grid-cols-2 gap-4">
                {[
                  { platform: 'iOS (iPhone)', url: 'https://apps.apple.com/app/zoiper5/id1450272949', ikon: '🍎' },
                  { platform: 'Android', url: 'https://play.google.com/store/apps/details?id=com.zoiper.android.app', ikon: '🤖' },
                  { platform: 'Windows', url: 'https://www.zoiper.com/en/voip-softphone/download/zoiper5/for/windows', ikon: '🪟' },
                  { platform: 'macOS', url: 'https://www.zoiper.com/en/voip-softphone/download/zoiper5/for/mac', ikon: '🍏' },
                ].map((item) => (
                  <a
                    key={item.platform}
                    href={item.url}
                    target="_blank"
                    rel="noopener noreferrer"
                    className="flex items-center gap-3 p-4 border rounded-lg hover:bg-blue-50 hover:border-blue-300 transition-colors"
                  >
                    <span className="text-2xl">{item.ikon}</span>
                    <div>
                      <div className="font-medium">{item.platform}</div>
                      <div className="text-xs text-blue-600">İndir →</div>
                    </div>
                  </a>
                ))}
              </div>
              <div className="mt-4 p-3 bg-blue-50 rounded-lg text-sm text-blue-700">
                💡 Zoiper 5 ücretsiz sürümü yeterlidir. Pro sürüm gerekmez.
              </div>
            </div>
          )}

          {/* Adım 2: Hesap */}
          {aktifAdim === 2 && (
            <div>
              <h2 className="text-xl font-bold mb-4">👤 Zoiper'ı Açın</h2>
              <ol className="space-y-4">
                {[
                  'Zoiper uygulamasını açın',
                  '"Create account" veya "Hesap Ekle" butonuna tıklayın',
                  '"SIP" seçeneğini seçin (VoIP değil)',
                  'Aşağıdaki bilgileri girin (Adım 3)',
                ].map((adim, i) => (
                  <li key={i} className="flex items-start gap-3">
                    <span className="w-7 h-7 rounded-full bg-blue-600 text-white flex items-center justify-center text-sm font-bold flex-shrink-0">
                      {i + 1}
                    </span>
                    <span className="text-gray-700 pt-0.5">{adim}</span>
                  </li>
                ))}
              </ol>
            </div>
          )}

          {/* Adım 3: SIP Ayarları */}
          {aktifAdim === 3 && sipBilgi && (
            <div>
              <h2 className="text-xl font-bold mb-4">⚙️ SIP Bağlantı Bilgileri</h2>
              <p className="text-gray-600 mb-4">Bu bilgileri Zoiper'a girin:</p>

              <div className="space-y-3">
                {[
                  { etiket: 'Sunucu / Host', deger: sipBilgi.sunucu, alan: 'sunucu' },
                  { etiket: 'Port', deger: sipBilgi.port, alan: 'port' },
                  { etiket: 'Kullanıcı Adı', deger: sipBilgi.kullanici_adi, alan: 'kullanici' },
                  { etiket: 'Şifre', deger: sipBilgi.sifre, alan: 'sifre' },
                  { etiket: 'Domain', deger: sipBilgi.domain, alan: 'domain' },
                ].map((item) => (
                  <div key={item.alan} className="flex items-center justify-between p-3 bg-gray-50 rounded-lg border">
                    <div>
                      <div className="text-xs text-gray-500">{item.etiket}</div>
                      <div className="font-mono font-medium">{item.deger}</div>
                    </div>
                    <button
                      onClick={() => kopyala(item.deger, item.alan)}
                      className={`px-3 py-1 rounded text-sm transition-colors ${
                        kopyalandi === item.alan
                          ? 'bg-green-100 text-green-700'
                          : 'bg-blue-100 text-blue-700 hover:bg-blue-200'
                      }`}
                    >
                      {kopyalandi === item.alan ? '✓ Kopyalandı' : 'Kopyala'}
                    </button>
                  </div>
                ))}
              </div>

              <button
                onClick={() => {
                  const tumBilgi = `Sunucu: ${sipBilgi.sunucu}\nPort: ${sipBilgi.port}\nKullanıcı: ${sipBilgi.kullanici_adi}\nŞifre: ${sipBilgi.sifre}\nDomain: ${sipBilgi.domain}`
                  kopyala(tumBilgi, 'tum')
                }}
                className="mt-4 w-full py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition-colors"
              >
                {kopyalandi === 'tum' ? '✓ Tüm Bilgiler Kopyalandı' : '📋 Tüm Bilgileri Kopyala'}
              </button>
            </div>
          )}

          {/* Adım 4: Bağlan */}
          {aktifAdim === 4 && (
            <div>
              <h2 className="text-xl font-bold mb-4">🔗 Bağlantıyı Tamamlayın</h2>
              <ol className="space-y-4">
                {[
                  'Bilgileri girdikten sonra "Kaydet" veya "Register" butonuna tıklayın',
                  'Zoiper\'ın üst kısmında yeşil ışık veya "Registered" yazısı görünmeli',
                  'Yeşil ışık görünüyorsa bağlantı başarılı!',
                  'Kırmızı ise sunucu adresini ve şifreyi kontrol edin',
                ].map((adim, i) => (
                  <li key={i} className="flex items-start gap-3">
                    <span className="w-7 h-7 rounded-full bg-green-600 text-white flex items-center justify-center text-sm font-bold flex-shrink-0">
                      {i + 1}
                    </span>
                    <span className="text-gray-700 pt-0.5">{adim}</span>
                  </li>
                ))}
              </ol>
              <div className="mt-4 p-3 bg-yellow-50 rounded-lg text-sm text-yellow-700 border border-yellow-200">
                ⚠️ Bağlantı sorunu yaşıyorsanız: Güvenlik duvarınızın 5060 (UDP) portuna izin verdiğinden emin olun.
              </div>
            </div>
          )}

          {/* Adım 5: Test */}
          {aktifAdim === 5 && (
            <div>
              <h2 className="text-xl font-bold mb-4">✅ Test Edin</h2>
              <div className="space-y-4">
                <div className="p-4 bg-green-50 rounded-lg border border-green-200">
                  <h3 className="font-semibold text-green-800 mb-2">Test Çağrısı</h3>
                  <p className="text-green-700 text-sm">
                    Başka bir telefondan <strong>31.57.77.166</strong> numarasını arayın.
                    AI asistanı cevapladıktan sonra "yetkili" veya "insan" deyin.
                    Zoiper uygulamanız çalmalı!
                  </p>
                </div>
                <div className="p-4 bg-blue-50 rounded-lg border border-blue-200">
                  <h3 className="font-semibold text-blue-800 mb-2">Yönlendirme Ayarı</h3>
                  <p className="text-blue-700 text-sm">
                    Dashboard → Çağrı Yönlendirme bölümünden "Uygulama (Zoiper)" seçeneğinin aktif olduğunu kontrol edin.
                  </p>
                </div>
              </div>
            </div>
          )}
        </div>

        {/* Navigasyon butonları */}
        <div className="flex justify-between">
          <button
            onClick={() => setAktifAdim(Math.max(1, aktifAdim - 1))}
            disabled={aktifAdim === 1}
            className="px-6 py-2 border rounded-lg text-gray-600 hover:bg-gray-100 disabled:opacity-40 disabled:cursor-not-allowed"
          >
            ← Önceki
          </button>
          <button
            onClick={() => setAktifAdim(Math.min(5, aktifAdim + 1))}
            disabled={aktifAdim === 5}
            className="px-6 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 disabled:opacity-40 disabled:cursor-not-allowed"
          >
            Sonraki →
          </button>
        </div>
      </div>
    </div>
  )
}
