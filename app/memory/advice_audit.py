"""
Backtest and audit logging for investment advice.
Tracks advice outcomes over time (30d, 90d, 180d, 1yr).
"""

import json
from datetime import datetime, timedelta
from sqlalchemy import text
from app.memory.hipporag_store import engine

def create_advice_audit(ticker: str, advice_id, decision: str, 
                        price_at_advice: float, confidence: float,
                        portfolio_weight_pct: float = None,
                        buy_zone: list = None, stop_loss: list = None,
                        take_profit: list = None):
    """
    Create an audit record when advice is given.
    Records the price at the time of advice for future comparison.
    advice_id can be int or UUID - will be converted to string.
    """
    sql = text("""
    INSERT INTO advice_audit (
        ticker, advice_id, decision, price_at_advice, confidence,
        portfolio_weight_pct, buy_zone, stop_loss, take_profit,
        advised_at
    ) VALUES (
        :ticker, :advice_id, :decision, :price_at_advice, :confidence,
        :portfolio_weight_pct, :buy_zone, :stop_loss, :take_profit,
        NOW()
    )
    RETURNING audit_id;
    """)
    
    with engine.begin() as conn:
        return conn.execute(sql, {
            "ticker": ticker,
            "advice_id": str(advice_id),  # Convert to string to handle UUID
            "decision": decision,
            "price_at_advice": price_at_advice,
            "confidence": confidence,
            "portfolio_weight_pct": portfolio_weight_pct,
            "buy_zone": json.dumps(buy_zone) if buy_zone else None,
            "stop_loss": json.dumps(stop_loss) if stop_loss else None,
            "take_profit": json.dumps(take_profit) if take_profit else None
        }).scalar_one()

def update_audit_outcomes(ticker: str, current_price: float):
    """
    Update audit records with current price and calculate outcomes.
    Run this periodically (e.g., daily) to track advice performance.
    """
    sql = text("""
    UPDATE advice_audit
    SET 
        price_after_30d = CASE 
            WHEN advised_at <= NOW() - INTERVAL '30 days' 
            AND price_after_30d IS NULL 
            THEN :current_price 
            ELSE price_after_30d 
        END,
        price_after_90d = CASE 
            WHEN advised_at <= NOW() - INTERVAL '90 days' 
            AND price_after_90d IS NULL 
            THEN :current_price 
            ELSE price_after_90d 
        END,
        price_after_180d = CASE 
            WHEN advised_at <= NOW() - INTERVAL '180 days' 
            AND price_after_180d IS NULL 
            THEN :current_price 
            ELSE price_after_180d 
        END,
        price_after_1yr = CASE 
            WHEN advised_at <= NOW() - INTERVAL '1 year' 
            AND price_after_1yr IS NULL 
            THEN :current_price 
            ELSE price_after_1yr 
        END
    WHERE ticker = :ticker
    AND (price_after_30d IS NULL 
         OR price_after_90d IS NULL 
         OR price_after_180d IS NULL 
         OR price_after_1yr IS NULL);
    """)
    
    with engine.begin() as conn:
        conn.execute(sql, {"ticker": ticker, "current_price": current_price})

def label_advice_outcome(audit_id: int):
    """
    Automatically label the outcome of advice based on price changes.
    Labels: 'success', 'neutral', 'failure', 'pending'
    """
    sql = text("""
    UPDATE advice_audit
    SET outcome_label = CASE
        -- BUY advice
        WHEN decision = 'BUY' AND price_after_90d IS NOT NULL THEN
            CASE 
                WHEN price_after_90d > price_at_advice * 1.10 THEN 'success'
                WHEN price_after_90d < price_at_advice * 0.95 THEN 'failure'
                ELSE 'neutral'
            END
        -- SELL advice
        WHEN decision = 'SELL' AND price_after_90d IS NOT NULL THEN
            CASE 
                WHEN price_after_90d < price_at_advice * 0.95 THEN 'success'
                WHEN price_after_90d > price_at_advice * 1.05 THEN 'failure'
                ELSE 'neutral'
            END
        -- HOLD advice
        WHEN decision = 'HOLD' AND price_after_90d IS NOT NULL THEN
            CASE 
                WHEN ABS(price_after_90d - price_at_advice) / price_at_advice < 0.05 THEN 'success'
                ELSE 'neutral'
            END
        ELSE 'pending'
    END,
    outcome_evaluated_at = NOW()
    WHERE audit_id = :audit_id;
    """)
    
    with engine.begin() as conn:
        conn.execute(sql, {"audit_id": audit_id})

