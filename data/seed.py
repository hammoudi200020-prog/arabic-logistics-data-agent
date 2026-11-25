"""
Generate realistic (fake) Saudi logistics data and load it into PostgreSQL.
Hidden patterns are built in on purpose, so the AI agent has real "why" questions to discover.
"""
import os
import random
from datetime import datetime, timedelta

import psycopg2
from psycopg2.extras import execute_values
from dotenv import load_dotenv

load_dotenv()
random.seed(42)  # same data every run

NOW = datetime(2026, 11, 25, 12, 0)
DAYS_BACK = 180
NUM_SHIPMENTS = 5000

# (name_ar, name_en, region) -> ids start at 1 in this order
CITIES = [
    ("جدة", "Jeddah", "Makkah"),               # 1
    ("مكة المكرمة", "Makkah", "Makkah"),        # 2
    ("الطائف", "Taif", "Makkah"),              # 3
    ("الرياض", "Riyadh", "Riyadh"),            # 4
    ("الدمام", "Dammam", "Eastern"),           # 5
    ("الخبر", "Khobar", "Eastern"),            # 6
    ("المدينة المنورة", "Madinah", "Madinah"),  # 7
    ("بريدة", "Buraidah", "Qassim"),           # 8
    ("أبها", "Abha", "Asir"),                  # 9
    ("جازان", "Jazan", "Jazan"),               # 10
    ("تبوك", "Tabuk", "Tabuk"),                # 11
    ("حائل", "Hail", "Hail"),                  # 12
]
CITY_WEIGHTS = [25, 6, 4, 25, 10, 5, 7, 3, 4, 3, 4, 4]

# Fictional carrier names
CARRIERS = [
    ("سريع إكسبريس", "express"),     # 1
    ("الوطنية للشحن", "standard"),   # 2
    ("دروب للتوصيل", "standard"),    # 3
    ("صقر اللوجستية", "standard"),   # 4  <- the "problem" carrier
    ("الاقتصادي للنقل", "economy"),  # 5
]
CARRIER_WEIGHTS = [15, 30, 25, 15, 15]

PREFIXES = ["شركة", "مؤسسة", "متجر", "مصنع"]
WORDS = ["الأفق", "النخيل", "الريادة", "البحر الأحمر", "الواحة", "المستقبل", "السلام",
         "الجزيرة", "الفجر", "الرمال", "القمة", "الوفاء", "الصفوة", "الأصالة", "التميز"]
SEGMENTS = ["retail", "corporate", "government"]
SEGMENT_WEIGHTS = [50, 35, 15]

BASE_DAYS = {"express": (1, 2), "standard": (2, 4), "economy": (4, 7)}
RATE_PER_KG = {"express": 4.5, "standard": 2.5, "economy": 1.5}


def pick_delay(carrier_id, origin_id, dest_id, segment, created):
    """Decide if a shipment is late, why, and by how many days (hidden patterns live here)."""
    p = 0.07
    reasons = {"wrong_address": 2, "no_driver": 1, "weather": 1, "warehouse_backlog": 1}

    # Pattern 1: carrier 4 is short on drivers, worst on shipments to Riyadh
    if carrier_id == 4:
        p += 0.25
        reasons["no_driver"] += 6
        if dest_id == 4:
            p += 0.10

    # Pattern 2: summer weather delays in the Eastern Province (July-August)
    if dest_id in (5, 6) and created.month in (7, 8):
        p += 0.20
        reasons["weather"] += 6

    # Pattern 3: corporate shipments out of Jeddah (port) get stuck in customs
    if origin_id == 1 and segment == "corporate":
        p += 0.12
        reasons["customs"] = 5

    # Pattern 4: sales season backlog in the first half of November
    if datetime(2026, 11, 1) <= created < datetime(2026, 11, 16):
        p += 0.20
        reasons["warehouse_backlog"] += 6

    if random.random() < p:
        reason = random.choices(list(reasons), weights=list(reasons.values()))[0]
        return reason, random.randint(1, 5)
    return None, 0


