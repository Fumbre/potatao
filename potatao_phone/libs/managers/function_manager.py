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
        print("[FunctionManager] get_sdcard_data not implemented yet")
        return False

    
    # ── RECORDING ───────────────────────────────────────

    def start_recording(self):
        """open file once — called when REC pressed"""
        folder = self._get_rec_folder()
        self._ensure_folder(folder)

        path = f"{folder}/record.wav"
        self._rec_file       = open(path, "wb")
        self._rec_byte_count = 0

        # write placeholder WAV header — real values written on stop
        self._rec_file.write(bytearray(44))
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

        # write real WAV header now we know total size
        self._rec_file.seek(0)
        self._rec_file.write(
            self._make_wav_header(self._rec_byte_count)
        )
        self._rec_file.close()
        self._rec_file       = None
        self._rec_byte_count = 0
        print("[FunctionManager] Recording stopped and saved")

        self.mic.deinit()   # ← clean up I2S hardware


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

    def _get_rec_folder(self) -> str:
        """builds folder path from current stack context"""
        stack        = self.state_manager._stack
        current_list = stack[-1]
        cursor       = self.state_manager.cursor()
        current_item = current_list[cursor]
        parent_id    = current_item["parent_id"]

        if parent_id == 0:
            folder_name = "sd_card"
        else:
            # find parent name from stack below
            parent_list = stack[-2]
            parent_item = None
            for item in parent_list:
                if item["id"] == parent_id:
                    parent_item = item
                    break
            folder_name = parent_item["name"].lower().replace(" ", "_") if parent_item else "unknown"

        return f"/sd/recordings/{folder_name}"

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
