/**
 * VoiceAI Platform — TestButton Bileşeni
 * Entegrasyon bağlantılarını test eden buton.
 * 
 * Kullanım:
 *   <TestButton onTest={async () => {
 *     const sonuc = await api.testSip(ayarlar)
 *     return sonuc
 *   }} />
 */
"use client"

import { useState } from "react"
import { Loader2, CheckCircle, XCircle, Wifi } from "lucide-react"

interface TestResult {
  basarili: boolean
  mesaj: string
}

type Durum = "bosta" | "test_ediliyor" | "basarili" | "basarisiz"

interface TestButtonProps {
  onTest: () => Promise<TestResult>
  label?: string
  kucuk?: boolean
}

export default function TestButton({
  onTest,
  label = "Test Et",
  kucuk = false,
}: TestButtonProps) {
  const [durum, setDurum] = useState<Durum>("bosta")
  const [sonucMesaj, setSonucMesaj] = useState("")

  const handleTest = async () => {
    setDurum("test_ediliyor")
    setSonucMesaj("")

    try {
      const sonuc = await onTest()
      setDurum(sonuc.basarili ? "basarili" : "basarisiz")
      setSonucMesaj(sonuc.mesaj)

      // 5 saniye sonra sıfırla
      setTimeout(() => {
        setDurum("bosta")
        setSonucMesaj("")
      }, 5000)
    } catch (err) {
      setDurum("basarisiz")
      setSonucMesaj("Bağlantı testi başarısız oldu.")
      setTimeout(() => setDurum("bosta"), 5000)
    }
  }

  const ikon = {
    bosta:          <Wifi size={kucuk ? 14 : 16} />,
    test_ediliyor:  <Loader2 size={kucuk ? 14 : 16} className="animate-spin" />,
    basarili:       <CheckCircle size={kucuk ? 14 : 16} />,
    basarisiz:      <XCircle size={kucuk ? 14 : 16} />,
  }[durum]

  const renkler = {
    bosta:          "bg-gray-100 text-gray-700 hover:bg-gray-200 border-gray-300",
    test_ediliyor:  "bg-blue-100 text-blue-700 border-blue-300 cursor-not-allowed",
    basarili:       "bg-green-100 text-green-700 border-green-300",
    basarisiz:      "bg-red-100 text-red-700 border-red-300",
  }[durum]

  const metinler = {
    bosta:          label,
    test_ediliyor:  "Test ediliyor...",
    basarili:       "Başarılı",
    basarisiz:      "Başarısız",
  }[durum]

  return (
    <div className="space-y-1">
      <button
        type="button"
        onClick={handleTest}
        disabled={durum === "test_ediliyor"}
        className={`
          flex items-center gap-1.5 border rounded-lg font-medium
          transition-all duration-200
          ${kucuk ? "px-2.5 py-1.5 text-xs" : "px-3 py-2 text-sm"}
          ${renkler}
        `}
      >
        {ikon}
        <span>{metinler}</span>
      </button>

      {/* Sonuç mesajı */}
      {sonucMesaj && (
        <p className={`text-xs ${durum === "basarili" ? "text-green-600" : "text-red-600"}`}>
          {sonucMesaj}
        </p>
      )}
    </div>
  )
}
