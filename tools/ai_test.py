"""ai_test.py — Gemini bağlantısını yoxlayır (açarı çap etmir). Nəticə: logs/ai_test.log"""
import sys, time, traceback
from pathlib import Path
ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "app"))
out = []
def log(s):
    out.append(s); print(s)
try:
    import ai
    from google import genai
    from google.genai import types
    import google.genai as gg
    log(f"google-genai versiya: {getattr(gg, '__version__', '?')}")
    log(f"açar tapıldı: {ai.available()} · modellər: {ai._models()}")
    client = genai.Client(api_key=ai._key(), http_options=types.HttpOptions(timeout=40_000))
    for m in ai._models():
        t = time.time()
        try:
            r = client.models.generate_content(model=m, contents="Bir sözlə cavab ver: Bakı hansı ölkənin paytaxtıdır?",
                                               config=types.GenerateContentConfig(max_output_tokens=256))
            log(f"OK   {m}: {time.time() - t:.1f}s · {repr((r.text or '')[:60])}")
        except Exception as e:
            log(f"XETA {m}: {time.time() - t:.1f}s · {type(e).__name__}: {str(e)[:220]}")
    t = time.time()
    try:
        n = 0
        for ch in ai.stream("Salam! İki cümlə ilə özünü təqdim et."):
            n += len(ch)
        log(f"stream OK: {n} simvol, {time.time() - t:.1f}s")
    except Exception as e:
        log(f"stream XETA: {time.time() - t:.1f}s · {type(e).__name__}: {str(e)[:220]}")
except Exception:
    log(traceback.format_exc()[-1500:])
(ROOT / "logs").mkdir(exist_ok=True)
(ROOT / "logs" / "ai_test.log").write_text("\n".join(out), encoding="utf-8")
