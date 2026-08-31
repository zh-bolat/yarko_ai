import asyncio
import os
import sys

# Ensure app path
sys.path.insert(0, "/home/bolatov/test/yarko-ai")

from app.gemini_client import gemini_client
from app.config import settings

async def main():
    print(f"Model: {settings.GEMINI_MODEL}")
    try:
        res = await gemini_client.analyze_message("привет...")
        print("Intent:", res.intent)
        print("Draft reply:", res.draft_reply)
        print("Cost:", res.cost_rub)
    except Exception as e:
        print("Exception:", str(e))

asyncio.run(main())
