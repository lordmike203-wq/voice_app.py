from fastapi import FastAPI, UploadFile, File, Form
from fastapi.responses import StreamingResponse, JSONResponse
import requests
import os

app = FastAPI()

# 👇 uses the env var you set in Render (e.g. ELEVENLABS...)
ELEVEN_API_KEY = os.getenv("ELEVENLABS")  # make sure the key name matches Render

ELEVEN_CLONE_URL = "https://api.elevenlabs.io/v1/voice-cloning/instant-voice-cloning"
ELEVEN_TTS_URL = "https://api.elevenlabs.io/v1/text-to-speech/{voice_id}"


@app.get("/")
def root():
    return {"message": "Voice backend is running"}


@app.post("/clone-voice")
async def clone_voice(
    file: UploadFile = File(...),
    name: str = Form("MyClonedVoice"),
):
    """
    Upload a voice sample and get back a voice_id from ElevenLabs.
    """
    if not ELEVEN_API_KEY:
        return JSONResponse(
            status_code=500,
            content={"error": "ELEVENLABS env var not set on server"},
        )

    try:
        headers = {"xi-api-key": ELEVEN_API_KEY}

        # Read file bytes from upload
        file_bytes = await file.read()

        files = {
            "files": (
                file.filename or "voice_sample.wav",
                file_bytes,
                file.content_type or "audio/wav",
            )
        }
        data = {"name": name}

        resp = requests.post(ELEVEN_CLONE_URL, headers=headers, data=data, files=files)

        if resp.status_code == 200:
            data = resp.json()
            voice_id = data.get("voice_id")
            if not voice_id:
                return JSONResponse(
                    status_code=500,
                    content={"error": "No voice_id in ElevenLabs response", "raw": data},
                )
            return {"voice_id": voice_id}
        else:
            return JSONResponse(
                status_code=resp.status_code,
                content={"error": "ElevenLabs error", "details": resp.text},
            )

    except Exception as e:
        return JSONResponse(
            status_code=500,
            content={"error": f"Exception: {e}"},
        )


@app.post("/speak")
async def speak(
    voice_id: str = Form(...),
    text: str = Form(...),
):
    """
    Generate speech using a cloned voice.
    """
    if not ELEVEN_API_KEY:
        return JSONResponse(
            status_code=500,
            content={"error": "ELEVENLABS env var not set on server"},
        )

    if not text.strip():
        return JSONResponse(
            status_code=400,
            content={"error": "Text is empty"},
        )

    url = ELEVEN_TTS_URL.format(voice_id=voice_id)
    headers = {
        "Content-Type": "application/json",
        "xi-api-key": ELEVEN_API_KEY,
    }
    body = {
        "text": text,
        "model_id": "eleven_monolingual_v1",
    }

    try:
        resp = requests.post(url, json=body, headers=headers)

        if resp.status_code == 200:
            audio_bytes = resp.content
            return StreamingResponse(
                iter([audio_bytes]),
                media_type="audio/mpeg",
            )
        else:
            return JSONResponse(
                status_code=resp.status_code,
                content={"error": "ElevenLabs TTS error", "details": resp.text},
            )

    except Exception as e:
        return JSONResponse(
            status_code=500,
            content={"error": f"Exception: {e}"},
        )
