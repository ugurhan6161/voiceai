"""
Memory Manager — Müşteri Hafıza Sistemi
Kısa, Orta ve Uzun Hafıza Yönetimi
"""
import os
import json
import redis
import asyncpg
from typing import Dict, List, Optional, Any
from datetime import datetime, timedelta
from dataclasses import dataclass, asdict


@dataclass
class ShortMemory:
    """
    Kısa Hafıza: Aktif çağrı sırasında geçici bilgiler
    Redis'te saklanır, çağrı bitince silinir
    """
    session_id: str
    phone: str
    conversation_history: List[Dict[str, str]]
    current_intent: Optional[str] = None
    collected_slots: Dict[str, Any] = None
    created_at: str = None
    
    def __post_init__(self):
        if self.collected_slots is None:
            self.collected_slots = {}
        if self.created_at is None:
            self.created_at = datetime.now().isoformat()


@dataclass
class MediumMemory:
    """
    Orta Hafıza: Son 10 çağrı özeti
    PostgreSQL'de saklanır
    """
    phone: str
    call_summary: str
    intent: str
    outcome: str  # success, failed, transferred
    duration_seconds: float
    timestamp: str
    metadata: Dict[str, Any] = None
    
    def __post_init__(self):
        if self.metadata is None:
            self.metadata = {}


@dataclass
class LongMemory:
    """
    Uzun Hafıza: Müşteri profili
    PostgreSQL'de saklanır
    """
    phone: str
    customer_name: Optional[str] = None
    email: Optional[str] = None
    preferences: Dict[str, Any] = None
    total_calls: int = 0
    successful_reservations: int = 0
    last_call_date: Optional[str] = None
    vip_status: bool = False
    notes: Optional[str] = None
    created_at: str = None
    updated_at: str = None
    
    def __post_init__(self):
        if self.preferences is None:
            self.preferences = {}
        if self.created_at is None:
            self.created_at = datetime.now().isoformat()
        if self.updated_at is None:
            self.updated_at = datetime.now().isoformat()


