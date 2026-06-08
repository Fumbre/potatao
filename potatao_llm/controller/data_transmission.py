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



router = APIRouter(prefix="/communicating")

# WebSocket endpoint 
# Pi Zero will connect to ws://IP_OF_MY_MAC:8000/communicating/audio
@router.websocket("/audio")
async def audio_endpoint(websocket: WebSocket):
    """
    Pi Zero connects here and sends audio + language.
    PC processes and sends back translated audio.
    """
    await websocket.accept()
    print("[Server] Pi Zero connected.")
 
    try:
        while True:
            # Receive message from Pi Zero
            # Expected format: [1 byte: lang_len][lang_len bytes: language][rest: audio]

            # TODO
            # it should receive .json like:
            # {data: "bytes.array", translate_to: ["French", "Chineese"] org_language: "Portugal"}
            # and it will be encrepted so we need to decrept this (do not consider this right now, Sunny will handle it)
            data = await websocket.receive_bytes() 
 
            if len(data) < 2:
                print("[Server] Message too short, ignoring.")
                continue
 
            # Parse language name from the first part of the message
            lang_len = data[0]                 # first byte = length of language string
            
            # next N bytes = language name
            # Example: if lang_len = 6, read data[1:7] and get "French"
            language = data[1:1 + lang_len].decode()  

            # rest = WAV (Waveform Audio File Format) audio bytes
            audio = data[1 + lang_len:]               
 
            print(f"[Server] Received {len(audio)} bytes of audio, target language: {language}")
 
            # Pipeline 
            # Speech to text
            text = await asyncio.to_thread(TranslatorProcesser.get_transcriber().transcribe, audio)
            print(f"[Server] Transcribed: {text}")

            # if silence
            if not text:
                print("[Server] Empty transcription, skipping.")
                continue
 
            # Translate text to target language
            translated_text = await asyncio.to_thread(TranslatorProcesser.get_translator().translate, text, language)
            print(f"[Server] Translated: {translated_text}")
 
            # Convert translated text to audio
            audio_response = await asyncio.to_thread(TranslatorProcesser.get_tts().synthesize, translated_text, language)
            print(f"[Server] TTS generated {len(audio_response)} bytes.")
 
            # Send audio back to Pi Zero 
            await websocket.send_bytes(audio_response)
            print("[Server] Audio sent back to Pi Zero.")
 
    except WebSocketDisconnect:
        print("[Server] Pi Zero disconnected.")
    except Exception as e:
        print(f"[Server] Error: {e}")
 