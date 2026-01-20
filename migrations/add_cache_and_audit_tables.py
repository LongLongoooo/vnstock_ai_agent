"""
Database migration script to add numeric_cache and advice_audit tables.
Run this once to set up the new tables.
"""

from sqlalchemy import text
from app.memory.hipporag_store import engine

def run_migration():
    """Execute the migration to add new tables"""
    
    print("🔧 Running database migration...")
    
    # Create numeric_cache table
    print("📊 Creating numeric_cache table...")
    create_numeric_cache = """
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
    
    # Create advice_audit table
    print("📈 Creating advice_audit table...")
    create_advice_audit = """
    CREATE TABLE IF NOT EXISTS advice_audit (
        audit_id SERIAL PRIMARY KEY,
        ticker VARCHAR(20) NOT NULL,
        advice_id TEXT,  -- TEXT to support both INTEGER and UUID
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
    
    try:
        with engine.begin() as conn:
            # Execute numeric_cache table creation
            conn.execute(text(create_numeric_cache))
            print("✅ numeric_cache table created/verified")
            
            # Execute advice_audit table creation
            conn.execute(text(create_advice_audit))
            print("✅ advice_audit table created/verified")
        
        print("\n🎉 Migration completed successfully!")
        print("\nNew features available:")
        print("  ✅ Trusted source filtering for numeric data")
        print("  ✅ Numeric cache for price/PE/PB/ROE tracking")
        print("  ✅ Advice audit logging for performance tracking")
        
    except Exception as e:
        print(f"\n❌ Migration failed: {e}")
        raise

if __name__ == "__main__":
    run_migration()
