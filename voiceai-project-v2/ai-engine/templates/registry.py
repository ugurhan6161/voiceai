"""
VoiceAI Platform — Şablon Registry
Tüm sektör şablonlarının merkezi kaydı.
Yeni şablon eklemek için bu dosyayı güncelle.
"""

# ── ŞABLON İMPORTLARI ─────────────────────────────────────────

# Konaklama & Turizm
from templates.konaklama.otel import OtelSablonu
from templates.konaklama.pansiyon_apart import PansiyonApartSablonu
from templates.konaklama.kamp_bungalov import KampBungalovSablonu
from templates.konaklama.tekne_yat import TekneYatSablonu

# Sağlık & Klinik
from templates.saglik.klinik_poliklinik import KlinikPoliklinikSablonu
from templates.saglik.dis_klinigi import DisKlinigi Sablonu
from templates.saglik.goz_klinigi import GozKlinigiSablonu
from templates.saglik.spa_masaj import SpaMasajSablonu
from templates.saglik.eczane import EczaneSablonu
from templates.saglik.veteriner import VeterinerSablonu

# Kişisel Bakım & Güzellik
from templates.kisisel_bakim.kuafor_berber import KuaforBerberSablonu
from templates.kisisel_bakim.guzellik_salonu import GuzellikSalonuSablonu
from templates.kisisel_bakim.epilasyon_lazer import EpilasyonLazerSablonu
from templates.kisisel_bakim.spor_salonu import SporSalonuSablonu

# Yiyecek & İçecek
from templates.yiyecek_icecek.restoran import RestoranSablonu
from templates.yiyecek_icecek.kafe import KafeSablonu
from templates.yiyecek_icecek.pastane import PastaneSablonu

# Ev & Yaşam Hizmetleri
from templates.ev_hizmetleri.hali_yikama import HaliYikamaSablonu
from templates.ev_hizmetleri.kuru_temizleme import KuruTemizlemeSablonu
from templates.ev_hizmetleri.ev_tamircisi import EvTamircisiSablonu
from templates.ev_hizmetleri.pvc_cam_usta import PvcCamUstaSablonu
from templates.ev_hizmetleri.mobilya_tamiri import MobilyaTamiriSablonu
from templates.ev_hizmetleri.bahce_bakim import BahceBakimSablonu

# Araç & Taşımacilik
from templates.arac_tasima.arac_kiralama import AracKiralamaSablonu
from templates.arac_tasima.oto_servis import OtoServisSablonu
from templates.arac_tasima.arac_yikama import AracYikamaSablonu
from templates.arac_tasima.lastikci import LastikciSablonu
from templates.arac_tasima.ozel_sofor import OzelSoforSablonu

# Enerji & Temel Hizmetler
from templates.enerji_temel.su_bayii import SuBayiiSablonu
from templates.enerji_temel.tup_gaz_bayii import TupGazBayiiSablonu
from templates.enerji_temel.elektrikci import ElektrikciSablonu
from templates.enerji_temel.tesisatci import TesisatciSablonu
from templates.enerji_temel.isitma_klima import IsitmaKlimaSablonu

# Eğitim & Danışmanlık
from templates.egitim_danismanlik.ozel_ders import OzelDersSablonu
from templates.egitim_danismanlik.muzik_okulu import MuzikOkuluSablonu
from templates.egitim_danismanlik.avukatlik import AvukatlikSablonu
from templates.egitim_danismanlik.muhasebe import MuhasebeSablonu
from templates.egitim_danismanlik.emlak import EmlakSablonu

# Özel Hizmetler
from templates.ozel_hizmetler.fotograf_studyo import FotografStudyoSablonu
from templates.ozel_hizmetler.evcil_hayvan import EvcilHayvanSablonu
from templates.ozel_hizmetler.organizasyon import OrganizasyonSablonu
from templates.ozel_hizmetler.matbaa import MatbaaSablonu
from templates.ozel_hizmetler.ozel_sablon import OzelSablonSablonu

# ── MERKEZ KAYIT ──────────────────────────────────────────────

