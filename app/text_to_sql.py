import sys
import time
from functools import lru_cache

import psycopg2

import llm
from db import get_schema, run_query

MAX_ATTEMPTS = 3

SQL_PROMPT = """You are an expert PostgreSQL analyst for a Saudi logistics company.

Database schema:
{schema}

Rules:
- Write ONE PostgreSQL SELECT query that answers the question.
- Return ONLY the SQL. No explanation, no markdown.

Question (may be in Arabic): {question}
"""

FIX_PROMPT = """
Your previous attempts FAILED. Learn from these errors and write a corrected query:
{history}
"""

ANSWER_PROMPT = """You are a helpful data analyst at a Saudi logistics company.
A manager asked a question. A SQL query was run to answer it.

Question: {question}

SQL used:
{sql}

Result columns: {columns}
Result rows (up to 50):
{rows}

Write a short, clear answer for the manager:
- Answer in the SAME language as the question (Arabic question -> Arabic answer, English -> English).
- Use the actual numbers from the result.
- 1 to 4 sentences. No SQL, no technical words.
- If the result is empty, say that no data was found.
"""


class UnsafeQueryError(Exception):
    pass


@lru_cache(maxsize=1)
def cached_schema():
    """Read the schema once, then reuse it."""
    return get_schema()


def clean_sql(text):
    """Remove markdown code fences if the model adds them."""
    text = text.strip()
    if text.startswith("```"):
        text = text.split("\n", 1)[1]
    if text.endswith("```"):
        text = text.rsplit("```", 1)[0]
    return text.strip().rstrip(";")


def check_safe(sql):
    """Safety layer 2: only read queries are allowed (layer 1 is the read-only DB connection)."""
    first_word = sql.strip().split()[0].upper() if sql.strip() else ""
    if first_word not in ("SELECT", "WITH"):
        raise UnsafeQueryError(f"Only SELECT queries are allowed, got: {first_word or 'empty'}")


def generate_and_run(question, demo_error=False):
    """Write SQL, run it, and if it fails, show the error to the model and retry."""
    history = []

    for attempt in range(1, MAX_ATTEMPTS + 1):
        prompt = SQL_PROMPT.format(schema=cached_schema(), question=question)
        if history:
            past = "\n".join(
                f"Attempt {i}:\nSQL: {h['sql']}\nERROR: {h['error']}\n"
                for i, h in enumerate(history, 1)
            )
            prompt += FIX_PROMPT.format(history=past)

        sql = clean_sql(llm.ask_model(prompt))

        # Demo mode: break the first query on purpose to watch the agent fix itself
        if demo_error and attempt == 1:
            sql = sql.replace("shipments", "shipmentz")

        try:
            check_safe(sql)
            columns, rows = run_query(sql)
            return sql, columns, rows, history
        except (psycopg2.Error, UnsafeQueryError) as e:
            error = str(e).strip().splitlines()[0]
            print(f"  Attempt {attempt} failed: {error}")
            history.append({"sql": sql, "error": error})

    raise RuntimeError(f"Could not answer after {MAX_ATTEMPTS} attempts.")


def explain_result(question, sql, columns, rows):
    rows_text = "\n".join(str(tuple(str(v) for v in row)) for row in rows[:50])
    prompt = ANSWER_PROMPT.format(
        question=question, sql=sql, columns=columns, rows=rows_text or "(no rows)"
    )
    return llm.ask_model(prompt).strip()


def answer_question(question, demo_error=False):
    """Full pipeline: question -> SQL (with self-correction) -> run -> human answer."""
    sql, columns, rows, failed_attempts = generate_and_run(question, demo_error)
    answer = explain_result(question, sql, columns, rows)
    return {
        "question": question,
        "sql": sql,
        "columns": columns,
        "rows": rows,
        "answer": answer,
        "failed_attempts": failed_attempts,
        "model": llm.last_model_used,
    }


if __name__ == "__main__":
    args = sys.argv[1:]
    demo_error = "--demo-error" in args
    args = [a for a in args if a != "--demo-error"]

    if args:
        question = " ".join(args)
    else:
        question = input("Ask your question / اسأل سؤالك: ")

    print("Thinking...")
    start = time.time()
    result = answer_question(question, demo_error)
    total_seconds = time.time() - start

    print("\n--- SQL ---")
    print(result["sql"])

    print("\n--- Raw result ---")
    print(result["columns"])
    for row in result["rows"][:10]:
        print(row)

    print("\n--- Answer ---")
    print(result["answer"])

    fixes = len(result["failed_attempts"])
    print(f"\nModel: {result['model']} | Self-corrections: {fixes} | Total time: {total_seconds:.1f}s")