class MemoryManager:
    """
    Üç katmanlı hafıza sistemi yöneticisi
    """
    
    def __init__(self, firma_id: str = "firma_1"):
        self.firma_id = firma_id
        
        # Redis bağlantısı (kısa hafıza)
        redis_host = os.getenv("REDIS_HOST", "redis")
        redis_password = os.getenv("REDIS_PASSWORD", "")
        self.redis_client = redis.Redis(
            host=redis_host,
            port=6379,
            password=redis_password if redis_password else None,
            decode_responses=True
        )
        
        # PostgreSQL bağlantısı (orta ve uzun hafıza)
        self.pg_pool: Optional[asyncpg.Pool] = None
    
    async def _ensure_pg_connection(self):
        """PostgreSQL bağlantı havuzu oluştur"""
        if self.pg_pool is None:
            pg_host = os.getenv("POSTGRES_HOST", "postgres")
            pg_user = os.getenv("POSTGRES_USER", "voiceai")
            pg_password = os.getenv("POSTGRES_PASSWORD", "VoiceAI2026!")
            pg_db = os.getenv("POSTGRES_DB", "voiceai")
            
            self.pg_pool = await asyncpg.create_pool(
                host=pg_host,
                port=5432,
                user=pg_user,
                password=pg_password,
                database=pg_db,
                min_size=2,
                max_size=10
            )
    
    async def close(self):
        """Bağlantıları kapat"""
        if self.pg_pool:
            await self.pg_pool.close()
        if self.redis_client:
            self.redis_client.close()
    
    # ═══════════════════════════════════════════════════════════
    # KISA HAFIZA (Redis - Aktif Çağrı)
    # ═══════════════════════════════════════════════════════════
    
    def save_short_memory(self, memory: ShortMemory, ttl: int = 3600):
        """
        Kısa hafızayı Redis'e kaydet
        
        Args:
            memory: Kısa hafıza objesi
            ttl: Yaşam süresi (saniye, varsayılan 1 saat)
        """
        key = f"short_memory:{self.firma_id}:{memory.session_id}"
        data = asdict(memory)
        
        # JSON olarak kaydet
        self.redis_client.setex(
            key,
            ttl,
            json.dumps(data, ensure_ascii=False)
        )
    
    def get_short_memory(self, session_id: str) -> Optional[ShortMemory]:
        """
        Kısa hafızayı Redis'ten al
        
        Args:
            session_id: Oturum ID
        
        Returns:
            Kısa hafıza objesi veya None
        """
        key = f"short_memory:{self.firma_id}:{session_id}"
        data = self.redis_client.get(key)
        
        if data:
            memory_dict = json.loads(data)
            return ShortMemory(**memory_dict)
        
        return None
    
    def delete_short_memory(self, session_id: str):
        """
        Kısa hafızayı sil (çağrı bitince)
        
        Args:
            session_id: Oturum ID
        """
        key = f"short_memory:{self.firma_id}:{session_id}"
        self.redis_client.delete(key)
    
    def update_short_memory_slots(
        self,
        session_id: str,
        slots: Dict[str, Any]
    ):
        """
        Kısa hafızadaki slot'ları güncelle
        
        Args:
            session_id: Oturum ID
            slots: Güncellenecek slot'lar
        """
        memory = self.get_short_memory(session_id)
        if memory:
            memory.collected_slots.update(slots)
            self.save_short_memory(memory)
    
    # ═══════════════════════════════════════════════════════════
    # ORTA HAFIZA (PostgreSQL - Son 10 Çağrı)
    # ═══════════════════════════════════════════════════════════
    
    async def save_medium_memory(self, memory: MediumMemory):
        """
        Orta hafızayı PostgreSQL'e kaydet
        
        Args:
            memory: Orta hafıza objesi
        """
        await self._ensure_pg_connection()
        
        query = f"""
        INSERT INTO {self.firma_id}.call_history (
            phone, call_summary, intent, outcome,
            duration_seconds, timestamp, metadata
        ) VALUES ($1, $2, $3, $4, $5, $6, $7)
        """
        
        await self.pg_pool.execute(
            query,
            memory.phone,
            memory.call_summary,
            memory.intent,
            memory.outcome,
            memory.duration_seconds,
            memory.timestamp,
            json.dumps(memory.metadata)
        )
    
    async def get_medium_memory(
        self,
        phone: str,
        limit: int = 10
    ) -> List[MediumMemory]:
        """
        Telefon numarasına göre son N çağrıyı al
        
        Args:
            phone: Telefon numarası
            limit: Kaç çağrı (varsayılan 10)
        
        Returns:
            Orta hafıza listesi
        """
        await self._ensure_pg_connection()
        
        query = f"""
        SELECT phone, call_summary, intent, outcome,
               duration_seconds, timestamp, metadata
        FROM {self.firma_id}.call_history
        WHERE phone = $1
        ORDER BY timestamp DESC
        LIMIT $2
        """
        
        rows = await self.pg_pool.fetch(query, phone, limit)
        
        memories = []
        for row in rows:
            memories.append(MediumMemory(
                phone=row['phone'],
                call_summary=row['call_summary'],
                intent=row['intent'],
                outcome=row['outcome'],
                duration_seconds=row['duration_seconds'],
                timestamp=row['timestamp'],
                metadata=json.loads(row['metadata']) if row['metadata'] else {}
            ))
        
        return memories
    
    async def get_call_summary_for_context(self, phone: str) -> str:
        """
        LLM için bağlam oluştur (son çağrı özetleri)
        
        Args:
            phone: Telefon numarası
        
        Returns:
            Özet metin
        """
        memories = await self.get_medium_memory(phone, limit=3)
        
        if not memories:
            return "Bu müşteri ilk kez arıyor."
        
        summary_parts = [f"Müşteri daha önce {len(memories)} kez aradı:"]
        
        for i, mem in enumerate(memories, 1):
            summary_parts.append(
                f"{i}. {mem.timestamp[:10]} - {mem.intent} - {mem.outcome}"
            )
        
        return "\n".join(summary_parts)
    
    # ═══════════════════════════════════════════════════════════
    # UZUN HAFIZA (PostgreSQL - Müşteri Profili)
    # ═══════════════════════════════════════════════════════════
    
    async def save_long_memory(self, memory: LongMemory):
        """
        Uzun hafızayı PostgreSQL'e kaydet (upsert)
        
        Args:
            memory: Uzun hafıza objesi
        """
        await self._ensure_pg_connection()
        
        query = f"""
        INSERT INTO {self.firma_id}.customer_profiles (
            phone, customer_name, email, preferences,
            total_calls, successful_reservations, last_call_date,
            vip_status, notes, created_at, updated_at
        ) VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10, $11)
        ON CONFLICT (phone) DO UPDATE SET
            customer_name = COALESCE(EXCLUDED.customer_name, {self.firma_id}.customer_profiles.customer_name),
            email = COALESCE(EXCLUDED.email, {self.firma_id}.customer_profiles.email),
            preferences = EXCLUDED.preferences,
            total_calls = EXCLUDED.total_calls,
            successful_reservations = EXCLUDED.successful_reservations,
            last_call_date = EXCLUDED.last_call_date,
            vip_status = EXCLUDED.vip_status,
            notes = COALESCE(EXCLUDED.notes, {self.firma_id}.customer_profiles.notes),
            updated_at = EXCLUDED.updated_at
        """
        
        await self.pg_pool.execute(
            query,
            memory.phone,
            memory.customer_name,
            memory.email,
            json.dumps(memory.preferences),
            memory.total_calls,
            memory.successful_reservations,
            memory.last_call_date,
            memory.vip_status,
            memory.notes,
            memory.created_at,
            memory.updated_at
        )
    
    async def get_long_memory(self, phone: str) -> Optional[LongMemory]:
        """
        Telefon numarasına göre müşteri profilini al
        
        Args:
            phone: Telefon numarası
        
        Returns:
            Uzun hafıza objesi veya None
        """
        await self._ensure_pg_connection()
        
        query = f"""
        SELECT phone, customer_name, email, preferences,
               total_calls, successful_reservations, last_call_date,
               vip_status, notes, created_at, updated_at
        FROM {self.firma_id}.customer_profiles
        WHERE phone = $1
        """
        
        row = await self.pg_pool.fetchrow(query, phone)
        
        if row:
            return LongMemory(
                phone=row['phone'],
                customer_name=row['customer_name'],
                email=row['email'],
                preferences=json.loads(row['preferences']) if row['preferences'] else {},
                total_calls=row['total_calls'],
                successful_reservations=row['successful_reservations'],
                last_call_date=row['last_call_date'],
                vip_status=row['vip_status'],
                notes=row['notes'],
                created_at=row['created_at'],
                updated_at=row['updated_at']
            )
        
        return None
    
    async def increment_call_count(self, phone: str):
        """
        Müşterinin çağrı sayısını artır
        
        Args:
            phone: Telefon numarası
        """
        profile = await self.get_long_memory(phone)
        
        if profile:
            profile.total_calls += 1
            profile.last_call_date = datetime.now().isoformat()
            profile.updated_at = datetime.now().isoformat()
        else:
            profile = LongMemory(
                phone=phone,
                total_calls=1,
                last_call_date=datetime.now().isoformat()
            )
        
        await self.save_long_memory(profile)
    
    async def get_customer_context_for_llm(self, phone: str) -> str:
        """
        LLM için tam müşteri bağlamı oluştur
        
        Args:
            phone: Telefon numarası
        
        Returns:
            Bağlam metni
        """
        # Uzun hafıza (profil)
        profile = await self.get_long_memory(phone)
        
        # Orta hafıza (son çağrılar)
        call_summary = await self.get_call_summary_for_context(phone)
        
        if not profile:
            return f"Yeni müşteri.\n{call_summary}"
        
        context_parts = [
            f"Müşteri: {profile.customer_name or 'İsim bilinmiyor'}",
            f"Telefon: {profile.phone}",
            f"Toplam çağrı: {profile.total_calls}",
            f"Başarılı rezervasyon: {profile.successful_reservations}",
        ]
        
        if profile.vip_status:
            context_parts.append("⭐ VIP Müşteri")
        
        if profile.preferences:
            prefs = ", ".join([f"{k}: {v}" for k, v in profile.preferences.items()])
            context_parts.append(f"Tercihler: {prefs}")
        
        if profile.notes:
            context_parts.append(f"Notlar: {profile.notes}")
        
        context_parts.append(f"\n{call_summary}")
        
        return "\n".join(context_parts)


# Singleton instance
_memory_manager: Optional[MemoryManager] = None


def get_memory_manager(firma_id: str = "firma_1") -> MemoryManager:
    """Global memory manager instance döndür"""
    global _memory_manager
    if _memory_manager is None:
        _memory_manager = MemoryManager(firma_id=firma_id)
    return _memory_manager


async def cleanup_memory_manager():
    """Global memory manager'ı temizle"""
    global _memory_manager
    if _memory_manager:
        await _memory_manager.close()
        _memory_manager = None
