---
name: perplexity
description: Perplexity Agent API ile güncel, web kaynaklı ve kaynak gösterilen araştırma yapar. Kullanıcı "Perplexity'de araştır", "Perplexity'ye sor", "webde araştır, kaynaklarıyla", güncel haber, fiyat, kur, piyasa, uçuş/otel/etkinlik bilgisi veya derin araştırma istediğinde kullan.
---

# Perplexity araştırma

Web kaynaklı cevaplar için `scripts/ask.py` betiğini çalıştır (Perplexity Agent API, `POST /v1/agent`).

## Kurulum (bir kez)
```bash
pip install -q perplexityai
```
API anahtarı `PERPLEXITY_API_KEY` ortam değişkeninden okunur. Anahtarı asla yazdırma, loglama, sohbete isteme.
Bu bulut ortamında anahtar ağ proxy'si tarafından enjekte edilir; değişken boşsa komutu
`PERPLEXITY_API_KEY=proxy-injected` önekiyle çalıştır.

## Kullanım
```bash
python3 .claude/skills/perplexity/scripts/ask.py "SORU" --effort low
```
Derinlik (`--effort`): `fast` tek bilgi · `low` günlük araştırma (varsayılan) · `medium` çok kaynaklı ·
`high` derin araştırma · `xhigh` kod çalıştıran açık uçlu iş · `ultra` en kapsamlı (uzun sürer, pahalı).

Diğer seçenekler:
- `--model openai/gpt-5.6-sol` → belirli model + web_search/fetch_url araçları (effort yerine)
- `--previous-response-id ID` → önceki cevabın devamı (çıktıdaki `response_id`)
- `--schema dosya.json` → JSON Schema ile yapılandırılmış çıktı
- `--json` → cevap + kaynaklar JSON olarak

## Cevaplama kuralları
- Kullanıcıya Türkçe, kısa ve düzenli özet ver; önce cevap, sonra kaynaklar (başlık + URL).
- Varsayılan `low`; kullanıcı "detaylı/derin araştır" derse `medium` veya `high`.
- 401 → anahtar sorunu (konsoldan kontrol/rotate); 429 → kota/hız sınırı, sonra tekrar dene.
