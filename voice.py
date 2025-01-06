import sounddevice as sd
import queue
from vosk import Model, KaldiRecognizer
from miio import Device
import google.generativeai as genai


genai.configure(api_key="API KEY")
lamp = Device("192.168.29.49", "miio LAMP TOKEN")
audio_queue = queue.Queue()


def audio_callback(indata, frames, time, status):
	if status:
		print(f"Audio status: {status}", file=sys.stderr)
	audio_queue.put(bytes(indata))

def power(value:bool):
	lamp.send("set_power",["on" if value else "off"]);
def color_RGB(red:int,green:int, blue:int):
	lamp.send("set_rgb",[int(red)<<16|int(green)<<8|int(blue)]);
def brightness(percentage:int):
	lamp.send("set_bright",[int(percentage)]);
	

if __name__ == "__main__":
	try:
		model = genai.GenerativeModel(model_name="gemini-1.5-pro-latest", tools=[power, color_RGB,brightness])
		chat = model.start_chat()
		recognizer = KaldiRecognizer(Model("vosk-model-small-en-in-0.4"), 16000)
		print("Starting live transcription...")
		with sd.RawInputStream(samplerate=16000, blocksize=8000, dtype="int16",channels=1, callback=audio_callback):
			while True:	
				data = audio_queue.get()
				if recognizer.AcceptWaveform(data):
					text = recognizer.Result()[14:-3]
					if "raspberry" in text:
						try:
							print(text)
							response = (chat.send_message(text.replace('read','red')))
							for part in response.parts:
								if fn := part.function_call:
									args = ", ".join(f"{key}={val}" for key, val in fn.args.items())
									exec(f"{fn.name}({args})")
						except Exception:
							print("ERROR")
							pass						
							
							
	except FileNotFoundError:
		print("Model not found. Make sure to download it and set the correct path.")
		sys.exit(1)
