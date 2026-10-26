-- init.sql: Schema for ApexQuant AI Platform

-- Enable UUID extension if available
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- 1. Users Table
CREATE TABLE IF NOT EXISTS users (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    email VARCHAR(255) UNIQUE NOT NULL,
    hashed_password VARCHAR(255) NOT NULL,
    full_name VARCHAR(100),
    role VARCHAR(20) DEFAULT 'user' NOT NULL, -- 'user', 'admin', 'guest'
    risk_limit_pct NUMERIC(5,2) DEFAULT 2.0 NOT NULL, -- default max risk per trade
    max_drawdown_limit_pct NUMERIC(5,2) DEFAULT 10.0 NOT NULL,
    is_active BOOLEAN DEFAULT TRUE NOT NULL,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP NOT NULL,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP NOT NULL
);

-- 2. Portfolios Table
CREATE TABLE IF NOT EXISTS portfolios (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    name VARCHAR(100) NOT NULL,
    type VARCHAR(20) NOT NULL, -- 'live', 'paper', 'backtest'
    currency VARCHAR(10) DEFAULT 'USD' NOT NULL,
    balance NUMERIC(18,4) DEFAULT 100000.0000 NOT NULL, -- Cash balance
    initial_balance NUMERIC(18,4) DEFAULT 100000.0000 NOT NULL,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP NOT NULL,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP NOT NULL
);

-- 3. Positions Table
CREATE TABLE IF NOT EXISTS positions (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    portfolio_id UUID NOT NULL REFERENCES portfolios(id) ON DELETE CASCADE,
    ticker VARCHAR(20) NOT NULL,
    quantity NUMERIC(18,8) NOT NULL, -- Positive for long, negative for short (or handle via 'side' field)
    side VARCHAR(10) DEFAULT 'long' NOT NULL, -- 'long', 'short'
    entry_price NUMERIC(18,4) NOT NULL,
    current_price NUMERIC(18,4) NOT NULL,
    stop_loss NUMERIC(18,4),
    take_profit NUMERIC(18,4),
    status VARCHAR(20) DEFAULT 'open' NOT NULL, -- 'open', 'closed'
    pnl NUMERIC(18,4) DEFAULT 0.0000 NOT NULL, -- Realized or unrealized PnL
    opened_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP NOT NULL,
    closed_at TIMESTAMP WITH TIME ZONE
);

-- 4. Trades Table
CREATE TABLE IF NOT EXISTS trades (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    portfolio_id UUID NOT NULL REFERENCES portfolios(id) ON DELETE CASCADE,
    position_id UUID REFERENCES positions(id) ON DELETE SET NULL,
    ticker VARCHAR(20) NOT NULL,
    quantity NUMERIC(18,8) NOT NULL,
    price NUMERIC(18,4) NOT NULL,
    action VARCHAR(10) NOT NULL, -- 'buy', 'sell'
    fee NUMERIC(10,4) DEFAULT 0.0000 NOT NULL,
    slippage NUMERIC(10,4) DEFAULT 0.0000 NOT NULL,
    timestamp TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP NOT NULL
);

-- 5. Backtests Table
CREATE TABLE IF NOT EXISTS backtests (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    strategy_name VARCHAR(100) NOT NULL,
    ticker VARCHAR(50) NOT NULL,
    timeframe VARCHAR(10) NOT NULL,
    start_date TIMESTAMP WITH TIME ZONE NOT NULL,
    end_date TIMESTAMP WITH TIME ZONE NOT NULL,
    initial_balance NUMERIC(18,4) NOT NULL,
    final_balance NUMERIC(18,4) NOT NULL,
    total_trades INT DEFAULT 0 NOT NULL,
    winning_trades INT DEFAULT 0 NOT NULL,
    losing_trades INT DEFAULT 0 NOT NULL,
    win_rate NUMERIC(5,2) DEFAULT 0.00 NOT NULL,
    profit_factor NUMERIC(10,2) DEFAULT 0.00 NOT NULL,
    max_drawdown NUMERIC(5,2) DEFAULT 0.00 NOT NULL,
    sharpe_ratio NUMERIC(10,4),
    sortino_ratio NUMERIC(10,4),
    status VARCHAR(20) DEFAULT 'pending' NOT NULL, -- 'pending', 'running', 'completed', 'failed'
    equity_curve JSONB DEFAULT '[]'::jsonb NOT NULL, -- Array of date-balance pairs
    metrics JSONB DEFAULT '{}'::jsonb NOT NULL, -- Extra performance metrics
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP NOT NULL
);

-- 6. Alerts Table
CREATE TABLE IF NOT EXISTS alerts (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    ticker VARCHAR(20) NOT NULL,
    condition_type VARCHAR(20) NOT NULL, -- 'price_above', 'price_below', 'indicator_crossover'
    condition_value NUMERIC(18,4) NOT NULL,
    is_triggered BOOLEAN DEFAULT FALSE NOT NULL,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP NOT NULL
);

-- 7. Agent Analysis Logs Table
CREATE TABLE IF NOT EXISTS agent_analysis_logs (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID REFERENCES users(id) ON DELETE SET NULL,
    ticker VARCHAR(20) NOT NULL,
    timeframe VARCHAR(10) DEFAULT '1D' NOT NULL,
    confidence_score INT NOT NULL, -- 0 to 100
    trade_grade VARCHAR(5) NOT NULL, -- 'A+', 'A', 'B', 'C', 'Avoid'
    agent_responses JSONB NOT NULL, -- Combined structured JSON output of all 15 agents
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP NOT NULL
);

-- Create Indexes for performance
CREATE INDEX IF NOT EXISTS idx_users_email ON users(email);
CREATE INDEX IF NOT EXISTS idx_portfolios_user_id ON portfolios(user_id);
CREATE INDEX IF NOT EXISTS idx_positions_portfolio_id ON positions(portfolio_id);
CREATE INDEX IF NOT EXISTS idx_positions_ticker_status ON positions(ticker, status);
CREATE INDEX IF NOT EXISTS idx_trades_portfolio_id ON trades(portfolio_id);
CREATE INDEX IF NOT EXISTS idx_backtests_user_id ON backtests(user_id);
CREATE INDEX IF NOT EXISTS idx_alerts_user_ticker ON alerts(user_id, ticker);
CREATE INDEX IF NOT EXISTS idx_agent_analysis_ticker ON agent_analysis_logs(ticker);
