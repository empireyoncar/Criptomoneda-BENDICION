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

CREATE TABLE IF NOT EXISTS stake_rewards (
    id BIGSERIAL PRIMARY KEY,
    stake_id UUID NOT NULL UNIQUE REFERENCES stakes(stake_id) ON DELETE CASCADE,
    user_id VARCHAR(255) NOT NULL,
    wallet VARCHAR(255),
    reward_don DOUBLE PRECISION NOT NULL,
    transfer_tx_id VARCHAR(255),
    timestamp BIGINT NOT NULL,
    status VARCHAR(32) NOT NULL,
    paid_timestamp BIGINT,
    last_error TEXT,
    last_attempt_timestamp BIGINT,
    attempt_count INTEGER NOT NULL DEFAULT 0,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_stake_rewards_status ON stake_rewards(status);
CREATE INDEX IF NOT EXISTS idx_stake_rewards_user_id ON stake_rewards(user_id);

CREATE TABLE IF NOT EXISTS stake_payouts (
    payout_id UUID PRIMARY KEY,
    stake_id UUID NOT NULL UNIQUE REFERENCES stakes(stake_id) ON DELETE CASCADE,
    user_id VARCHAR(255) NOT NULL,
    wallet VARCHAR(255),
    amount DOUBLE PRECISION NOT NULL,
    asset VARCHAR(32) NOT NULL,
    status VARCHAR(32) NOT NULL,
    created_timestamp BIGINT NOT NULL,
    paid_timestamp BIGINT NOT NULL,
    source VARCHAR(64),
    reward_record_timestamp BIGINT,
    transfer_tx_id VARCHAR(255),
    don_api JSONB,
    idempotency_key VARCHAR(255) UNIQUE,
    support_note TEXT,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_stake_payouts_user_id ON stake_payouts(user_id);
CREATE INDEX IF NOT EXISTS idx_stake_payouts_status ON stake_payouts(status);