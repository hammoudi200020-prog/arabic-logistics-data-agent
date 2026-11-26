"""
Semantic layer: the business meaning of the data.
The AI sees column names, but it does not know what "late" or "on-time rate"
means in OUR company. These rules teach it.
"""

BUSINESS_RULES = """
Business definitions (ALWAYS follow these exactly):

1. Late shipment (delivered late):
   status = 'delivered' AND delivered_at::date > promised_date
   IMPORTANT: compare DATES, not timestamps. A shipment delivered on the promised day at any hour is ON TIME.

2. On-time shipment:
   status = 'delivered' AND delivered_at::date <= promised_date

3. Currently delayed (not delivered yet, past the promised date):
   status = 'delayed'

4. On-time rate (percentage):
   on-time shipments / all delivered shipments * 100

5. Delay in days:
   delivered_at::date - promised_date   (only for late shipments)

6. Exclude status = 'cancelled' from performance metrics unless the question asks about cancellations.

7. Revenue / cost = SUM(cost_sar), in Saudi Riyals.

8. Time periods:
   - "this month" / "هذا الشهر" = created_at >= date_trunc('month', CURRENT_DATE)
   - "last month" / "الشهر الماضي" = the previous full calendar month
   - Use created_at for "when the shipment was sent" unless the question says delivered.

Value meanings (English value -> Arabic meaning):
- delay_reason: weather = الطقس, customs = الجمارك, no_driver = عدم توفر سائق,
  wrong_address = عنوان خاطئ, warehouse_backlog = ضغط المستودع
- status: delivered = تم التسليم, in_transit = في الطريق, delayed = متأخرة حالياً, cancelled = ملغاة
- customers.segment: retail = أفراد / تجزئة, corporate = شركات, government = جهات حكومية
- carriers.service_type: express = سريع, standard = عادي, economy = اقتصادي

Names:
- carriers.name and customers.name are stored in Arabic.
- cities have both name_ar (Arabic) and name_en (English). Match the language of the question,
  e.g. WHERE c.name_ar = 'جدة' or WHERE c.name_en = 'Jeddah'.
- shipments has TWO city columns: origin_city_id (from) and destination_city_id (to).
  Join the cities table separately for each one when needed.
"""