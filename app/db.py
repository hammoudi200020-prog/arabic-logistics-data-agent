import os
import psycopg2
from dotenv import load_dotenv

load_dotenv()


def get_connection():
    """Open a READ-ONLY connection to the database."""
    conn = psycopg2.connect(
        host="127.0.0.1",
        port=5432,
        dbname=os.getenv("POSTGRES_DB"),
        user=os.getenv("POSTGRES_USER"),
        password=os.getenv("POSTGRES_PASSWORD"),
    )
    conn.set_client_encoding("UTF8")
    conn.set_session(readonly=True)  # the AI can read, but never change or delete
    return conn


def get_schema():
    """Return every table and its columns as text, to show to the AI."""
    sql = """
        SELECT table_name, column_name, data_type
        FROM information_schema.columns
        WHERE table_schema = 'public'
        ORDER BY table_name, ordinal_position;
    """
    conn = get_connection()
    try:
        with conn.cursor() as cur:
            cur.execute(sql)
            rows = cur.fetchall()
    finally:
        conn.close()

    tables = {}
    for table, column, dtype in rows:
        tables.setdefault(table, []).append(f"{column} ({dtype})")

    return "\n".join(f"{t}: {', '.join(cols)}" for t, cols in tables.items())


def run_query(sql):
    """Run a SQL query and return (column names, rows)."""
    conn = get_connection()
    try:
        with conn.cursor() as cur:
            cur.execute(sql)
            columns = [desc[0] for desc in cur.description]
            rows = cur.fetchall()
    finally:
        conn.close()
    return columns, rows


if __name__ == "__main__":
    print(get_schema())
    print()
    print(run_query("SELECT COUNT(*) FROM shipments"))