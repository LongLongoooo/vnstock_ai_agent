import re
from app.agent.split_advice_service import new_advice, update_advice
from app.memory.hipporag_store import get_latest_strategy
from app.memory.numeric_cache import get_numeric_snapshot, compare_snapshots
from app.memory.advice_audit import get_audit_statistics, get_recent_audits
from app.utils.formatter import format_advice_report

TICKER_RE = re.compile(r'"([^"]+)"')

def handle_command(cmd: str):
    if cmd.startswith("/newadvice"):
        m = TICKER_RE.search(cmd)
        ticker = m.group(1) if m else cmd.split()[-1]
        result = new_advice(ticker)
        
        # Display formatted report if available
        if "_formatted_report" in result:
            print("\n" + result["_formatted_report"])
        
        return result

    if cmd.startswith("/updateadvice"):
        m = TICKER_RE.search(cmd)
        ticker = m.group(1) if m else cmd.split()[-1]
        result = update_advice(ticker)
        
        # Display formatted report if available
        if "_formatted_report" in result:
            print("\n" + result["_formatted_report"])
        
        return result
    
    if cmd.startswith("/recall"):
        m = TICKER_RE.search(cmd)
        ticker = m.group(1) if m else cmd.split()[-1]
        
        latest = get_latest_strategy(ticker)
        if not latest:
            return {
                "message": f"No advice found for {ticker}",
                "ticker": ticker,
                "has_advice": False
            }
        
        # Return the stored strategy and format it
        strategy = latest["strategy_props"]
        strategy["_retrieved_at"] = str(latest["created_at"])
        strategy["_version_id"] = latest.get("version_id")
        strategy["ticker"] = ticker
        strategy["has_advice"] = True
        
        # Generate formatted report for recalled advice
        formatted = format_advice_report(strategy, ticker)
        print("\n" + formatted)
        strategy["_formatted_report"] = formatted
        
        return strategy
    
    if cmd.startswith("/cache"):
        m = TICKER_RE.search(cmd)
        ticker = m.group(1) if m else cmd.split()[-1]
        
        snapshot = get_numeric_snapshot(ticker)
        if not snapshot:
            return {
                "message": f"No cached data for {ticker}",
                "ticker": ticker,
                "has_cache": False
            }
        
        return {
            "ticker": ticker,
            "has_cache": True,
            "snapshot": snapshot
        }
    
    if cmd.startswith("/stats"):
        # Parse optional ticker
        m = TICKER_RE.search(cmd)
        ticker = m.group(1) if m else None
        
        stats = get_audit_statistics(ticker=ticker)
        if not stats:
            return {
                "message": f"No audit statistics available" + (f" for {ticker}" if ticker else ""),
                "has_stats": False
            }
        
        return {
            "has_stats": True,
            "ticker": ticker,
            "statistics": stats
        }
    
    if cmd.startswith("/audits"):
        # Parse optional ticker
        m = TICKER_RE.search(cmd)
        ticker = m.group(1) if m else None
        
        audits = get_recent_audits(ticker=ticker, limit=10)
        return {
            "ticker": ticker,
            "count": len(audits),
            "audits": audits
        }

    return {
        "error": "Unknown command. Available commands: /newadvice, /updateadvice, /recall, /cache, /stats, /audits"
    }
