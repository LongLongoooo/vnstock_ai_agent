"""
Quantitative scoring system for investment decisions.
Provides numerical scores based on multiple factors with emphasis on critical risks.
"""

def calculate_fundamental_score(valuation_metrics: dict, financial_metrics: dict) -> dict:
    """
    Calculate fundamental score (0-100) based on:
    - PE ratio (relative to sector average)
    - PB ratio (relative to sector average)
    - ROE (higher is better)
    - Revenue growth
    - Profit margin
    - Debt/Equity ratio
    """
    score = 0
    max_score = 100
    factors = {}
    
    # PE Score (20 points)
    pe = valuation_metrics.get("pe")
    if pe:
        if pe < 10:
            pe_score = 20
        elif pe < 15:
            pe_score = 15
        elif pe < 20:
            pe_score = 10
        elif pe < 25:
            pe_score = 5
        else:
            pe_score = 0
        score += pe_score
        factors["pe_score"] = pe_score
    
    # PB Score (15 points)
    pb = valuation_metrics.get("pb")
    if pb:
        if pb < 1:
            pb_score = 15
        elif pb < 2:
            pb_score = 12
        elif pb < 3:
            pb_score = 8
        elif pb < 5:
            pb_score = 4
        else:
            pb_score = 0
        score += pb_score
        factors["pb_score"] = pb_score
    
    # ROE Score (25 points)
    roe = valuation_metrics.get("roe")
    if roe:
        if roe > 20:
            roe_score = 25
        elif roe > 15:
            roe_score = 20
        elif roe > 10:
            roe_score = 15
        elif roe > 5:
            roe_score = 10
        else:
            roe_score = 5
        score += roe_score
        factors["roe_score"] = roe_score
    
    # Revenue Growth Score (15 points)
    revenue_growth = valuation_metrics.get("revenue_growth_yoy")
    if revenue_growth:
        if revenue_growth > 20:
            growth_score = 15
        elif revenue_growth > 10:
            growth_score = 12
        elif revenue_growth > 5:
            growth_score = 8
        elif revenue_growth > 0:
            growth_score = 5
        else:
            growth_score = 0
        score += growth_score
        factors["revenue_growth_score"] = growth_score
    
    # Profit Margin Score (15 points)
    profit_margin = valuation_metrics.get("profit_margin")
    if profit_margin:
        if profit_margin > 15:
            margin_score = 15
        elif profit_margin > 10:
            margin_score = 12
        elif profit_margin > 5:
            margin_score = 8
        elif profit_margin > 0:
            margin_score = 5
        else:
            margin_score = 0
        score += margin_score
        factors["profit_margin_score"] = margin_score
    
    # Debt/Equity Score (10 points) - lower is better
    debt_to_equity = valuation_metrics.get("debt_to_equity")
    if debt_to_equity is not None:
        if debt_to_equity < 0.5:
            debt_score = 10
        elif debt_to_equity < 1.0:
            debt_score = 8
        elif debt_to_equity < 1.5:
            debt_score = 5
        elif debt_to_equity < 2.0:
            debt_score = 3
        else:
            debt_score = 0
        score += debt_score
        factors["debt_score"] = debt_score
    
    return {
        "total_score": round(score, 2),
        "max_score": max_score,
        "percentage": round((score / max_score) * 100, 2),
        "rating": _get_rating(score / max_score),
        "breakdown": factors
    }

def calculate_technical_score(technical_indicators: dict, technical_summary: str) -> dict:
    """
    Calculate technical score (0-100) based on:
    - RSI (oversold/overbought)
    - MACD (bullish/bearish)
    - Volume trend
    - Price relative to support/resistance
    - SMA crossovers
    """
    score = 50  # Neutral baseline
    factors = {}
    
    # RSI Score (30 points)
    rsi = technical_indicators.get("rsi")
    if rsi is not None:
        if 30 <= rsi <= 50:  # Oversold to neutral - good for buying
            rsi_score = 30
        elif 50 < rsi <= 60:  # Slightly bullish
            rsi_score = 25
        elif 60 < rsi <= 70:  # Bullish but getting expensive
            rsi_score = 15
        elif rsi < 30:  # Very oversold - risky but opportunity
            rsi_score = 20
        else:  # Overbought (>70)
            rsi_score = 5
        score += (rsi_score - 15)  # Adjust from baseline
        factors["rsi_score"] = rsi_score
    
    # MACD Score (25 points)
    macd = technical_indicators.get("macd")
    if macd:
        if macd == "bullish":
            macd_score = 25
            score += 25
        elif macd == "neutral":
            macd_score = 12
            score += 0  # No change from baseline
        else:  # bearish
            macd_score = 0
            score -= 25
        factors["macd_score"] = macd_score
    
    # Volume Trend Score (20 points)
    volume_trend = technical_indicators.get("volume_trend")
    if volume_trend:
        if volume_trend == "increasing":
            volume_score = 20
            score += 15
        elif volume_trend == "stable":
            volume_score = 10
            score += 0
        else:  # decreasing
            volume_score = 0
            score -= 10
        factors["volume_score"] = volume_score
    
    # SMA Crossover Score (25 points)
    sma_50 = technical_indicators.get("sma_50")
    sma_200 = technical_indicators.get("sma_200")
    if sma_50 and sma_200:
        if sma_50 > sma_200:  # Golden cross - bullish
            sma_score = 25
            score += 10
        else:  # Death cross - bearish
            sma_score = 5
            score -= 10
        factors["sma_crossover_score"] = sma_score
    
    # Clamp to 0-100
    score = max(0, min(100, score))
    
    return {
        "total_score": round(score, 2),
        "max_score": 100,
        "percentage": round(score, 2),
        "rating": _get_rating(score / 100),
        "breakdown": factors
    }

