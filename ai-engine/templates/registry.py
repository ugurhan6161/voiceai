"""
VoiceAI Platform — Şablon Registry
Tüm sektör şablonlarını merkezi olarak yönetir.
"""
from typing import Dict, Optional, List, Type
from .base_template import BaseTemplate

# ── ŞABLON İMPORTLARI ────────────────────────────────────────
# Konaklama
from .konaklama.otel import OtelTemplate
from .konaklama.pansiyon_apart import PansiyonApartTemplate
from .konaklama.kamp_bungalov import KampBungalovTemplate

# Sağlık
from .saglik.klinik import KlinikTemplate
from .saglik.dis_klinigi import DisKlinigiTemplate
from .saglik.veteriner import VeterinerTemplate
from .saglik.psikolog import PsikologTemplate
from .saglik.fizik_tedavi import FizikTedaviTemplate

# Ev Hizmetleri
from .ev_hizmetleri.hali_yikama import HaliYikamaTemplate
from .ev_hizmetleri.kuru_temizleme import KuruTemizlemeTemplate
from .ev_hizmetleri.bahce_bakim import BahceBakimTemplate
from .ev_hizmetleri.ev_tamircisi import EvTamircisiTemplate
from .ev_hizmetleri.mobilya_tamiri import MobilyaTamiriTemplate
from .ev_hizmetleri.pvc_cam_usta import PvcCamUstaTemplate

# Enerji / Temel
from .enerji_temel.su_tup_bayii import SuTupBayiiTemplate
from .enerji_temel.elektrikci import ElektrikciTemplate
from .enerji_temel.tesisatci import TesisatciTemplate
from .enerji_temel.isitma_klima import IsitmaKlimaTemplate

# Araç / Taşıma
from .arac_tasima.oto_servis import OtoServisTemplate
from .arac_tasima.arac_kiralama import AracKiralamaTemplate
from .arac_tasima.arac_yikama import AracYikamaTemplate
from .arac_tasima.lastikci import LastikciTemplate
from .arac_tasima.ozel_sofor import OzelSoforTemplate

# Kişisel Bakım
from .kisisel_bakim.kuafor_berber import KuaforBerberTemplate
from .kisisel_bakim.guzellik_salonu import GuzellikSalonuTemplate
from .kisisel_bakim.epilasyon_lazer import EpilasyonLazerTemplate
from .kisisel_bakim.spor_salonu import SporSalonuTemplate

# Eğitim / Danışmanlık
from .egitim_danismanlik.ozel_ders import OzelDersTemplate
from .egitim_danismanlik.muzik_okulu import MuzikOkuluTemplate
from .egitim_danismanlik.avukatlik import AvukatlikTemplate
from .egitim_danismanlik.emlak import EmlakTemplate
from .egitim_danismanlik.muhasebe import MuhasebeTemplate

# Yiyecek / İçecek
from .yiyecek_icecek.restoran import RestoranTemplate
from .yiyecek_icecek.kafe import KafeTemplate
from .yiyecek_icecek.catering import CateringTemplate
from .yiyecek_icecek.pastane import PastaneTemplate

# Özel Hizmetler
from .ozel_hizmetler.dugun_organizasyon import DugunOrganizasyonTemplate
from .ozel_hizmetler.fotografci import FotografciTemplate
from .ozel_hizmetler.temizlik_sirketi import TemizlikSirketiTemplate
from .ozel_hizmetler.nakliyat import NakliyatTemplate
from .ozel_hizmetler.sigorta import SigortaTemplate

