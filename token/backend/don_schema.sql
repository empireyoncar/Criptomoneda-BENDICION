CREATE TABLE IF NOT EXISTS don_accounts (
    user_id TEXT PRIMARY KEY,
    balance NUMERIC(30, 8) NOT NULL DEFAULT 0,
    updated_timestamp BIGINT NOT NULL DEFAULT 0
);

CREATE TABLE IF NOT EXISTS don_transactions (
    tx_id TEXT PRIMARY KEY,
    tx_type TEXT NOT NULL,
    user_from TEXT,
    user_to TEXT,
    amount NUMERIC(30, 8) NOT NULL,
    timestamp BIGINT NOT NULL,
    datetime TEXT NOT NULL,
    metadata_json TEXT NOT NULL DEFAULT '{}'
);

CREATE INDEX IF NOT EXISTS idx_don_transactions_timestamp
    ON don_transactions (timestamp DESC);

CREATE INDEX IF NOT EXISTS idx_don_transactions_user_from
    ON don_transactions (user_from);

CREATE INDEX IF NOT EXISTS idx_don_transactions_user_to
    ON don_transactions (user_to);