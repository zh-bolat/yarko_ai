import asyncio
import os
import sys

sys.path.insert(0, "/home/bolatov/test/yarko-ai")

from app.context_manager import context_manager
from app.config import settings
from app.gemini_client import gemini_client
import logging

logging.basicConfig(level=logging.INFO)

async def test_ready(user_id, merged, history):
    print("READY CALLED!")
    try:
        print("Calling Gemini...")
        res = await gemini_client.analyze_message(merged)
        print("Gemini response:", res.intent)
    except Exception as e:
        print("Error:", e)

async def main():
    settings.MESSAGE_BUFFER_TIMEOUT_SEC = 2
    print("Adding message...")
    await context_manager.add_message(123, "хочу в турцию на 10 дней 100 тысяч", test_ready)
    print("Waiting...")
    await asyncio.sleep(15)
    print("Done")

asyncio.run(main())