def generate():
    cities = list(CITIES)
    carriers = list(CARRIERS)
    city_ids = list(range(1, len(CITIES) + 1))

    # 60 customers (every prefix + word combination)
    names = [f"{p} {w}" for p in PREFIXES for w in WORDS]
    random.shuffle(names)
    customers = []
    for name in names:
        city_id = random.choices(city_ids, weights=CITY_WEIGHTS)[0]
        segment = random.choices(SEGMENTS, weights=SEGMENT_WEIGHTS)[0]
        customers.append((name, city_id, segment))

    shipments = []
    for _ in range(NUM_SHIPMENTS):
        cust_idx = random.randrange(len(customers))
        customer_id = cust_idx + 1
        _, origin_id, segment = customers[cust_idx]

        carrier_id = random.choices(range(1, len(CARRIERS) + 1), weights=CARRIER_WEIGHTS)[0]
        service = CARRIERS[carrier_id - 1][1]

        dest_id = origin_id
        while dest_id == origin_id:
            dest_id = random.choices(city_ids, weights=CITY_WEIGHTS)[0]

        created = NOW - timedelta(days=random.uniform(0, DAYS_BACK))
        created = created.replace(second=0, microsecond=0)

        lo, hi = BASE_DAYS[service]
        transit_days = random.randint(lo, hi)
        if CITIES[origin_id - 1][2] != CITIES[dest_id - 1][2]:
            transit_days += 1  # different region = one extra day
        promised = (created + timedelta(days=transit_days)).date()

        reason, delay_days = pick_delay(carrier_id, origin_id, dest_id, segment, created)

        if delay_days:
            actual_date = promised + timedelta(days=delay_days)
        else:
            actual_date = promised - timedelta(days=random.choice([0, 0, 1]))
        actual = datetime.combine(actual_date, datetime.min.time()) + timedelta(
            hours=random.randint(8, 21), minutes=random.randint(0, 59))
        if actual <= created:
            actual = created + timedelta(hours=random.randint(4, 10))

        if segment == "retail":
            weight = round(random.uniform(0.5, 30), 2)
        else:
            weight = round(random.uniform(5, 300), 2)
        cost = round(15 + weight * RATE_PER_KG[service] * random.uniform(0.9, 1.1), 2)

        if random.random() < 0.02:
            status, delivered_at, delay_reason = "cancelled", None, None
        elif actual <= NOW:
            status, delivered_at, delay_reason = "delivered", actual, reason
        elif NOW.date() > promised:
            status, delivered_at, delay_reason = "delayed", None, reason
        else:
            status, delivered_at, delay_reason = "in_transit", None, None

        shipments.append((customer_id, carrier_id, origin_id, dest_id, created, promised,
                          delivered_at, status, weight, cost, delay_reason))

    return cities, carriers, customers, shipments


def main():
    cities, carriers, customers, shipments = generate()

    conn = psycopg2.connect(
        host="127.0.0.1",
        port=5432,
        dbname=os.getenv("POSTGRES_DB"),
        user=os.getenv("POSTGRES_USER"),
        password=os.getenv("POSTGRES_PASSWORD"),
    )
    conn.set_client_encoding("UTF8")

    with conn, conn.cursor() as cur:
        cur.execute("TRUNCATE shipments, customers, carriers, cities RESTART IDENTITY CASCADE")
        execute_values(cur, "INSERT INTO cities (name_ar, name_en, region) VALUES %s", cities)
        execute_values(cur, "INSERT INTO carriers (name, service_type) VALUES %s", carriers)
        execute_values(cur, "INSERT INTO customers (name, city_id, segment) VALUES %s", customers)
        execute_values(
            cur,
            """INSERT INTO shipments (customer_id, carrier_id, origin_city_id, destination_city_id,
               created_at, promised_date, delivered_at, status, weight_kg, cost_sar, delay_reason)
               VALUES %s""",
            shipments,
        )
    conn.close()

    print(f"Inserted {len(cities)} cities, {len(carriers)} carriers, "
          f"{len(customers)} customers, {len(shipments)} shipments.")


if __name__ == "__main__":
    main()
