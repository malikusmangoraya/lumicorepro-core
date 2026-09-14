-- Automotive / Car Dealership Schema
-- Full-stack backbone for vehicle dealerships: inventory, brands, bookings,
-- test drives, leads, staff, and order history.

CREATE TABLE IF NOT EXISTS vehicle_brands (
    id SERIAL PRIMARY KEY,
    name VARCHAR(120) NOT NULL UNIQUE,
    country VARCHAR(60),
    logo_url TEXT,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS vehicle_models (
    id SERIAL PRIMARY KEY,
    brand_id INTEGER NOT NULL REFERENCES vehicle_brands(id) ON DELETE CASCADE,
    name VARCHAR(120) NOT NULL,
    body_type VARCHAR(40) DEFAULT 'sedan',           -- sedan/suv/coupe/hatchback/truck/van
    engine_type VARCHAR(40) DEFAULT 'petrol',         -- petrol/diesel/ev/hybrid
    year INTEGER,
    price NUMERIC(12,2) NOT NULL,
    mileage_km INTEGER DEFAULT 0,
    fuel_efficiency_kmpl NUMERIC(6,1),
    horsepower INTEGER,
    color VARCHAR(40),
    image_url TEXT,
    is_featured BOOLEAN DEFAULT FALSE,
    is_available BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    UNIQUE (brand_id, name, year)
);

CREATE INDEX IF NOT EXISTS idx_vehicle_models_brand ON vehicle_models(brand_id);
CREATE INDEX IF NOT EXISTS idx_vehicle_models_body ON vehicle_models(body_type);
CREATE INDEX IF NOT EXISTS idx_vehicle_models_price ON vehicle_models(price);

CREATE TABLE IF NOT EXISTS test_drive_bookings (
    id SERIAL PRIMARY KEY,
    vehicle_id INTEGER NOT NULL REFERENCES vehicle_models(id) ON DELETE CASCADE,
    customer_name VARCHAR(120) NOT NULL,
    customer_email VARCHAR(160) NOT NULL,
    customer_phone VARCHAR(40),
    preferred_date DATE,
    preferred_time_slot VARCHAR(20),
    status VARCHAR(30) DEFAULT 'pending',            -- pending/confirmed/completed/cancelled
    notes TEXT,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_bookings_vehicle ON test_drive_bookings(vehicle_id);
CREATE INDEX IF NOT EXISTS idx_bookings_status ON test_drive_bookings(status);

CREATE TABLE IF NOT EXISTS sales_leads (
    id SERIAL PRIMARY KEY,
    vehicle_id INTEGER REFERENCES vehicle_models(id) ON DELETE SET NULL,
    customer_name VARCHAR(120) NOT NULL,
    customer_email VARCHAR(160) NOT NULL,
    customer_phone VARCHAR(40),
    message TEXT,
    source VARCHAR(40) DEFAULT 'website',            -- website/social/in_reference/call
    status VARCHAR(30) DEFAULT 'new',                -- new/contacted/negotiating/closed/lost
    created_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_leads_status ON sales_leads(status);
CREATE INDEX IF NOT EXISTS idx_leads_created ON sales_leads(created_at);

CREATE TABLE IF NOT EXISTS promotions (
    id SERIAL PRIMARY KEY,
    title VARCHAR(160) NOT NULL,
    description TEXT,
    discount_percent NUMERIC(5,2),
    starts_at DATE,
    ends_at DATE,
    is_active BOOLEAN DEFAULT TRUE
);

CREATE TABLE IF NOT EXISTS user_favorites (
    id SERIAL PRIMARY KEY,
    user_id INTEGER REFERENCES users(id) ON DELETE CASCADE,
    vehicle_id INTEGER NOT NULL REFERENCES vehicle_models(id) ON DELETE CASCADE,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    UNIQUE (user_id, vehicle_id)
);