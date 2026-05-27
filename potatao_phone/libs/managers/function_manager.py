# libs/managers/function_manager.py
import os
import struct
from libs.data_query.ui import get_view

class FunctionManager:
    # WAV constants
    SAMPLE_RATE    = 24000
    NUM_CHANNELS   = 1
    BITS_PER_SAMPLE = 16
    MIC_HEADER_SIZE = 8   # seq_num (4B) + timestamp_ms (4B)

    def __init__(self, state_manager, db, wifi=None, nrf=None, mic=None, sd=None):
        self.state_manager = state_manager
        self.db = db
        self.wifi = wifi
        self.nrf = nrf
        self.mic = mic
        self.sd = sd

        # recording state — file handle lives here between chunks
        self._rec_file       = None
        self._rec_byte_count = 0

        # registry — name -> methods
        self._registry = {
            "link":           self._link,
            "send_wifi":      self._send_wifi,
            "send_nrf":       self._send_nrf,
            "receive_nrf":    self._receive_nrf,
            "write_sd":       self._write_sd,
            "get_sdcard_data": self._get_sdcard_data,
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
        rows = get_view(self.db, parent_id)

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

    def _send_nrf(self, context: dict) -> bool:
        """rec button → send audio via nrf"""
        if self.nrf is None:
            print("[FunctionManager] NRF not available")
            return False
        self.state_manager.rec_destination = "nrf"
        return True

    def _receive_nrf(self, context: dict) -> bool:
        """receive audio via nrf"""
        if self.nrf is None:
            print("[FunctionManager] NRF not available")
            return False
        self.state_manager.rec_destination = "nrf"
        return True

    def _write_sd(self, context: dict) -> bool:
        self.state_manager.rec_destination = "sd"
        return True

    def _get_sdcard_data(self, context: dict) -> bool:
        for f in os.listdir("/sd/recordings"):
            print("  ", f)
        return False

    
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
