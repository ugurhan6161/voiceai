/**
 * VoiceAI Platform — Admin Şablon Yönetimi Sayfası
 * 40+ şablonu görüntüle, aktif/pasif yap, yeni ekle.
 */
"use client"

import { useState, useEffect } from "react"

interface Sablon {
  kod: string
  ad: string
  kategori: string
  ikon: string
  aciklama?: string
  aktif: boolean
}

interface KategoriGrubu {
  ad: string
  ikon: string
  sablonlar: Sablon[]
}

export default function SablonYonetimiSayfasi() {
  const [kategoriler, setKategoriler] = useState<Record<string, KategoriGrubu>>({})
  const [yukleniyor, setYukleniyor] = useState(true)
  const [seciliSablon, setSeciliSablon] = useState<Sablon | null>(null)

  useEffect(() => {
    fetch("/api/sablonlar/?sadece_aktif=false")
      .then((r) => r.json())
      .then((veri) => {
        setKategoriler(veri.kategoriler)
        setYukleniyor(false)
      })
  }, [])

  const aktifligDegistir = async (kod: string, aktif: boolean) => {
    await fetch(`/api/sablonlar/${kod}`, {
      method: "PUT",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ aktif }),
    })
    // State güncelle
    setKategoriler((prev) => {
      const yeni = { ...prev }
      for (const kat of Object.values(yeni)) {
        const sablon = kat.sablonlar.find((s) => s.kod === kod)
        if (sablon) sablon.aktif = aktif
      }
      return yeni
    })
  }

  const toplamSablon = Object.values(kategoriler)
    .reduce((acc, k) => acc + k.sablonlar.length, 0)
  const aktifSablon = Object.values(kategoriler)
    .reduce((acc, k) => acc + k.sablonlar.filter((s) => s.aktif).length, 0)

  return (
    <div className="max-w-6xl mx-auto p-6 space-y-6">
      {/* Başlık */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-gray-900">Şablon Yönetimi</h1>
          <p className="text-sm text-gray-500 mt-1">
            {aktifSablon} aktif / {toplamSablon} toplam şablon
          </p>
        </div>
        <button className="px-4 py-2 bg-blue-600 text-white rounded-lg text-sm hover:bg-blue-700 flex items-center gap-2">
          <span>+</span> Yeni Şablon
        </button>
      </div>

      {yukleniyor ? (
        <div className="text-center py-12 text-gray-400">Yükleniyor...</div>
      ) : (
        <div className="space-y-6">
          {Object.entries(kategoriler).map(([katKod, kategori]) => (
            <div key={katKod} className="bg-white border border-gray-200 rounded-xl overflow-hidden">
              {/* Kategori başlığı */}
              <div className="bg-gray-50 px-5 py-3 border-b border-gray-200 flex items-center gap-2">
                <span className="text-xl">{kategori.ikon}</span>
                <h2 className="font-semibold text-gray-800">{kategori.ad}</h2>
                <span className="ml-auto text-xs text-gray-500 bg-gray-200 px-2 py-0.5 rounded-full">
                  {kategori.sablonlar.length} şablon
                </span>
              </div>

              {/* Şablon listesi */}
              <div className="divide-y divide-gray-100">
                {kategori.sablonlar.map((sablon) => (
                  <div key={sablon.kod} className="flex items-center gap-4 px-5 py-3 hover:bg-gray-50">
                    <span className="text-2xl w-8 text-center">{sablon.ikon}</span>

                    <div className="flex-1">
                      <p className="font-medium text-sm text-gray-900">{sablon.ad}</p>
                      <p className="text-xs text-gray-400 font-mono">{sablon.kod}</p>
                    </div>

                    {/* Aktif/Pasif toggle */}
                    <label className="flex items-center gap-2 cursor-pointer">
                      <span className="text-xs text-gray-500">{sablon.aktif ? "Aktif" : "Pasif"}</span>
                      <div
                        onClick={() => aktifligDegistir(sablon.kod, !sablon.aktif)}
                        className={`w-10 h-5 rounded-full transition-colors cursor-pointer relative
                          ${sablon.aktif ? "bg-blue-500" : "bg-gray-300"}`}
                      >
                        <div className={`absolute top-0.5 w-4 h-4 bg-white rounded-full shadow transition-transform
                          ${sablon.aktif ? "translate-x-5" : "translate-x-0.5"}`}
                        />
                      </div>
                    </label>

                    {/* Detay butonu */}
                    <button
                      onClick={() => setSeciliSablon(sablon)}
                      className="px-3 py-1 text-xs border border-gray-300 text-gray-600 rounded-lg hover:bg-gray-100"
                    >
                      Detay
                    </button>
                  </div>
                ))}
              </div>
            </div>
          ))}
        </div>
      )}

      {/* Detay Modal */}
      {seciliSablon && (
        <div className="fixed inset-0 bg-black/40 flex items-center justify-center z-50 p-4">
          <div className="bg-white rounded-xl shadow-xl max-w-lg w-full p-6 space-y-4">
            <div className="flex items-start justify-between">
              <div className="flex items-center gap-3">
                <span className="text-3xl">{seciliSablon.ikon}</span>
                <div>
                  <h2 className="font-bold text-gray-900">{seciliSablon.ad}</h2>
                  <p className="text-xs text-gray-400 font-mono">{seciliSablon.kod}</p>
                </div>
              </div>
              <button
                onClick={() => setSeciliSablon(null)}
                className="text-gray-400 hover:text-gray-600 text-xl"
              >
                ×
              </button>
            </div>

            <div className="text-sm text-gray-600 space-y-2">
              <p><span className="font-medium">Kategori:</span> {seciliSablon.kategori}</p>
              <p><span className="font-medium">Durum:</span> {seciliSablon.aktif ? "✅ Aktif" : "⛔ Pasif"}</p>
              {seciliSablon.aciklama && (
                <p><span className="font-medium">Açıklama:</span> {seciliSablon.aciklama}</p>
              )}
            </div>

            <div className="flex gap-2 pt-2">
              <button
                onClick={() => aktifligDegistir(seciliSablon.kod, !seciliSablon.aktif)}
                className={`flex-1 py-2 text-sm rounded-lg font-medium
                  ${seciliSablon.aktif
                    ? "bg-red-50 text-red-600 border border-red-200 hover:bg-red-100"
                    : "bg-green-50 text-green-600 border border-green-200 hover:bg-green-100"
                  }`}
              >
                {seciliSablon.aktif ? "Pasif Yap" : "Aktif Yap"}
              </button>
              <button
                onClick={() => setSeciliSablon(null)}
                className="flex-1 py-2 text-sm bg-gray-100 text-gray-700 rounded-lg hover:bg-gray-200"
              >
                Kapat
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  )
}
