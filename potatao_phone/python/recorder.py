import serial
import wave
import struct

# Настрой порт под свой (тот самый usbmodem)
SERIAL_PORT = '/dev/cu.usbmodem1101' 
BAUD_RATE = 115200 # Для USB не так критично, но пусть будет
OUTPUT_FILE = "recording.wav"

def record():
    try:
        ser = serial.Serial(SERIAL_PORT, BAUD_RATE)
        print(f"Подключено к {SERIAL_PORT}. Зажми кнопку на Pico для записи...")
        
        frames = []
        
        while True:
            # Читаем данные из порта порциями
            if ser.in_waiting > 0:
                raw_data = ser.read(ser.in_waiting)
                
                # Обработка данных (сдвиг 32-bit -> 24-bit/16-bit)
                # Чтобы не усложнять, сохраним как есть 32-битный звук
                frames.append(raw_data)
                print(".", end="", flush=True)
                
    except KeyboardInterrupt:
        print("\nЗапись остановлена. Сохраняю в wav...")
        
        with wave.open(OUTPUT_FILE, 'wb') as wf:
            wf.setnchannels(1)          # Моно
            wf.setsampwidth(4)         # 32 бита (4 байта)
            wf.setframerate(16000)      # 16 кГц
            wf.writeframes(b''.join(frames))
            
        print(f"Готово! Файл сохранен: {OUTPUT_FILE}")
    finally:
        if 'ser' in locals():
            ser.close()

if __name__ == "__main__":
    record()