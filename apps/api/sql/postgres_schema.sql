CREATE EXTENSION IF NOT EXISTS pgcrypto;

DO $$
BEGIN
    IF NOT EXISTS (SELECT 1 FROM pg_type WHERE typname = 'risklevel') THEN
        CREATE TYPE risklevel AS ENUM ('conservative', 'balanced', 'aggressive');
    END IF;
END $$;

DO $$
BEGIN
    IF NOT EXISTS (SELECT 1 FROM pg_type WHERE typname = 'userstatus') THEN
        CREATE TYPE userstatus AS ENUM ('active', 'disabled', 'deleted');
    END IF;
END $$;

DO $$
BEGIN
    IF NOT EXISTS (SELECT 1 FROM pg_type WHERE typname = 'messagerole') THEN
        CREATE TYPE messagerole AS ENUM ('user', 'assistant', 'system');
    END IF;
END $$;

DO $$
BEGIN
    IF NOT EXISTS (SELECT 1 FROM pg_type WHERE typname = 'strategystatus') THEN
        CREATE TYPE strategystatus AS ENUM (
            'draft',
            'generated',
            'approved',
            'rejected',
            'expired',
            'executed'
        );
    END IF;
END $$;

DO $$
BEGIN
    IF NOT EXISTS (SELECT 1 FROM pg_type WHERE typname = 'transactionstatus') THEN
        CREATE TYPE transactionstatus AS ENUM (
            'draft',
            'prepared',
            'signed',
            'submitted',
            'confirmed',
            'failed',
            'expired'
        );
    END IF;
END $$;

DO $$
BEGIN
    IF NOT EXISTS (SELECT 1 FROM pg_type WHERE typname = 'transactiontype') THEN
        CREATE TYPE transactiontype AS ENUM (
            'swap',
            'lend',
            'withdraw',
            'stake',
            'unstake',
            'rebalance'
        );
    END IF;
END $$;

CREATE TABLE IF NOT EXISTS users (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    wallet_address VARCHAR(64) NOT NULL UNIQUE,
    email VARCHAR(255) UNIQUE,
    password_hash VARCHAR(255),
    risk_level risklevel NOT NULL DEFAULT 'balanced',
    status userstatus NOT NULL DEFAULT 'active',
    preferences JSONB NOT NULL DEFAULT '{}'::jsonb,
    last_login_at TIMESTAMP WITHOUT TIME ZONE,
    created_at TIMESTAMP WITHOUT TIME ZONE NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMP WITHOUT TIME ZONE NOT NULL DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS ix_users_wallet_address ON users (wallet_address);
CREATE INDEX IF NOT EXISTS ix_users_email ON users (email);
CREATE INDEX IF NOT EXISTS ix_users_risk_level ON users (risk_level);
CREATE INDEX IF NOT EXISTS ix_users_status ON users (status);

CREATE TABLE IF NOT EXISTS chat_sessions (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL REFERENCES users(id),
    session_id VARCHAR(64) NOT NULL UNIQUE,
    title VARCHAR(255),
    created_at TIMESTAMP WITHOUT TIME ZONE NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMP WITHOUT TIME ZONE NOT NULL DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS ix_chat_sessions_user_id ON chat_sessions (user_id);
CREATE INDEX IF NOT EXISTS ix_chat_sessions_session_id ON chat_sessions (session_id);
CREATE INDEX IF NOT EXISTS ix_chat_sessions_created_at ON chat_sessions (created_at);

CREATE TABLE IF NOT EXISTS chat_messages (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    session_id UUID NOT NULL REFERENCES chat_sessions(id),
    role messagerole NOT NULL,
    content TEXT NOT NULL,
    intent VARCHAR(64),
    extra_data JSONB NOT NULL DEFAULT '{}'::jsonb,
    created_at TIMESTAMP WITHOUT TIME ZONE NOT NULL DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS ix_chat_messages_session_id ON chat_messages (session_id);
CREATE INDEX IF NOT EXISTS ix_chat_messages_role ON chat_messages (role);
CREATE INDEX IF NOT EXISTS ix_chat_messages_created_at ON chat_messages (created_at);

CREATE TABLE IF NOT EXISTS strategies (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL REFERENCES users(id),
    strategy_type VARCHAR(32) NOT NULL,
    status strategystatus NOT NULL DEFAULT 'draft',
    input_token VARCHAR(32) NOT NULL,
    output_token VARCHAR(32),
    input_amount NUMERIC(38, 18),
    estimated_apy NUMERIC(10, 4),
    risk_level VARCHAR(32) NOT NULL,
    protocol_name VARCHAR(64),
    title VARCHAR(255) NOT NULL,
    summary TEXT,
    steps JSONB NOT NULL DEFAULT '[]'::jsonb,
    strategy_payload JSONB NOT NULL DEFAULT '{}'::jsonb,
    risk_assessment JSONB NOT NULL DEFAULT '{}'::jsonb,
    expires_at TIMESTAMP WITHOUT TIME ZONE,
    created_at TIMESTAMP WITHOUT TIME ZONE NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMP WITHOUT TIME ZONE NOT NULL DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS ix_strategies_user_id ON strategies (user_id);
CREATE INDEX IF NOT EXISTS ix_strategies_strategy_type ON strategies (strategy_type);
CREATE INDEX IF NOT EXISTS ix_strategies_status ON strategies (status);
CREATE INDEX IF NOT EXISTS ix_strategies_risk_level ON strategies (risk_level);
CREATE INDEX IF NOT EXISTS ix_strategies_protocol_name ON strategies (protocol_name);
CREATE INDEX IF NOT EXISTS ix_strategies_created_at ON strategies (created_at);

CREATE TABLE IF NOT EXISTS transactions (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL REFERENCES users(id),
    strategy_id UUID NOT NULL REFERENCES strategies(id),
    signature VARCHAR(128) UNIQUE,
    status transactionstatus NOT NULL DEFAULT 'draft',
    tx_type transactiontype NOT NULL,
    chain VARCHAR(16) NOT NULL DEFAULT 'solana',
    from_token VARCHAR(32),
    to_token VARCHAR(32),
    amount NUMERIC(38, 18),
    slippage_bps INTEGER,
    tx_payload JSONB NOT NULL DEFAULT '{}'::jsonb,
    simulation_result JSONB NOT NULL DEFAULT '{}'::jsonb,
    error_message TEXT,
    submitted_at TIMESTAMP WITHOUT TIME ZONE,
    confirmed_at TIMESTAMP WITHOUT TIME ZONE,
    created_at TIMESTAMP WITHOUT TIME ZONE NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMP WITHOUT TIME ZONE NOT NULL DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS ix_transactions_user_id ON transactions (user_id);
CREATE INDEX IF NOT EXISTS ix_transactions_strategy_id ON transactions (strategy_id);
CREATE INDEX IF NOT EXISTS ix_transactions_signature ON transactions (signature);
CREATE INDEX IF NOT EXISTS ix_transactions_status ON transactions (status);
CREATE INDEX IF NOT EXISTS ix_transactions_tx_type ON transactions (tx_type);
CREATE INDEX IF NOT EXISTS ix_transactions_created_at ON transactions (created_at);
