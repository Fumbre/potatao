import socket
import wave
import struct

# --- CONFIGURATION ---
# Use "0.0.0.0" to listen on all available network interfaces
UDP_IP = "10.42.0.1" 
UDP_PORT = 5005
OUTPUT_FILENAME = "recorded_audio.wav"

# Setup the socket
sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
sock.bind((UDP_IP, UDP_PORT))

print(f"Listening for audio on port {UDP_PORT}...")
print("Press Ctrl+C to stop recording and save the file.")

audio_frames = []

try:
    while True:
        # Receive a chunk of data (matches the 1024-byte chunks from Pico)
        data, addr = sock.recvfrom(2048) 
        audio_frames.append(data)
        
        # Simple progress indicator
        if len(audio_frames) % 20 == 0:
            print(f"Received {len(audio_frames)} packets...", end="\r")

except KeyboardInterrupt:
    print("\nStopping... Saving to WAV.")

finally:
    # --- SAVE TO WAV FILE ---
    # We combine all chunks into one big byte string
    all_audio = b"".join(audio_frames)
    
    with wave.open(OUTPUT_FILENAME, 'wb') as wav_file:
        # Params: (nchannels, sampwidth, framerate, nframes, comptype, compname)
        # 1 channel (Mono), 2 bytes per sample (16-bit), 16000Hz
        wav_file.setnchannels(1)
        wav_file.setsampwidth(2) 
        wav_file.setframerate(8000)
        wav_file.writeframes(all_audio)

    print(f"Saved: {OUTPUT_FILENAME}")
    sock.close()