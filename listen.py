import sounddevice as sd
import soundfile as sf
import whisper
import tempfile
import os

model = whisper.load_model("base")

def listen():
    print("듣는 중... (3초)")
    sample_rate = 44100
    duration = 3

    audio = sd.rec(int(duration * sample_rate), samplerate=sample_rate, channels=1, dtype='float32')
    sd.wait()

    with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as f:
        sf.write(f.name, audio, sample_rate)
        result = model.transcribe(f.name, language="ko")
        os.unlink(f.name)

    return result["text"]