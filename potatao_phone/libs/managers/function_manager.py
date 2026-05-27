# libs/managers/function_manager.py
import os
from libs.data_query.ui import get_view 


class FunctionManager:

    def __init__(self, state_manager, db, wifi=None, nrf=None, mic=None, sd=None):
        self.state_manager = state_manager
        self.db = db
        self.wifi = wifi
        self.nrf = nrf
        self.mic = mic
        self.sd = sd

        # registry — name -> methods
        self._registry = {
            "link":           self._link,
            "send_wifi":      self._send_wifi,
            "send_nrf":       self._send_nrf,
            "receive_nrf":    self._receive_nrf,
            "write_sd":       self._write_sd,
            "get_sdcard_data": self._get_sdcard_data,
            "write_sdcard": self._write_sdcard, 
            "read_mic": self._read_mic,
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
        """rec button → write audio to sd card"""
        self.state_manager.rec_destination = "sd"
        return True

    def _get_sdcard_data(self, context: dict) -> bool:
        """read folder contents and push to stack"""
        # skip for now 
        print("[FunctionManager] get_sdcard_data not implemented yet")
        return False
    
    def _read_mic(self):
        if self.mic is None:
            print("Mic is not init")
            return False
        
        # path_id = context[-1]["parent_id"]

        # path_name = path_id == 0 if "sd_card" else context[-2][path_id]["name"]
        
        if self.state_manager.is_recording:
            buff = self.mic.process()
            return buff
    
    def _write_sdcard(self, context: dict, buff, name):
        with open("/sd/{name}.wav", "wb") as f:
            f.write(bytearray(44))

             