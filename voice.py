import os
import io
import sounddevice as sd
import soundfile as sf
from elevenlabs import ElevenLabs

client = ElevenLabs(api_key=os.getenv("ELEVENLABS_API_KEY"))

VOICE_ID = "cgSgspJ2msm6clMCkdW9"


def speak(text):
    audio = client.text_to_speech.convert(
        voice_id=VOICE_ID,
        text=text,
        model_id="eleven_multilingual_v2"
    )
    audio_bytes = b"".join(audio)
    audio_data, sample_rate = sf.read(io.BytesIO(audio_bytes))
    sd.play(audio_data, sample_rate)
    sd.wait()