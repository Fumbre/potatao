import socket
import wave
import struct
import time

UDP_IP = "10.42.0.54"
UDP_PORT = 5005
OUTPUT_FILENAME = "recorded_audio.wav"
SAMPLE_RATE = 16000
CHUNK_SAMPLES = 256      # 512 bytes / 2 bytes per sample
CHUNK_DURATION_MS = (CHUNK_SAMPLES / SAMPLE_RATE) * 1000  # ~32ms per chunk

sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
sock.bind((UDP_IP, UDP_PORT))
sock.settimeout(3.0)  # stop after 3s of silence

print(f"Listening on port {UDP_PORT}...")
print("Press button on Pico to record, release to stop.")

audio_chunks = {}   # seq_num → audio_bytes
expected_seq = 0
lost_packets = 0

try:
    while True:
        try:
            data, addr = sock.recvfrom(2048)
        except socket.timeout:
            print("Silence detected — stopping")
            break

        if len(data) < 8:
            continue

        # unpack header
        seq_num, timestamp_ms = struct.unpack('<II', data[:8])
        audio_data = data[8:]

        audio_chunks[seq_num] = audio_data

        # track lost packets
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

    # reconstruct audio — fill missing chunks with silence
    if audio_chunks:
        max_seq = max(audio_chunks.keys())
        silence = bytearray(CHUNK_SAMPLES * 2)  # 16-bit silence = zeros

        all_audio = bytearray()
        for i in range(max_seq + 1):
            if i in audio_chunks:
                all_audio += audio_chunks[i]
            else:
                all_audio += silence  # fill gap with silence ✅

        with wave.open(OUTPUT_FILENAME, 'wb') as wav:
            wav.setnchannels(1)
            wav.setsampwidth(2)
            wav.setframerate(SAMPLE_RATE)
            wav.writeframes(all_audio)

        print(f"✅ Saved: {OUTPUT_FILENAME}")
        print(f"   Duration: ~{(max_seq * CHUNK_DURATION_MS) / 1000:.1f}s")

    sock.close()