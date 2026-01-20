import os, json
from sqlalchemy import create_engine, text
from app.utils.config import DATABASE_URL

engine = create_engine(DATABASE_URL, pool_pre_ping=True, future=True)

def upsert_company_node(ticker: str):
    sql = text("""
    INSERT INTO kg_nodes(node_type, key, label, properties)
    VALUES ('Company', :key, :label, '{}'::jsonb)
    ON CONFLICT (node_type, key) DO UPDATE SET
        updated_at = NOW(), is_active = TRUE
    RETURNING node_id;
    """)
    with engine.begin() as conn:
        return conn.execute(sql, {"key": ticker, "label": ticker}).scalar_one()

def insert_evidence_node(ticker: str, evidence_summary: list, source_urls: list, macro_tags=None, micro_tags=None):
    node_sql = text("""
    INSERT INTO kg_nodes(node_type, key, label, properties)
    VALUES ('Evidence', :key, :label, :props)
    RETURNING node_id;
    """)
    key = f"{ticker}_evidence_{os.urandom(4).hex()}"
    props = {"ticker": ticker, "summary": evidence_summary, "urls": source_urls}

    with engine.begin() as conn:
        evidence_node_id = conn.execute(node_sql, {
            "key": key,
            "label": f"Evidence for {ticker}",
            "props": json.dumps(props)
        }).scalar_one()

        ev_sql = text("""
        INSERT INTO evidence_summaries(
            evidence_node_id, company_ticker, summary_text, source_urls, macro_tags, micro_tags
        ) VALUES (
            :nid, :ticker, :summary, :urls, :macro_tags, :micro_tags
        );
        """)
        conn.execute(ev_sql, {
            "nid": evidence_node_id,
            "ticker": ticker,
            "summary": "\n".join(evidence_summary),
            "urls": source_urls,
            "macro_tags": macro_tags,
            "micro_tags": micro_tags
        })

    return evidence_node_id

def insert_strategy_node(ticker: str, strategy_json: dict):
    node_sql = text("""
    INSERT INTO kg_nodes(node_type, key, label, properties)
    VALUES ('Strategy', :key, :label, :props)
    RETURNING node_id;
    """)
    key = f"{ticker}_{strategy_json.get('decision','NA')}_{os.urandom(4).hex()}"
    with engine.begin() as conn:
        return conn.execute(node_sql, {
            "key": key,
            "label": f"Strategy for {ticker}",
            "props": json.dumps(strategy_json)
        }).scalar_one()

def insert_edge(from_id, to_id, edge_type, props=None):
    sql = text("""
    INSERT INTO kg_edges(from_node_id, to_node_id, edge_type, properties)
    VALUES (:f, :t, :etype, :props);
    """)
    with engine.begin() as conn:
        conn.execute(sql, {
            "f": from_id, "t": to_id,
            "etype": edge_type,
            "props": json.dumps(props or {})
        })

def get_latest_strategy(ticker: str):
    sql = text("""
    SELECT sv.*, n.properties AS strategy_props
    FROM strategy_versions sv
    JOIN kg_nodes n ON n.node_id = sv.strategy_node_id
    WHERE sv.company_ticker = :ticker
    ORDER BY sv.created_at DESC
    LIMIT 1;
    """)
    with engine.connect() as conn:
        row = conn.execute(sql, {"ticker": ticker}).mappings().first()
    return row

def store_new_strategy(ticker: str, strategy_json: dict, evidence_node_id: str, company_node_id: str):
    strategy_node_id = insert_strategy_node(ticker, strategy_json)

    # Link graph
    insert_edge(company_node_id, strategy_node_id, "HAS_STRATEGY")
    insert_edge(strategy_node_id, evidence_node_id, "SUPPORTED_BY")

    # Insert into strategy_versions cache
    sql = text("""
    INSERT INTO strategy_versions(
        company_ticker, strategy_node_id, evidence_node_id, previous_strategy_id,
        decision, risk_level, portfolio_weight_pct,
        buy_zone_low, buy_zone_high,
        stop_loss_low, stop_loss_high,
        take_profit_low, take_profit_high,
        holding_months, confidence
    )
    VALUES (
        :ticker, :snid, :enid, :prev,
        :decision, :risk_level, :w,
        :bzl, :bzh,
        :sll, :slh,
        :tpl, :tph,
        :hm, :conf
    )
    RETURNING strategy_id;
    """)
    prev = None
    latest = get_latest_strategy(ticker)
    if latest:
        prev = latest["strategy_id"]

    with engine.begin() as conn:
        sid = conn.execute(sql, {
            "ticker": ticker,
            "snid": strategy_node_id,
            "enid": evidence_node_id,
            "prev": prev,
            "decision": strategy_json.get("decision"),
            "risk_level": strategy_json.get("risk_level"),
            "w": strategy_json.get("portfolio_weight_pct"),
            "bzl": strategy_json.get("buy_zone", [None, None])[0],
            "bzh": strategy_json.get("buy_zone", [None, None])[1],
            "sll": strategy_json.get("stop_loss", [None, None])[0],
            "slh": strategy_json.get("stop_loss", [None, None])[1],
            "tpl": strategy_json.get("take_profit", [None, None])[0],
            "tph": strategy_json.get("take_profit", [None, None])[1],
            "hm": strategy_json.get("holding_months"),
            "conf": strategy_json.get("confidence")
        }).scalar_one()

    return sid, strategy_node_id
