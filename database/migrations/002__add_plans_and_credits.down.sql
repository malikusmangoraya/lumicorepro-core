-- V2: rollback (plans + subscriptions + users stripe cols)

DROP TABLE IF EXISTS subscriptions;
DROP TABLE IF EXISTS plans;

ALTER TABLE users DROP COLUMN IF EXISTS stripe_customer_id;
ALTER TABLE users DROP COLUMN IF EXISTS subscription_status;
ALTER TABLE users DROP COLUMN IF EXISTS subscription_plan;