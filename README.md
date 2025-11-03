# LexChunk Backend (secure server-side translation)

This backend extracts **lexical chunks** with spaCy + Textacy **and** performs **server-side translation** (Microsoft Translator), so your API keys are never exposed in the browser.

## Endpoints
- `GET /health` → `{"ok": true, "translator": true/false}`
- `POST /chunks` → returns `{"collocations":[...]}`
- `POST /translate` → returns `{"text","translation"}`
- `POST /analyze` → **recommended**: returns `{"text","translation","collocations":[...]} (plus per-chunk translations)`

## Environment variables (Render → Environment Variables)
- `MS_API_KEY` (required for translation)
- `MS_REGION` (default: `northeurope`)
- `MS_API_BASE` (default: `https://api.cognitive.microsofttranslator.com`)

## Deploy on Render
Build: `pip install -r requirements.txt`  
Start: `uvicorn app:app --host 0.0.0.0 --port $PORT`

## Local
```bash
python -m venv venv && source venv/bin/activate
pip install -r requirements.txt
export MS_API_KEY=YOUR_KEY
export MS_REGION=northeurope
uvicorn app:app --reload --port 8000
```

## Frontend usage
Call `/analyze` with JSON:
```json
{"text":"She takes care of her little brother every day.","target_lang":"zh-CN"}
```
Response includes `translation` and chunk list with `translation` per phrase.
