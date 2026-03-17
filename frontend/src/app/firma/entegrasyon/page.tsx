/**
 * VoiceAI Platform — Firma Entegrasyon Ayarları Sayfası
 * Firmalar kendi SIP, PMS/CRM ve takvim bağlantılarını buradan yönetir.
 */
"use client"

import { useState } from "react"
import ApiKeyInput from "@/components/settings/ApiKeyInput"

type Sekme = "telefon" | "dis_sistem" | "takvim" | "webhook"

export default function FirmaEntegrasyonSayfasi() {
  const [aktifSekme, setAktifSekme] = useState<Sekme>("telefon")

  // Telefon
  const [sipNumara, setSipNumara] = useState("")
  const [sipSaglayici, setSipSaglayici] = useState("netgsm")

  // Dış sistem
  const [pmsUrl, setPmsUrl] = useState("")
  const [pmsApiKey, setPmsApiKey] = useState("")
  const [pmsBagli, setPmsBagli] = useState(false)

  // Google Calendar
  const [calendarBagli, setCalendarBagli] = useState(false)
  const [calendarEmail, setCalendarEmail] = useState("")

  // Webhook
  const [webhookUrl, setWebhookUrl] = useState("")
  const [webhookSecret, setWebhookSecret] = useState("")

  const baglantiTest = async (tur: string, ayarlar: object) => {
    const yanit = await fetch("/api/ayarlar/firma/test", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ tur, ayarlar }),
    })
    return await yanit.json()
  }

  const ayarKaydet = async (tur: string, ayarlar: object) => {
    await fetch("/api/ayarlar/firma/entegrasyon", {
      method: "PUT",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ tur, ayarlar }),
    })
  }

  const sekmeler = [
    { id: "telefon" as Sekme,    ad: "Telefon",      ikon: "📞" },
    { id: "dis_sistem" as Sekme, ad: "PMS / CRM",    ikon: "🔗" },
    { id: "takvim" as Sekme,     ad: "Takvim",       ikon: "📅" },
    { id: "webhook" as Sekme,    ad: "Webhook",      ikon: "🔔" },
  ]

  return (
    <div className="max-w-3xl mx-auto p-6 space-y-6">
      <div>
        <h1 className="text-2xl font-bold text-gray-900">Entegrasyon Ayarları</h1>
        <p className="text-sm text-gray-500 mt-1">
          Dış sistemlerle bağlantılarınızı yönetin. Tüm anahtarlar şifreli saklanır.
        </p>
      </div>

      {/* Sekmeler */}
      <div className="flex gap-1 border-b">
        {sekmeler.map((s) => (
          <button
            key={s.id}
            onClick={() => setAktifSekme(s.id)}
            className={`px-4 py-2.5 text-sm font-medium rounded-t-lg transition-colors flex items-center gap-1.5
              ${aktifSekme === s.id
                ? "bg-white border border-b-white border-gray-200 text-blue-600 -mb-px"
                : "text-gray-500 hover:text-gray-700"}`}
          >
            {s.ikon} {s.ad}
          </button>
        ))}
      </div>

      {/* ── Telefon ── */}
      {aktifSekme === "telefon" && (
        <div className="bg-white border border-gray-200 rounded-xl p-6 space-y-4">
          <h2 className="font-semibold text-gray-800">📞 Telefon Numarası</h2>
          <p className="text-sm text-gray-500">
            Asistanınızın cevap vereceği telefon numarasını ve SIP sağlayıcısını seçin.
          </p>

          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">
              Telefon Numarası
            </label>
            <input
              type="text"
              value={sipNumara}
              onChange={(e) => setSipNumara(e.target.value)}
              placeholder="0212 XXX XX XX"
              className="w-full px-3 py-2 border border-gray-300 rounded-lg text-sm"
            />
          </div>

          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">
              SIP Sağlayıcı
            </label>
            <div className="flex gap-4">
              {["netgsm", "verimor", "twilio"].map((s) => (
                <label key={s} className="flex items-center gap-2 text-sm cursor-pointer">
                  <input
                    type="radio"
                    name="sip_saglayici"
                    value={s}
                    checked={sipSaglayici === s}
                    onChange={() => setSipSaglayici(s)}
                    className="text-blue-600"
                  />
                  <span className="capitalize font-medium">{s}</span>
                </label>
              ))}
            </div>
          </div>

          <button
            onClick={() => ayarKaydet("sip_numarasi", { numara: sipNumara, saglayici: sipSaglayici })}
            className="px-4 py-2 bg-blue-600 text-white rounded-lg text-sm hover:bg-blue-700"
          >
            Kaydet
          </button>
        </div>
      )}

      {/* ── PMS/CRM ── */}
      {aktifSekme === "dis_sistem" && (
        <div className="bg-white border border-gray-200 rounded-xl p-6 space-y-4">
          <h2 className="font-semibold text-gray-800">🔗 Dış Sistem Entegrasyonu</h2>
          <p className="text-sm text-gray-500">
            Otel PMS, klinik HIS veya CRM sisteminizle bağlantı kurun.
            Bağlantı kurulduğunda asistan rezervasyonları doğrudan sisteminize yazar.
          </p>

          {pmsBagli && (
            <div className="bg-green-50 border border-green-200 text-green-700 px-3 py-2 rounded-lg text-sm flex items-center gap-2">
              ✅ Bağlantı aktif
            </div>
          )}

          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">API URL</label>
            <input
              type="url"
              value={pmsUrl}
              onChange={(e) => setPmsUrl(e.target.value)}
              placeholder="https://pms.sisteminiz.com/api/v1"
              className="w-full px-3 py-2 border border-gray-300 rounded-lg text-sm"
            />
          </div>

          <ApiKeyInput
            label="API Anahtarı"
            value={pmsApiKey}
            onChange={setPmsApiKey}
            isEncrypted
            hint="PMS/CRM sisteminizin API anahtarı"
            onTest={() => baglantiTest("pms_api", { url: pmsUrl, api_key: pmsApiKey })}
          />

          <button
            onClick={() => ayarKaydet("pms_api", { url: pmsUrl, api_key: pmsApiKey })}
            className="px-4 py-2 bg-blue-600 text-white rounded-lg text-sm hover:bg-blue-700"
          >
            Kaydet
          </button>
        </div>
      )}

      {/* ── Takvim ── */}
      {aktifSekme === "takvim" && (
        <div className="bg-white border border-gray-200 rounded-xl p-6 space-y-4">
          <h2 className="font-semibold text-gray-800">📅 Takvim Entegrasyonu</h2>
          <p className="text-sm text-gray-500">
            Takvim entegrasyonu sayesinde asistan gerçek müsaitlik durumunu görebilir.
          </p>

          {/* Google Calendar */}
          <div className="border border-gray-200 rounded-lg p-4 space-y-3">
            <div className="flex items-center justify-between">
              <div className="flex items-center gap-2">
                <span className="text-2xl">📅</span>
                <div>
                  <p className="font-medium text-sm">Google Calendar</p>
                  {calendarBagli && (
                    <p className="text-xs text-green-600">✅ Bağlı: {calendarEmail}</p>
                  )}
                </div>
              </div>
              {calendarBagli ? (
                <button
                  onClick={() => setCalendarBagli(false)}
                  className="px-3 py-1.5 text-sm border border-red-300 text-red-600 rounded-lg hover:bg-red-50"
                >
                  Bağlantıyı Kes
                </button>
              ) : (
                <button
                  onClick={() => {
                    // Google OAuth akışı başlatılır
                    window.location.href = "/api/auth/google/calendar"
                  }}
                  className="px-3 py-1.5 text-sm bg-white border border-gray-300 rounded-lg hover:bg-gray-50 flex items-center gap-1.5"
                >
                  <span>🔗</span> Google ile Bağla
                </button>
              )}
            </div>
          </div>

          {/* Outlook */}
          <div className="border border-gray-200 rounded-lg p-4">
            <div className="flex items-center justify-between">
              <div className="flex items-center gap-2">
                <span className="text-2xl">📆</span>
                <p className="font-medium text-sm">Outlook Calendar</p>
              </div>
              <button className="px-3 py-1.5 text-sm bg-white border border-gray-300 rounded-lg hover:bg-gray-50 flex items-center gap-1.5">
                <span>🔗</span> Microsoft ile Bağla
              </button>
            </div>
          </div>
        </div>
      )}

      {/* ── Webhook ── */}
      {aktifSekme === "webhook" && (
        <div className="bg-white border border-gray-200 rounded-xl p-6 space-y-4">
          <h2 className="font-semibold text-gray-800">🔔 Webhook Ayarları</h2>
          <p className="text-sm text-gray-500">
            Her çağrı sonunda belirlediğiniz URL'e bildirim gönderilir.
            Kendi sisteminizi tetiklemek için kullanın.
          </p>

          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">Webhook URL</label>
            <input
              type="url"
              value={webhookUrl}
              onChange={(e) => setWebhookUrl(e.target.value)}
              placeholder="https://sisteminiz.com/webhook/voiceai"
              className="w-full px-3 py-2 border border-gray-300 rounded-lg text-sm"
            />
          </div>

          <ApiKeyInput
            label="Webhook Secret"
            value={webhookSecret}
            onChange={setWebhookSecret}
            isEncrypted
            hint="İsteklerinizi doğrulamak için kullanılır (HMAC-SHA256)"
          />

          <div className="bg-gray-50 border border-gray-200 rounded-lg p-3 text-xs font-mono text-gray-600">
            <p className="font-semibold mb-1">Gönderilecek veri örneği:</p>
            {`{
  "firma_id": 1,
  "cagri_id": 12345,
  "telefon": "05XXXXXXXXX",
  "sonuc": "rezervasyon",
  "ozet": "2 kişilik oda, 15 Mart"
}`}
          </div>

          <button
            onClick={() => ayarKaydet("webhook", { url: webhookUrl, secret: webhookSecret })}
            className="px-4 py-2 bg-blue-600 text-white rounded-lg text-sm hover:bg-blue-700"
          >
            Kaydet
          </button>
        </div>
      )}
    </div>
  )
}
