import os

from dotenv import load_dotenv
from google import genai
from google.genai import types

load_dotenv()

PRIMARY_MODEL = os.getenv("GEMINI_MODEL", "gemini-3.5-flash")
FALLBACK_MODEL = os.getenv("GEMINI_FALLBACK_MODEL", "gemini-3.5-flash-lite")
TIMEOUT_SECONDS = 20

client = genai.Client(
    api_key=os.getenv("GEMINI_API_KEY"),
    http_options=types.HttpOptions(
        timeout=TIMEOUT_SECONDS * 1000,  # milliseconds
        retry_options=types.HttpRetryOptions(attempts=1),  # no hidden retries
    ),
)

PRIMARY_CONFIG = types.GenerateContentConfig(
    thinking_config=types.ThinkingConfig(thinking_level="low"),
)

last_model_used = None


def ask_model(prompt):
    """Try the primary model; if it fails or times out, fall back to the lighter model."""
    global last_model_used
    errors = []

    for model in (PRIMARY_MODEL, FALLBACK_MODEL):
        config = PRIMARY_CONFIG if model == PRIMARY_MODEL else None
        try:
            response = client.models.generate_content(model=model, contents=prompt, config=config)
            if model != PRIMARY_MODEL:
                print(f"  -> Fallback used: {model}")
            last_model_used = model
            return response.text
        except Exception as e:
            short_error = str(e).split("\n")[0][:100]
            print(f"  {model} failed: {short_error}")
            errors.append(f"{model}: {short_error}")

    raise RuntimeError("All models failed -> " + " | ".join(errors))