def calculate_critical_risk_score(legal_governance: dict, key_risks: list) -> dict:
    """
    ⚠️ CRITICAL RISK ASSESSMENT - MOST IMPORTANT FOR VIETNAMESE STOCKS
    
    Calculate critical risk score (0-100, where higher = EXTREMELY DANGEROUS).
    This is a DEAL-BREAKER score - high scores should override all other factors.
    
    Categories:
    - CRITICAL (90-100): AVOID at all costs - leadership arrests, fraud, bankruptcy
    - HIGH (70-89): Major red flags - serious violations, investigations
    - MODERATE (40-69): Notable concerns - regulatory issues, disputes
    - LOW (20-39): Minor risks - normal business risks
    - VERY LOW (0-19): Minimal risks - clean governance
    """
    score = 0
    max_score = 100
    factors = {}
    
    # Legal/Governance Risk (0-60 points) - HIGHEST WEIGHT
    severity = legal_governance.get("severity", "NONE")
    has_critical = legal_governance.get("has_critical_issues", False)
    
    severity_scores = {
        "CRITICAL": 60,  # Leadership arrests, fraud, death sentences
        "HIGH": 45,      # Major violations, criminal investigations
        "MODERATE": 30,  # Regulatory issues, significant disputes
        "LOW": 15,       # Minor violations, warnings
        "NONE": 0        # Clean record
    }
    legal_risk_score = severity_scores.get(severity, 0)
    
    # If critical issues detected, automatically maximum score
    if has_critical:
        legal_risk_score = 60
    
    score += legal_risk_score
    factors["legal_governance_risk"] = legal_risk_score
    factors["has_critical_issues"] = has_critical
    
    # Number of Identified Risks (0-25 points)
    risk_count = len(key_risks)
    if risk_count >= 8:
        risk_count_score = 25
    elif risk_count >= 6:
        risk_count_score = 20
    elif risk_count >= 4:
        risk_count_score = 15
    elif risk_count >= 2:
        risk_count_score = 10
    else:
        risk_count_score = 5
    
    score += risk_count_score
    factors["risk_count_score"] = risk_count_score
    factors["total_risks"] = risk_count
    
    # Risk Severity Analysis (0-15 points)
    # Analyze risk descriptions for severity keywords
    critical_keywords = ["phá sản", "bắt giữ", "tử hình", "lừa đảo", "tham nhũng", 
                         "scandal", "fraud", "arrest", "bankruptcy"]
    high_keywords = ["kiện", "điều tra", "vi phạm", "phạt", "lawsuit", "investigation"]
    
    critical_risk_count = sum(1 for risk in key_risks 
                             if any(kw in risk.lower() for kw in critical_keywords))
    high_risk_count = sum(1 for risk in key_risks 
                         if any(kw in risk.lower() for kw in high_keywords))
    
    severity_score = min(critical_risk_count * 8 + high_risk_count * 3, 15)
    score += severity_score
    factors["severity_analysis_score"] = severity_score
    factors["critical_risks_found"] = critical_risk_count
    factors["high_risks_found"] = high_risk_count
    
    # Calculate final rating
    percentage = round((score / max_score) * 100, 2)
    rating = _get_critical_risk_rating(percentage)
    
    # Generate investment recommendation based on risk
    if percentage >= 90:
        recommendation = "AVOID - CRITICAL RISK"
        action = "DO NOT INVEST"
    elif percentage >= 70:
        recommendation = "AVOID - HIGH RISK"
        action = "STAY AWAY"
    elif percentage >= 40:
        recommendation = "CAUTION - MODERATE RISK"
        action = "PROCEED WITH EXTREME CAUTION"
    elif percentage >= 20:
        recommendation = "ACCEPTABLE - LOW RISK"
        action = "MONITOR CLOSELY"
    else:
        recommendation = "SAFE - VERY LOW RISK"
        action = "SAFE TO PROCEED"
    
    return {
        "total_score": round(score, 2),
        "max_score": max_score,
        "percentage": percentage,
        "rating": rating,
        "recommendation": recommendation,
        "action": action,
        "is_deal_breaker": percentage >= 70,  # High/Critical risk = deal breaker
        "breakdown": factors,
        "legal_issues": legal_governance.get("issues", []),
        "legal_summary": legal_governance.get("summary", "No critical issues found")
    }

