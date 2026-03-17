/**
 * VoiceAI Platform — ApiKeyInput Bileşeni
 * Şifreli API anahtarları ve şifre alanları için özel input.
 * 
 * Kullanım:
 *   <ApiKeyInput
 *     label="Netgsm SIP Şifresi"
 *     value={sifre}
 *     onChange={setSifre}
 *     isEncrypted
 *     onTest={() => handleTest('sip_netgsm')}
 *   />
 */
"use client"

import { useState } from "react"
import { Eye, EyeOff, Edit2, X, Check } from "lucide-react"
import TestButton from "./TestButton"

interface ApiKeyInputProps {
  label: string
  value: string
  onChange: (val: string) => void
  isEncrypted?: boolean      // Şifreli alan mı? (••••••• göster)
  placeholder?: string
  hint?: string              // Küçük açıklama metni
  onTest?: () => Promise<TestResult>  // Test Et butonu
  disabled?: boolean
  required?: boolean
}

interface TestResult {
  basarili: boolean
  mesaj: string
}

export default function ApiKeyInput({
  label,
  value,
  onChange,
  isEncrypted = false,
  placeholder,
  hint,
  onTest,
  disabled = false,
  required = false,
}: ApiKeyInputProps) {
  const [goster, setGoster] = useState(false)
  const [duzenliyor, setDuzenliyor] = useState(false)
  const [geciciDeger, setGeciciDeger] = useState("")

  // Şifreli alanda mevcut değer varsa "dolu" kabul et
  const dolu = value && value.length > 0
  const maskeli = isEncrypted && dolu && !duzenliyor

  const duzenlemeyiBaslat = () => {
    setGeciciDeger("")
    setDuzenliyor(true)
  }

  const duzenlemeyiIptalEt = () => {
    setGeciciDeger("")
    setDuzenliyor(false)
  }

  const duzenlemeyiKaydet = () => {
    if (geciciDeger) {
      onChange(geciciDeger)
    }
    setDuzenliyor(false)
    setGeciciDeger("")
  }

  return (
    <div className="space-y-1">
      {/* Label */}
      <label className="block text-sm font-medium text-gray-700">
        {label}
        {required && <span className="text-red-500 ml-1">*</span>}
      </label>

      {/* Input Alanı */}
      <div className="flex gap-2">
        <div className="relative flex-1">
          {maskeli ? (
            /* Şifreli değer — masked göster */
            <div className="flex items-center w-full px-3 py-2 border border-gray-300 rounded-lg bg-gray-50 text-gray-500">
              <span className="flex-1 font-mono text-sm tracking-widest">
                {value}
              </span>
              <button
                type="button"
                onClick={duzenlemeyiBaslat}
                className="ml-2 p-1 text-gray-400 hover:text-blue-600 transition-colors"
                title="Düzenle"
              >
                <Edit2 size={14} />
              </button>
            </div>
          ) : duzenliyor ? (
            /* Düzenleme modu */
            <div className="flex items-center gap-2">
              <input
                type={goster ? "text" : "password"}
                value={geciciDeger}
                onChange={(e) => setGeciciDeger(e.target.value)}
                placeholder="Yeni değeri girin..."
                className="flex-1 px-3 py-2 border border-blue-400 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500 font-mono text-sm"
                autoFocus
                onKeyDown={(e) => {
                  if (e.key === "Enter") duzenlemeyiKaydet()
                  if (e.key === "Escape") duzenlemeyiIptalEt()
                }}
              />
              <button
                type="button"
                onClick={() => setGoster(!goster)}
                className="p-2 text-gray-400 hover:text-gray-600"
              >
                {goster ? <EyeOff size={16} /> : <Eye size={16} />}
              </button>
              <button
                type="button"
                onClick={duzenlemeyiKaydet}
                className="p-2 text-green-600 hover:text-green-700"
                title="Onayla"
              >
                <Check size={16} />
              </button>
              <button
                type="button"
                onClick={duzenlemeyiIptalEt}
                className="p-2 text-red-500 hover:text-red-600"
                title="İptal"
              >
                <X size={16} />
              </button>
            </div>
          ) : (
            /* Normal input */
            <div className="relative">
              <input
                type={isEncrypted && !goster ? "password" : "text"}
                value={value}
                onChange={(e) => onChange(e.target.value)}
                placeholder={placeholder}
                disabled={disabled}
                className="w-full px-3 py-2 border border-gray-300 rounded-lg
                           focus:outline-none focus:ring-2 focus:ring-blue-500
                           disabled:bg-gray-100 disabled:cursor-not-allowed
                           font-mono text-sm pr-10"
              />
              {isEncrypted && (
                <button
                  type="button"
                  onClick={() => setGoster(!goster)}
                  className="absolute right-3 top-1/2 -translate-y-1/2 text-gray-400 hover:text-gray-600"
                >
                  {goster ? <EyeOff size={16} /> : <Eye size={16} />}
                </button>
              )}
            </div>
          )}
        </div>

        {/* Test Et Butonu */}
        {onTest && !duzenliyor && (
          <TestButton onTest={onTest} />
        )}
      </div>

      {/* Hint metni */}
      {hint && (
        <p className="text-xs text-gray-500">{hint}</p>
      )}

      {/* Şifreli alan bilgisi */}
      {isEncrypted && dolu && !duzenliyor && (
        <p className="text-xs text-green-600 flex items-center gap-1">
          <span>🔒</span> Şifrelenmiş olarak saklanıyor
        </p>
      )}
    </div>
  )
}
