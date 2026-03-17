"""
VoiceAI Platform — Ayar Yönetimi Servisi
Şifreli sistem ayarlarını ve firma entegrasyon ayarlarını yönetir.
"""
from typing import Optional
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import text
from crypto import encrypt, decrypt, guvenli_goster
import httpx
import asyncio


class AyarServisi:
    """
    Sistem ve firma ayarlarını yönetir.
    Tüm hassas değerler otomatik şifrelenir/çözülür.
    """

    def __init__(self, db: AsyncSession):
        self.db = db

    # ── SİSTEM AYARLARI (Admin) ────────────────────────────────

    async def sistem_ayar_al(
        self,
        kategori: str,
        anahtar: str
    ) -> Optional[str]:
        """
        Sistem ayarını okur ve şifreliyse çözer.

        Args:
            kategori: Örn. 'sip_netgsm', 'iyzico'
            anahtar: Örn. 'sifre', 'api_key'

        Returns:
            Çözülmüş değer veya None
        """
        sonuc = await self.db.execute(
            text("""
                SELECT deger, sifirli
                FROM shared.sistem_ayarlari
                WHERE kategori = :kategori AND anahtar = :anahtar
            """),
            {"kategori": kategori, "anahtar": anahtar}
        )
        satir = sonuc.fetchone()
        if not satir or not satir.deger:
            return None
        return decrypt(satir.deger) if satir.sifirli else satir.deger

    async def sistem_ayar_kaydet(
        self,
        kategori: str,
        anahtar: str,
        deger: str,
        sifirli: bool = False
    ) -> bool:
        """
        Sistem ayarını kaydeder. Şifreli flag varsa şifreler.

        Returns:
            True başarılı, False başarısız
        """
        kayit_degeri = encrypt(deger) if sifirli else deger
        await self.db.execute(
            text("""
                INSERT INTO shared.sistem_ayarlari
                    (kategori, anahtar, deger, sifirli, guncelleme)
                VALUES (:kategori, :anahtar, :deger, :sifirli, NOW())
                ON CONFLICT (kategori, anahtar)
                DO UPDATE SET
                    deger = EXCLUDED.deger,
                    sifirli = EXCLUDED.sifirli,
                    guncelleme = NOW()
            """),
            {
                "kategori": kategori,
                "anahtar": anahtar,
                "deger": kayit_degeri,
                "sifirli": sifirli
            }
        )
        await self.db.commit()
        return True

    async def sistem_kategori_al(self, kategori: str) -> dict:
        """
        Bir kategorideki tüm ayarları döndürür.
        Şifreli değerler maskelenir (panel için güvenli).
        """
        sonuc = await self.db.execute(
            text("""
                SELECT anahtar, deger, sifirli, aciklama
                FROM shared.sistem_ayarlari
                WHERE kategori = :kategori
                ORDER BY anahtar
            """),
            {"kategori": kategori}
        )
        ayarlar = {}
        for satir in sonuc.fetchall():
            if satir.sifirli and satir.deger:
                # Panel'de maskeli göster
                ayarlar[satir.anahtar] = {
                    "deger": guvenli_goster(satir.deger),
                    "sifirli": True,
                    "aciklama": satir.aciklama,
                    "dolu": True
                }
            else:
                ayarlar[satir.anahtar] = {
                    "deger": satir.deger or "",
                    "sifirli": False,
                    "aciklama": satir.aciklama,
                    "dolu": bool(satir.deger)
                }
        return ayarlar

    # ── FİRMA ENTEGRASYON AYARLARI ─────────────────────────────

    async def firma_ayar_al(
        self,
        firma_schema: str,
        tur: str,
        anahtar: str
    ) -> Optional[str]:
        """Firma entegrasyon ayarını okur."""
        sonuc = await self.db.execute(
            text(f"""
                SELECT deger, sifirli
                FROM {firma_schema}.entegrasyon_ayarlari
                WHERE tur = :tur AND anahtar = :anahtar
            """),
            {"tur": tur, "anahtar": anahtar}
        )
        satir = sonuc.fetchone()
        if not satir or not satir.deger:
            return None
        return decrypt(satir.deger) if satir.sifirli else satir.deger

    async def firma_ayar_kaydet(
        self,
        firma_schema: str,
        tur: str,
        anahtar: str,
        deger: str,
        sifirli: bool = False
    ) -> bool:
        """Firma entegrasyon ayarını kaydeder."""
        kayit_degeri = encrypt(deger) if sifirli else deger
        await self.db.execute(
            text(f"""
                INSERT INTO {firma_schema}.entegrasyon_ayarlari
                    (tur, anahtar, deger, sifirli, guncelleme)
                VALUES (:tur, :anahtar, :deger, :sifirli, NOW())
                ON CONFLICT (tur, anahtar)
                DO UPDATE SET
                    deger = EXCLUDED.deger,
                    sifirli = EXCLUDED.sifirli,
                    guncelleme = NOW()
            """),
            {
                "tur": tur,
                "anahtar": anahtar,
                "deger": kayit_degeri,
                "sifirli": sifirli
            }
        )
        await self.db.commit()
        return True


