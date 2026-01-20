"""
Numeric cache for reliable fact storage and comparison.
Stores latest price, PE/PB/ROE snapshots with timestamps.
"""

import json
from datetime import datetime
from sqlalchemy import text
from app.memory.hipporag_store import engine

def upsert_numeric_snapshot(ticker: str, price: float = None, pe: float = None, 
                            pb: float = None, roe: float = None, source_url: str = None):
    """
    Store or update the latest numeric snapshot for a ticker.
    Only stores hard facts with timestamp and source.
    """
    sql = text("""
    INSERT INTO numeric_cache (
        ticker, price, pe, pb, roe, source_url, cached_at
    ) VALUES (
        :ticker, :price, :pe, :pb, :roe, :source_url, NOW()
    )
    ON CONFLICT (ticker) DO UPDATE SET
        price = COALESCE(EXCLUDED.price, numeric_cache.price),
        pe = COALESCE(EXCLUDED.pe, numeric_cache.pe),
        pb = COALESCE(EXCLUDED.pb, numeric_cache.pb),
        roe = COALESCE(EXCLUDED.roe, numeric_cache.roe),
        source_url = COALESCE(EXCLUDED.source_url, numeric_cache.source_url),
        cached_at = NOW()
    RETURNING cache_id;
    """)
    
    with engine.begin() as conn:
        return conn.execute(sql, {
            "ticker": ticker,
            "price": price,
            "pe": pe,
            "pb": pb,
            "roe": roe,
            "source_url": source_url
        }).scalar_one()

def get_numeric_snapshot(ticker: str):
    """
    Retrieve the latest cached numeric snapshot for a ticker.
    Returns None if no cache exists.
    """
    sql = text("""
    SELECT ticker, price, pe, pb, roe, source_url, cached_at
    FROM numeric_cache
    WHERE ticker = :ticker
    ORDER BY cached_at DESC
    LIMIT 1;
    """)
    
    with engine.connect() as conn:
        row = conn.execute(sql, {"ticker": ticker}).mappings().first()
    
    if row:
        return {
            "ticker": row["ticker"],
            "price": float(row["price"]) if row["price"] else None,
            "pe": float(row["pe"]) if row["pe"] else None,
            "pb": float(row["pb"]) if row["pb"] else None,
            "roe": float(row["roe"]) if row["roe"] else None,
            "source_url": row["source_url"],
            "cached_at": str(row["cached_at"])
        }
    return None

def compare_snapshots(ticker: str, new_price: float = None, new_pe: float = None,
                     new_pb: float = None, new_roe: float = None):
    """
    Compare new values against cached values.
    Returns dict with changes and percentage differences.
    """
    old = get_numeric_snapshot(ticker)
    if not old:
        return {"has_baseline": False, "message": "No previous snapshot to compare"}
    
    changes = {"has_baseline": True, "ticker": ticker, "changes": []}
    
    if new_price and old["price"]:
        pct_change = ((new_price - old["price"]) / old["price"]) * 100
        changes["changes"].append({
            "metric": "price",
            "old": old["price"],
            "new": new_price,
            "change_pct": round(pct_change, 2)
        })
    
    if new_pe and old["pe"]:
        pct_change = ((new_pe - old["pe"]) / old["pe"]) * 100
        changes["changes"].append({
            "metric": "PE",
            "old": old["pe"],
            "new": new_pe,
            "change_pct": round(pct_change, 2)
        })
    
    if new_pb and old["pb"]:
        pct_change = ((new_pb - old["pb"]) / old["pb"]) * 100
        changes["changes"].append({
            "metric": "PB",
            "old": old["pb"],
            "new": new_pb,
            "change_pct": round(pct_change, 2)
        })
    
    if new_roe and old["roe"]:
        pct_change = ((new_roe - old["roe"]) / old["roe"]) * 100
        changes["changes"].append({
            "metric": "ROE",
            "old": old["roe"],
            "new": new_roe,
            "change_pct": round(pct_change, 2)
        })
    
    changes["baseline_date"] = old["cached_at"]
    return changes

# Create table SQL (run once during setup)
CREATE_NUMERIC_CACHE_TABLE = """
CREATE TABLE IF NOT EXISTS numeric_cache (
    cache_id SERIAL PRIMARY KEY,
    ticker VARCHAR(20) NOT NULL UNIQUE,
    price NUMERIC(15,2),
    pe NUMERIC(10,2),
    pb NUMERIC(10,2),
    roe NUMERIC(10,2),
    source_url TEXT,
    cached_at TIMESTAMP NOT NULL DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_numeric_cache_ticker ON numeric_cache(ticker);
CREATE INDEX IF NOT EXISTS idx_numeric_cache_cached_at ON numeric_cache(cached_at DESC);
"""
