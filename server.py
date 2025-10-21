import asyncio
import logging
from io import BytesIO
from pathlib import Path
from typing import Optional
from uuid import uuid4

from fastapi import FastAPI, File, Form, HTTPException, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, HTMLResponse, JSONResponse
from pydub import AudioSegment

from mixer import mix_audio_segments

logger = logging.getLogger("audio_mixer.api")

app = FastAPI(title="Audio Mixer Service", version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

OUTPUT_DIR = Path("outputs")
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
INDEX_HTML = Path(__file__).parent / "templates" / "index.html"


async def _load_audio(upload: UploadFile) -> AudioSegment:
    data = await upload.read()
    if not data:
        raise HTTPException(status_code=400, detail=f"File {upload.filename!r} kosong.")

    file_format: Optional[str] = None
    if upload.filename:
        suffix = Path(upload.filename).suffix.lower()
        if suffix.startswith("."):
            suffix = suffix[1:]
        file_format = suffix or None

    try:
        return AudioSegment.from_file(BytesIO(data), format=file_format)
    except Exception as exc:  # pragma: no cover - pydub raises general Exception
        logger.exception("Gagal memuat file audio %s", upload.filename)
        raise HTTPException(
            status_code=400,
            detail=f"Gagal membaca file audio {upload.filename!r}: {exc}",
        ) from exc


def _build_output_filename() -> Path:
    unique_name = f"mix-{uuid4().hex}.mp3"
    return OUTPUT_DIR / unique_name


async def _export_audio(segment: AudioSegment, output_path: Path) -> None:
    await asyncio.to_thread(segment.export, output_path, format="mp3")


@app.get("/health")
async def health_check() -> JSONResponse:
    return JSONResponse({"status": "ok"})


@app.post("/api/mix")
async def mix_endpoint(
    music: UploadFile = File(..., description="File musik latar (MP3/WAV)"),
    voice: UploadFile = File(..., description="File voice over (MP3/WAV)"),
    delay_seconds: int = Form(5),
    duck_db: int = Form(-10),
    silence_thresh: int = Form(-50),
    min_silence_ms: int = Form(500),
    fade_in_ms: int = Form(2000),
    fade_out_ms: int = Form(2000),
    post_voice_duration: int = Form(10000),
    voice_boost_db: int = Form(3),
    transition_ms: int = Form(200),
) -> JSONResponse:
    music_segment = await _load_audio(music)
    voice_segment = await _load_audio(voice)

    mixed, metadata = mix_audio_segments(
        music_segment,
        voice_segment,
        delay_seconds=delay_seconds,
        duck_db=duck_db,
        silence_thresh=silence_thresh,
        min_silence_ms=min_silence_ms,
        fade_in_ms=fade_in_ms,
        fade_out_ms=fade_out_ms,
        post_voice_duration=post_voice_duration,
        voice_boost_db=voice_boost_db,
        transition_ms=transition_ms,
    )

    output_path = _build_output_filename()
    await _export_audio(mixed, output_path)

    metadata["output_file"] = output_path.name

    logger.info("Output siap: %s", output_path)

    return JSONResponse(
        {
            "message": "Mixing berhasil",
            "download_url": f"/download/{output_path.name}",
            "metadata": metadata,
        }
    )


@app.get("/download/{filename}")
async def download_file(filename: str) -> FileResponse:
    target_path = OUTPUT_DIR / filename
    if not target_path.exists():
        raise HTTPException(status_code=404, detail="File tidak ditemukan.")
    return FileResponse(
        target_path,
        media_type="audio/mpeg",
        filename=target_path.name,
    )


@app.get("/", response_class=HTMLResponse)
async def index() -> HTMLResponse:
    if not INDEX_HTML.exists():
        raise HTTPException(status_code=500, detail="Halaman antarmuka tidak ditemukan.")
    return HTMLResponse(INDEX_HTML.read_text(encoding="utf-8"))
