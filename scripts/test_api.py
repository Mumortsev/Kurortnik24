
import asyncio
import aiohttp
import sys

API_URL = "https://kurortnik24-production.up.railway.app/api"

async def main():
    async with aiohttp.ClientSession() as session:
        print("Creating category 'Test'...")
        async with session.post(f"{API_URL}/categories", json={"name": "Test", "order": 1}) as resp:
            print(f"Status: {resp.status}")
            print(f"Body: {await resp.text()}")

if __name__ == "__main__":
    if sys.platform == 'win32':
        asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())
    asyncio.run(main())
