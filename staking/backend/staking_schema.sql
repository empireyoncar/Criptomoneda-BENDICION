CREATE TABLE IF NOT EXISTS stakes (
    stake_id UUID PRIMARY KEY,
    user_id VARCHAR(255) NOT NULL,
    wallet VARCHAR(255) NOT NULL,
    amount_bend BIGINT NOT NULL,
    days INTEGER NOT NULL,
    reward_don DOUBLE PRECISION NOT NULL,
    transfer_tx_id VARCHAR(255) NOT NULL UNIQUE,
    timestamp BIGINT NOT NULL,
    end_timestamp BIGINT NOT NULL,
    status VARCHAR(32) NOT NULL,
    finished_timestamp BIGINT,
    cancelled_timestamp BIGINT,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_stakes_user_id ON stakes(user_id);
CREATE INDEX IF NOT EXISTS idx_stakes_wallet ON stakes(wallet);
CREATE INDEX IF NOT EXISTS idx_stakes_status ON stakes(status);
CREATE INDEX IF NOT EXISTS idx_stakes_end_timestamp ON stakes(end_timestamp);