def get_audit_statistics(ticker: str = None, decision: str = None):
    """
    Get performance statistics for advice.
    Returns success rate, average return, etc.
    """
    where_clauses = ["outcome_label IN ('success', 'neutral', 'failure')"]
    params = {}
    
    if ticker:
        where_clauses.append("ticker = :ticker")
        params["ticker"] = ticker
    
    if decision:
        where_clauses.append("decision = :decision")
        params["decision"] = decision
    
    where_sql = " AND ".join(where_clauses)
    
    sql = text(f"""
    SELECT 
        COUNT(*) as total_advice,
        SUM(CASE WHEN outcome_label = 'success' THEN 1 ELSE 0 END) as successes,
        SUM(CASE WHEN outcome_label = 'failure' THEN 1 ELSE 0 END) as failures,
        SUM(CASE WHEN outcome_label = 'neutral' THEN 1 ELSE 0 END) as neutrals,
        AVG(CASE 
            WHEN price_after_90d IS NOT NULL 
            THEN (price_after_90d - price_at_advice) / price_at_advice * 100 
        END) as avg_return_pct_90d,
        AVG(confidence) as avg_confidence
    FROM advice_audit
    WHERE {where_sql};
    """)
    
    with engine.connect() as conn:
        row = conn.execute(sql, params).mappings().first()
    
    if row and row["total_advice"] > 0:
        return {
            "total_advice": row["total_advice"],
            "successes": row["successes"],
            "failures": row["failures"],
            "neutrals": row["neutrals"],
            "success_rate": round(row["successes"] / row["total_advice"] * 100, 2) if row["total_advice"] > 0 else 0,
            "avg_return_pct_90d": round(float(row["avg_return_pct_90d"]), 2) if row["avg_return_pct_90d"] else None,
            "avg_confidence": round(float(row["avg_confidence"]), 2) if row["avg_confidence"] else None
        }
    return None

def get_recent_audits(ticker: str = None, limit: int = 10):
    """Get recent advice audits for review"""
    where_clause = "WHERE ticker = :ticker" if ticker else ""
    params = {"ticker": ticker} if ticker else {}
    
    sql = text(f"""
    SELECT 
        audit_id, ticker, decision, price_at_advice, confidence,
        price_after_30d, price_after_90d, price_after_180d, price_after_1yr,
        outcome_label, advised_at, outcome_evaluated_at
    FROM advice_audit
    {where_clause}
    ORDER BY advised_at DESC
    LIMIT :limit;
    """)
    
    params["limit"] = limit
    
    with engine.connect() as conn:
        rows = conn.execute(sql, params).mappings().fetchall()
    
    return [dict(row) for row in rows]

# Create table SQL (run once during setup)
CREATE_ADVICE_AUDIT_TABLE = """
CREATE TABLE IF NOT EXISTS advice_audit (
    audit_id SERIAL PRIMARY KEY,
    ticker VARCHAR(20) NOT NULL,
    advice_id TEXT,  -- Changed to TEXT to support both INTEGER and UUID
    decision VARCHAR(20) NOT NULL,
    price_at_advice NUMERIC(15,2) NOT NULL,
    confidence NUMERIC(3,2),
    portfolio_weight_pct NUMERIC(5,2),
    buy_zone JSONB,
    stop_loss JSONB,
    take_profit JSONB,
    advised_at TIMESTAMP NOT NULL DEFAULT NOW(),
    
    -- Price snapshots at future dates
    price_after_30d NUMERIC(15,2),
    price_after_90d NUMERIC(15,2),
    price_after_180d NUMERIC(15,2),
    price_after_1yr NUMERIC(15,2),
    
    -- Outcome evaluation
    outcome_label VARCHAR(20),  -- 'success', 'neutral', 'failure', 'pending'
    outcome_evaluated_at TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_advice_audit_ticker ON advice_audit(ticker);
CREATE INDEX IF NOT EXISTS idx_advice_audit_advised_at ON advice_audit(advised_at DESC);
CREATE INDEX IF NOT EXISTS idx_advice_audit_outcome ON advice_audit(outcome_label);
"""
