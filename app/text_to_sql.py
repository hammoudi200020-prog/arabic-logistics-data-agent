import os
import sys
import time
from functools import lru_cache

from dotenv import load_dotenv
from google import genai
from google.genai import types

from db import get_schema, run_query

load_dotenv()
client = genai.Client(api_key=os.getenv("GEMINI_API_KEY"))
MODEL = os.getenv("GEMINI_MODEL")

PROMPT = """You are an expert PostgreSQL analyst for a Saudi logistics company.

Database schema:
{schema}

Rules:
- Write ONE PostgreSQL SELECT query that answers the question.
- Return ONLY the SQL. No explanation, no markdown.

Question (may be in Arabic): {question}
"""


@lru_cache(maxsize=1)
def cached_schema():
    """Read the schema once, then reuse it."""
    return get_schema()


def clean_sql(text):
    """Remove ```sql fences if the model adds them."""
    text = text.strip()
    if text.startswith("```"):
        text = text.split("\n", 1)[1]
    if text.endswith("```"):
        text = text.rsplit("```", 1)[0]
    return text.strip()


def question_to_sql(question):
    prompt = PROMPT.format(schema=cached_schema(), question=question)
    response = client.models.generate_content(
        model=MODEL,
        contents=prompt,
        config=types.GenerateContentConfig(
            thinking_config=types.ThinkingConfig(thinking_level="low"),
        ),
    )
    return clean_sql(response.text)


if __name__ == "__main__":
    if len(sys.argv) > 1:
        question = " ".join(sys.argv[1:])
    else:
        question = input("Ask your question / اسأل سؤالك: ")

    print("Thinking...")
    start = time.time()
    sql = question_to_sql(question)
    llm_seconds = time.time() - start

    print("\n--- SQL ---")
    print(sql)

    columns, rows = run_query(sql)
    total_seconds = time.time() - start

    print("\n--- Result ---")
    print(columns)
    for row in rows[:20]:
        print(row)

    print(f"\nAI time: {llm_seconds:.1f}s | Total time: {total_seconds:.1f}s")