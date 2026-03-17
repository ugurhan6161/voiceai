/**
 * VoiceAI Platform — Admin Sistem Ayarları Sayfası
 * SIP, SMS, iyzico, SMTP ayarlarını panelden yönetme.
 */
"use client"

import { useState, useEffect } from "react"
import ApiKeyInput from "@/components/settings/ApiKeyInput"
import TestButton from "@/components/settings/TestButton"

type Sekme = "sip" | "sms" | "odeme" | "email" | "genel"

interface SipAyarlari {
  host: string
  kullanici: string
  sifre: string
  aktif: boolean
}

interface IyzicoAyarlari {
  api_key: string
  secret_key: string
  mod: "sandbox" | "production"
}

export default function SistemAyarlariSayfasi() {
  const [aktifSekme, setAktifSekme] = useState<Sekme>("sip")
  const [kaydediliyor, setKaydediliyor] = useState(false)
  const [basariMesaji, setBasariMesaji] = useState("")

  // SIP Ayarları
  const [netgsmSip, setNetgsmSip] = useState<SipAyarlari>({
    host: "sip.netgsm.com.tr",
    kullanici: "",
    sifre: "",
    aktif: true,
  })
  const [verimorSip, setVerimorSip] = useState<SipAyarlari>({
    host: "sip.verimor.com.tr",
    kullanici: "",
    sifre: "",
    aktif: false,
  })

  // SMS Ayarları
  const [smsKullanici, setSmsKullanici] = useState("")
  const [smsSifre, setSmsSifre] = useState("")
  const [smsBaslik, setSmsBaslik] = useState("")

  // iyzico Ayarları
  const [iyzico, setIyzico] = useState<IyzicoAyarlari>({
    api_key: "",
    secret_key: "",
    mod: "sandbox",
  })

  // SMTP Ayarları
  const [smtp, setSmtp] = useState({
    host: "",
    port: "587",
    kullanici: "",
    sifre: "",
    gonderen_ad: "",
  })

  const ayarlariKaydet = async (tip: string) => {
    setKaydediliyor(true)
    try {
      const endpointler: Record<string, { url: string; veri: object }> = {
        sip_netgsm: { url: "/api/ayarlar/sistem/sip/netgsm", veri: netgsmSip },
        sip_verimor: { url: "/api/ayarlar/sistem/sip/verimor", veri: verimorSip },
        sms: { url: "/api/ayarlar/sistem/sms/netgsm", veri: { kullanici: smsKullanici, sifre: smsSifre, baslik: smsBaslik } },
        iyzico: { url: "/api/ayarlar/sistem/iyzico", veri: iyzico },
        smtp: { url: "/api/ayarlar/sistem/smtp", veri: smtp },
      }

      const { url, veri } = endpointler[tip]
      const yanit = await fetch(url, {
        method: "PUT",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(veri),
      })

      if (yanit.ok) {
        setBasariMesaji("✅ Ayarlar kaydedildi.")
        setTimeout(() => setBasariMesaji(""), 3000)
      }
    } finally {
      setKaydediliyor(false)
    }
  }

  const baglantiTest = async (tur: string, ayarlar: object) => {
    const yanit = await fetch("/api/ayarlar/test", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ tur, ayarlar }),
    })
    return await yanit.json()
  }

  const sekmeler: { id: Sekme; ad: string; ikon: string }[] = [
    { id: "sip",    ad: "SIP / Telefon",    ikon: "📞" },
    { id: "sms",    ad: "SMS",               ikon: "💬" },
    { id: "odeme",  ad: "Ödeme (iyzico)",    ikon: "💳" },
    { id: "email",  ad: "E-posta (SMTP)",    ikon: "📧" },
    { id: "genel",  ad: "Genel",             ikon: "⚙️" },
  ]

  return (
    <div className="max-w-4xl mx-auto p-6 space-y-6">
      <div>
        <h1 className="text-2xl font-bold text-gray-900">Sistem Ayarları</h1>
        <p className="text-gray-500 text-sm mt-1">
          Tüm API anahtarları ve şifreler AES-256 ile şifrelenmiş olarak saklanır.
        </p>
      </div>

      {basariMesaji && (
        <div className="bg-green-50 border border-green-200 text-green-700 px-4 py-3 rounded-lg text-sm">
          {basariMesaji}
        </div>
      )}

      {/* Sekmeler */}
      <div className="flex gap-1 border-b border-gray-200">
        {sekmeler.map((s) => (
          <button
            key={s.id}
            onClick={() => setAktifSekme(s.id)}
            className={`px-4 py-2.5 text-sm font-medium rounded-t-lg transition-colors flex items-center gap-1.5
              ${aktifSekme === s.id
                ? "bg-white border border-b-white border-gray-200 text-blue-600 -mb-px"
                : "text-gray-500 hover:text-gray-700"
              }`}
          >
            <span>{s.ikon}</span> {s.ad}
          </button>
        ))}
      </div>

      {/* ── SIP Ayarları ── */}
      {aktifSekme === "sip" && (
        <div className="space-y-6">
          {/* Netgsm */}
          <div className="bg-white border border-gray-200 rounded-xl p-6 space-y-4">
            <div className="flex items-center justify-between">
              <h2 className="font-semibold text-gray-800 flex items-center gap-2">
                <span>📞</span> Netgsm SIP Trunk
              </h2>
              <label className="flex items-center gap-2 text-sm text-gray-600">
                <input
                  type="checkbox"
                  checked={netgsmSip.aktif}
                  onChange={(e) => setNetgsmSip({ ...netgsmSip, aktif: e.target.checked })}
                  className="rounded"
                />
                Aktif
              </label>
            </div>

            <div className="grid grid-cols-2 gap-4">
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">SIP Host</label>
                <input
                  type="text"
                  value={netgsmSip.host}
                  onChange={(e) => setNetgsmSip({ ...netgsmSip, host: e.target.value })}
                  className="w-full px-3 py-2 border border-gray-300 rounded-lg text-sm"
                />
              </div>
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">Kullanıcı Adı</label>
                <input
                  type="text"
                  value={netgsmSip.kullanici}
                  onChange={(e) => setNetgsmSip({ ...netgsmSip, kullanici: e.target.value })}
                  placeholder="05XXXXXXXXX"
                  className="w-full px-3 py-2 border border-gray-300 rounded-lg text-sm"
                />
              </div>
            </div>

            <ApiKeyInput
              label="SIP Şifresi"
              value={netgsmSip.sifre}
              onChange={(v) => setNetgsmSip({ ...netgsmSip, sifre: v })}
              isEncrypted
              placeholder="Netgsm SIP şifreniz"
              onTest={() => baglantiTest("sip_netgsm", netgsmSip)}
            />

            <button
              onClick={() => ayarlariKaydet("sip_netgsm")}
              disabled={kaydediliyor}
              className="px-4 py-2 bg-blue-600 text-white rounded-lg text-sm hover:bg-blue-700 disabled:opacity-50"
            >
              {kaydediliyor ? "Kaydediliyor..." : "Kaydet"}
            </button>
          </div>

          {/* Verimor */}
          <div className="bg-white border border-gray-200 rounded-xl p-6 space-y-4">
            <div className="flex items-center justify-between">
              <h2 className="font-semibold text-gray-800 flex items-center gap-2">
                <span>📞</span> Verimor SIP Trunk
              </h2>
              <label className="flex items-center gap-2 text-sm text-gray-600">
                <input
                  type="checkbox"
                  checked={verimorSip.aktif}
                  onChange={(e) => setVerimorSip({ ...verimorSip, aktif: e.target.checked })}
                  className="rounded"
                />
                Aktif
              </label>
            </div>

            <ApiKeyInput
              label="Verimor SIP Şifresi"
              value={verimorSip.sifre}
              onChange={(v) => setVerimorSip({ ...verimorSip, sifre: v })}
              isEncrypted
              onTest={() => baglantiTest("sip_verimor", verimorSip)}
            />

            <button
              onClick={() => ayarlariKaydet("sip_verimor")}
              disabled={kaydediliyor}
              className="px-4 py-2 bg-blue-600 text-white rounded-lg text-sm hover:bg-blue-700 disabled:opacity-50"
            >
              Kaydet
            </button>
          </div>
        </div>
      )}

      {/* ── SMS Ayarları ── */}
      {aktifSekme === "sms" && (
        <div className="bg-white border border-gray-200 rounded-xl p-6 space-y-4">
          <h2 className="font-semibold text-gray-800">💬 Netgsm SMS API</h2>

          <div className="grid grid-cols-2 gap-4">
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">Kullanıcı Adı</label>
              <input
                type="text"
                value={smsKullanici}
                onChange={(e) => setSmsKullanici(e.target.value)}
                className="w-full px-3 py-2 border border-gray-300 rounded-lg text-sm"
              />
            </div>
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">SMS Başlığı</label>
              <input
                type="text"
                value={smsBaslik}
                onChange={(e) => setSmsBaslik(e.target.value)}
                placeholder="FIRMAADINIZ"
                className="w-full px-3 py-2 border border-gray-300 rounded-lg text-sm"
              />
            </div>
          </div>

          <ApiKeyInput
            label="SMS API Şifresi"
            value={smsSifre}
            onChange={setSmsSifre}
            isEncrypted
            onTest={() => baglantiTest("sms_netgsm", { kullanici: smsKullanici, sifre: smsSifre })}
          />

          <button
            onClick={() => ayarlariKaydet("sms")}
            className="px-4 py-2 bg-blue-600 text-white rounded-lg text-sm hover:bg-blue-700"
          >
            Kaydet
          </button>
        </div>
      )}

      {/* ── iyzico Ayarları ── */}
      {aktifSekme === "odeme" && (
        <div className="bg-white border border-gray-200 rounded-xl p-6 space-y-4">
          <h2 className="font-semibold text-gray-800">💳 iyzico Ödeme Sistemi</h2>

          <div className="flex gap-4">
            <label className="flex items-center gap-2 text-sm">
              <input
                type="radio"
                checked={iyzico.mod === "sandbox"}
                onChange={() => setIyzico({ ...iyzico, mod: "sandbox" })}
              />
              <span className="text-yellow-600 font-medium">🧪 Sandbox (Test)</span>
            </label>
            <label className="flex items-center gap-2 text-sm">
              <input
                type="radio"
                checked={iyzico.mod === "production"}
                onChange={() => setIyzico({ ...iyzico, mod: "production" })}
              />
              <span className="text-green-600 font-medium">🚀 Production (Canlı)</span>
            </label>
          </div>

          {iyzico.mod === "production" && (
            <div className="bg-orange-50 border border-orange-200 text-orange-700 px-3 py-2 rounded-lg text-sm">
              ⚠️ Production modunda gerçek ödemeler alınır. Dikkatli olun.
            </div>
          )}

          <ApiKeyInput
            label="API Key"
            value={iyzico.api_key}
            onChange={(v) => setIyzico({ ...iyzico, api_key: v })}
            isEncrypted
            hint="iyzico merchant panelinden alınır"
          />
          <ApiKeyInput
            label="Secret Key"
            value={iyzico.secret_key}
            onChange={(v) => setIyzico({ ...iyzico, secret_key: v })}
            isEncrypted
            onTest={() => baglantiTest("iyzico", iyzico)}
          />

          <button
            onClick={() => ayarlariKaydet("iyzico")}
            className="px-4 py-2 bg-blue-600 text-white rounded-lg text-sm hover:bg-blue-700"
          >
            Kaydet
          </button>
        </div>
      )}

      {/* ── SMTP Ayarları ── */}
      {aktifSekme === "email" && (
        <div className="bg-white border border-gray-200 rounded-xl p-6 space-y-4">
          <h2 className="font-semibold text-gray-800">📧 E-posta (SMTP)</h2>

          <div className="grid grid-cols-3 gap-4">
            <div className="col-span-2">
              <label className="block text-sm font-medium text-gray-700 mb-1">SMTP Host</label>
              <input
                type="text"
                value={smtp.host}
                onChange={(e) => setSmtp({ ...smtp, host: e.target.value })}
                placeholder="smtp.gmail.com"
                className="w-full px-3 py-2 border border-gray-300 rounded-lg text-sm"
              />
            </div>
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">Port</label>
              <input
                type="text"
                value={smtp.port}
                onChange={(e) => setSmtp({ ...smtp, port: e.target.value })}
                className="w-full px-3 py-2 border border-gray-300 rounded-lg text-sm"
              />
            </div>
          </div>

          <div className="grid grid-cols-2 gap-4">
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">E-posta Adresi</label>
              <input
                type="email"
                value={smtp.kullanici}
                onChange={(e) => setSmtp({ ...smtp, kullanici: e.target.value })}
                className="w-full px-3 py-2 border border-gray-300 rounded-lg text-sm"
              />
            </div>
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">Gönderen Adı</label>
              <input
                type="text"
                value={smtp.gonderen_ad}
                onChange={(e) => setSmtp({ ...smtp, gonderen_ad: e.target.value })}
                placeholder="VoiceAI Platform"
                className="w-full px-3 py-2 border border-gray-300 rounded-lg text-sm"
              />
            </div>
          </div>

          <ApiKeyInput
            label="E-posta Şifresi / Uygulama Şifresi"
            value={smtp.sifre}
            onChange={(v) => setSmtp({ ...smtp, sifre: v })}
            isEncrypted
            hint="Gmail için 'Uygulama Şifresi' oluşturun"
            onTest={() => baglantiTest("smtp", smtp)}
          />

          <button
            onClick={() => ayarlariKaydet("smtp")}
            className="px-4 py-2 bg-blue-600 text-white rounded-lg text-sm hover:bg-blue-700"
          >
            Kaydet
          </button>
        </div>
      )}
    </div>
  )
}
