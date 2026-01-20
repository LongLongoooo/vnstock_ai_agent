from app.tools.web_search import google_search

def search_market_snapshot(ticker: str):
    """
    Live web snapshot for price, PE, PB, ROE, sector context, technical analysis, and multi-timeframe data.
    Uses trusted sources for numeric/financial data.
    """
    # Queries that need trusted numeric sources (price, valuations, financials)
    numeric_queries = [
        f"{ticker} giá cổ phiếu hôm nay",
        f"{ticker} P/E P/B ROE CafeF",
        f"{ticker} báo cáo tài chính quý gần nhất",
        f"{ticker} báo cáo tài chính tháng gần nhất",
        f"{ticker} nợ xấu, nợ phải trả trong quý và năm",
        f"{ticker} tăng trưởng doanh thu lợi nhuận",
        f"{ticker} tỷ suất cổ tức lịch sử",
        f"{ticker} dòng tiền hoạt động đầu tư",
        f"{ticker} so sánh định giá cùng ngành",
    ]
    
    # General queries (broader sources OK)
    general_queries = [
        f"{ticker} ngành kinh doanh chính",
        f"{ticker} thay đổi nhân sự gần nhất",
        f"{ticker} đánh giá sức khỏe công ty hiện tại",
        f"{ticker} đỉnh và đáy của mã trong vòng 4 năm",
        f"{ticker} phân tích kỹ thuật RSI MACD",
        f"{ticker} hỗ trợ kháng cự",
        f"{ticker} khối lượng giao dịch xu hướng",
        f"{ticker} đối thủ cạnh tranh thị phần",
        f"{ticker} lợi thế cạnh tranh",
        f"{ticker} triển vọng tương lai dự án mới",
        f"{ticker} rủi ro thách thức",
        f"{ticker} vị thế cạnh tranh thị trường",
        f"{ticker} thị phần so với đối thủ"
    ]

    hits = []
    
    # Search numeric queries with trusted source filter
    for q in numeric_queries:
        hits.extend(google_search(q, top_k=3, require_trusted_numeric=True))
    
    # Search general queries without filter
    for q in general_queries:
        hits.extend(google_search(q, top_k=3))

    return hits
