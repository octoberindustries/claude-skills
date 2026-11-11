#!/usr/bin/env python3
"""Perplexity Agent API ile web kaynaklı cevap alır.

Kullanım:
  python3 ask.py "soru" [--effort fast|low|medium|high|xhigh|ultra]
                        [--model openai/gpt-5.6-sol] [--previous-response-id ID]
                        [--schema schema.json] [--json]

Anahtar yalnızca PERPLEXITY_API_KEY ortam değişkeninden okunur; asla yazdırılmaz.
"""
from __future__ import annotations

import argparse
import json
import os
import sys

import perplexity
from perplexity import Perplexity

EFFORTS = ["fast", "low", "medium", "high", "xhigh", "ultra"]


def collect_sources(response) -> list[dict]:
    seen: dict[str, dict] = {}
    for item in response.output or []:
        if getattr(item, "type", None) == "search_results":
            for r in item.results or []:
                url = getattr(r, "url", None)
                if url and url not in seen:
                    seen[url] = {"title": getattr(r, "title", None), "url": url,
                                 "date": getattr(r, "date", None)}
        elif getattr(item, "type", None) == "message":
            for part in item.content or []:
                for a in getattr(part, "annotations", None) or []:
                    url = getattr(a, "url", None)
                    if url and url not in seen:
                        seen[url] = {"title": getattr(a, "title", None), "url": url, "date": None}
    return list(seen.values())


def main() -> int:
    ap = argparse.ArgumentParser(description="Perplexity Agent API ile web kaynaklı cevap")
    ap.add_argument("question")
    ap.add_argument("--effort", choices=EFFORTS, default=None,
                    help="Araştırma derinliği (model verilmezse varsayılan: low)")
    ap.add_argument("--model", help="Örn. openai/gpt-5.6-sol (web_search aracıyla)")
    ap.add_argument("--instructions", help="Sistem talimatı (yalnızca --model ile)")
    ap.add_argument("--previous-response-id", help="Önceki cevabın id'si (devam sorusu)")
    ap.add_argument("--schema", help="Yapılandırılmış çıktı için JSON Schema dosyası")
    ap.add_argument("--json", action="store_true", help="Sonucu JSON olarak yazdır")
    args = ap.parse_args()

    if not os.environ.get("PERPLEXITY_API_KEY"):
        print("HATA: PERPLEXITY_API_KEY tanımlı değil. Anahtarı https://console.perplexity.ai "
              "adresinden oluşturup kendi terminalinizde export edin.", file=sys.stderr)
        return 2

    params: dict = {"input": args.question}
    if args.model:
        params["model"] = args.model
        params["tools"] = [{"type": "web_search"}, {"type": "fetch_url"}]
        if args.instructions:
            params["instructions"] = args.instructions
        if args.effort:
            print("UYARI: --model verildiği için --effort yok sayıldı.", file=sys.stderr)
    else:
        params["effort"] = args.effort or "low"
    if args.previous_response_id:
        params["previous_response_id"] = args.previous_response_id
    if args.schema:
        with open(args.schema, encoding="utf-8") as f:
            schema = json.load(f)
        params["response_format"] = {"type": "json_schema",
                                     "json_schema": {"name": "result", "schema": schema}}

    client = Perplexity(max_retries=3, timeout=600)  # SDK, 429'da Retry-After'a uyar
    try:
        response = client.responses.create(**params)
    except perplexity.AuthenticationError:
        print("HATA 401: API anahtarı geçersiz veya yetkisiz. Konsoldan kontrol edin; "
              "anahtar sızdıysa yenileyin (rotate).", file=sys.stderr)
        return 1
    except perplexity.RateLimitError:
        print("HATA 429: Hız/kota sınırı. Biraz sonra tekrar deneyin.", file=sys.stderr)
        return 1
    except perplexity.APIConnectionError as e:
        print(f"HATA: Bağlantı kurulamadı: {e}", file=sys.stderr)
        return 1
    except perplexity.APIStatusError as e:
        print(f"HATA {e.status_code}: {e.message}", file=sys.stderr)
        return 1

    sources = collect_sources(response)
    if args.json:
        print(json.dumps({"id": response.id, "model": response.model,
                          "answer": response.output_text, "sources": sources},
                         ensure_ascii=False, indent=2))
    else:
        print(response.output_text)
        if sources:
            print("\nKaynaklar:")
            for i, s in enumerate(sources, 1):
                print(f"  [{i}] {s['title'] or s['url']} — {s['url']}")
        print(f"\n(response_id: {response.id} · model: {response.model})")
    return 0


if __name__ == "__main__":
    sys.exit(main())
