import os
from os.path import join, dirname, expanduser, expandvars
import tempfile
import wave
import pyaudio
import keyboard
import pyautogui
import pyperclip
from groq import Groq

def loadenv(filename):
    with open(expanduser(expandvars(filename))) as f:
        for line in f.readlines():
            key, value = line.strip().split("=")
            os.environ[key] = value.strip('"\'')

if "GROQ_API_KEY" not in os.environ:
    loadenv("/etc/dictate.env")
client = Groq(api_key=os.environ.get("GROQ_API_KEY"))
BASE = expanduser(expandvars("$HOME/.config/dictate"))

def slurp(filename):
    full = join(BASE, filename)
    if not os.path.exists(full): return ''
    with open(full) as f:
        return f.read().strip()

def spit(filename, data):
    print(f"Saving to {filename} with {data}")
    with open(join(BASE, filename), "w") as f:
        f.write(data)

def state_save(state): spit("state", state)
def state_save_idle(): state_save("I")
def state_save_recording(): state_save("R")
def state_save_transcribing(): state_save("T")
def model_current(): return slurp("model")
def lang_current(): return slurp("lang")
def prompt_current(): return slurp("prompt")

def record_audio(sample_rate=16000, channels=1, chunk=1024):
    p = pyaudio.PyAudio()
    stream = p.open(
        format=pyaudio.paInt16,
        channels=channels,
        rate=sample_rate,
        input=True,
        frames_per_buffer=chunk,
    )

    print("Press and hold the PAUSE button to start recording...")
    frames = []

    state_save_idle()
    keyboard.wait("pause")  # Wait for PAUSE button to be pressed
    print("Recording... (Release PAUSE to stop)")

    state_save_recording()
    while keyboard.is_pressed("pause"):
        data = stream.read(chunk)
        frames.append(data)

    print("Recording finished.")
    stream.stop_stream()
    stream.close()
    p.terminate()
    return frames, sample_rate

def save_audio(frames, sample_rate):
    with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as temp_audio:
        wf = wave.open(temp_audio.name, "wb")
        wf.setnchannels(1)
        wf.setsampwidth(pyaudio.PyAudio().get_sample_size(pyaudio.paInt16))
        wf.setframerate(sample_rate)
        wf.writeframes(b"".join(frames))
        wf.close()
        return temp_audio.name

def transcribe_audio(audio_file_path):
    state_save_transcribing()
    try:
        model = model_current()
        lang = lang_current()
        prompt = "" #prompt_current()
        print(f"Using model: {model}, language: {lang}, prompt: {prompt}")
        with open(audio_file_path, "rb") as file:
            transcription = client.audio.transcriptions.create(
                file=(os.path.basename(audio_file_path), file.read()),
                model=model,
                prompt=prompt,
                # prompt="""The audio is by a programmer discussing programming issues, the programmer mostly uses python and might mention python libraries or reference code in his speech.""",
                response_format="text",
                language=lang,
            )
            transcription = str(transcription).strip()
        return transcription  # This is now directly the transcription text
    except Exception as e:
        print(f"An error occurred: {str(e)}")
        return None

def copy_transcription_to_clipboard(text):
    pyperclip.copy(text)
    pyautogui.hotkey("ctrl", "v")

def main():
    while True:
        frames, sample_rate = record_audio()
        temp_audio_file = save_audio(frames, sample_rate)
        print("Transcribing...")
        transcription = transcribe_audio(temp_audio_file)

        if transcription:
            print("\nTranscription:")
            print(transcription)
            print("Copying transcription to clipboard...")
            copy_transcription_to_clipboard(transcription)
            print("Transcription copied to clipboard and pasted into the application.")
        else:
            print("Transcription failed.")

        os.unlink(temp_audio_file)
        print("\nReady for next recording. Press PAUSE to start.")

if __name__ == "__main__":
    main()
