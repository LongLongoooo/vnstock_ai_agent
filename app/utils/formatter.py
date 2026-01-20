"""
Output formatter to display investment advice in a readable format.
"""

def format_advice_report(strategy: dict, ticker: str) -> str:
    """
    Format strategy JSON into a nice readable report.
    """
    
    # Extract data with safe defaults
    decision = strategy.get("decision") or "N/A"
    risk_level = strategy.get("risk_level") or "N/A"
    portfolio_weight = strategy.get("portfolio_weight_pct") or 0
    buy_zone = strategy.get("buy_zone") or [0, 0]
    stop_loss = strategy.get("stop_loss") or [0, 0]
    take_profit = strategy.get("take_profit") or [0, 0]
    holding_months = strategy.get("holding_months") or 0
    confidence = strategy.get("confidence") or 0
    
    # Get summaries from metadata if available
    part1 = strategy.get("_part1_summary") or {}
    part2 = strategy.get("_part2_summary") or {}
    
    # Technical data
    price_current = part1.get("price_current") or 0
    valuation = part1.get("valuation_metrics") or {}
    technical = part1.get("technical_summary") or "N/A"
    
    # Extract RSI, MACD from technical summary (rough parsing)
    rsi = "N/A"
    macd = "N/A"
    support = "N/A"
    resistance = "N/A"
    
    # Financial data
    financial = part1.get("financial_summary") or "N/A"
    dividend_cf = part1.get("dividend_cashflow") or "N/A"
    competitive = part1.get("competitive_position") or "N/A"
    
    # News
    news_highlights = part1.get("news_highlights") or []
    
    # Risks
    key_risks = strategy.get("key_risks") or []
    
    # Macro
    cycle = part2.get("economic_cycle_phase") or "N/A"
    gdp = part2.get("gdp_growth_outlook") or "N/A"
    inflation = part2.get("inflation_trend") or "N/A"
    interest = part2.get("interest_rate_trend") or "N/A"
    vnindex = part2.get("vnindex_sentiment") or "N/A"
    sector_rotation = part2.get("sector_rotation_analysis") or "N/A"
    
    # Multi-timeframe outlooks
    short_term = strategy.get("short_term_outlook") or {}
    mid_term = strategy.get("mid_term_outlook") or {}
    long_term = strategy.get("long_term_outlook") or {}
    
    # Build the report
    report = f"""
📌 Stock Strategy Report — {ticker} (Updated)
🎯 Overall Recommendation: {decision}

Risk Level: {risk_level}
Portfolio Weight: {portfolio_weight}%
Buy Zone: {buy_zone[0]:,.0f} – {buy_zone[1]:,.0f}
Stop Loss: {stop_loss[0]:,.0f} – {stop_loss[1]:,.0f}
Take Profit: {take_profit[0]:,.0f} – {take_profit[1]:,.0f}
Suggested Holding Period: {holding_months} months
Confidence: {int(confidence * 100)}%

📈 Technical Overview (Short-term)

Current price: {price_current:,.1f}k
{technical}

🏢 Company & Business Fundamentals

Competitive Position:
{competitive}

Financial Health (Recent):
{financial}

{dividend_cf}

Valuation Metrics:
P/E: {valuation.get('pe', 'N/A')}
P/B: {valuation.get('pb', 'N/A')}
ROE: {valuation.get('roe', 'N/A')}%

📰 Key Recent News
"""
    
    for news in news_highlights[:5]:
        report += f"• {news}\n"
    
    report += f"""
⚠️ Risks to Watch
"""
    
    for risk in key_risks[:6]:
        report += f"• {risk}\n"
    
    report += f"""
🌏 Macro & Market Environment

Economic cycle: {cycle.capitalize()} phase
GDP growth: {gdp.capitalize()}
Inflation: {inflation.capitalize()}
Interest rates: {interest.capitalize()}
VN-Index sentiment: {vnindex.capitalize()}
Sector rotation: {sector_rotation}
Market timing: {part2.get('market_timing_suggestion', 'N/A').replace('_', ' ').title()}

⏳ Outlook by Time Horizon

Short-term (0–3 months): {short_term.get('decision', 'N/A')}
Price Target: {(short_term.get('price_target') or 0):,.0f}k
Confidence: {int((short_term.get('confidence') or 0) * 100)}%
Rationale: {', '.join((short_term.get('key_factors') or [])[:2])}

Mid-term (3–12 months): {mid_term.get('decision', 'N/A')}
Price Target: {(mid_term.get('price_target') or 0):,.0f}k
Confidence: {int((mid_term.get('confidence') or 0) * 100)}%
Drivers: {', '.join((mid_term.get('key_factors') or [])[:2])}

Long-term (1–5 years): {long_term.get('decision', 'N/A')}
Intrinsic Value Range: {(long_term.get('intrinsic_value_range') or [0, 0])[0]:,.0f}k – {(long_term.get('intrinsic_value_range') or [0, 0])[1]:,.0f}k
Confidence: {int((long_term.get('confidence') or 0) * 100)}%
Drivers: {', '.join((long_term.get('key_factors') or [])[:2])}

📝 Summary

{strategy.get('cycle_assessment') or 'Analysis based on current market conditions and company fundamentals.'}

{' '.join((strategy.get('reasons') or [])[:3])}
"""
    
    return report.strip()
