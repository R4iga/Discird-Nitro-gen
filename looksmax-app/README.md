# Looks Analysis App (Safety-optional Safe/Edgy Modes)

A minimal FastAPI app that accepts a user photo and context, then calls an OpenAI vision model to produce a concise, looks-focused analysis. Two modes:
- Safe: neutral, concise, no edgy jargon. Default for all users.
- Edgy: Looksmax-style tone/jargon for adults (18+) only, still with safety constraints (no medical advice or drug regimens).

## Features
- Image upload + age confirmation
- Optional goals and notes
- Adult-only options: numeric rating and high-level procedure discussion
- Mode toggle: `safe` vs `edgy` (edgy requires 18+ confirmation)

## Prerequisites
- OpenAI API key with access to a vision-capable model (e.g., `gpt-4o-mini`)

## Run with Docker (recommended)

```bash
cd looksmax-app
# Create .env with your key
cp .env.example .env
# Edit .env and set OPENAI_API_KEY=...

# Build
docker build -t looksmax-app .

# Run (exposes 8000)
docker run --rm -p 8000:8000 --env-file .env looksmax-app
```
Open `http://localhost:8000`.

## Local run (if you have Python tooling available)
```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
export $(grep -v '^#' .env | xargs)
uvicorn main:app --host 0.0.0.0 --port 8000
```

## Notes
- No medical advice. Any procedures are discussed only at a high level; consult licensed professionals.
- Under 18 or not adult-confirmed: no rating and no procedure talk.
- Images are handled in-memory only.