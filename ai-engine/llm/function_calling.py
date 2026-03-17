"""
Function Calling Engine
LLM'den gelen JSON fonksiyon çağrılarını parse eder ve ilgili aksiyonları gerçekleştirir.
"""

import json
import logging
import asyncpg
from datetime import datetime
from typing import Dict, Any, Optional, List
import os

logger = logging.getLogger(__name__)


class FunctionCallingEngine:
    """LLM fonksiyon çağrılarını yönetir ve veritabanı işlemlerini gerçekleştirir."""
    
    def __init__(self):
        self.db_pool: Optional[asyncpg.Pool] = None
        self.supported_functions = {
            "rezervasyon_al": self._rezervasyon_al,
            "rezervasyon_sorgula": self._rezervasyon_sorgula,
            "rezervasyon_iptal": self._rezervasyon_iptal,
            "fiyat_sor": self._fiyat_sor,
            "musaitlik_kontrol": self._musaitlik_kontrol,
        }
        logger.info("FunctionCallingEngine initialized")
    
    async def initialize_db(self):
        """PostgreSQL bağlantı havuzunu başlatır."""
        try:
            db_host = os.getenv("POSTGRES_HOST", "postgres")
            db_port = int(os.getenv("POSTGRES_PORT", "5432"))
            db_name = os.getenv("POSTGRES_DB", "voiceai")
            db_user = os.getenv("POSTGRES_USER", "voiceai")
            db_password = os.getenv("POSTGRES_PASSWORD", "VoiceAI2026!")
            
            self.db_pool = await asyncpg.create_pool(
                host=db_host,
                port=db_port,
                database=db_name,
                user=db_user,
                password=db_password,
                min_size=2,
                max_size=10,
            )
            logger.info(f"✅ Database pool created: {db_host}:{db_port}/{db_name}")
        except Exception as e:
            logger.error(f"❌ Failed to create database pool: {e}")
            raise
    
    async def close_db(self):
        """Veritabanı bağlantı havuzunu kapatır."""
        if self.db_pool:
            await self.db_pool.close()
            logger.info("Database pool closed")
    
    async def parse_and_execute(
        self, 
        llm_response: str, 
        firma_id: int,
        call_context: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        LLM yanıtını parse eder ve fonksiyon çağrısı varsa çalıştırır.
        
        Args:
            llm_response: LLM'den gelen yanıt (JSON veya text)
            firma_id: Firma ID
            call_context: Çağrı bağlamı (caller_id, channel_id, vb.)
        
        Returns:
            Fonksiyon sonucu veya hata mesajı
        """
        try:
            # JSON parse et
            try:
                data = json.loads(llm_response)
            except json.JSONDecodeError:
                # JSON değilse, text yanıt olarak kabul et
                return {
                    "success": True,
                    "type": "text_response",
                    "message": llm_response
                }
            
            # Fonksiyon çağrısı kontrolü
            if "function_call" in data:
                function_name = data["function_call"].get("name")
                arguments = data["function_call"].get("arguments", {})
                
                if function_name in self.supported_functions:
                    logger.info(f"🔧 Executing function: {function_name} with args: {arguments}")
                    
                    # Fonksiyonu çalıştır
                    result = await self.supported_functions[function_name](
                        firma_id=firma_id,
                        arguments=arguments,
                        call_context=call_context
                    )
                    
                    return {
                        "success": True,
                        "type": "function_result",
                        "function_name": function_name,
                        "result": result
                    }
                else:
                    logger.warning(f"⚠️ Unsupported function: {function_name}")
                    return {
                        "success": False,
                        "error": f"Desteklenmeyen fonksiyon: {function_name}"
                    }
            
            # Fonksiyon çağrısı yoksa text yanıt
            return {
                "success": True,
                "type": "text_response",
                "message": data.get("message", str(data))
            }
            
        except Exception as e:
            logger.error(f"❌ Error parsing/executing function: {e}")
            return {
                "success": False,
                "error": str(e)
            }
    
    async def _rezervasyon_al(
        self, 
        firma_id: int, 
        arguments: Dict[str, Any],
        call_context: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Yeni rezervasyon oluşturur.
        
        Args:
            tarih: Rezervasyon tarihi (YYYY-MM-DD)
            saat: Rezervasyon saati (HH:MM)
            kisi_sayisi: Kişi sayısı
            isim: Müşteri adı
            telefon: Müşteri telefonu
        """
        try:
            tarih = arguments.get("tarih")
            saat = arguments.get("saat")
            kisi_sayisi = arguments.get("kisi_sayisi")
            isim = arguments.get("isim")
            telefon = arguments.get("telefon") or call_context.get("caller_id")
            
            # Zorunlu alanları kontrol et
            if not all([tarih, saat, kisi_sayisi, isim, telefon]):
                return {
                    "success": False,
                    "message": "Eksik bilgi var. Lütfen tüm bilgileri sağlayın."
                }
            
            # Veritabanına kaydet
            async with self.db_pool.acquire() as conn:
                query = f"""
                    INSERT INTO firma_{firma_id}.rezervasyonlar 
                    (musteri_ad, telefon, tarih, saat, kisi_sayisi, durum, olusturma_zamani)
                    VALUES ($1, $2, $3, $4, $5, $6, $7)
                    RETURNING id
                """
                
                rezervasyon_id = await conn.fetchval(
                    query,
                    isim,
                    telefon,
                    tarih,
                    saat,
                    kisi_sayisi,
                    "onaylandi",
                    datetime.now()
                )
                
                logger.info(f"✅ Rezervasyon oluşturuldu: ID={rezervasyon_id}, Firma={firma_id}")
                
                return {
                    "success": True,
                    "rezervasyon_id": rezervasyon_id,
                    "message": f"Rezervasyonunuz başarıyla oluşturuldu. Rezervasyon numaranız: {rezervasyon_id}. {tarih} tarihinde saat {saat} için {kisi_sayisi} kişilik rezervasyonunuz onaylandı."
                }
                
        except Exception as e:
            logger.error(f"❌ Rezervasyon oluşturma hatası: {e}")
            return {
                "success": False,
                "message": "Rezervasyon oluşturulurken bir hata oluştu. Lütfen tekrar deneyin."
            }
    
    async def _rezervasyon_sorgula(
        self, 
        firma_id: int, 
        arguments: Dict[str, Any],
        call_context: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Telefon numarasına göre rezervasyonları sorgular.
        
        Args:
            telefon: Müşteri telefonu
        """
        try:
            telefon = arguments.get("telefon") or call_context.get("caller_id")
            
            if not telefon:
                return {
                    "success": False,
                    "message": "Telefon numarası gerekli."
                }
            
            async with self.db_pool.acquire() as conn:
                query = f"""
                    SELECT id, musteri_ad, tarih, saat, kisi_sayisi, durum
                    FROM firma_{firma_id}.rezervasyonlar
                    WHERE telefon = $1 AND durum != 'iptal'
                    ORDER BY tarih DESC, saat DESC
                    LIMIT 5
                """
                
                rows = await conn.fetch(query, telefon)
                
                if not rows:
                    return {
                        "success": True,
                        "rezervasyonlar": [],
                        "message": "Bu telefon numarasına ait aktif rezervasyon bulunamadı."
                    }
                
                rezervasyonlar = [
                    {
                        "id": row["id"],
                        "isim": row["musteri_ad"],
                        "tarih": str(row["tarih"]),
                        "saat": str(row["saat"]),
                        "kisi_sayisi": row["kisi_sayisi"],
                        "durum": row["durum"]
                    }
                    for row in rows
                ]
                
                # Mesaj oluştur
                if len(rezervasyonlar) == 1:
                    r = rezervasyonlar[0]
                    message = f"Rezervasyonunuz bulundu: {r['tarih']} tarihinde saat {r['saat']} için {r['kisi_sayisi']} kişilik rezervasyon. Durum: {r['durum']}."
                else:
                    message = f"{len(rezervasyonlar)} adet rezervasyonunuz bulundu."
                
                return {
                    "success": True,
                    "rezervasyonlar": rezervasyonlar,
                    "message": message
                }
                
        except Exception as e:
            logger.error(f"❌ Rezervasyon sorgulama hatası: {e}")
            return {
                "success": False,
                "message": "Rezervasyon sorgulanırken bir hata oluştu."
            }
    
    async def _rezervasyon_iptal(
        self, 
        firma_id: int, 
        arguments: Dict[str, Any],
        call_context: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Rezervasyonu iptal eder.
        
        Args:
            rezervasyon_id: Rezervasyon ID
        """
        try:
            rezervasyon_id = arguments.get("rezervasyon_id")
            
            if not rezervasyon_id:
                return {
                    "success": False,
                    "message": "Rezervasyon numarası gerekli."
                }
            
            async with self.db_pool.acquire() as conn:
                query = f"""
                    UPDATE firma_{firma_id}.rezervasyonlar
                    SET durum = 'iptal', iptal_zamani = $1
                    WHERE id = $2 AND durum != 'iptal'
                    RETURNING id, musteri_ad, tarih, saat
                """
                
                row = await conn.fetchrow(query, datetime.now(), rezervasyon_id)
                
                if not row:
                    return {
                        "success": False,
                        "message": "Rezervasyon bulunamadı veya zaten iptal edilmiş."
                    }
                
                logger.info(f"✅ Rezervasyon iptal edildi: ID={rezervasyon_id}, Firma={firma_id}")
                
                return {
                    "success": True,
                    "message": f"{row['tarih']} tarihli saat {row['saat']} rezervasyonunuz iptal edildi."
                }
                
        except Exception as e:
            logger.error(f"❌ Rezervasyon iptal hatası: {e}")
            return {
                "success": False,
                "message": "Rezervasyon iptal edilirken bir hata oluştu."
            }
    
    async def _fiyat_sor(
        self, 
        firma_id: int, 
        arguments: Dict[str, Any],
        call_context: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Hizmet fiyatlarını sorgular.
        
        Args:
            hizmet_turu: Hizmet türü (oda_tipi, tedavi_turu, vb.)
        """
        try:
            hizmet_turu = arguments.get("hizmet_turu", "genel")
            
            async with self.db_pool.acquire() as conn:
                # Firma ayarlarından fiyat bilgisini çek
                query = f"""
                    SELECT fiyat_listesi
                    FROM firma_{firma_id}.ayarlar
                    WHERE aktif = true
                    LIMIT 1
                """
                
                row = await conn.fetchrow(query)
                
                if row and row["fiyat_listesi"]:
                    fiyat_listesi = row["fiyat_listesi"]
                    
                    if hizmet_turu in fiyat_listesi:
                        fiyat = fiyat_listesi[hizmet_turu]
                        return {
                            "success": True,
                            "hizmet": hizmet_turu,
                            "fiyat": fiyat,
                            "message": f"{hizmet_turu} için fiyatımız {fiyat} TL'dir."
                        }
                
                return {
                    "success": True,
                    "message": "Fiyat bilgisi için lütfen yetkilimizle görüşün."
                }
                
        except Exception as e:
            logger.error(f"❌ Fiyat sorgulama hatası: {e}")
            return {
                "success": False,
                "message": "Fiyat bilgisi alınırken bir hata oluştu."
            }
    
    async def _musaitlik_kontrol(
        self, 
        firma_id: int, 
        arguments: Dict[str, Any],
        call_context: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Belirli tarih ve saat için müsaitlik kontrolü yapar.
        
        Args:
            tarih: Kontrol edilecek tarih (YYYY-MM-DD)
            saat: Kontrol edilecek saat (HH:MM) - opsiyonel
        """
        try:
            tarih = arguments.get("tarih")
            saat = arguments.get("saat")
            
            if not tarih:
                return {
                    "success": False,
                    "message": "Tarih bilgisi gerekli."
                }
            
            async with self.db_pool.acquire() as conn:
                if saat:
                    # Belirli saat için kontrol
                    query = f"""
                        SELECT COUNT(*) as rezervasyon_sayisi
                        FROM firma_{firma_id}.rezervasyonlar
                        WHERE tarih = $1 AND saat = $2 AND durum = 'onaylandi'
                    """
                    count = await conn.fetchval(query, tarih, saat)
                    
                    # Basit kapasite kontrolü (örnek: max 10 rezervasyon)
                    if count < 10:
                        return {
                            "success": True,
                            "musait": True,
                            "message": f"{tarih} tarihinde saat {saat} için yerimiz mevcut."
                        }
                    else:
                        return {
                            "success": True,
                            "musait": False,
                            "message": f"{tarih} tarihinde saat {saat} için maalesef yerimiz dolu."
                        }
                else:
                    # Tüm gün için kontrol
                    query = f"""
                        SELECT saat, COUNT(*) as rezervasyon_sayisi
                        FROM firma_{firma_id}.rezervasyonlar
                        WHERE tarih = $1 AND durum = 'onaylandi'
                        GROUP BY saat
                        HAVING COUNT(*) < 10
                        ORDER BY saat
                        LIMIT 5
                    """
                    rows = await conn.fetch(query, tarih)
                    
                    if rows:
                        musait_saatler = [str(row["saat"]) for row in rows]
                        return {
                            "success": True,
                            "musait": True,
                            "musait_saatler": musait_saatler,
                            "message": f"{tarih} tarihinde şu saatler müsait: {', '.join(musait_saatler)}"
                        }
                    else:
                        return {
                            "success": True,
                            "musait": False,
                            "message": f"{tarih} tarihinde maalesef müsait yerimiz bulunmuyor."
                        }
                
        except Exception as e:
            logger.error(f"❌ Müsaitlik kontrol hatası: {e}")
            return {
                "success": False,
                "message": "Müsaitlik kontrol edilirken bir hata oluştu."
            }


# Global instance
function_engine = FunctionCallingEngine()
