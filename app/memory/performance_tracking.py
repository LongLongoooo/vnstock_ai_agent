"""
Track quantitative performance metrics over time.
"""

from sqlalchemy import text
from app.memory.hipporag_store import engine

def calculate_realized_returns(ticker: str) -> dict:
    """
    Calculate actual returns from advice given in the past.
    """
    sql = text("""
    SELECT 
        ticker,
        decision,
        price_at_advice,
        price_after_30d,
        price_after_90d,
        confidence,
        CASE 
            WHEN price_after_30d IS NOT NULL 
            THEN ((price_after_30d - price_at_advice) / price_at_advice * 100)
        END as return_30d,
        CASE 
            WHEN price_after_90d IS NOT NULL 
            THEN ((price_after_90d - price_at_advice) / price_at_advice * 100)
        END as return_90d
    FROM advice_audit
    WHERE ticker = :ticker
    ORDER BY advised_at DESC;
    """)
    
    with engine.connect() as conn:
        rows = conn.execute(sql, {"ticker": ticker}).mappings().fetchall()
    
    if not rows:
        return None
    
    returns_30d = [r["return_30d"] for r in rows if r["return_30d"] is not None]
    returns_90d = [r["return_90d"] for r in rows if r["return_90d"] is not None]
    
    return {
        "ticker": ticker,
        "total_advice_count": len(rows),
        "avg_return_30d": round(sum(returns_30d) / len(returns_30d), 2) if returns_30d else None,
        "avg_return_90d": round(sum(returns_90d) / len(returns_90d), 2) if returns_90d else None,
        "best_return_30d": round(max(returns_30d), 2) if returns_30d else None,
        "worst_return_30d": round(min(returns_30d), 2) if returns_30d else None,
        "best_return_90d": round(max(returns_90d), 2) if returns_90d else None,
        "worst_return_90d": round(min(returns_90d), 2) if returns_90d else None,
        "win_rate_30d": round(sum(1 for r in returns_30d if r > 0) / len(returns_30d) * 100, 2) if returns_30d else None,
        "win_rate_90d": round(sum(1 for r in returns_90d if r > 0) / len(returns_90d) * 100, 2) if returns_90d else None
    }