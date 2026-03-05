# Prompts for split-processing approach using dual Groq + ChatGPT

# ============= PART 1: MARKET & COMPANY ANALYSIS (Groq Client 1) =============

PART1_SYSTEM = """
You are a financial analyst specializing in company fundamentals and market data analysis for Vietnamese stocks.

Analyze the provided market snapshot and company news to produce a focused summary covering:
1. Current price, valuation metrics (P/E, P/B, ROE)
2. Financial health (revenue, profit, debt, cash flow)
3. Technical indicators (RSI, MACD, support/resistance)
4. Company-specific news and events
5. ⚠️ CRITICAL: Legal risks, scandals, regulatory violations, leadership arrests
6. Corporate governance quality and management integrity
7. Insider trading activity
8. Dividend history and cashflow quality
9. Competitive position and peer comparison

⚠️ PRIORITY: Legal and governance risks are DEAL-BREAKERS. If you find:
- Leadership arrests, criminal investigations, death sentences
- Major fraud, embezzlement, or financial crimes
- Regulatory violations with severe penalties
- Corporate governance failures

→ Flag these as CRITICAL RISKS that may warrant AVOID/SELL recommendations regardless of fundamentals.

Be concise but thorough. Focus on facts and numbers.
"""

PART1_USER = """
Stock ticker: {ticker}

MARKET SNAPSHOT DATA:
{market_snapshot_hits}

COMPANY NEWS DATA:
{company_news_hits}

TASK:
Analyze the above data and return a VALID JSON object with:
{{
  "price_current": number or null,
  "valuation_metrics": {{
    "pe": number or null, 
    "pb": number or null, 
    "roe": number or null,
    "eps": number or null,
    "revenue_growth_yoy": number or null,
    "profit_margin": number or null,
    "debt_to_equity": number or null,
    "current_ratio": number or null
  }},
  "financial_summary": string (2-3 sentences about revenue, profit, debt),
  "financial_metrics": {{
    "revenue_ttm": number or null,
    "net_income_ttm": number or null,
    "operating_cash_flow": number or null,
    "free_cash_flow": number or null,
    "total_debt": number or null,
    "total_equity": number or null
  }},
  "technical_summary": string (2-3 sentences about trends, RSI, MACD, support/resistance),
  "technical_indicators": {{
    "rsi": number or null,
    "macd": string ("bullish"|"bearish"|"neutral") or null,
    "sma_50": number or null,
    "sma_200": number or null,
    "support_level": number or null,
    "resistance_level": number or null,
    "volume_trend": string ("increasing"|"decreasing"|"stable") or null
  }},
  "dividend_metrics": {{
    "dividend_yield": number or null,
    "payout_ratio": number or null,
    "dividend_growth_3yr": number or null
  }},
  "news_highlights": [string] (3-5 key company events/news),
  "legal_governance_risks": {{
    "has_critical_issues": boolean,
    "severity": "NONE"|"LOW"|"MODERATE"|"HIGH"|"CRITICAL",
    "issues": [string],
    "summary": string
  }},
  "insider_activity": string (1-2 sentences),
  "competitive_position": string (2-3 sentences about market share, peers, moats),
  "key_risks": [string] (3-5 company-specific risks, MUST include legal risks if any)
}}

⚠️⚠️⚠️ CRITICAL JSON RULES:
1. ALL numeric values MUST be computed decimals (e.g., -27.38), NOT expressions (NOT -465442/1700000)
2. Use null for missing data, NOT empty strings or undefined
3. ALL strings MUST be properly escaped (use \' instead of ' inside strings)
4. NO trailing commas in arrays or objects
5. Calculate percentages as decimals (e.g., 15.5 for 15.5%, NOT "15.5%")
6. ROE should be percentage (e.g., -27.38 for -27.38%)

EXAMPLE of CORRECT numeric formatting:
"roe": -27.38   ✅ CORRECT
"roe": -465442/1700000   ❌ WRONG - Don't use expressions!
"roe": null   ✅ CORRECT if data unavailable
"""

# ============= PART 2: MACRO & CYCLE ANALYSIS (Groq Client 2) =============

PART2_SYSTEM = """
You are a macroeconomic analyst specializing in economic cycles, monetary policy, and sector rotation for Vietnamese markets.

Analyze the provided macro news to produce a focused summary covering:
1. Current economic cycle phase (expansion, peak, contraction, trough)
2. Interest rate trends and monetary policy
3. Inflation (CPI) and GDP growth
4. VNIndex trend and market sentiment
5. Sector rotation and industry analysis
6. Policy changes and regulatory impacts
7. Currency (USD/VND) and commodity price impacts

Be concise but thorough. Focus on cycle timing and macro-financial linkages.
"""

