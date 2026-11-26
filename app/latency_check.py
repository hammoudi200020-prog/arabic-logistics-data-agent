import os
import time

from dotenv import load_dotenv
from google import genai

load_dotenv()
client = genai.Client(api_key=os.getenv("GEMINI_API_KEY"))

MODELS = [
    "gemini-3.5-flash",
    "gemini-3.5-flash-lite",
    "gemini-3.1-flash-lite",
]

PROMPT = "Write a PostgreSQL query that counts all rows in a table called shipments. Return only SQL."

for model in MODELS:
    times = []
    for attempt in range(2):
        start = time.time()
        try:
            client.models.generate_content(model=model, contents=PROMPT)
            times.append(time.time() - start)
        except Exception as e:
            print(f"{model}: ERROR -> {str(e)[:120]}")
            break
    if times:
        print(f"{model}: " + " | ".join(f"{t:.1f}s" for t in times))