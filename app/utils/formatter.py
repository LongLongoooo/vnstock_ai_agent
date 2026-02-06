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
    
    # NEW: Quantitative Analysis Section with Critical Risk Emphasis
    quant = strategy.get("quantitative_analysis", {})
    critical_risk = quant.get("critical_risk_score", {})
    
    # Build critical risk warning if needed
    critical_warning = ""
    if critical_risk.get("is_deal_breaker"):
        critical_warning = f"""
⚠️⚠️⚠️ CRITICAL RISK ALERT ⚠️⚠️⚠️
════════════════════════════════════════════════════

{critical_risk.get('recommendation', 'AVOID - HIGH RISK')}
Action: {critical_risk.get('action', 'DO NOT INVEST')}

Legal/Governance Issues:
{critical_risk.get('legal_summary', 'Serious issues detected')}

Specific Issues:
"""
        for issue in critical_risk.get("legal_issues", []):
            critical_warning += f"• {issue}\n"
        
        critical_warning += "\n════════════════════════════════════════════════════\n"
    
    # Build the report
    report = f"""
📌 Stock Strategy Report — {ticker} (Updated)

{critical_warning}

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

📊 Quantitative Analysis
────────────────────────────────────────────────────

Overall Investment Scores:
• Composite Score: {quant.get('composite_score', {}).get('composite_score', 'N/A')}/100 
  Rating: {quant.get('composite_score', {}).get('rating', 'N/A')}
  Weights: Fundamental 35%, Technical 25%, Critical Risk 40%
  {f"⚠️ {quant.get('composite_score', {}).get('critical_risk_warning', '')}" if quant.get('composite_score', {}).get('critical_risk_warning') else ''}

Component Scores:
• Fundamental Score: {quant.get('fundamental_score', {}).get('percentage', 'N/A')}/100
  Rating: {quant.get('fundamental_score', {}).get('rating', 'N/A')}

• Technical Score: {quant.get('technical_score', {}).get('percentage', 'N/A')}/100
  Rating: {quant.get('technical_score', {}).get('rating', 'N/A')}

• ⚠️ Critical Risk Score: {critical_risk.get('percentage', 'N/A')}/100
  Rating: {critical_risk.get('rating', 'N/A')}
  Status: {"🔴 DEAL-BREAKER" if critical_risk.get('is_deal_breaker') else "✅ Acceptable"}

Risk Breakdown:
• Legal/Governance Risk: {critical_risk.get('breakdown', {}).get('legal_governance_risk', 'N/A')}/60 points
• Total Risks Identified: {critical_risk.get('breakdown', {}).get('total_risks', 'N/A')}
• Critical Risks Found: {critical_risk.get('breakdown', {}).get('critical_risks_found', 0)}
• High Risks Found: {critical_risk.get('breakdown', {}).get('high_risks_found', 0)}

Expected Returns:
• Short-term (0-3mo): {quant.get('expected_returns', {}).get('returns_by_timeframe', {}).get('short_term', 'N/A')}%
• Mid-term (3-12mo): {quant.get('expected_returns', {}).get('returns_by_timeframe', {}).get('mid_term', 'N/A')}%
• Long-term (1-5yr): {quant.get('expected_returns', {}).get('returns_by_timeframe', {}).get('long_term', 'N/A')}%
• Weighted Expected Return: {quant.get('expected_returns', {}).get('weighted_expected_return', 'N/A')}%

Best/Worst Case:
• Best Case: +{quant.get('expected_returns', {}).get('best_case', 'N/A')}%
• Worst Case: {quant.get('expected_returns', {}).get('worst_case', 'N/A')}%

Current Valuation:
• P/E Ratio: {quant.get('price_metrics', {}).get('pe_ratio', 'N/A')}
• P/B Ratio: {quant.get('price_metrics', {}).get('pb_ratio', 'N/A')}
• ROE: {quant.get('price_metrics', {}).get('roe', 'N/A')}%
• Upside Potential: {quant.get('price_metrics', {}).get('upside_potential_pct', 'N/A')}%

Investment Recommendation:
{quant.get('risk_assessment', {}).get('recommendation', 'Assess based on scores above')}
Action: {quant.get('risk_assessment', {}).get('action', 'Proceed with caution')}

📝 Summary

{strategy.get('cycle_assessment') or 'Analysis based on current market conditions and company fundamentals.'}

{' '.join((strategy.get('reasons') or [])[:3])}
"""
    
    return report.strip()
