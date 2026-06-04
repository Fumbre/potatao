# libs/managers/function_manager.py
import os
import struct
import gc
from libs.data_query.ui import get_view

class FunctionManager:
    # WAV constants
    SAMPLE_RATE    = 24000
    NUM_CHANNELS   = 1
    BITS_PER_SAMPLE = 16
    MIC_HEADER_SIZE = 8   # seq_num (4B) + timestamp_ms (4B)

    def __init__(self, state_manager, db, wifi=None, nrf=None, mic=None, sd=None, speaker=None):
        self.state_manager = state_manager
        self.db = db
        self.wifi = wifi
        self.nrf = nrf
        self.mic = mic
        self.sd = sd
        self.speaker = speaker

        # recording state — file handle lives here between chunks
        self._rec_file       = None
        self._rec_byte_count = 0

        # sending files manager
        self._snd_file = None

        self._rcv_file = None
        self._rcv_byte_count  = 0
        self._rcv_chunk_index = 0


        #nrf setup
        #put it to state manager
        self.address = b"1Node"
        self.nrf_endmarker = b'\xff\xff\xff\xff'  

        #speaker setup
        self._speaker_file = None

        # registry — name -> methods
        self._registry = {
            "link":           self._link,
            "send_wifi":      self._send_wifi,
            "send_nrf":       self._send_nrf,
            "receive_nrf":    self._receive_nrf,
            "write_sd":       self._write_sd,
            "get_sdcard_data": self._get_sdcard_data,
            "send_data_to_nrf":    self._send_data_to_nrf, 
            "send_nrf_chank": self._send_nrf_chank,
            "stop_nrf_send": self._stop_nrf_send,
            "play_speaker": self._play_speaker,
            "start_speaker": self._start_speaker,
            "stop_speaker": self._stop_speaker,
        }

    def execute(self, function_name: str, context: dict) -> bool:
        """
        Executes function by name.
        Returns True if UI needs re-render, False if not.
        """
        fn = self._registry.get(function_name)
        if fn is None:
            print(f"[FunctionManager] Unknown function: {function_name}")
            return False
        return fn(context)


    # ── FUNCTIONS ───────────────────────────────────────

    def _link(self, item: dict) -> bool:
        """fetch children from db and push to stack"""

        parent_id = item["id"]
        rows = get_view(self.db, parent_id, "/sd/potatao.db")

        if not rows:
            print(f"[FunctionManager] No children for id {parent_id}")
            return False


        self.state_manager.push_stack(rows)
        self.state_manager.reset_cursor()
        return True

    def _send_wifi(self, context: dict) -> bool:
        """rec button → send audio via wifi"""
        if self.wifi is None:
            print("[FunctionManager] WiFi not available")
            return False
        
        self.wifi.connect()
        
        self.state_manager.rec_destination = "wifi"
        return True



    def _send_nrf(self, context: dict):
        """rec button → send audio via nrf"""
        if self.nrf is None:
            print("[FunctionManager] NRF not available")
            return False
        self._get_sdcard_data(context, "send_data_to_nrf")
        return True
    
    def _send_data_to_nrf(self, context: dict):
        # set flag to true
        self.state_manager.is_nrf_sending = True
        print(self.state_manager.is_nrf_sending)
        print(context["name"])
        filename = context["name"]
        path = f"sd/recordings/{filename}"
        self._snd_file = open(path, "rb")
        self.nrf.open_tx_pipe(self.address)
        #skip wav header
        self._snd_file.seek(44)

    def _send_nrf_chank(self):
        if self.nrf is None or self._snd_file is None:
            return
          
        chunk_size = 24
        chunk = self._snd_file.read(chunk_size)
        if not chunk:
            end_marker = b'\xff\xff\xff\xff' + b'\x00' * (chunk_size - 4)
            try:
                self.nrf.send(end_marker)
            except OSError:
                pass
            self._stop_nrf_send()
            return
        
        if len(chunk) < chunk_size:
            chunk = chunk + b'\x00' * (chunk_size - len(chunk))
        
        try:
            self.nrf.send(chunk)
        except OSError:
            print(f"[NRF] Send failed at chunk")
    
    def _stop_nrf_send(self):
        print(f"[NRF] Done — {self._snd_chunk_index} chunks sent")
        self.state_manager.is_nrf_sending = False
        if self._snd_file:
            self._snd_file.close()
            self._snd_file = None
        



    def _receive_nrf(self, context: dict) -> bool:
        """receive audio via nrf"""
        if self.nrf is None:
            print("[FunctionManager] NRF not available")
            return False
        # self.state_manager.rec_destination = "nrf"
        folder = "/sd/recordings"
        self._ensure_folder(folder)
        index = self._get_next_index(folder)
        path  = f"{folder}/record_{index}.wav"

        self._rcv_file       = open(path, "wb")
        self._rcv_byte_count = 0
        self._rcv_chunk_index = 0

        # Write blank header placeholder — filled in on stop
        self._rcv_file.write(bytearray(44))

        self.nrf.open_rx_pipe(0, self.address)
        self.nrf.start_listening()
        self.state_manager.is_nrf_receiving = True
        print(f"[NRF] Receiving → {path}")
        return True

    def _receive_nrf_chunk(self):
        """call every loop while is_nrf_receiving is True"""
        if self.nrf is None or self._rcv_file is None:
            return

        #nado podumat' esli nikto ne otpravlyat////if nothing received for a long time what should we do
        if not self.nrf.any():           # nothing arrived yet 
            return

        chunk = self.nrf.recv()

        # Check for end marker in first 4 bytes
        if chunk[:4] == self.nrf_endmarker:
            self._stop_nrf_receive()
            return

        self._rcv_file.write(chunk)
        self._rcv_byte_count  += len(chunk)
        self._rcv_chunk_index += 1


    def _stop_nrf_receive(self):
        """write real WAV header and close"""
        if self._rcv_file is None:
            return

        self.nrf.stop_listening()
        self.state_manager.is_nrf_receiving = False

        # Rewind and write correct WAV header
        # Use same params your mic records at (e.g. 8000 Hz, mono, 16-bit)
        self._rcv_file.seek(0)
        self._rcv_file.write(
            self._make_wav_header(self._rcv_byte_count)
        )
        self._rcv_file.close()
        self._rcv_file        = None
        print(f"[NRF] Received {self._rcv_chunk_index} chunks, {self._rcv_byte_count} bytes saved")



    def _start_speaker(self, context: dict):
        if hasattr(self, '_speaker_file') and self._speaker_file is not None:
            try:
                self._speaker_file.close()
            except:
                pass
            self._speaker_file = None

        gc.collect()
            
        self.speaker.init()
        self.state_manager.is_playing = True
        path = f"/sd/recordings/{context["name"]}"
        print(path)
        self._speaker_file = open(path, "rb")
        self._speaker_file.read(44)   # skip WAV header

    def _play_speaker(self):
        num_read = self._speaker_file.readinto(self.speaker.buf)        
        if num_read == 0:
            self._stop_speaker()
            return
            
        # Pass a memoryview slice of the preallocated buffer
        self.speaker.play_chunk(memoryview(self.speaker.buf)[:num_read])


    def _stop_speaker(self):
        self.state_manager.is_playing = False
        self.speaker.deinit()

        if self._speaker_file is not None:
            try:
                self._speaker_file.close()
            except:
                pass
            self._speaker_file = None
            print("[Speaker] File handles closed cleanly")
        
        try:
            os.sync()
        except:
            pass



    def _write_sd(self, context: dict) -> bool:
        self.state_manager.rec_destination = "sd"
        return True

    def _get_sdcard_data(self, context: dict, function_name: str = 'start_speaker') -> bool:
        folder = "/sd/recordings"
        try:
            names = os.listdir(folder)
        except OSError:
            print(f"[FunctionManager] No recordings folder")
            return False

        rows = []
        for name in sorted(names):
            if not name.lower().endswith(".wav"):
                continue
            rows.append({
                "id":            len(rows),
                "function_name": function_name,
                "name":          name,
                "parent_id":     context.get("id", -1),
                "order_num":     len(rows),
            })

        if not rows:
            print("[FunctionManager] No recordings found")
            return False

        self.state_manager.push_stack(rows)
        self.state_manager.reset_cursor()
        return True

    
    # ── RECORDING ───────────────────────────────────────

    def _get_next_index(self, folder: str) -> int:
        """scan folder for record_N.wav files and return max N + 1"""

        max_index = -1
        try:
            for name in os.listdir(folder):
                lower = name.lower()
                if lower.startswith("record_") and lower.endswith(".wav"):
                    try:
                        n = int(lower[7:-4])
                        if n > max_index:
                            max_index = n
                    except ValueError:
                        pass
        except OSError:
            pass
        return max_index + 1

    def start_recording(self):
        """open file once — called when REC pressed"""
        gc.collect()

        folder = "/sd/recordings"
        self._ensure_folder(folder)

        index = self._get_next_index(folder)
        path = f"{folder}/record_{index}.wav"

        self._rec_file       = open(path, "wb")   # SD ops while I2S is idle
        self._rec_byte_count = 0
        self._rec_file.write(bytearray(44))        # placeholder WAV header

        self.mic.init()                            # start I2S only after SD is done
        print(f"[FunctionManager] Recording started → {path}")

    def write_chunk(self):
        """write one mic chunk — called every loop while recording"""
        if self.mic is None or self._rec_file is None:
            return

        chunk = self.mic.process()
        if chunk is None:
            return

        self._rec_file.write(chunk)
        self._rec_byte_count += len(chunk)


    def stop_recording(self):
        """fix WAV header and close file — called when REC released"""
        if self._rec_file is None:
            return
        
        self.mic.deinit()                          # stop I2S before SD ops

        self._rec_file.seek(0)
        self._rec_file.write(
            self._make_wav_header(self._rec_byte_count)
        )
        self._rec_file.close()
        self._rec_file       = None
        self._rec_byte_count = 0
        print("[FunctionManager] Recording stopped and saved")
        try:
            os.sync()
        except:
            pass



    def _make_wav_header(self, data_size: int) -> bytes:
        byte_rate   = self.SAMPLE_RATE * self.NUM_CHANNELS * self.BITS_PER_SAMPLE // 8
        block_align = self.NUM_CHANNELS * self.BITS_PER_SAMPLE // 8
        return struct.pack(
            '<4sI4s4sIHHIIHH4sI',
            b'RIFF', 36 + data_size,
            b'WAVE',
            b'fmt ', 16,
            1,                        # PCM format
            self.NUM_CHANNELS,
            self.SAMPLE_RATE,
            byte_rate,
            block_align,
            self.BITS_PER_SAMPLE,
            b'data', data_size
        )

    def _ensure_folder(self, path: str):
        """creates folder if it doesn't exist"""
        parts = path.split("/")
        current = ""
        for part in parts:
            if not part:
                continue
            current = f"{current}/{part}"
            try:
                os.mkdir(current)
            except OSError:
                pass   # already exists

        