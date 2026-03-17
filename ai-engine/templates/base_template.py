"""
VoiceAI Platform — Temel Şablon Sınıfı
Tüm sektör şablonları bu sınıftan miras alır.
"""
from abc import ABC, abstractmethod
from dataclasses import dataclass


@dataclass
class Slot:
    """Konuşmada toplanacak bilgi birimi."""
    ad: str           # Örn: "tarih"
    soru: str         # Örn: "Hangi tarih için rezervasyon istiyorsunuz?"
    zorunlu: bool = True
    tip: str = "metin"  # metin | tarih | saat | sayi | telefon


@dataclass
class Fonksiyon:
    """AI'ın çağırabileceği aksiyon."""
    ad: str
    aciklama: str
    parametreler: dict  # JSON Schema formatı
    tetikleyiciler: list[str]  # Türkçe tetikleyici kelimeler


class BaseTemplate(ABC):
    """
    Tüm sektör şablonlarının temel sınıfı.
    Yeni şablon eklemek için bu sınıftan miras al
    ve tüm abstract metodları implement et.
    """

    # Alt sınıf tarafından tanımlanır
    KOD: str = ""
    AD: str = ""
    KATEGORI: str = ""
    IKON: str = "🏢"

    @abstractmethod
    def get_db_schema(self) -> str:
        """
        Bu sektör için PostgreSQL tablo şemasını döndürür.
        {schema} placeholder'ı firma schema adı ile değiştirilir.
        """
        ...

    @abstractmethod
    def get_system_prompt(self, firma_adi: str, asistan_adi: str) -> str:
        """
        LLM için sistem promptunu döndürür.
        Asistan kişiliğini ve davranışını tanımlar.
        """
        ...

    @abstractmethod
    def get_functions(self) -> list[Fonksiyon]:
        """
        AI'ın kullanabileceği fonksiyonların listesini döndürür.
        Her fonksiyon bir DB aksiyonuna karşılık gelir.
        """
        ...

    @abstractmethod
    def get_slots(self) -> list[Slot]:
        """
        Bir işlemi tamamlamak için toplanması gereken
        bilgi birimlerinin listesini döndürür.
        """
        ...

    def get_sms_templates(self) -> dict:
        """
        Bu sektör için SMS şablonlarını döndürür.
        Alt sınıflar override edebilir.
        """
        return {
            "onay": "Sayın {isim}, {tarih} tarihli {hizmet} işleminiz onaylandı. {firma_adi}",
            "hatirlatma": "Sayın {isim}, {tarih} tarihindeki randevunuzu hatırlatırız. {firma_adi}",
            "iptal": "Sayın {isim}, {tarih} tarihli randevunuz iptal edildi. {firma_adi}",
        }

    def get_panel_modules(self) -> list[str]:
        """
        Bu sektör için firma panelinde gösterilecek
        modüllerin listesini döndürür.
        """
        return [
            "dashboard",
            "hizmetler",
            "takvim",
            "cagrilar",
            "sms",
            "entegrasyon",
            "raporlar",
            "fatura",
        ]

    def get_karsilama_metni(self, firma_adi: str) -> str:
        """Asistanın çağrıyı karşılama metni."""
        return f"Merhaba, {firma_adi}'e hoş geldiniz. Size nasıl yardımcı olabilirim?"

    def get_aktarim_metni(self) -> str:
        """Yetkili aktarımı öncesi müşteriye söylenen metin."""
        return "Sizi yetkili personelimize bağlıyorum, lütfen bekleyiniz."

    def get_mesai_disi_metni(self) -> str:
        """Mesai saati dışında söylenen metin."""
        return "Şu an çalışma saatlerimiz dışındasınız. Mesai saatlerimizde tekrar arayabilirsiniz."
