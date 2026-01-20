import json
from app.tools.market_search import search_market_snapshot
from app.tools.news_search import search_company_news, search_macro_news
from app.agent.llm_client import chat_json
from app.agent.prompts import (
    NEWADVICE_SYSTEM, NEWADVICE_USER,
    UPDATEADVICE_SYSTEM, UPDATEADVICE_USER
)
from app.memory.hipporag_store import (
    upsert_company_node, insert_evidence_node,
    store_new_strategy, get_latest_strategy
)

def _collect_evidence(ticker: str, sector_hint: str = None):
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
    evidence = _collect_evidence(ticker, sector_hint)

    user_prompt = NEWADVICE_USER.format(
        ticker=ticker,
        market_snapshot_hits=json.dumps(evidence["market_snapshot_hits"], ensure_ascii=False),
        company_news_hits=json.dumps(evidence["company_news_hits"], ensure_ascii=False),
        macro_news_hits=json.dumps(evidence["macro_news_hits"], ensure_ascii=False),
    )

    raw_json = chat_json(NEWADVICE_SYSTEM, user_prompt)
    strategy = json.loads(raw_json)

    # Build evidence summary + urls for memory
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
    return strategy

def update_advice(ticker: str, sector_hint: str = None):
    latest = get_latest_strategy(ticker)
    if not latest:
        return {"error": "No previous strategy. Use /newadvice first."}

    prev_strategy = latest["strategy_props"]
    prev_evidence_summary = prev_strategy.get("evidence_summary", prev_strategy.get("reasons", []))

    evidence = _collect_evidence(ticker, sector_hint)

    user_prompt = UPDATEADVICE_USER.format(
        ticker=ticker,
        previous_strategy=json.dumps(prev_strategy, ensure_ascii=False),
        previous_evidence_summary=json.dumps(prev_evidence_summary, ensure_ascii=False),
        market_snapshot_hits=json.dumps(evidence["market_snapshot_hits"], ensure_ascii=False),
        company_news_hits=json.dumps(evidence["company_news_hits"], ensure_ascii=False),
        macro_news_hits=json.dumps(evidence["macro_news_hits"], ensure_ascii=False),
    )

    raw_json = chat_json(UPDATEADVICE_SYSTEM, user_prompt)
    updated = json.loads(raw_json)

    # Merge for storage: keep final strategy format consistent
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
        "evidence_summary": updated.get("new_evidence_summary", [])
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

    return new_strategy
