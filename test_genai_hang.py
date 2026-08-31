import asyncio
import os
import sys

sys.path.insert(0, "/home/bolatov/test/yarko-ai")
from app.config import settings
from google import genai
from pydantic import BaseModel

class R(BaseModel):
    hello: str

async def main():
    client = genai.Client(api_key=settings.GEMINI_API_KEY)
    
    print("Testing async generate_content...")
    try:
        task = asyncio.create_task(client.aio.models.generate_content(
            model=settings.GEMINI_MODEL,
            contents="say hi",
            config={"response_mime_type": "application/json", "response_schema": R}
        ))
        res = await asyncio.wait_for(task, timeout=5)
        print("ASYNC SUCCESS:", res.text)
    except Exception as e:
        print("ASYNC FAILED:", e)

    print("Testing sync generate_content in thread...")
    try:
        def sync_call():
            return client.models.generate_content(
                model=settings.GEMINI_MODEL,
                contents="say hi",
                config={"response_mime_type": "application/json", "response_schema": R}
            )
        res = await asyncio.wait_for(asyncio.to_thread(sync_call), timeout=5)
        print("SYNC IN THREAD SUCCESS:", res.text)
    except Exception as e:
        print("SYNC IN THREAD FAILED:", e)

asyncio.run(main())
