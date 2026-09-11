-- V2: Billing plans, Stripe sub fields on users, subscription table
-- Marker: applied once; uses IF NOT EXISTS / ADD COLUMN IF NOT EXISTS (idempotent)

CREATE TABLE IF NOT EXISTS plans (
    id SERIAL PRIMARY KEY,
    name VARCHAR(120) NOT NULL,
    slug VARCHAR(120) UNIQUE NOT NULL,
    description TEXT DEFAULT '',
    stripe_product_id VARCHAR(255) DEFAULT '',
    stripe_price_id VARCHAR(255) DEFAULT '',
    amount NUMERIC(12, 2) DEFAULT 0,
    currency VARCHAR(10) DEFAULT 'usd',
    interval VARCHAR(20) DEFAULT 'month',
    credits_grant INT DEFAULT 0,
    features JSONB DEFAULT '[]',
    highlight BOOLEAN DEFAULT false,
    is_active BOOLEAN DEFAULT true,
    sort_order INT DEFAULT 0,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS subscriptions (
    id SERIAL PRIMARY KEY,
    user_id INT REFERENCES users(id) ON DELETE CASCADE,
    plan_id INT REFERENCES plans(id) ON DELETE SET NULL,
    stripe_subscription_id VARCHAR(255) UNIQUE,
    stripe_customer_id VARCHAR(255),
    price_id VARCHAR(255),
    status VARCHAR(30) DEFAULT 'active',
    plan_name VARCHAR(120) DEFAULT '',
    amount NUMERIC(12, 2) DEFAULT 0,
    currency VARCHAR(10) DEFAULT 'usd',
    interval VARCHAR(20) DEFAULT 'month',
    cancel_at_period_end BOOLEAN DEFAULT false,
    current_period_start TIMESTAMP WITH TIME ZONE,
    current_period_end TIMESTAMP WITH TIME ZONE,
    trial_end TIMESTAMP WITH TIME ZONE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_subscriptions_user ON subscriptions(user_id);
CREATE INDEX IF NOT EXISTS idx_subscriptions_status ON subscriptions(status);
CREATE INDEX IF NOT EXISTS idx_plans_active ON plans(is_active, sort_order);

ALTER TABLE users ADD COLUMN IF NOT EXISTS stripe_customer_id VARCHAR(255);
ALTER TABLE users ADD COLUMN IF NOT EXISTS subscription_status VARCHAR(30) DEFAULT '';
ALTER TABLE users ADD COLUMN IF NOT EXISTS subscription_plan VARCHAR(120) DEFAULT '';