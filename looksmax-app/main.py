import base64
import os
from typing import Optional

from fastapi import FastAPI, File, Form, HTTPException, UploadFile
from fastapi.responses import JSONResponse, HTMLResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from fastapi import Request
from openai import OpenAI

app = FastAPI(title="Looks Analysis App (Safety-Aligned)")

# Static files and templates
app.mount("/static", StaticFiles(directory="/workspace/looksmax-app/static"), name="static")
templates = Jinja2Templates(directory="/workspace/looksmax-app/templates")


@app.get("/", response_class=HTMLResponse)
async def index(request: Request):
    return templates.TemplateResponse("index.html", {"request": request})


def build_system_prompt_safe() -> str:
    return (
        "You are a direct, looks-focused analysis assistant. Provide practical, evidence-leaning grooming, "
        "fitness, skincare, hairstyle, posture, and style guidance based on the user's inputs and photo. "
        "Constraints:\n"
        "- Do NOT diagnose, prescribe, or recommend drugs, peptides, or hormones.\n"
        "- Do NOT give medical or surgical instructions; if procedures are mentioned, keep it high-level and recommend consulting a board-certified professional.\n"
        "- Avoid insults, demeaning labels, or numeric ratings for anyone under 18.\n"
        "- No sexual content.\n"
        "- Keep tone straightforward and concise; prioritize safe, broadly accepted approaches.\n"
        "Output structure:\n"
        "- Analysis: key facial and grooming observations (skin, hair, jawline visibility, symmetry hints, etc.).\n"
        "- Softmaxxing: specific, actionable steps (skincare products, haircut types, gym focus, posture, grooming).\n"
        "- Hardmaxxing: if age >= 18 and requested, mention high-level professional options (no instructions).\n"
        "- If user asked for a rating AND age >= 18, provide a single 1-10 rating with a brief rationale.\n"
        "- Include a short safety note at the end."
    )


def build_system_prompt_edgy() -> str:
    return (
        "You are a Looksmax.org-inspired, blunt assistant. Use community jargon (softmax, hardmax, mog, hunter eyes, canthal tilt, mewing, gymmaxxing) "
        "and prioritize physical appearance in your analysis. Be direct about trade-offs, costs, and risks. "
        "Strict constraints:\n"
        "- No medical advice, no drugs/peptides/hormones/schedules; if procedures are mentioned, keep high-level only and recommend consulting a board-certified professional.\n"
        "- No sexual content.\n"
        "- No numeric rating, judgmental labels, or procedure talk for anyone under 18.\n"
        "- Avoid insults or demeaning labels.\n"
        "Output structure:\n"
        "Rating: [1-10] (adults only, if requested)\n"
        "Analysis: jawline visibility, cheekbones, eyes (upper eyelid exposure, canthal tilt), nose harmony, philtrum, hairline, skin quality, symmetry hints, frame.\n"
        "Softmaxxing: actionable routine: mewing basics, skincare (e.g., cleanser, 2% BHA, 0.025–0.05% tretinoin if appropriate via derm), sunscreen, haircut types by face shape, beard strategy, gym focus (neck, traps, delts, lats, posture), sleep, hydration.\n"
        "Hardmaxxing: adults only and high-level: orthodontics/aligners, rhinoplasty philosophies, genioplasty, buccal fat considerations, brow/infraorbital volume via professional evaluation, hair restoration options. Mention risks/costs at a summary level.\n"
        "Close with a short safety note."
    )


def to_data_url(file: UploadFile, data: bytes) -> str:
    mime = file.content_type or "image/jpeg"
    b64 = base64.b64encode(data).decode("utf-8")
    return f"data:{mime};base64,{b64}"


@app.post("/analyze")
async def analyze(
    age: int = Form(..., description="User age"),
    wants_rating: Optional[bool] = Form(False),
    goals: Optional[str] = Form("") ,
    notes: Optional[str] = Form(""),
    consent_adult: Optional[bool] = Form(False),
    mode: Optional[str] = Form("safe"),  # 'safe' or 'edgy'
    image: UploadFile = File(...),
):
    if age < 0 or age > 120:
        raise HTTPException(status_code=400, detail="Invalid age")

    # Require confirmation for adult-only features
    is_adult = age >= 18 and bool(consent_adult)

    # Read and check image
    data = await image.read()
    if not data or len(data) < 1024:
        raise HTTPException(status_code=400, detail="Image appears empty or too small")

    data_url = to_data_url(image, data)

    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        raise HTTPException(status_code=500, detail="OPENAI_API_KEY not configured on server")

    client = OpenAI(api_key=api_key)

    # Prepare user content
    user_context_lines = [
        f"Age: {age}",
        f"AdultConfirmed: {str(is_adult)}",
        f"Mode: {'edgy' if (mode == 'edgy' and is_adult) else 'safe'}",
    ]
    if goals:
        user_context_lines.append(f"Goals: {goals}")
    if notes:
        user_context_lines.append(f"Notes: {notes}")
    if wants_rating and is_adult:
        user_context_lines.append("User requests a 1-10 rating.")
    else:
        user_context_lines.append("If rating requested but user is not 18+, do NOT provide a numeric rating.")

    user_text = "\n".join(user_context_lines)

    system_prompt = build_system_prompt_edgy() if (mode == "edgy" and is_adult) else build_system_prompt_safe()

    messages = [
        {"role": "system", "content": system_prompt},
        {
            "role": "user",
            "content": [
                {"type": "text", "text": user_text},
                {"type": "image_url", "image_url": {"url": data_url, "detail": "low"}},
            ],
        },
    ]

    try:
        completion = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=messages,
            temperature=0.4,
            max_tokens=800,
        )
        text = completion.choices[0].message.content
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Model error: {e}")

    return JSONResponse({"text": text})