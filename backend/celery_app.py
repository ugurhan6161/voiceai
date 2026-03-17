"""
VoiceAI Platform — Celery Uygulama Konfigürasyonu
"""
from celery import Celery
from celery.schedules import crontab
import os

redis_password = os.getenv('REDIS_PASSWORD', '')
redis_host = os.getenv('REDIS_HOST', 'voiceai-redis')
redis_port = os.getenv('REDIS_PORT', '6379')

if redis_password:
    redis_url = f"redis://:{redis_password}@{redis_host}:{redis_port}/0"
else:
    redis_url = f"redis://{redis_host}:{redis_port}/0"

celery = Celery(
    'voiceai',
    broker=redis_url,
    backend=redis_url,
    include=[
        'tasks.sms_tasks',
        'tasks.billing_tasks',
    ]
)

celery.conf.update(
    task_serializer='json',
    accept_content=['json'],
    result_serializer='json',
    timezone='Europe/Istanbul',
    enable_utc=True,
    task_routes={
        'sms.*': {'queue': 'sms'},
        'billing.*': {'queue': 'billing'},
        'callback.*': {'queue': 'callback'},
    },
    # Beat schedule — periyodik görevler
    beat_schedule={
        # Her saat randevu hatırlatma SMS'i gönder
        'randevu-hatirlatma-saatlik': {
            'task': 'sms.randevu_hatirlatma',
            'schedule': crontab(minute=0),  # Her saat başı
        },
        # Her gün gece yarısı kullanım sayaçlarını PostgreSQL'e kaydet
        'kullanim-sayac-gece': {
            'task': 'billing.kullanim_kaydet',
            'schedule': crontab(hour=0, minute=5),
        },
        # Her gün sabah 9'da gecikmiş ödemeleri kontrol et
        'gecikme-kontrol': {
            'task': 'billing.gecikme_kontrol',
            'schedule': crontab(hour=9, minute=0),
        },
        # Her gün sabah 8'de geri arama kuyruğunu işle
        'geri-arama-isle': {
            'task': 'callback.geri_arama_isle',
            'schedule': crontab(hour=8, minute=0),
        },
    }
)
