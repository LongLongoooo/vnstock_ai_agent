"""
Split-processing advice service using dual Groq to handle token limits.

Strategy (Groq-only fallback):
1. Groq Client 1: Analyzes market_snapshot + company_news → Part 1 summary
2. Groq Client 2: Analyzes macro_news → Part 2 summary
3. Groq Client 1 (reused): Combines Part 1 + Part 2 → Final comprehensive strategy

This approach uses only 2 Groq API keys, no OpenAI needed.
"""

import json
from app.tools.market_search import search_market_snapshot
from app.tools.news_search import search_company_news, search_macro_news
from app.agent.llm_client import chat_json
from app.agent.split_prompts import (
    PART1_SYSTEM, PART1_USER,
    PART2_SYSTEM, PART2_USER,
    SYNTHESIS_SYSTEM, SYNTHESIS_USER,
    UPDATE_PART1_USER, UPDATE_PART2_USER, UPDATE_SYNTHESIS_USER
)
from app.memory.hipporag_store import (
    upsert_company_node, insert_evidence_node,
    store_new_strategy, get_latest_strategy
)
from app.memory.numeric_cache import upsert_numeric_snapshot, get_numeric_snapshot
from app.memory.advice_audit import create_advice_audit
from app.utils.formatter import format_advice_report
from app.tools.quant_score_sys import (
    calculate_fundamental_score,
    calculate_technical_score,
    calculate_critical_risk_score,
    calculate_expected_return,
    calculate_composite_score,
    calculate_sharpe_ratio
)

def _collect_evidence(ticker: str, sector_hint: str = None):
    """Collect evidence from all sources"""
    market_hits = search_market_snapshot(ticker)
    company_news = search_company_news(ticker)
    macro_news = search_macro_news(sector_hint)
    
    # Flatten macro_news which is a list of lists
    macro_news_flat = []
    for result_list in macro_news:
        if isinstance(result_list, list):
            macro_news_flat.extend(result_list)
        else:
            macro_news_flat.append(result_list)

    return {
        "market_snapshot_hits": market_hits,
        "company_news_hits": company_news,
        "macro_news_hits": macro_news_flat
    }

