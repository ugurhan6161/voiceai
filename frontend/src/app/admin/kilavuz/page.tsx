'use client';

import React from 'react';

export default function AdminKilavuzPage() {
  const kilavuzContent = `
# VoiceAI Paneli Kullanım Kılavuzu

VoiceAI, yapay zeka destekli Türkçe sesli resepsiyonist SaaS platformudur.

## 1. Giriş Bilgileri
- **Admin Paneli:** http://31.57.77.166/admin/login
- **Firma Paneli:** http://31.57.77.166/firma/login

## 2. SIP / Zoiper Kurulumu
Çağrıları yanıtlamak için aşağıdaki bilgileri kullanın:
- **Domain:** 31.57.77.166
- **Port:** 5060
- **Kullanıcı:** firma_{id}_dahili
- **Protokol:** UDP

## 3. Çok Dilli Destek
Müşteriler çağrı başında dil seçimi yapabilir (TR/EN/AR/RU).
  `;

  return (
    <div className="p-8 max-w-4xl mx-auto">
      <div className="bg-white shadow rounded-lg p-8 prose">
        <h1 className="text-3xl font-bold mb-6 text-gray-900">Kullanım Kılavuzu</h1>
        
        <section className="mb-8">
          <h2 className="text-xl font-semibold mb-4 text-indigo-700">1. Sistem Erişimi</h2>
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            <div className="border p-4 rounded bg-gray-50">
              <h3 className="font-medium text-gray-800">Admin Paneli</h3>
              <p className="text-sm text-gray-600">Sistem ayarları ve firma yönetimi için kullanılır.</p>
              <a href="/admin/login" className="text-indigo-600 text-sm hover:underline mt-2 inline-block">Giriş Yap →</a>
            </div>
            <div className="border p-4 rounded bg-gray-50">
              <h3 className="font-medium text-gray-800">Firma Paneli</h3>
              <p className="text-sm text-gray-600">Ajan ayarları ve çağrı takibi için kullanılır.</p>
              <a href="/firma/login" className="text-indigo-600 text-sm hover:underline mt-2 inline-block">Giriş Yap →</a>
            </div>
          </div>
        </section>

        <section className="mb-8">
          <h2 className="text-xl font-semibold mb-4 text-indigo-700">2. Zoiper / MicroSIP Kurulumu</h2>
          <p className="text-gray-700 mb-4">Gelen çağrıları karşılamak için herhangi bir SIP istemcisi kullanabilirsiniz:</p>
          <ul className="list-disc pl-5 space-y-2 text-gray-600">
            <li><strong>Sunucu:</strong> 31.57.77.166</li>
            <li><strong>Kullanıcı:</strong> Dahili numaranız (Örn: firma_1_dahili)</li>
            <li><strong>Şifre:</strong> Ajan ayarlarında belirtilen şifre</li>
            <li><strong>Protokol:</strong> UDP (Port: 5060)</li>
          </ul>
        </section>

        <section className="mb-8">
          <h2 className="text-xl font-semibold mb-4 text-indigo-700">3. Dil Seçenekleri</h2>
          <p className="text-gray-700">Sistem 4 farklı dilde tam kapsamlı resepsiyonist hizmeti sunar:</p>
          <div className="flex gap-4 mt-2">
            <span className="px-3 py-1 bg-green-100 text-green-800 rounded-full text-sm">Türkçe</span>
            <span className="px-3 py-1 bg-blue-100 text-blue-800 rounded-full text-sm">English</span>
            <span className="px-3 py-1 bg-yellow-100 text-yellow-800 rounded-full text-sm">العربية</span>
            <span className="px-3 py-1 bg-red-100 text-red-800 rounded-full text-sm">Русский</span>
          </div>
        </section>

        <div className="mt-8 pt-6 border-t text-sm text-gray-500">
          Destek için: support@voiceai.com
        </div>
      </div>
    </div>
  );
}
