import socket
import wave
import struct
import time

UDP_IP = "10.42.0.1"  # Match your updated IP
UDP_PORT = 5005
OUTPUT_FILENAME = "recorded_audio.wav"
SAMPLE_RATE = 24000      # Updated to 24kHz

sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
sock.bind((UDP_IP, UDP_PORT))
sock.settimeout(3.0)  # Stop after 3 seconds of silence

print(f"Listening on port {UDP_PORT} at {SAMPLE_RATE}Hz...")
print("Awaiting incoming stream from Pico...")

audio_chunks = {}   # seq_num -> audio_bytes
expected_seq = 0
lost_packets = 0
detected_chunk_samples = None

try:
    while True:
        try:
            data, addr = sock.recvfrom(2048)
        except socket.timeout:
            print("\nSilence detected — stopping recording")
            break

        if len(data) < 8:
            continue

        # Unpack the 8-byte header (Sequence Number, Timestamp)
        seq_num, timestamp_ms = struct.unpack('<II', data[:8])
        audio_data = data[8:]

        # Dynamically learn the chunk size from the first valid packet
        if detected_chunk_samples is None and len(audio_data) > 0:
            # 2 bytes per sample for 16-bit PCM audio
            detected_chunk_samples = len(audio_data) // 2
            print(f"ℹ️ Auto-detected payload: {len(audio_data)} bytes ({detected_chunk_samples} samples) per packet.")

        audio_chunks[seq_num] = audio_data

        # Track lost packets
        if seq_num > expected_seq:
            lost = seq_num - expected_seq
            lost_packets += lost
            print(f"⚠️  Lost {lost} packet(s) at seq {expected_seq}-{seq_num-1}")

        expected_seq = seq_num + 1

        if len(audio_chunks) % 20 == 0:
            print(f"Received {len(audio_chunks)} packets, lost {lost_packets}...", end="\r")

except KeyboardInterrupt:
    print("\nStopped manually")

finally:
    print(f"\nTotal received: {len(audio_chunks)} packets")
    print(f"Total lost:     {lost_packets} packets")

    if audio_chunks and detected_chunk_samples:
        max_seq = max(audio_chunks.keys())
        
        # Match silence size perfectly to the detected audio chunks
        silence = bytearray(detected_chunk_samples * 2)  

        all_audio = bytearray()
        for i in range(max_seq + 1):
            if i in audio_chunks:
                all_audio += audio_chunks[i]
            else:
                all_audio += silence  # Fill gap with silence

        # Save to WAV with accurate headers
        with wave.open(OUTPUT_FILENAME, 'wb') as wav:
            wav.setnchannels(1)      # Mono
            wav.setsampwidth(2)      # 16-bit (2 bytes)
            wav.setframerate(SAMPLE_RATE)
            wav.writeframes(all_audio)

        # Calculate exact duration based on dynamic chunk sizes
        chunk_duration_ms = (detected_chunk_samples / SAMPLE_RATE) * 1000
        total_duration_s = ((max_seq + 1) * chunk_duration_ms) / 1000

        print(f"✅ Saved: {OUTPUT_FILENAME}")
        print(f"   Final Duration: ~{total_duration_s:.2f}s")
    else:
        print("❌ No audio data received.")

    sock.close()