SABLON_KAYITLARI: dict = {

    # Konaklama
    "otel":             OtelSablonu,
    "pansiyon_apart":   PansiyonApartSablonu,
    "kamp_bungalov":    KampBungalovSablonu,
    "tekne_yat":        TekneYatSablonu,

    # Sağlık
    "klinik_poliklinik": KlinikPoliklinikSablonu,
    "dis_klinigi":       DisKlinigiSablonu,
    "goz_klinigi":       GozKlinigiSablonu,
    "spa_masaj":         SpaMasajSablonu,
    "eczane":            EczaneSablonu,
    "veteriner":         VeterinerSablonu,

    # Kişisel Bakım
    "kuafor_berber":     KuaforBerberSablonu,
    "guzellik_salonu":   GuzellikSalonuSablonu,
    "epilasyon_lazer":   EpilasyonLazerSablonu,
    "spor_salonu":       SporSalonuSablonu,

    # Yiyecek & İçecek
    "restoran":          RestoranSablonu,
    "kafe":              KafeSablonu,
    "pastane":           PastaneSablonu,

    # Ev Hizmetleri
    "hali_yikama":       HaliYikamaSablonu,
    "kuru_temizleme":    KuruTemizlemeSablonu,
    "ev_tamircisi":      EvTamircisiSablonu,
    "pvc_cam_usta":      PvcCamUstaSablonu,
    "mobilya_tamiri":    MobilyaTamiriSablonu,
    "bahce_bakim":       BahceBakimSablonu,

    # Araç
    "arac_kiralama":     AracKiralamaSablonu,
    "oto_servis":        OtoServisSablonu,
    "arac_yikama":       AracYikamaSablonu,
    "lastikci":          LastikciSablonu,
    "ozel_sofor":        OzelSoforSablonu,

    # Enerji & Temel
    "su_bayii":          SuBayiiSablonu,
    "tup_gaz_bayii":     TupGazBayiiSablonu,
    "elektrikci":        ElektrikciSablonu,
    "tesisatci":         TesisatciSablonu,
    "isitma_klima":      IsitmaKlimaSablonu,

    # Eğitim & Danışmanlık
    "ozel_ders":         OzelDersSablonu,
    "muzik_okulu":       MuzikOkuluSablonu,
    "avukatlik":         AvukatlikSablonu,
    "muhasebe":          MuhasebeSablonu,
    "emlak":             EmlakSablonu,

    # Özel
    "fotograf_studyo":   FotografStudyoSablonu,
    "evcil_hayvan":      EvcilHayvanSablonu,
    "organizasyon":      OrganizasyonSablonu,
    "matbaa":            MatbaaSablonu,
    "ozel_sablon":       OzelSablonSablonu,
}

# Kategori bilgileri (panel için)
KATEGORILER = {
    "konaklama":          {"ad": "Konaklama & Turizm",        "ikon": "🏨"},
    "saglik":             {"ad": "Sağlık & Klinik",            "ikon": "🏥"},
    "kisisel_bakim":      {"ad": "Kişisel Bakım & Güzellik",   "ikon": "💈"},
    "yiyecek_icecek":     {"ad": "Yiyecek & İçecek",           "ikon": "🍽️"},
    "ev_hizmetleri":      {"ad": "Ev & Yaşam Hizmetleri",      "ikon": "🏠"},
    "arac_tasima":        {"ad": "Araç & Taşımacilik",          "ikon": "🚗"},
    "enerji_temel":       {"ad": "Enerji & Temel Hizmetler",   "ikon": "⚡"},
    "egitim_danismanlik": {"ad": "Eğitim & Danışmanlık",       "ikon": "📚"},
    "ozel_hizmetler":     {"ad": "Özel Hizmetler",             "ikon": "⭐"},
}


def get_sablon(kod: str):
    """Şablon koduna göre şablon sınıfını döndürür."""
    if kod not in SABLON_KAYITLARI:
        raise ValueError(f"Bilinmeyen şablon kodu: {kod}")
    return SABLON_KAYITLARI[kod]()


def get_tum_sablonlar() -> list[dict]:
    """Panel için tüm şablonların listesini döndürür."""
    return [
        {"kod": kod, "sinif": sinif.__name__}
        for kod, sinif in SABLON_KAYITLARI.items()
    ]