def new_advice(ticker: str, sector_hint: str = None):
    """
    Generate new investment advice using split processing with quantitative scores.
    """
    # Step 1: Collect evidence
    evidence = _collect_evidence(ticker, sector_hint)
    
    # Step 2: Part 1 - Company & Market Analysis (Groq Client 1)
    part1_user = PART1_USER.format(
        ticker=ticker,
        market_snapshot_hits=json.dumps(evidence["market_snapshot_hits"], ensure_ascii=False),
        company_news_hits=json.dumps(evidence["company_news_hits"], ensure_ascii=False)
    )
    part1_json = chat_json(PART1_SYSTEM, part1_user, client_num=1)
    part1_summary = json.loads(part1_json)
    
    # Step 3: Part 2 - Macro & Cycle Analysis (Groq Client 2)
    part2_user = PART2_USER.format(
        ticker=ticker,
        sector=sector_hint or "chung",
        macro_news_hits=json.dumps(evidence["macro_news_hits"], ensure_ascii=False)
    )
    part2_json = chat_json(PART2_SYSTEM, part2_user, client_num=2)
    part2_summary = json.loads(part2_json)
    
    # Step 4: Final Synthesis (Groq Client 1 - reused)
    # Using Groq instead of OpenAI to avoid quota issues
    synthesis_user = SYNTHESIS_USER.format(
        ticker=ticker,
        part1_summary=json.dumps(part1_summary, ensure_ascii=False, indent=2),
        part2_summary=json.dumps(part2_summary, ensure_ascii=False, indent=2)
    )
    final_json = chat_json(SYNTHESIS_SYSTEM, synthesis_user, client_num=1)
    strategy = json.loads(final_json)
    
    # Ensure all required fields have valid defaults (handle None values)
    strategy.setdefault("buy_zone", [0, 0])
    strategy.setdefault("stop_loss", [0, 0])
    strategy.setdefault("take_profit", [0, 0])
    strategy.setdefault("key_risks", [])
    strategy.setdefault("reasons", [])
    strategy.setdefault("evidence_summary", [])
    strategy.setdefault("short_term_outlook", {})
    strategy.setdefault("mid_term_outlook", {})
    strategy.setdefault("long_term_outlook", {})
    
    # Fix None values in arrays
    if strategy["buy_zone"] is None:
        strategy["buy_zone"] = [0, 0]
    if strategy["stop_loss"] is None:
        strategy["stop_loss"] = [0, 0]
    if strategy["take_profit"] is None:
        strategy["take_profit"] = [0, 0]
    if strategy["key_risks"] is None:
        strategy["key_risks"] = []
    if strategy["reasons"] is None:
        strategy["reasons"] = []
    if strategy["evidence_summary"] is None:
        strategy["evidence_summary"] = []
    if strategy["short_term_outlook"] is None:
        strategy["short_term_outlook"] = {}
    if strategy["mid_term_outlook"] is None:
        strategy["mid_term_outlook"] = {}
    if strategy["long_term_outlook"] is None:
        strategy["long_term_outlook"] = {}
    
    # Fix None values in part1_summary
    if part1_summary.get("valuation_metrics") is None:
        part1_summary["valuation_metrics"] = {}
    if part1_summary.get("news_highlights") is None:
        part1_summary["news_highlights"] = []
    if part1_summary.get("key_risks") is None:
        part1_summary["key_risks"] = []
    
    # Fix None values in part2_summary
    for key in ["economic_cycle_phase", "cycle_assessment", "interest_rate_trend", 
                "inflation_trend", "gdp_growth_outlook", "vnindex_sentiment",
                "sector_rotation_analysis", "market_timing_suggestion"]:
        if part2_summary.get(key) is None:
            part2_summary[key] = "N/A"
    if part2_summary.get("policy_impacts") is None:
        part2_summary["policy_impacts"] = []
    if part2_summary.get("macro_financial_linkages") is None:
        part2_summary["macro_financial_linkages"] = "N/A"
    
    # Step 5: Store in memory
    evidence_summary = strategy.get("evidence_summary", [])
    urls = []
    for block in evidence.values():
        for h in block:
            if h.get("link"):
                urls.append(h["link"])

    company_node_id = upsert_company_node(ticker)
    evidence_node_id = insert_evidence_node(
        ticker=ticker,
        evidence_summary=evidence_summary or strategy.get("reasons", []),
        source_urls=urls[:10]
    )

    store_new_strategy(ticker, strategy, evidence_node_id, company_node_id)
    
    # Step 6: Store numeric snapshot and create audit record
    try:
        # Extract price and metrics from part1_summary
        price = part1_summary.get("price_current")
        valuation_metrics = part1_summary.get("valuation_metrics") or {}
        pe = valuation_metrics.get("pe")
        pb = valuation_metrics.get("pb")
        roe = valuation_metrics.get("roe")
        
        # Find trusted source URL
        source_url = None
        for h in evidence["market_snapshot_hits"]:
            if h.get("is_trusted"):
                source_url = h.get("link")
                break
        
        # Cache numeric snapshot if we have at least price
        if price:
            upsert_numeric_snapshot(ticker, price, pe, pb, roe, source_url)
        
        # Create audit record
        if price:
            create_advice_audit(
                ticker=ticker,
                advice_id=company_node_id,
                decision=strategy.get("decision"),
                price_at_advice=price,
                confidence=strategy.get("confidence", 0),
                portfolio_weight_pct=strategy.get("portfolio_weight_pct"),
                buy_zone=strategy.get("buy_zone"),
                stop_loss=strategy.get("stop_loss"),
                take_profit=strategy.get("take_profit")
            )
    except Exception as e:
        # Don't fail the whole request if audit logging fails
        print(f"Warning: Failed to create audit record: {e}")
    
    # Add metadata about split processing
    strategy["_processing_method"] = "split_dual_groq_only"
    strategy["_part1_summary"] = part1_summary
    strategy["_part2_summary"] = part2_summary
    
    # NEW: Calculate quantitative scores from the analysis (BEFORE formatting report)
    valuation_metrics = part1_summary.get("valuation_metrics", {})
    financial_metrics = part1_summary.get("financial_metrics", {})
    technical_indicators = part1_summary.get("technical_indicators", {})
    legal_governance = part1_summary.get("legal_governance_risks", {})
    
    # Calculate scores
    fundamental_score = calculate_fundamental_score(valuation_metrics, financial_metrics)
    technical_score = calculate_technical_score(
        technical_indicators,
        part1_summary.get("technical_summary", "")
    )
    
    # ⚠️ CRITICAL: Calculate critical risk score (most important for Vietnamese stocks)
    critical_risk_score = calculate_critical_risk_score(
        legal_governance,
        strategy.get("key_risks", [])
    )
    
    # Calculate composite score (critical risk can override other factors)
    composite_score = calculate_composite_score(
        fundamental_score,
        technical_score,
        critical_risk_score
    )
    
    # Calculate expected returns
    price_current = part1_summary.get("price_current", 0)
    price_targets = {
        "short_term": strategy.get("short_term_outlook", {}).get("price_target"),
        "mid_term": strategy.get("mid_term_outlook", {}).get("price_target"),
        "long_term": (strategy.get("long_term_outlook", {}).get("intrinsic_value_range") or [0, 0])[1]
    }
    expected_returns = calculate_expected_return(price_current, price_targets)
    
    # ⚠️ ADJUST DECISION IF CRITICAL RISK DETECTED (but don't completely override)
    if critical_risk_score.get("is_deal_breaker"):
        # Reduce confidence and portfolio weight, but don't force AVOID
        strategy["confidence"] = max(0.3, strategy.get("confidence", 0.5) * 0.6)
        strategy["portfolio_weight_pct"] = max(0, strategy.get("portfolio_weight_pct", 0) * 0.5)
        
        # Change risk level
        if strategy.get("risk_level") != "EXTREMELY_RISKY":
            strategy["risk_level"] = "RISKY" if strategy.get("risk_level") == "MODERATE" else "EXTREMELY_RISKY"
        
        # Add critical risk warning to reasons
        critical_warning = f"⚠️ CRITICAL RISK: {critical_risk_score.get('legal_summary', 'Serious legal/governance issues detected')}"
        if "reasons" in strategy:
            strategy["reasons"].insert(0, critical_warning)
        
        # Add to key risks
        if "key_risks" in strategy and critical_warning not in strategy["key_risks"]:
            strategy["key_risks"].insert(0, critical_warning)
    
    # Add quantitative analysis to strategy
    strategy["quantitative_analysis"] = {
        "fundamental_score": fundamental_score,
        "technical_score": technical_score,
        "critical_risk_score": critical_risk_score,
        "composite_score": composite_score,
        "expected_returns": expected_returns,
        "price_metrics": {
            "current_price": price_current,
            "pe_ratio": valuation_metrics.get("pe"),
            "pb_ratio": valuation_metrics.get("pb"),
            "roe": valuation_metrics.get("roe"),
            "upside_potential_pct": expected_returns.get("weighted_expected_return", 0)
        },
        "risk_assessment": {
            "is_deal_breaker": critical_risk_score.get("is_deal_breaker", False),
            "recommendation": critical_risk_score.get("recommendation"),
            "action": critical_risk_score.get("action")
        }
    }
    
    # Add formatted report for display (AFTER quantitative analysis is added)
    strategy["_formatted_report"] = format_advice_report(strategy, ticker)
    
    return strategy

