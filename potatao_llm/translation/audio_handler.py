import webrtcvad

class StreamingVAD:

    def __init__(self, max_seconds=2.0, holdover_seconds=0.6):
        # Initialize WebRTC VAD with aggressiveness mode 2 (balanced for noise filtering)
        self.vad = webrtcvad.Vad(2)
        
        # Calculate the maximum allowed buffer size in bytes for a single sentence
        # Formula: 16000 samples/sec * 2 bytes/sample (16-bit PCM) * max_seconds
        self.max_buffer_size = int(16000 * 2 * max_seconds)
        
        # Convert holdover seconds into the number of 20ms frames
        # Each frame is 20ms (0.02s), so 0.6s equals 30 frames
        self.holdover_frames = int(holdover_seconds / 0.02)
        
        # Internal buffer to store valid voice data (including tolerated pauses)
        self.voice_buffer = bytearray()
        
        # State flag to track whether the user is currently within an active speaking period
        self.speaking = False      
        
        # Counter to track continuous silence frames during a speaking period
        self.silence_counter = 0   

    def process(self, frame: bytes) -> tuple[str, bytes] | None:
        """
        Processes a 20ms audio frame and returns a routing signal:
        - ('silence', frame): Pure background noise, safe to echo back immediately.
        - ('speech_ready', chunk): A complete sentence captured, ready for AI translation.
        - None: Voice is accumulating in the buffer, do nothing.
        """
        # Run WebRTC VAD to check if the current 20ms frame contains human speech
        is_speech = self.vad.is_speech(frame, 16000)
        if is_speech:
            # --- Case A: Human voice detected ---
            # Reset silence tracker since user is actively talking
            self.speaking = True
            self.silence_counter = 0
            
            # Append this active voice frame into our sentence buffer
            self.voice_buffer.extend(frame)
            
            # Anti-latency check: If the user talks continuously without taking a breath 
            # and hits the hard limit (e.g., 2 seconds), force a cut to trigger translation.
            if len(self.voice_buffer) >= self.max_buffer_size:
                chunk = self.voice_buffer[:self.max_buffer_size]
                self.voice_buffer = self.voice_buffer[self.max_buffer_size:]
                return "speech_ready", bytes(chunk)
                
            return None
            
        else:
            # --- Case B: Silence or background noise detected ---
            if self.speaking:
                # Sub-case B1: User was talking just now, meaning this could be a mid-sentence pause,
                # a stutter, or a breath. We TEMPORARILY tolerate it and save it to keep semantics coherent.
                self.voice_buffer.extend(frame)
                self.silence_counter += 1
                
                # If the continuous silence duration exceeds our holdover threshold (e.g., 0.6s),
                # we determine that the user has officially finished speaking the current sentence.
                if self.silence_counter >= self.holdover_frames:
                    chunk = bytes(self.voice_buffer)
                    self.voice_buffer.clear()
                    self.speaking = False
                    self.silence_counter = 0
                    return "speech_ready", chunk # Trigger downstream ASR / Translation
                    
                return None
            else:
                # Sub-case B2: Complete silence period (user is not speaking at all).
                # Directly echo back the raw frame to the client to maintain stream continuity.
                return "silence", frame


class PCMFrameSplitter:

    def __init__(self, frame_size=640):
        # Internal FIFO byte buffer to accumulate streaming network packets
        self.buffer = bytearray()
        
        # Target frame size in bytes. 
        # For 16000Hz, 16-bit mono PCM, a 20ms frame is exactly 640 bytes.
        self.frame_size = frame_size  

    def push(self, data: bytes):
        """Appends raw encrypted/decrypted chunks from WebSocket into the buffer."""
        self.buffer.extend(data)

    def next_frame(self):
        """
        Extracts exactly one 20ms frame (640 bytes) from the front of the buffer.
        Returns None if there is not enough data.
        """
        if len(self.buffer) < self.frame_size:
            return None

        # Slice out the oldest 640 bytes
        frame = self.buffer[:self.frame_size]
        # Remove the sliced bytes from the buffer (FIFO queue operation)
        self.buffer = self.buffer[self.frame_size:]
        return bytes(frame)