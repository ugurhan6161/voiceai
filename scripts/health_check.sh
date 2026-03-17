#!/bin/bash
# ─────────────────────────────────────────────────────────────
#  VoiceAI Platform — Servis Sağlık Kontrolü
#  Kullanım: bash scripts/health_check.sh
# ─────────────────────────────────────────────────────────────

echo "🏥 VoiceAI Servis Sağlık Kontrolü"
echo "=================================="

check_service() {
  local name=$1
  local container=$2
  
  if docker ps --format '{{.Names}}' | grep -q "^${container}$"; then
    STATUS=$(docker inspect --format='{{.State.Health.Status}}' $container 2>/dev/null || echo "running")
    echo "✅ $name: Çalışıyor ($STATUS)"
  else
    echo "❌ $name: ÇALIŞMIYOR!"
  fi
}

check_service "Nginx"        "voiceai-nginx"
check_service "Asterisk"     "voiceai-asterisk"
check_service "PostgreSQL"   "voiceai-postgres"
check_service "Redis"        "voiceai-redis"
check_service "Ollama/LLM"   "voiceai-ollama"
check_service "Whisper/STT"  "voiceai-whisper"
check_service "XTTS/TTS"     "voiceai-xtts"
check_service "AI Engine"    "voiceai-ai-engine"
check_service "Backend"      "voiceai-backend"
check_service "Frontend"     "voiceai-frontend"
check_service "Celery"       "voiceai-celery"
check_service "Grafana"      "voiceai-grafana"

echo ""
echo "📊 Sistem Kaynakları:"
echo "─────────────────────"
echo "RAM: $(free -h | awk '/^Mem:/ {print $3 " / " $2}')"
echo "CPU: $(top -bn1 | grep "Cpu(s)" | awk '{print $2}')% kullanımda"
echo "Disk: $(df -h / | awk 'NR==2 {print $3 " / " $2 " (" $5 " dolu)"}')"

echo ""
echo "🐳 Docker İstatistikleri:"
docker stats --no-stream --format "table {{.Name}}\t{{.CPUPerc}}\t{{.MemUsage}}" \
  2>/dev/null | head -15
