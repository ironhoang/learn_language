"""Gemini native TTS implementation of TTSProvider.

Gemini's TTS models return raw 16-bit PCM (24kHz mono) rather than a
container format, so this wraps the bytes in a WAV header via `wave` before
handing back a real audio file — everything downstream (ffprobe, ffmpeg,
your ears) expects a container, not bare PCM. Language is auto-detected from
the input text (Vietnamese included), so there's no language param to pass.
"""

import os
import wave
from pathlib import Path

from dotenv import load_dotenv

from generator.providers.tts import TTSProvider, TTSResult

load_dotenv(Path(__file__).resolve().parent.parent.parent / ".env")

_VOICE_MAP = {
    "male": "Puck",
    "female": "Kore",
}

_MODEL = "gemini-2.5-flash-preview-tts"


def resolve_voice(voice: str) -> str:
    key = voice.lower()
    try:
        return _VOICE_MAP[key]
    except KeyError:
        raise ValueError(
            f"No Gemini TTS voice mapped for voice={voice!r}. Available: {list(_VOICE_MAP)}"
        )


class GeminiTTSProvider(TTSProvider):
    """`voice` must already be a concrete Gemini voice name — resolve it with
    resolve_voice("male"/"female") before calling synthesize(). Gemini TTS has
    no rate control, so `rate` is accepted but ignored."""

    def __init__(self):
        from google import genai

        api_key = os.environ.get("GEMINI_API_KEY") or os.environ.get("GOOGLE_API_KEY")
        if not api_key:
            raise RuntimeError(
                "GEMINI_API_KEY (or GOOGLE_API_KEY) not set — see content-pipeline/.env.example"
            )
        self._client = genai.Client(api_key=api_key)

    def synthesize(self, text: str, voice: str, out_path: Path, rate: str = "+0%") -> TTSResult:
        from google.genai import types

        response = self._client.models.generate_content(
            model=_MODEL,
            contents=text,
            config=types.GenerateContentConfig(
                response_modalities=["AUDIO"],
                speech_config=types.SpeechConfig(
                    voice_config=types.VoiceConfig(
                        prebuilt_voice_config=types.PrebuiltVoiceConfig(voice_name=voice)
                    )
                ),
            ),
        )
        pcm = response.candidates[0].content.parts[0].inline_data.data

        out_path.parent.mkdir(parents=True, exist_ok=True)
        with wave.open(str(out_path), "wb") as wf:
            wf.setnchannels(1)
            wf.setsampwidth(2)
            wf.setframerate(24000)
            wf.writeframes(pcm)

        return TTSResult(audio_path=out_path, word_boundaries=[])
