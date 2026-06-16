import asyncio
import keyboard
import pyaudiowpatch as pyaudio
import wave
import io
import os
import time  # <-- Added time import
from shazamio import Shazam
from pydub import AudioSegment


def record_stream(p, device, chunk=512):
	try:
		stream = p.open(
			format=pyaudio.paInt16,
			channels=device["maxInputChannels"],
			rate=int(device["defaultSampleRate"]),
			frames_per_buffer=chunk,
			input=True,
			input_device_index=device["index"]
		)
	except Exception:
		return None, device

	frames = []

	while keyboard.is_pressed('f19'):
		try:
			# Check how many frames are actively waiting in the hardware buffer
			available = stream.get_read_available()

			if available > 0:
				# Read only what is available to guarantee we never block
				data = stream.read(min(available, chunk), exception_on_overflow=False)
				frames.append(data)
			else:
				# If the virtual cable is dead silent, yield the CPU for 10ms
				time.sleep(0.01)

		except Exception:
			pass

	try:
		stream.stop_stream()
		stream.close()
	except Exception:
		pass

	return frames, device


async def main():
	while True:
		p = pyaudio.PyAudio()

		loopback_devices = []
		for i in range(p.get_device_count()):
			dev = p.get_device_info_by_index(i)
			if dev.get("isLoopbackDevice"):
				loopback_devices.append(dev)

		if not loopback_devices:
			print("No loopback devices found.")
			p.terminate()
			return

		print(f"Found {len(loopback_devices)} audio outputs. Ready. Hold F19 to record...")
		keyboard.wait('f19')
		print("Recording from all sources...")

		tasks = []
		for dev in loopback_devices:
			tasks.append(asyncio.to_thread(record_stream, p, dev))

		results = await asyncio.gather(*tasks)

		print("Recording stopped. Mixing audio tracks...")
		p.terminate()

		mixed_audio = None

		for frames, dev in results:
			if not frames:
				continue

			wav_io = io.BytesIO()
			with wave.open(wav_io, 'wb') as wf:
				wf.setnchannels(dev["maxInputChannels"])
				wf.setsampwidth(p.get_sample_size(pyaudio.paInt16))
				wf.setframerate(int(dev["defaultSampleRate"]))
				wf.writeframes(b''.join(frames))

			wav_io.seek(0)
			segment = AudioSegment.from_wav(wav_io)

			if mixed_audio is None:
				mixed_audio = segment
			else:
				mixed_audio = mixed_audio.overlay(segment)

		if mixed_audio is None:
			print("Failed to capture any audio.")
			return

		FILENAME = "mixed_recording_verification.wav"
		mixed_audio.export(FILENAME, format="wav")
		print(f"Mixed file saved to: {os.path.abspath(FILENAME)}")

		final_io = io.BytesIO()
		mixed_audio.export(final_io, format="wav")
		wav_bytes = final_io.getvalue()

		print("Analyzing with Shazam...")
		shazam = Shazam()
		out = await shazam.recognize(wav_bytes)

		if 'track' in out:
			track = out['track']
			title = track.get('title', 'Unknown Title')
			artist = track.get('subtitle', 'Unknown Artist')
			match_offset = out.get('matches', [{}])[0].get('offset', 'N/A')

			print("\n" + "=" * 30)
			print(f"TRACK:  {title}")
			print(f"ARTIST: {artist}")
			print("-" * 30)
			print(f"Match Offset: {match_offset} seconds")
			print(f"Shazam ID:    {track.get('key', 'N/A')}")
			print("=" * 30)
		else:
			print("\nNo match found.")


if __name__ == "__main__":
	asyncio.run(main())