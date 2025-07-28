import asyncio
import time
from fastapi import FastAPI
from fastapi.responses import StreamingResponse

app = FastAPI()

async def slow_text_generator():
    """
    A simple async generator that yields a chunk of text every 2 seconds.
    This simulates a slow process like an LLM generating a response.
    """
    for i in range(1, 6):
        # Simulate work being done to generate a chunk
        # time.sleep(2)  # In a real async app, we avoid sync sleep
        await asyncio.sleep(2) # Use async sleep to not block the server

        chunk = f"Chunk {i}: This is a piece of the response. Timestamp: {time.time()}\n"
        print(f"SERVER: Yielding chunk {i}")
        yield chunk

@app.get("/stream")
async def stream_test():
    """
    This endpoint uses the perfect generator and streams the response.
    """
    return StreamingResponse(slow_text_generator(), media_type="text/plain")