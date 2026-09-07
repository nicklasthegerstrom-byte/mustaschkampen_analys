"""
Stresstest — skickar N parallella anrop till /analyze och rapporterar svarstider.

Användning:
    pip install httpx
    python tests/stresstest.py --image din_bild.jpg --n 20
"""
import asyncio
import time
import argparse
import httpx

URL = "https://mustaschkampen-analys.onrender.com/analyze"


async def send(client: httpx.AsyncClient, image_path: str, i: int):
    with open(image_path, "rb") as f:
        files = {"file": (image_path, f, "image/jpeg")}
        t = time.time()
        try:
            r = await client.post(URL, files=files, timeout=120)
            elapsed = time.time() - t
            print(f"[{i:02d}] {r.status_code} — {elapsed:.1f}s")
        except Exception as e:
            elapsed = time.time() - t
            print(f"[{i:02d}] FEL efter {elapsed:.1f}s: {e}")


async def main(image_path: str, n: int, delay: float):
    print(f"Skickar {n} anrop till {URL} (delay: {delay}s mellan varje)")
    print(f"Bild: {image_path}\n")
    start = time.time()
    async with httpx.AsyncClient() as client:
        tasks = []
        for i in range(n):
            tasks.append(asyncio.create_task(send(client, image_path, i)))
            if delay > 0:
                await asyncio.sleep(delay)
        await asyncio.gather(*tasks)
    print(f"\nTotalt: {time.time() - start:.1f}s")


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--image", required=True, help="Sökväg till testbild (jpg)")
    parser.add_argument("--n", type=int, default=20, help="Antal anrop")
    parser.add_argument("--delay", type=float, default=0, help="Sekunder mellan varje anrop")
    args = parser.parse_args()
    asyncio.run(main(args.image, args.n, args.delay))
