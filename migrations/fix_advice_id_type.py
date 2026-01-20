"""
Fix advice_audit table to use TEXT for advice_id instead of INTEGER.
Run this to fix the UUID type mismatch error.
"""

from sqlalchemy import text
from app.memory.hipporag_store import engine

def fix_advice_id_type():
    """Change advice_id from INTEGER to TEXT to support UUID"""
    
    print("🔧 Fixing advice_audit table...")
    
    sql = text("""
    ALTER TABLE advice_audit 
    ALTER COLUMN advice_id TYPE TEXT;
    """)
    
    try:
        with engine.begin() as conn:
            conn.execute(sql)
        print("✅ advice_id column changed to TEXT successfully!")
        print("🎉 Now supports both INTEGER and UUID values")
    except Exception as e:
        print(f"❌ Migration failed: {e}")
        print("\nNote: If the table doesn't exist yet, run add_cache_and_audit_tables.py first")
        raise

if __name__ == "__main__":
    fix_advice_id_type()
