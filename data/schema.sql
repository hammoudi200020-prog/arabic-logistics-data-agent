-- المدن
CREATE TABLE cities (
    id SERIAL PRIMARY KEY,
    name_ar VARCHAR(50) NOT NULL,
    name_en VARCHAR(50) NOT NULL,
    region VARCHAR(50) NOT NULL
);

-- شركات النقل
CREATE TABLE carriers (
    id SERIAL PRIMARY KEY,
    name VARCHAR(100) NOT NULL,
    service_type VARCHAR(20) NOT NULL  -- express / standard / economy
);

-- العملاء
CREATE TABLE customers (
    id SERIAL PRIMARY KEY,
    name VARCHAR(100) NOT NULL,
    city_id INT REFERENCES cities(id),
    segment VARCHAR(20) NOT NULL  -- retail / corporate / government
);

-- الشحنات
CREATE TABLE shipments (
    id SERIAL PRIMARY KEY,
    customer_id INT REFERENCES customers(id),
    carrier_id INT REFERENCES carriers(id),
    origin_city_id INT REFERENCES cities(id),
    destination_city_id INT REFERENCES cities(id),
    created_at TIMESTAMP NOT NULL,
    promised_date DATE NOT NULL,
    delivered_at TIMESTAMP,
    status VARCHAR(20) NOT NULL,  -- delivered / in_transit / delayed / cancelled
    weight_kg NUMERIC(8,2) NOT NULL,
    cost_sar NUMERIC(10,2) NOT NULL,
    delay_reason VARCHAR(50)  -- weather / customs / no_driver / wrong_address / warehouse_backlog
);