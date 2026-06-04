'''
This file is the entry point of the potatao_llm server.
It receives audio and the target language from the Pi Zero via WebSocket,
runs it through the transcription, translation and TTS pipeline,
and sends the translated audio back.
'''
# This is necessary to use 'await', which allows you to wait for slow 
# operations (network, processing) without freezing the server
import asyncio
from fastapi import FastAPI, WebSocket, WebSocketDisconnect

# Import the server that will run the FastAPI application
import uvicorn
 
from transcriber import FasterWhisperTranscriber  # swap to OpenAITranscriber if needed
from translator  import OllamaTranslator          # swap to OpenAITranslator if needed
from tts         import PiperTTS                  # swap to ElevenLabsTTS / OpenAITTS if needed
 
# Create FastAPI
app = FastAPI()
 
# Initialise components once at startup 
# Change these lines to switch implementations without touching anything else
transcriber = FasterWhisperTranscriber(model_size="base")
translator = OllamaTranslator(model="mistral")
tts = PiperTTS()

# WebSocket endpoint 
# Pi Zero will connect to ws://IP_OF_MY_MAC:8000/audio
@app.websocket("/audio")
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
            text = await asyncio.to_thread(transcriber.transcribe, audio)
            print(f"[Server] Transcribed: {text}")

            # if silence
            if not text:
                print("[Server] Empty transcription, skipping.")
                continue
 
            # Translate text to target language
            translated_text = await asyncio.to_thread(translator.translate, text, language)
            print(f"[Server] Translated: {translated_text}")
 
            # Convert translated text to audio
            audio_response = await asyncio.to_thread(tts.synthesize, translated_text, language)
            print(f"[Server] TTS generated {len(audio_response)} bytes.")
 
            # Send audio back to Pi Zero 
            await websocket.send_bytes(audio_response)
            print("[Server] Audio sent back to Pi Zero.")
 
    except WebSocketDisconnect:
        print("[Server] Pi Zero disconnected.")
    except Exception as e:
        print(f"[Server] Error: {e}")
 
 
# Health check endpoint
# Allows to check if the server is running by opening http://IP:8000/health in your browser
@app.get("/health")
async def health():
    return {"status": "ok"}
 

if __name__ == "__main__":
    # Run with: python server.py
    # Or: uvicorn server:app --host 0.0.0.0 --port 8000
    uvicorn.run(app, host="0.0.0.0", port=8000)