def calculate_expected_return(
    current_price: float,
    price_targets: dict,
    probabilities: dict = None
) -> dict:
    """
    Calculate expected returns with probability weighting.
    """
    if not probabilities:
        probabilities = {
            "short_term": 0.3,
            "mid_term": 0.5,
            "long_term": 0.2
        }
    
    returns = {}
    weighted_return = 0
    
    # Short-term expected return
    short_target = price_targets.get("short_term")
    if short_target and current_price:
        short_return = ((short_target - current_price) / current_price) * 100
        returns["short_term"] = round(short_return, 2)
        weighted_return += short_return * probabilities["short_term"]
    
    # Mid-term expected return
    mid_target = price_targets.get("mid_term")
    if mid_target and current_price:
        mid_return = ((mid_target - current_price) / current_price) * 100
        returns["mid_term"] = round(mid_return, 2)
        weighted_return += mid_return * probabilities["mid_term"]
    
    # Long-term expected return
    long_target = price_targets.get("long_term")
    if long_target and current_price:
        long_return = ((long_target - current_price) / current_price) * 100
        returns["long_term"] = round(long_return, 2)
        weighted_return += long_return * probabilities["long_term"]
    
    return {
        "returns_by_timeframe": returns,
        "weighted_expected_return": round(weighted_return, 2),
        "best_case": round(max(returns.values()) if returns else 0, 2),
        "worst_case": round(min(returns.values()) if returns else 0, 2),
        "current_price": current_price
    }

def calculate_composite_score(
    fundamental_score: dict,
    technical_score: dict,
    critical_risk_score: dict,
    weights: dict = None
) -> dict:
    """
    Combine all scores into a composite investment score.
    
    Critical risk weighted at 40% of evaluation, but still allows investment if fundamentals are strong.
    """
    if not weights:
        weights = {
            "fundamental": 0.35,
            "technical": 0.25,
            "critical_risk": 0.40  # 40% weight for critical risk (negative)
        }
    
    # Check if critical risk is a deal-breaker
    is_deal_breaker = critical_risk_score.get("is_deal_breaker", False)
    critical_risk_pct = critical_risk_score.get("percentage", 0)
    
    # Normal calculation with 40% weight on critical risk
    composite = (
        fundamental_score["percentage"] * weights["fundamental"] +
        technical_score["percentage"] * weights["technical"] -
        critical_risk_pct * weights["critical_risk"]
    )
    
    # Add warning if critical risk is high, but don't completely cap the score
    if is_deal_breaker:
        warning = "⚠️ HIGH CRITICAL RISK - Proceed with extreme caution"
        # Reduce composite score further if deal-breaker, but don't cap it completely
        composite = composite * 0.7  # 30% penalty for deal-breaker risks
    else:
        warning = None
    
    composite = max(0, min(100, composite))  # Clamp to 0-100
    
    return {
        "composite_score": round(composite, 2),
        "rating": _get_rating(composite / 100),
        "is_deal_breaker": is_deal_breaker,
        "critical_risk_warning": warning,
        "components": {
            "fundamental": fundamental_score["percentage"],
            "technical": technical_score["percentage"],
            "critical_risk": critical_risk_pct
        },
        "weights_used": weights,
        "note": "Critical risk weighted at 40%. High risk reduces score by 30% but allows investment if fundamentals are strong."
    }

def calculate_sharpe_ratio(
    expected_return: float,
    volatility: float,
    risk_free_rate: float = 5.0
) -> float:
    """
    Calculate Sharpe Ratio for risk-adjusted returns.
    """
    if volatility == 0:
        return 0
    return round((expected_return - risk_free_rate) / volatility, 2)

def _get_rating(score_pct: float) -> str:
    """Convert score to letter rating"""
    if score_pct >= 0.9:
        return "A+"
    elif score_pct >= 0.8:
        return "A"
    elif score_pct >= 0.7:
        return "B+"
    elif score_pct >= 0.6:
        return "B"
    elif score_pct >= 0.5:
        return "C+"
    elif score_pct >= 0.4:
        return "C"
    elif score_pct >= 0.3:
        return "D"
    else:
        return "F"

def _get_critical_risk_rating(percentage: float) -> str:
    """Convert critical risk score to rating"""
    if percentage >= 90:
        return "🔴 CRITICAL - AVOID"
    elif percentage >= 70:
        return "🟠 HIGH RISK - AVOID"
    elif percentage >= 40:
        return "🟡 MODERATE RISK"
    elif percentage >= 20:
        return "🟢 LOW RISK"
    else:
        return "✅ VERY LOW RISK"