def update_advice(ticker: str, sector_hint: str = None):
    """
    Update existing advice using split processing.
    """
    latest = get_latest_strategy(ticker)
    if not latest:
        return {"error": "No previous strategy. Use /newadvice first."}

    prev_strategy = latest["strategy_props"]
    
    # Step 1: Collect new evidence
    evidence = _collect_evidence(ticker, sector_hint)
    
    # Step 2: Part 1 - Analyze company changes (Groq Client 1)
    part1_user = UPDATE_PART1_USER.format(
        ticker=ticker,
        previous_strategy=json.dumps(prev_strategy, ensure_ascii=False),
        market_snapshot_hits=json.dumps(evidence["market_snapshot_hits"], ensure_ascii=False),
        company_news_hits=json.dumps(evidence["company_news_hits"], ensure_ascii=False)
    )
    part1_json = chat_json(PART1_SYSTEM, part1_user, client_num=1)
    part1_changes = json.loads(part1_json)
    
    # Step 3: Part 2 - Analyze macro changes (Groq Client 2)
    part2_user = UPDATE_PART2_USER.format(
        ticker=ticker,
        sector=sector_hint or "chung",
        previous_strategy=json.dumps(prev_strategy, ensure_ascii=False),
        macro_news_hits=json.dumps(evidence["macro_news_hits"], ensure_ascii=False)
    )
    part2_json = chat_json(PART2_SYSTEM, part2_user, client_num=2)
    part2_changes = json.loads(part2_json)
    
    # Step 4: Final synthesis of updates (Groq Client 1 - reused)
    synthesis_user = UPDATE_SYNTHESIS_USER.format(
        ticker=ticker,
        previous_strategy=json.dumps(prev_strategy, ensure_ascii=False),
        part1_changes=json.dumps(part1_changes, ensure_ascii=False, indent=2),
        part2_changes=json.dumps(part2_changes, ensure_ascii=False, indent=2)
    )
    final_json = chat_json(SYNTHESIS_SYSTEM, synthesis_user, client_num=1)
    updated = json.loads(final_json)
    
    # Step 5: Merge and store
    new_strategy = {
        "decision": updated.get("action"),
        "risk_level": prev_strategy.get("risk_level"),
        "portfolio_weight_pct": updated.get("new_portfolio_weight_pct", prev_strategy.get("portfolio_weight_pct")),
        "buy_zone": updated.get("new_buy_zone", prev_strategy.get("buy_zone")),
        "stop_loss": updated.get("new_stop_loss", prev_strategy.get("stop_loss")),
        "take_profit": updated.get("new_take_profit", prev_strategy.get("take_profit")),
        "holding_months": updated.get("holding_months", prev_strategy.get("holding_months")),
        "confidence": updated.get("confidence"),
        "key_risks": prev_strategy.get("key_risks", []),
        "reasons": updated.get("why_update", []),
        "evidence_summary": updated.get("new_evidence_summary", []),
        "cycle_change": updated.get("cycle_change", "")
    }

    urls = []
    for block in evidence.values():
        for h in block:
            if h.get("link"):
                urls.append(h["link"])

    company_node_id = upsert_company_node(ticker)
    evidence_node_id = insert_evidence_node(
        ticker=ticker,
        evidence_summary=new_strategy["evidence_summary"] or new_strategy["reasons"],
        source_urls=urls[:10]
    )
    store_new_strategy(ticker, new_strategy, evidence_node_id, company_node_id)
    
    # Add metadata
    new_strategy["_processing_method"] = "split_dual_groq_only_update"
    new_strategy["_part1_changes"] = part1_changes
    new_strategy["_part2_changes"] = part2_changes
    
    # Calculate quantitative scores (similar to new_advice)
    valuation_metrics = part1_changes.get("valuation_metrics", {})
    financial_metrics = part1_changes.get("financial_metrics", {})
    technical_indicators = part1_changes.get("technical_indicators", {})
    legal_governance = part1_changes.get("legal_governance_risks", {})
    
    # Calculate scores
    fundamental_score = calculate_fundamental_score(valuation_metrics, financial_metrics)
    technical_score = calculate_technical_score(
        technical_indicators,
        part1_changes.get("technical_summary", "")
    )
    
    critical_risk_score = calculate_critical_risk_score(
        legal_governance,
        new_strategy.get("key_risks", [])
    )
    
    composite_score = calculate_composite_score(
        fundamental_score,
        technical_score,
        critical_risk_score
    )
    
    # Calculate expected returns
    price_current = part1_changes.get("price_current", 0)
    price_targets = {
        "short_term": new_strategy.get("short_term_outlook", {}).get("price_target"),
        "mid_term": new_strategy.get("mid_term_outlook", {}).get("price_target"),
        "long_term": (new_strategy.get("long_term_outlook", {}).get("intrinsic_value_range") or [0, 0])[1]
    }
    expected_returns = calculate_expected_return(price_current, price_targets)
    
    # Add quantitative analysis to strategy
    new_strategy["quantitative_analysis"] = {
        "fundamental_score": fundamental_score,
        "technical_score": technical_score,
        "critical_risk_score": critical_risk_score,
        "composite_score": composite_score,
        "expected_returns": expected_returns,
        "price_metrics": {
            "current_price": price_current,
            "pe_ratio": valuation_metrics.get("pe"),
            "pb_ratio": valuation_metrics.get("pb"),
            "roe": valuation_metrics.get("roe"),
            "upside_potential_pct": expected_returns.get("weighted_expected_return", 0)
        },
        "risk_assessment": {
            "is_deal_breaker": critical_risk_score.get("is_deal_breaker", False),
            "recommendation": critical_risk_score.get("recommendation"),
            "action": critical_risk_score.get("action")
        }
    }
    
    # Add formatted report for display (AFTER quantitative analysis is added)
    new_strategy["_formatted_report"] = format_advice_report(new_strategy, ticker)

    return new_strategy