# ── REGISTRY ─────────────────────────────────────────────────
TEMPLATE_REGISTRY: Dict[str, Type[BaseTemplate]] = {
    # Konaklama
    "otel": OtelTemplate,
    "pansiyon_apart": PansiyonApartTemplate,
    "kamp_bungalov": KampBungalovTemplate,

    # Sağlık
    "klinik": KlinikTemplate,
    "dis_klinigi": DisKlinigiTemplate,
    "veteriner": VeterinerTemplate,
    "psikolog": PsikologTemplate,
    "fizik_tedavi": FizikTedaviTemplate,

    # Ev Hizmetleri
    "hali_yikama": HaliYikamaTemplate,
    "kuru_temizleme": KuruTemizlemeTemplate,
    "bahce_bakim": BahceBakimTemplate,
    "ev_tamircisi": EvTamircisiTemplate,
    "mobilya_tamiri": MobilyaTamiriTemplate,
    "pvc_cam_usta": PvcCamUstaTemplate,

    # Enerji / Temel
    "su_tup_bayii": SuTupBayiiTemplate,
    "elektrikci": ElektrikciTemplate,
    "tesisatci": TesisatciTemplate,
    "isitma_klima": IsitmaKlimaTemplate,

    # Araç / Taşıma
    "oto_servis": OtoServisTemplate,
    "arac_kiralama": AracKiralamaTemplate,
    "arac_yikama": AracYikamaTemplate,
    "lastikci": LastikciTemplate,
    "ozel_sofor": OzelSoforTemplate,

    # Kişisel Bakım
    "kuafor_berber": KuaforBerberTemplate,
    "guzellik_salonu": GuzellikSalonuTemplate,
    "epilasyon_lazer": EpilasyonLazerTemplate,
    "spor_salonu": SporSalonuTemplate,

    # Eğitim / Danışmanlık
    "ozel_ders": OzelDersTemplate,
    "muzik_okulu": MuzikOkuluTemplate,
    "avukatlik": AvukatlikTemplate,
    "emlak": EmlakTemplate,
    "muhasebe": MuhasebeTemplate,

    # Yiyecek / İçecek
    "restoran": RestoranTemplate,
    "kafe": KafeTemplate,
    "catering": CateringTemplate,
    "pastane": PastaneTemplate,

    # Özel Hizmetler
    "dugun_organizasyon": DugunOrganizasyonTemplate,
    "fotografci": FotografciTemplate,
    "temizlik_sirketi": TemizlikSirketiTemplate,
    "nakliyat": NakliyatTemplate,
    "sigorta": SigortaTemplate,
}

# Sektör grupları (frontend için)
SEKTOR_GRUPLARI = {
    "konaklama": {
        "ad": "Konaklama",
        "ikon": "🏨",
        "sablonlar": ["otel", "pansiyon_apart", "kamp_bungalov"],
    },
    "saglik": {
        "ad": "Sağlık",
        "ikon": "🏥",
        "sablonlar": ["klinik", "dis_klinigi", "veteriner", "psikolog", "fizik_tedavi"],
    },
    "ev_hizmetleri": {
        "ad": "Ev Hizmetleri",
        "ikon": "🏠",
        "sablonlar": ["hali_yikama", "kuru_temizleme", "bahce_bakim", "ev_tamircisi", "mobilya_tamiri", "pvc_cam_usta"],
    },
    "enerji_temel": {
        "ad": "Enerji & Temel",
        "ikon": "⚡",
        "sablonlar": ["su_tup_bayii", "elektrikci", "tesisatci", "isitma_klima"],
    },
    "arac_tasima": {
        "ad": "Araç & Taşıma",
        "ikon": "🚗",
        "sablonlar": ["oto_servis", "arac_kiralama", "arac_yikama", "lastikci", "ozel_sofor"],
    },
    "kisisel_bakim": {
        "ad": "Kişisel Bakım",
        "ikon": "💇",
        "sablonlar": ["kuafor_berber", "guzellik_salonu", "epilasyon_lazer", "spor_salonu"],
    },
    "egitim_danismanlik": {
        "ad": "Eğitim & Danışmanlık",
        "ikon": "📚",
        "sablonlar": ["ozel_ders", "muzik_okulu", "avukatlik", "emlak", "muhasebe"],
    },
    "yiyecek_icecek": {
        "ad": "Yiyecek & İçecek",
        "ikon": "🍽️",
        "sablonlar": ["restoran", "kafe", "catering", "pastane"],
    },
    "ozel_hizmetler": {
        "ad": "Özel Hizmetler",
        "ikon": "✨",
        "sablonlar": ["dugun_organizasyon", "fotografci", "temizlik_sirketi", "nakliyat", "sigorta"],
    },
}


def get_template(template_id: str) -> Optional[BaseTemplate]:
    """Template ID'ye göre şablon örneği döndür"""
    cls = TEMPLATE_REGISTRY.get(template_id)
    if cls:
        return cls()
    return None


def list_templates() -> List[dict]:
    """Tüm şablonları listele"""
    result = []
    for tid, cls in TEMPLATE_REGISTRY.items():
        t = cls()
        result.append({
            "id": tid,
            "ad": getattr(t, "template_adi", tid),
            "sektor": getattr(t, "sektor", ""),
            "aciklama": getattr(t, "aciklama", ""),
        })
    return result


def list_by_sektor(sektor: str) -> List[dict]:
    """Sektöre göre şablonları listele"""
    return [t for t in list_templates() if t["sektor"] == sektor]


def get_sektor_gruplari() -> dict:
    """Sektör gruplarını döndür"""
    return SEKTOR_GRUPLARI


def toplam_sablon_sayisi() -> int:
    """Toplam şablon sayısı"""
    return len(TEMPLATE_REGISTRY)
