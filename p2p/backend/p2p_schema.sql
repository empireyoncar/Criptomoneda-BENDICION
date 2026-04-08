CREATE EXTENSION IF NOT EXISTS "pgcrypto";

CREATE TABLE IF NOT EXISTS p2p_offers (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  user_id TEXT NOT NULL,
  country TEXT NOT NULL DEFAULT 'N/A',
  side TEXT NOT NULL CHECK (side IN ('buy', 'sell')),
  asset TEXT NOT NULL DEFAULT 'BEN',
  fiat_currency TEXT NOT NULL DEFAULT 'USD',
  payment_method TEXT NOT NULL,
  payment_provider TEXT NOT NULL DEFAULT '',
  account_reference TEXT NOT NULL DEFAULT '',
  account_holder TEXT NOT NULL DEFAULT '',
  price NUMERIC(20,8) NOT NULL CHECK (price > 0),
  amount_total NUMERIC(20,8) NOT NULL CHECK (amount_total > 0),
  amount_available NUMERIC(20,8) NOT NULL CHECK (amount_available >= 0),
  min_limit NUMERIC(20,8) NOT NULL DEFAULT 0,
  max_limit NUMERIC(20,8) NOT NULL DEFAULT 0,
  completion_time_minutes INT NOT NULL DEFAULT 15 CHECK (completion_time_minutes IN (10, 15, 30, 60)),
  terms TEXT NOT NULL DEFAULT '',
  status TEXT NOT NULL CHECK (status IN ('active', 'paused', 'filled', 'cancelled')) DEFAULT 'active',
  created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
  updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_p2p_offers_status_side_asset ON p2p_offers(status, side, asset);
CREATE INDEX IF NOT EXISTS idx_p2p_offers_user_id ON p2p_offers(user_id);

ALTER TABLE p2p_offers ADD COLUMN IF NOT EXISTS country TEXT NOT NULL DEFAULT 'N/A';
ALTER TABLE p2p_offers ADD COLUMN IF NOT EXISTS payment_provider TEXT NOT NULL DEFAULT '';
ALTER TABLE p2p_offers ADD COLUMN IF NOT EXISTS account_reference TEXT NOT NULL DEFAULT '';
ALTER TABLE p2p_offers ADD COLUMN IF NOT EXISTS account_holder TEXT NOT NULL DEFAULT '';
ALTER TABLE p2p_offers ADD COLUMN IF NOT EXISTS completion_time_minutes INT NOT NULL DEFAULT 15;

CREATE TABLE IF NOT EXISTS p2p_orders (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  offer_id UUID NOT NULL REFERENCES p2p_offers(id),
  buyer_id TEXT NOT NULL,
  seller_id TEXT NOT NULL,
  amount NUMERIC(20,8) NOT NULL CHECK (amount > 0),
  unit_price NUMERIC(20,8) NOT NULL CHECK (unit_price > 0),
  total_fiat NUMERIC(20,8) NOT NULL CHECK (total_fiat > 0),
  payment_proof_url TEXT,
  status TEXT NOT NULL CHECK (status IN ('pending_payment', 'paid', 'released', 'refunded', 'disputed', 'cancelled', 'completed')) DEFAULT 'pending_payment',
  expires_at TIMESTAMPTZ,
  created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
  updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_p2p_orders_offer_id ON p2p_orders(offer_id);
CREATE INDEX IF NOT EXISTS idx_p2p_orders_buyer_id ON p2p_orders(buyer_id);
CREATE INDEX IF NOT EXISTS idx_p2p_orders_seller_id ON p2p_orders(seller_id);
CREATE INDEX IF NOT EXISTS idx_p2p_orders_status ON p2p_orders(status);

CREATE TABLE IF NOT EXISTS p2p_escrow_events (
  id BIGSERIAL PRIMARY KEY,
  order_id UUID NOT NULL REFERENCES p2p_orders(id),
  event_type TEXT NOT NULL CHECK (event_type IN ('hold', 'paid', 'release', 'refund', 'timeout', 'dispute_open', 'dispute_resolve')),
  actor_user_id TEXT,
  details JSONB NOT NULL DEFAULT '{}'::jsonb,
  created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_p2p_escrow_events_order_id ON p2p_escrow_events(order_id);

CREATE TABLE IF NOT EXISTS p2p_disputes (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  order_id UUID NOT NULL UNIQUE REFERENCES p2p_orders(id),
  opened_by_user_id TEXT NOT NULL,
  reason TEXT NOT NULL,
  evidence JSONB NOT NULL DEFAULT '[]'::jsonb,
  status TEXT NOT NULL CHECK (status IN ('open', 'under_review', 'resolved_buyer', 'resolved_seller', 'rejected')) DEFAULT 'open',
  admin_id TEXT,
  resolution_note TEXT,
  created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
  resolved_at TIMESTAMPTZ
);

CREATE INDEX IF NOT EXISTS idx_p2p_disputes_status ON p2p_disputes(status);

CREATE TABLE IF NOT EXISTS p2p_chat_messages (
  id BIGSERIAL PRIMARY KEY,
  order_id UUID NOT NULL REFERENCES p2p_orders(id),
  sender_user_id TEXT NOT NULL,
  message TEXT NOT NULL,
  message_type TEXT NOT NULL CHECK (message_type IN ('text', 'system', 'proof')) DEFAULT 'text',
  created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_p2p_chat_order_id_created_at ON p2p_chat_messages(order_id, created_at);

CREATE TABLE IF NOT EXISTS p2p_ratings (
  id BIGSERIAL PRIMARY KEY,
  order_id UUID NOT NULL REFERENCES p2p_orders(id),
  from_user_id TEXT NOT NULL,
  to_user_id TEXT NOT NULL,
  score INT NOT NULL CHECK (score BETWEEN 1 AND 5),
  comment TEXT NOT NULL DEFAULT '',
  created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
  UNIQUE(order_id, from_user_id)
);

CREATE INDEX IF NOT EXISTS idx_p2p_ratings_to_user_id ON p2p_ratings(to_user_id);

CREATE TABLE IF NOT EXISTS p2p_user_profiles (
  user_id TEXT PRIMARY KEY,
  bio TEXT NOT NULL DEFAULT '',
  created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
  updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS p2p_audit_log (
  id BIGSERIAL PRIMARY KEY,
  user_id TEXT,
  action TEXT NOT NULL,
  entity_type TEXT NOT NULL,
  entity_id TEXT,
  ip_address TEXT,
  user_agent TEXT,
  details JSONB NOT NULL DEFAULT '{}'::jsonb,
  created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_p2p_audit_user_id ON p2p_audit_log(user_id);
CREATE INDEX IF NOT EXISTS idx_p2p_audit_action ON p2p_audit_log(action);
