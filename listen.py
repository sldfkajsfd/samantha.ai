import os
os.environ["PATH"] = r"C:\ffmpeg\bin" + os.pathsep + os.environ.get("PATH", "")
import sounddevice as sd
import soundfile as sf
import whisper
import tempfile


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
        try:
          os.unlink(f.name)
        except PermissionError:
           pass

    return result["text"]