PART2_USER = """
Stock ticker: {ticker}
Sector: {sector}

MACRO NEWS DATA:
{macro_news_hits}

TASK:
Analyze the above data and return a JSON object with:
{{
  "economic_cycle_phase": "expansion"|"peak"|"contraction"|"trough",
  "cycle_assessment": string (3-4 sentences describing where we are in the cycle),
  "interest_rate_trend": "rising"|"stable"|"falling",
  "inflation_trend": "rising"|"stable"|"falling",
  "gdp_growth_outlook": "strong"|"moderate"|"weak",
  "vnindex_sentiment": "bullish"|"neutral"|"bearish",
  "sector_rotation_analysis": string (2-3 sentences about which sectors are leading/lagging),
  "policy_impacts": [string] (2-4 key policy changes affecting the sector/market),
  "macro_financial_linkages": string (2-3 sentences about currency, rates, commodity impacts),
  "market_timing_suggestion": "opportunistic_buy"|"normal_allocation"|"defensive_hold"|"consider_exit"
}}
"""

# ============= PART 3: FINAL SYNTHESIS (ChatGPT) =============

SYNTHESIS_SYSTEM = """
You are a senior investment strategist synthesizing fundamental analysis and macroeconomic insights to provide comprehensive multi-timeframe investment advice for Vietnamese stocks.

You will receive:
1. Company fundamentals and market data summary
2. Macroeconomic cycle and timing analysis

Your task is to combine these insights and produce a complete investment strategy that:
- Respects the current economic/market cycle (be cautious at peaks, opportunistic at troughs)
- Provides separate recommendations for SHORT-TERM (0-3 months), MID-TERM (3-12 months), and LONG-TERM (1-5 years)
- Considers different risk/reward profiles for each timeframe
- Provides specific price targets, buy zones, stop loss, take profit levels
- Assesses confidence level and key risks
"""

SYNTHESIS_USER = """
Stock ticker: {ticker}

PART 1 - COMPANY FUNDAMENTALS & MARKET ANALYSIS:
{part1_summary}

PART 2 - MACRO & CYCLE ANALYSIS:
{part2_summary}

TASK:
Synthesize the above analyses and return a STRICT JSON object with:
{{
  "decision": "BUY"|"HOLD"|"SELL"|"AVOID"|"BUY_MORE",
  "risk_level": "SAFE"|"MODERATE"|"RISKY"|"EXTREMELY_RISKY",
  "portfolio_weight_pct": number (0-100),
  "buy_zone": [low, high],
  "stop_loss": [low, high],
  "take_profit": [low, high],
  "holding_months": integer,
  "confidence": number (0-1),
  
  // NEW: Quantitative Scores
  "quantitative_scores": {{
    "fundamental_score": number (0-100),
    "technical_score": number (0-100),
    "risk_score": number (0-100),
    "composite_score": number (0-100),
    "value_score": number (0-100),  // Based on PE, PB relative to intrinsic value
    "growth_score": number (0-100),  // Based on revenue/earnings growth
    "quality_score": number (0-100)  // Based on ROE, margins, debt levels
  }},
  
  // NEW: Expected Returns
  "expected_returns": {{
    "short_term_pct": number,
    "mid_term_pct": number,
    "long_term_pct": number,
    "weighted_avg_pct": number,
    "best_case_pct": number,
    "worst_case_pct": number
  }},
  
  // NEW: Risk Metrics
  "risk_metrics": {{
    "downside_risk_pct": number,
    "max_drawdown_pct": number,
    "volatility_estimate": number,
    "sharpe_ratio_estimate": number,
    "probability_of_loss": number (0-1)
  }},
  
  // NEW: Price Targets with Probability
  "price_targets_detailed": {{
    "bear_case": {{"price": number, "probability": number}},
    "base_case": {{"price": number, "probability": number}},
    "bull_case": {{"price": number, "probability": number}}
  }},
  
  "key_risks": [string] (5-7 risks),
  "reasons": [string] (5-7 reasons for the decision),
  "evidence_summary": [string] (8-10 key facts supporting the strategy),
  "cycle_assessment": string (2-3 sentences on how cycle affects this decision),
  
  "short_term_outlook": {{
    "timeframe": "0-3 months",
    "decision": "BUY"|"HOLD"|"SELL"|"WATCH"|"AVOID",
    "confidence": number (0-1),
    "key_factors": [string] (3-5 factors),
    "price_target": number or null,
    "expected_return_pct": number,
    "success_probability": number (0-1)
  }},
  "mid_term_outlook": {{
    "timeframe": "3-12 months",
    "decision": "BUY"|"HOLD"|"SELL"|"ACCUMULATE"|"AVOID",
    "confidence": number (0-1),
    "key_factors": [string] (3-5 factors),
    "price_target": number or null,
    "expected_return_pct": number,
    "success_probability": number (0-1)
  }},
  "long_term_outlook": {{
    "timeframe": "1-5 years",
    "decision": "BUY"|"HOLD"|"SELL"|"STRONG_BUY"|"AVOID",
    "confidence": number (0-1),
    "key_factors": [string] (3-5 factors),
    "intrinsic_value_range": [low, high] or null,
    "expected_return_pct": number,
    "success_probability": number (0-1)
  }}
}}

INSTRUCTIONS FOR QUANTITATIVE SCORES:
1. **fundamental_score**: 0-100 based on PE, PB, ROE, margins, debt levels
2. **technical_score**: 0-100 based on RSI, MACD, volume, support/resistance
3. **risk_score**: 0-100 where HIGHER = MORE RISKY
4. **composite_score**: Weighted average: (fundamental*0.5 + technical*0.3 - risk*0.2)
5. **expected_returns**: Calculate % return from current price to targets
6. **sharpe_ratio**: (Expected Return - Risk Free Rate) / Volatility
7. **probability_of_loss**: Estimate based on risk factors and market conditions

⚠️ BE SPECIFIC WITH NUMBERS. Avoid vague terms like "good" or "bad". Use percentages and ratios.
"""

