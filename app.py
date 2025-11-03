
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import os, requests
import spacy
from textacy.extract import token_matches

# ---- Config via environment variables ----
MS_API_KEY = os.getenv("MS_API_KEY", "").strip()
MS_REGION = os.getenv("MS_REGION", "northeurope").strip()
MS_API_BASE = os.getenv("MS_API_BASE", "https://api.cognitive.microsofttranslator.com").rstrip("/")

# ensure spaCy model is available
try:
    nlp = spacy.load("en_core_web_sm")
except Exception:
    import spacy.cli
    spacy.cli.download("en_core_web_sm")
    nlp = spacy.load("en_core_web_sm")

app = FastAPI(title="Lexical Chunk Backend (secure translation)", version="1.1.0")

# CORS: allow all by default; restrict in production if needed
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

class Inp(BaseModel):
    text: str
    target_lang: str | None = "zh-CN"

def translate_ms(texts, target_lang="zh-CN"):
    """
    Server-side Microsoft Translator.
    Returns a list of translated strings aligned with `texts`.
    Requires MS_API_KEY (and optional MS_REGION) to be set in env.
    """
    if not MS_API_KEY:
        return [""] * len(texts)
    url = f"{MS_API_BASE}/translate?api-version=3.0&to={target_lang}"
    headers = {
        "Ocp-Apim-Subscription-Key": MS_API_KEY,
        "Content-Type": "application/json",
    }
    if MS_REGION:
        headers["Ocp-Apim-Subscription-Region"] = MS_REGION
    body = [{"Text": t} for t in texts]
    r = requests.post(url, headers=headers, json=body, timeout=30)
    r.raise_for_status()
    data = r.json()
    out = []
    for item in data:
        out.append(item.get("translations", [{}])[0].get("text", ""))
    return out

def extract_chunks(text: str):
    doc = nlp(text)
    results = []
    # 1) noun chunks
    for np in doc.noun_chunks:
        results.append({
            "type": "noun_chunk",
            "phrase": np.text,
            "start": np.start_char,
            "end": np.end_char,
            "sentence": np.sent.text,
        })
    # 2) verb / multiword expressions with token_matches patterns
    patterns = [
        [{"POS": "VERB"}, {"POS": {"IN": ["PART", "ADV"]}}],
        [{"LOWER": "take"}, {"LOWER": "care"}, {"LOWER": "of"}],
        [{"LOWER": "as"}, {"LOWER": "a"}, {"LOWER": "matter"}, {"LOWER": "of"}, {"LOWER": "fact"}],
        [{"LOWER": "on"}, {"LOWER": "the"}, {"LOWER": "other"}, {"LOWER": "hand"}],
        [{"LOWER": "as"}, {"LOWER": "a"}, {"LOWER": "result"}, {"LOWER": "of"}],
    ]
    for span in token_matches(doc, patterns=patterns):
        results.append({
            "type": "verb_chunk",
            "phrase": span.text,
            "start": span.start_char,
            "end": span.end_char,
            "sentence": span.sent.text,
        })
    return results

@app.get("/health")
def health():
    return {"ok": True, "translator": bool(MS_API_KEY)}

@app.post("/chunks")
def api_chunks(inp: Inp):
    return {"collocations": extract_chunks(inp.text)}

@app.post("/translate")
def api_translate(inp: Inp):
    translated = translate_ms([inp.text], inp.target_lang or "zh-CN")[0]
    return {"text": inp.text, "translation": translated, "target_lang": inp.target_lang or "zh-CN"}

@app.post("/analyze")
def api_analyze(inp: Inp):
    """
    End-to-end: returns chunks + full-text translation.
    Frontend can call only this endpoint to avoid exposing any API keys.
    """
    chunks = extract_chunks(inp.text)
    translation = translate_ms([inp.text], inp.target_lang or "zh-CN")[0]
    # also return per-chunk translations for hover tooltips
    if chunks:
        phrases = [c["phrase"] for c in chunks]
        chunk_trans = translate_ms(phrases, inp.target_lang or "zh-CN")
        for c, zh in zip(chunks, chunk_trans):
            c["translation"] = zh
    return {
        "text": inp.text,
        "translation": translation,
        "target_lang": inp.target_lang or "zh-CN",
        "collocations": chunks,
    }
