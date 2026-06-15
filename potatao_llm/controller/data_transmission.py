'''
It receives audio and the target language from the Pi Zero via WebSocket,
runs it through the transcription, translation and TTS pipeline,
and sends the translated audio back.
'''
# This is necessary to use 'await', which allows you to wait for slow 
# operations (network, processing) without freezing the server
import asyncio
from fastapi import WebSocket, WebSocketDisconnect
from fastapi.routing import APIRouter
from translation.processer import TranslatorProcesser
from translation.translator import OllamaTranslator
from translation.tts import PiperTTS
from encryption.aes.aes import AESUtil
from cache.redis.redis import RedisClient
from translation.audio_handler import PCMFrameSplitter,StreamingVAD
from typing import TypedDict
import json
import struct



router = APIRouter(prefix="/communicating")



class LanguageDict(TypedDict):
    language_name:str
    iso_code:str
    binary_code:int



# WebSocket endpoint 
# Pi Zero will connect to ws://IP_OF_MY_MAC:8000/communicating/audio
@router.websocket("/audio/{target_id}")
async def audio_endpoint(target_id:str,websocket: WebSocket):
    """
    Pi Zero connects here and sends audio + language.
    PC processes and sends back translated audio.
    """
    
    spliter = PCMFrameSplitter(frame_size=640)
    vad = StreamingVAD(max_seconds=6,holdover_seconds=0.6)

    
    await websocket.accept()
    print("[Server] Pi Zero connected.")
    count = 0
    try:
        while True:
            # Receive message from Pi Zero
            # data packet like: source lang binary code + target languages number + target languages + raw audio bytes
            data = await websocket.receive_bytes()
            # decrypt data 
            source_language,target_language_list,audio_data = parse_data(data=data,target_id=target_id)
            # cache audio into the buffer
            spliter.push(audio_data)
            while True:
                frame = spliter.next_frame()
                if not frame:
                    break
                result = vad.process(frame)
                if result is None:
                    continue     
                signal,payload = result
                if signal == "silence":
                    await websocket.send_bytes(payload)
                elif signal == "speech_ready":
                    await _run_pipeline(ws=websocket,target_id=target_id,source_language=source_language,target_language=target_language_list,audio_data=payload)
            
    except WebSocketDisconnect:
        print("[Server] Pi Zero disconnected.")
    except Exception as e:
        print(f"[Server] Error: {e}")
 
 

def parse_data(data:bytes,target_id:str):
    ## get aes key from the redis
    aes_key = RedisClient.get(f"aes_key:{target_id}")
    # decrypt data
    raw_data = AESUtil.decrypt_bytes(aes_key,data)
    offset = 0
    source_language = raw_data[offset]
    offset += 1
    target_language_number = raw_data[offset]
    offset += 1
    target_language_byte = raw_data[offset:offset+target_language_number]
    offset += target_language_number
    raw_audio = raw_data[offset:]
    source_lang_iso = None
    for language in _get_language_list():
        if ord(language["binary_code"]) == source_language:
            source_lang_iso = language["iso_code"]
            break
    
    lang_list = []
    
    for l in _get_language_list():
        for lang_byte in target_language_byte:
            if ord(language["binary_code"]) == lang_byte:
                lang_list.append(l["iso_code"])
                break
    
    return source_lang_iso,lang_list,raw_audio        


async def _run_pipeline(ws:WebSocket,target_id:str,source_language:str, target_language:list[str],audio_data:bytes)->None:
    ## transcribe raw audio to text
    wav_data = _pcm_to_wav(audio_data) 
    transcriber = TranslatorProcesser.get_transcriber()
    text = transcriber.transcribe(audio_bytes=wav_data,language=source_language)
    
    if not text or not text.strip():
        print("[Pipeline] Transcription returned empty text — skipping.")
        return
    
    ## get real targeted language
    real_lang_list = []
    for lang in target_language:
        if lang == source_language:
            continue
        real_lang_list.append(lang)
    
    # get translator and tts engine
    translator = TranslatorProcesser.get_translator()
    tts_engine = TranslatorProcesser.get_tts()
    # create translating tasks
    tasks = [_translate(language=tar_lang, text=text, translator=translator, tts_engine=tts_engine) for tar_lang in real_lang_list]  
    # Run all target languages concurrently
    results: list[tuple[str, bytes] | None] = await asyncio.gather(*tasks, return_exceptions=False)
    
    response_packet = bytearray()
    for target_iso, translated_audio in (r for r in results if r):
        binary_code = _iso_to_binary(target_iso)
        if binary_code is None:
           continue
        audio_len = len(translated_audio)
        response_packet += bytes([binary_code]) + audio_len.to_bytes(4, "big") + translated_audio
    
    # encrypt data
    aes_key = RedisClient.get(f"aes_key:{target_id}")
    print(f"[LLM] encrypt key={aes_key}")
    final_data =  AESUtil.encrypt_bytes(aes_key,response_packet)
    #send back to zero  
    await ws.send_bytes(final_data)





async def _translate(language:str,text:str,translator:OllamaTranslator,tts_engine:PiperTTS)->tuple[str,bytes] | None:
    try:
        translated_text:str = await asyncio.to_thread(
            translator.translate,
            text = text,
            target_language = language,
        )
        
        final_audio_bytes:bytes = await asyncio.to_thread(
            tts_engine.synthesize,
            text = translated_text,
            language = language,
        )
        return language,final_audio_bytes
    except Exception as e:
        print(f"[Pipeline] Error processing target language {language!r}: {e}")  
        return None



def _binary_to_iso(binary_code: int) -> str | None:
    """Look up an ISO code by its binary code. Returns None if not found."""
    for language in _get_language_list():
        if ord(language["binary_code"]) == binary_code:
            return language["iso_code"]
    return None
 
 
def _iso_to_binary(iso_code: str) -> int | None:
    """Look up a binary code by its ISO code. Returns None if not found."""
    for language in _get_language_list():
        if language["iso_code"] == iso_code:
            return ord(language["binary_code"])
    return None


def _get_language_list() -> list[LanguageDict]:
    data = RedisClient.get("lang_list")
    return json.loads(data)["data"]


def _pcm_to_wav(pcm_bytes: bytes, sample_rate: int = 24000) -> bytes:
    num_channels = 1
    bits_per_sample = 16
    byte_rate = sample_rate * num_channels * bits_per_sample // 8
    block_align = num_channels * bits_per_sample // 8
    data_size = len(pcm_bytes)
    header = struct.pack(
        '<4sI4s4sIHHIIHH4sI',
        b'RIFF', 36 + data_size,
        b'WAVE',
        b'fmt ', 16,
        1, num_channels,
        sample_rate, byte_rate,
        block_align, bits_per_sample,
        b'data', data_size
    )
    return header + pcm_bytes