import asyncio
import websockets
import subprocess
import os

async def test_audio_streaming():
    uri = "ws://localhost:8001/communicating/audio"
    
    try:
        async with websockets.connect(uri) as websocket:
            print("[Client] 已连接到服务器。")

            # 1. 读取本地测试音频文件
            if not os.path.exists("test.wav"):
                print("[Error] 找不到 test.wav 文件，请确保目录下有该文件。")
                return

            with open("test1.wav", "rb") as f:
                audio_bytes = f.read()

            # 2. 构建协议包
            language = "Chinese"
            lang_bytes = language.encode('utf-8')
            # 协议格式：[长度字节] + [语言名] + [音频数据]
            packet = bytes([len(lang_bytes)]) + lang_bytes + audio_bytes
            
            print(f"[Client] 正在发送 {len(packet)} 字节数据...")
            await websocket.send(packet)
            
            # 3. 接收服务器返回的响应
            response = await websocket.recv()
            print(f"[Client] 已接收到 {len(response)} 字节的音频响应。")

            # 4. 保存原始音频
            raw_output = "result_raw.wav"
            with open(raw_output, "wb") as f:
                f.write(response)
            
            print(f"[Client] 原始音频已保存为: {raw_output}")

            # 5. 自动转码逻辑 (解决 22050Hz 播放兼容性问题)
            compatible_output = "result_final.wav"
            print("[Client] 正在进行格式转换以确保兼容性...")
            
            # 使用 ffmpeg 将采样率强制转换为 44100Hz
            conv_process = subprocess.run(
                ["ffmpeg", "-y", "-i", raw_output, "-ar", "44100", compatible_output],
                capture_output=True
            )
            
            if conv_process.returncode == 0:
                print(f"[Client] 转换成功，最终文件: {compatible_output}")
                
                # 6. 尝试播放最终文件
                print("[Client] 尝试播放音频...")
                subprocess.run(["aplay", compatible_output])
            else:
                print("[Client] FFmpeg 转换失败，尝试直接播放原始文件...")
                subprocess.run(["aplay", "-r", "22050", "-f", "S16_LE", "-c", "1", raw_output])

    except Exception as e:
        print(f"[Client] 测试过程中发生错误: {e}")

if __name__ == "__main__":
    # 确保系统中安装了 ffmpeg 和 aplay
    asyncio.run(test_audio_streaming())