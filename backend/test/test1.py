import asyncio
import httpx
import time

URL = "http://localhost:8000/asr_blocking"  # 或 http://localhost:8000/asr
AUDIO_FILE = "test.mp3"  # 替换为你的音频文件路径
CONCURRENCY = 5

async def post_audio(client, idx):
    with open(AUDIO_FILE, "rb") as f:
        files = {"file": (AUDIO_FILE, f, "audio/mpeg")}
        start = time.time()
        resp = await client.post(URL, files=files)
        end = time.time()
        print(f"Task {idx}: status={resp.status_code}, time={end-start:.2f}s, result={resp.json()}")

async def main():
    async with httpx.AsyncClient(timeout=60) as client:
        tasks = [post_audio(client, i) for i in range(CONCURRENCY)]
        await asyncio.gather(*tasks)

if __name__ == "__main__":
    asyncio.run(main())