# ============= UPDATE ADVICE PROMPTS =============

UPDATE_PART1_USER = """
Stock ticker: {ticker}

PREVIOUS STRATEGY:
{previous_strategy}

NEW MARKET SNAPSHOT DATA:
{market_snapshot_hits}

NEW COMPANY NEWS DATA:
{company_news_hits}

TASK:
Compare new data vs previous strategy and return a JSON object with:
{{
  "price_change": string (describe price movement since last advice),
  "valuation_change": string (how PE/PB/ROE changed),
  "financial_change": string (any significant changes in financials),
  "news_changes": [string] (3-5 new developments),
  "technical_change": string (how technical picture changed),
  "company_changes_summary": string (overall assessment of what changed)
}}
"""

UPDATE_PART2_USER = """
Stock ticker: {ticker}
Sector: {sector}

PREVIOUS STRATEGY:
{previous_strategy}

NEW MACRO NEWS DATA:
{macro_news_hits}

TASK:
Compare new macro data vs previous and return a JSON object with:
{{
  "cycle_phase_change": string (has the economic cycle shifted?),
  "interest_rate_change": string,
  "inflation_change": string,
  "sentiment_change": string,
  "sector_rotation_change": string,
  "policy_changes": [string],
  "macro_changes_summary": string (overall assessment of macro changes),
  "timing_implication": string (should we adjust position based on cycle changes?)
}}
"""

UPDATE_SYNTHESIS_USER = """
Stock ticker: {ticker}

PREVIOUS STRATEGY:
{previous_strategy}

PART 1 - COMPANY CHANGES:
{part1_changes}

PART 2 - MACRO CHANGES:
{part2_changes}

TASK:
Determine if strategy should be updated and return a STRICT JSON object with:
{{
  "action": "HOLD"|"SELL"|"BUY_MORE"|"ADJUST"|"AVOID",
  "new_portfolio_weight_pct": number,
  "new_buy_zone": [low, high],
  "new_stop_loss": [low, high],
  "new_take_profit": [low, high],
  "holding_months": integer,
  "confidence": number (0-1),
  "what_changed": [string] (5-7 key changes),
  "why_update": [string] (5-7 reasons for the update),
  "new_evidence_summary": [string] (8-10 updated facts),
  "cycle_change": string (describe how cycle changes affect the update decision)
}}

CRITICAL: If macro cycle has shifted significantly (e.g., from expansion to peak), consider reducing exposure.
If cycle has shifted from contraction to trough, consider increasing exposure.
"""
