# libs/managers/function_manager.py
import os
import struct
import gc
from libs.data_query.ui import get_view
from libs.managers.state_manager import StateManager
import uasyncio
import struct
from libs.communication.communication import ws_connect,ws_send,disconnect,ws_receive,receive_disconnect
from libs.encrpytion.encryption import shake_hands,receive_hand_shake
from libs.mic.mic import Mic
from libs.nrf24.nrf24l01 import NRF24L01
from libs.wifi.wifi import Wifi
from libs.speaker.speaker import Speaker
from libs.encrpytion.encryption import register, encrypt_data,decrypt_data,CONVERSATION_AES_KEY,RECEIVE_AES_KEY
from libs.language.language_setting import init_language
from libs.managers.queue import SimpleQueue,HEADER_FMT
import utime


class FunctionManager:
    # WAV constants
    SAMPLE_RATE    = 24000
    NUM_CHANNELS   = 1
    BITS_PER_SAMPLE = 16
    MIC_HEADER_SIZE = 8   # seq_num (4B) + timestamp_ms (4B)
    
    

    def __init__(self, state_manager:StateManager, db, wifi:Wifi=None, nrf:NRF24L01=None, mic:Mic=None, sd=None, speaker:Speaker=None):
              
        self.out_buf = bytearray(1024)  # preallocated, no GC pressure   
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
        self.seq = 0
        self.last_seq = -1
        self.last_packet_time = 0

        #speaker setup
        self._speaker_file = None

        # registry — name -> methods
        self._registry = {
            "link":           self._link,
            "send_nrf":       self._send_nrf,
            "receive_nrf":    self._receive_nrf,
            "get_sdcard_data": self._get_sdcard_data,
            "send_data_to_nrf":    self._send_data_to_nrf, 
            "send_nrf_chunk": self._send_nrf_chunk,
            "stop_nrf_send": self._stop_nrf_send,
            "play_speaker": self._play_speaker,
            "start_speaker": self._start_speaker,
            "stop_speaker": self._stop_speaker,
            "pop_back": self._back_to_prev_menu,
            "link_wifi": self._link_wifi,
            "change_language": self.change_language,
            "set_language": self.set_language,
            "receive_translate_auido": self.start_receive_translate_audio
        }
        
        ## define the data transmitation structure
        self.data = {}
        ## define async task queue
        self.queue = SimpleQueue(maxsize=20)
        self.network_task = None

        self.LANGUAGE_DICT = {}

        # the menu folder for getting correct directory
        self.menu_folder = None

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

    def _back_to_prev_menu(self, who):
        self.state_manager.pop_stack()
        return True


    def _link_wifi(self, item: dict) -> bool:
        """Show notification right after a link that wifi is connecting"""
        parent_id = item["id"]
        rows = get_view(self.db, parent_id, "/sd/potatao.db")

        if not rows:
            print(f"[FunctionManager] No children for id {parent_id}")
            return False


        self.state_manager.push_stack(rows)
        self.state_manager.reset_cursor()

        print("we are here")
        if not self.state_manager.is_wifi_connected:
            self.state_manager.is_wifi_connecting = True

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
        self.nrf.set_power_speed(3, 2)
        filename = context["name"]
        path = f"/sd/{self.menu_folder}/{filename}"
        self._snd_file = open(path, "rb")
        self.nrf.open_tx_pipe(self.address)
        self.seq = 0
        print("START TX")


    def _send_nrf_chunk(self):
        chunk = self._snd_file.read(28)  # 28 bytes of audio data
        
        if not chunk:
            self._stop_nrf_send()
            return

        if len(chunk) < 28:
            chunk += bytes(28 - len(chunk))

        packet = struct.pack("<I", self.seq) + chunk

        try:

            self.nrf.send(packet)

            print("TX", self.seq)

        except Exception as e:

            print("SEND FAIL:", e)

            self.nrf.flush_tx()
            self.nrf.flush_rx()

        self.seq += 1

        utime.sleep_ms(1)
    
    def _stop_nrf_send(self):
        print(f"[NRF] Done — {self.seq} chunks sent")
        self.state_manager.is_nrf_sending = False
        if self._snd_file:
            self._snd_file.close()
            self._snd_file = None
        



    def _receive_nrf(self, context: dict) -> bool:
        """receive audio via nrf"""
        if self.nrf is None:
            print("[FunctionManager] NRF not available")
            return False
        

        self.nrf.set_power_speed(3, 2)
        self.nrf.open_rx_pipe(0, self.address)
        self.nrf.start_listening()
        self.state_manager.is_nrf_receiving = True
        print("NRF RX READY")
        
        # self.state_manager.rec_destination = "nrf"
        folder = "/sd/received"
        self._ensure_folder(folder)
        index = self._get_next_index(folder)
        path  = f"{folder}/record_{index}.wav"

        self._rcv_file       = open(path, "wb")
        self._rcv_byte_count = 0
        self._rcv_chunk_index = 0
        self.seq = 0
        self.last_seq = -1
        self.last_packet_time = utime.ticks_ms()
       
        return True

    def _receive_nrf_chunk(self):
        while self.nrf.any():
            print("NRF RX ANY")
            try:

                packet = self.nrf.recv()

                self.last_packet_time = utime.ticks_ms()

                self.seq = struct.unpack("<I", packet[:4])[0]

                data = packet[4:]

                # packet loss detect
                if self.last_seq != -1:

                    if self.seq != self.last_seq + 1:

                        lost = self.seq - self.last_seq - 1
                        print("LOST:", lost)

                self.last_seq = self.seq

                self._rcv_file.write(data)

                print("RX", self.seq)

            except Exception as e:

                print("RX ERROR:", e)

                self.nrf.flush_rx()

        # stop after silence
        if utime.ticks_diff(
            utime.ticks_ms(),
            self.last_packet_time
        ) > 3000:
            self._stop_nrf_receive()


    def _stop_nrf_receive(self):
        """write real WAV header and close"""
        if self._rcv_file is None:
            return

        self.nrf.stop_listening()
        self.state_manager.is_nrf_receiving = False

        # Rewind and write correct WAV header
        # Use same params your mic records at (e.g. 8000 Hz, mono, 16-bit)
        self._rcv_file.close()
        self._rcv_file        = None
        print(f"DONE")


    def start_receive_translate_audio(self, context):
        #shake hand with pico
        receive_hand_shake()
        # - connect to websocket
        loop = uasyncio.get_event_loop()
        loop.run_until_complete(ws_connect())
        self.speaker.init()
        self.state_manager.is_wifi_receiving = True
        # - if playing on speaker is impossible or bad
        # - put the received data to sd card
        
    
    def receiving_translated_audio(self):
        #receive data from websocket
        loop = uasyncio.get_event_loop()
        orginal_data = loop.run_until_complete(ws_receive())
        # decrypt data
        raw_audio = decrypt_data(orginal_data,RECEIVE_AES_KEY)
        # play audio with speaker
        self.speaker.play_chunk(raw_audio)
    
    def stop_receive_translated_audio(self):
        ## close websocket connection
        loop = uasyncio.get_event_loop()
        loop.run_until_complete(disconnect())
        #deinit speaker
        self.speaker.deinit()
        loop.run_until_complete(receive_disconnect())
        self.state_manager.is_wifi_receiving = False    
           
    
    
    def _start_speaker(self, context: dict):
        self.speaker.init()
        self.state_manager.is_playing = True
        path = f"/sd/{self.menu_folder}/{context['name']}"
        try:
            self._speaker_file = open(path, "rb")
            self._speaker_file.read(44)   # skip WAV header
        except OSError as e:
            if e.errno == 5: # EIO
                print("[Storage] Hardware EIO detected! Attempting filesystem remount reset...")
                self._stop_speaker()
            else:
                raise e

    def _play_speaker(self):
        # Safely attempt to pull the byte segment from the file stream
        num_read = self._speaker_file.readinto(self.speaker.buf)        

        if num_read == 0 or num_read is None:
            self._stop_speaker()
            return
            
        # Pass a memoryview slice of the preallocated buffer safely
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


    def _get_sdcard_data(self, context: dict, function_name: str = 'start_speaker') -> bool:
        """
         if context is not "recording" or "received"
         then  folder is "sd/recordings"
         else  folder is "sd/" or "sd/received"
        """

        print("from get sd card data", context["name"])

        print("function name:", function_name)

        if context["name"] != "recordings" and context["name"] != "received":
            folder ="/sd/recordings"
        else:
            folder = f"/sd/{context['name']}"
            # write the menu folder name to state
            self.menu_folder = context["name"]
            print(self.menu_folder)
        try:
            names = os.listdir(folder)
        except OSError:
            print(f"[FunctionManager] No {self.menu_folder} folder")
            return False

        rows = []
        for name in names:
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
        # print(f"[FunctionManager] Recording started → {path}")

    def wifi_connect(self): 
        self.state_manager.is_wifi_connected = self.wifi.connect()
        self.state_manager.is_wifi_connecting = not self.state_manager.is_wifi_connected

        if self.state_manager.is_wifi_connected :
            print('we are connected')
        return self.state_manager.is_wifi_connected

    def connect_to_backend(self):
        """reigester pico device to zero"""
        # self.state_manager.rec_destination = "wifi"

        register()
        
        self.LANGUAGE_DICT = init_language() # after connection


    def recording_to_backend(self):
        self.mic.init()
        
        # exchange encryption key with zero
        shake_hands(prefered_language=self.state_manager.prefered_language)
        # open websocket connection
        loop = uasyncio.get_event_loop()
        loop.run_until_complete(ws_connect())
        self.network_task = loop.create_task(ws_send(self.queue))

        # change state to wifi sending
        self.state_manager.is_wifi_sending = True
                
    def send_wifi_chunk(self):
        """send a chunk by wifi — called every loop while recording"""
        if self.mic is None:
            return
        
        raw_slice = self.mic.process()

        if not raw_slice or len(raw_slice) <= 0:
            return
        chunk = bytes(raw_slice)
        
        #create ws_send asyncio task
        if not self.queue.full():
            lang = self.state_manager.prefered_language_binary
            print(lang)
            packet = struct.pack(HEADER_FMT, lang, b'\x00' * 8) + chunk
            encrypted_data = encrypt_data(packet,CONVERSATION_AES_KEY)
            self.queue.put_nowait(encrypted_data)
            

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
        self._rec_file = None
        self._rec_byte_count = 0
        print("[FunctionManager] Recording stopped and saved")
        try:
            os.sync()
        except:
            pass
    
    def stop_wifi_recording(self):
        self.state_manager.is_wifi_sending = False
        ##stop async task
        self.network_task.cancel()
        self.network_task = None
        ##  websocket disconnection
        uasyncio.get_event_loop().run_until_complete(disconnect())

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

    def change_language(self, context):
        stck = []

        for index, lang in enumerate(self.LANGUAGE_DICT):
            stck.append({
                'id': index,
                'record_method': 'wifi',
                'name': lang,
                'parent_id': 0,
                'function_name': 'set_language',
                'binary_code': self.LANGUAGE_DICT[lang]['binary_code'],
                'iso_code': self.LANGUAGE_DICT[lang]['iso_code'],
            })
        self.state_manager.push_stack(stck)
        return True

    def set_language(self, context):
        print("set_language", context)

        self.state_manager.prefered_language = context["iso_code"]
        self.state_manager.prefered_language_binary = ord(context["binary_code"])

        self.state_manager.pop_stack()
        return True

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