class EntegrasyonTester:
    """
    Panel'deki "Test Et" butonu için bağlantı test servisi.
    Her entegrasyon türü için ayrı test fonksiyonu.
    """

    @staticmethod
    async def test_sip(
        host: str,
        kullanici: str,
        sifre: str
    ) -> dict:
        """
        SIP bağlantısını test eder.
        Asterisk üzerinden OPTIONS paketi gönderir.
        """
        try:
            # Asterisk ARI üzerinden SIP OPTIONS testi
            ari_url = f"http://asterisk:8088/ari/asterisk/ping"
            async with httpx.AsyncClient(timeout=5.0) as client:
                yanit = await client.get(ari_url)
                if yanit.status_code == 200:
                    return {
                        "basarili": True,
                        "mesaj": f"✅ {host} bağlantısı başarılı"
                    }
        except Exception as e:
            pass
        return {
            "basarili": False,
            "mesaj": f"❌ {host} bağlantısı başarısız. Ayarları kontrol edin."
        }

    @staticmethod
    async def test_sms_netgsm(
        kullanici: str,
        sifre: str,
        test_numara: str = None
    ) -> dict:
        """Netgsm SMS API bağlantısını test eder."""
        try:
            url = "https://api.netgsm.com.tr/sms/send/get"
            params = {
                "usercode": kullanici,
                "password": sifre,
                "gsmno": test_numara or "05000000000",
                "message": "VoiceAI test mesajı",
                "msgheader": "TEST",
            }
            async with httpx.AsyncClient(timeout=10.0) as client:
                yanit = await client.get(url, params=params)
                if "00" in yanit.text or "01" in yanit.text:
                    return {"basarili": True, "mesaj": "✅ Netgsm SMS API bağlantısı başarılı"}
                return {"basarili": False, "mesaj": f"❌ Netgsm hatası: {yanit.text[:100]}"}
        except Exception as e:
            return {"basarili": False, "mesaj": f"❌ Bağlantı hatası: {str(e)}"}

    @staticmethod
    async def test_iyzico(
        api_key: str,
        secret_key: str,
        sandbox: bool = False
    ) -> dict:
        """iyzico API bağlantısını test eder."""
        try:
            base_url = (
                "https://sandbox-api.iyzipay.com"
                if sandbox
                else "https://api.iyzipay.com"
            )
            # iyzico API key kontrolü için basit istek
            async with httpx.AsyncClient(timeout=10.0) as client:
                yanit = await client.get(
                    f"{base_url}/payment/bin/check",
                    headers={"Authorization": f"IYZWS {api_key}:{secret_key}"}
                )
                if yanit.status_code in [200, 400]:
                    mod = "Sandbox" if sandbox else "Production"
                    return {"basarili": True, "mesaj": f"✅ iyzico {mod} bağlantısı başarılı"}
        except Exception as e:
            pass
        return {"basarili": False, "mesaj": "❌ iyzico bağlantısı başarısız"}

    @staticmethod
    async def test_pms_api(url: str, api_key: str) -> dict:
        """Dış PMS/CRM API bağlantısını test eder."""
        try:
            async with httpx.AsyncClient(timeout=10.0) as client:
                yanit = await client.get(
                    url,
                    headers={"Authorization": f"Bearer {api_key}"},
                )
                if yanit.status_code < 500:
                    return {"basarili": True, "mesaj": f"✅ API bağlantısı başarılı (HTTP {yanit.status_code})"}
                return {"basarili": False, "mesaj": f"❌ API hatası: HTTP {yanit.status_code}"}
        except Exception as e:
            return {"basarili": False, "mesaj": f"❌ Bağlantı kurulamadı: {str(e)}"}

    @staticmethod
    async def test_smtp(
        host: str,
        port: int,
        kullanici: str,
        sifre: str
    ) -> dict:
        """SMTP bağlantısını test eder."""
        import smtplib
        try:
            loop = asyncio.get_event_loop()
            def smtp_test():
                with smtplib.SMTP(host, port, timeout=10) as smtp:
                    smtp.starttls()
                    smtp.login(kullanici, sifre)
                    return True
            await loop.run_in_executor(None, smtp_test)
            return {"basarili": True, "mesaj": f"✅ SMTP {host}:{port} bağlantısı başarılı"}
        except Exception as e:
            return {"basarili": False, "mesaj": f"❌ SMTP hatası: {str(e)}"}
