from app.tools.web_search import google_search
from app.utils.config import DEFAULT_NEWS_DAYS, DEFAULT_MACRO_DAYS

def search_company_news(ticker: str, days=DEFAULT_NEWS_DAYS):
    """Search for company-specific news with focus on catalysts, events, and sentiment"""
    queries = [
        f"{ticker} tin tức cổ phiếu {days} ngày gần đây",
        f"{ticker} thông báo quan trọng sự kiện",
        f"{ticker} kết quả kinh doanh mới nhất",
        f"{ticker} M&A đầu tư dự án mới",
        # ⚠️ CRITICAL: Legal & Regulatory Risks
        f"{ticker} bê bối pháp lý tranh chấp",
        f"{ticker} vi phạm pháp luật điều tra",
        f"{ticker} lãnh đạo bị bắt khởi tố",
        f"{ticker} rủi ro pháp lý tố cáo",
        f"{ticker} thanh tra kiểm toán vi phạm",
        f"{ticker} quản trị doanh nghiệp quản trị công ty",
        # Sentiment & Insider Activity
        f"{ticker} nhà đầu tư lớn mua bán",
        f"{ticker} tâm lý thị trường cộng đồng",
        f"{ticker} nội bộ giao dịch cổ phiếu",
        # Dividend & Cashflow
        f"{ticker} lịch sử cổ tức",
        f"{ticker} dòng tiền tự do",
        f"{ticker} chính sách cổ tức kế hoạch"
    ]
    
    hits = []
    for q in queries:
        hits.extend(google_search(q, top_k=3))
    
    return hits

def search_macro_news(sector: str = None, days=DEFAULT_MACRO_DAYS):
    answers = []
    
    if sector:
        queries = [
            # Economic indicators
            f"tin vĩ mô Việt Nam ảnh hưởng ngành {sector} {days} ngày gần đây",
            f"tin vĩ mô Việt Nam lãi suất CPI tỷ giá VNIndex {days} ngày gần đây",
            # Political & policy
            f"{sector} ảnh hưởng chính trị Việt Nam đối với ngành",
            f"{sector} ảnh hưởng chính trị thế giới đối với ngành",
            f"{sector} chính sách đối với ngành",
            f"chính sách mới ảnh hưởng ngành {sector}",
            f"thuế {sector} thay đổi",
            # Market sentiment
            "Thị trường tài chính đang có bong bóng tài chính không",
            f"Ngành {sector} có đang đối mặt với thách thưc gì không?",
            "Chỉ số tham lam sợ hãi của thị trường",
            # Sector rotation & industry analysis
            f"ngành {sector} Việt Nam triển vọng 2025",
            f"ngành {sector} dẫn dắt thị trường",
            f"luân chuyển ngành vào {sector}",
            # Macro-financial linkage
            f"tỷ giá ảnh hưởng {sector}",
            f"lãi suất ảnh hưởng ngành {sector}",
            f"giá dầu ảnh hưởng {sector}"
        ]
    else:
        queries = [
            f"tin vĩ mô Việt Nam lãi suất CPI tỷ giá VNIndex {days} ngày gần đây",
            "Thị trường tài chính đang có bong bóng tài chính không",
            "Chỉ số tham lam sợ hãi của thị trường",
            "ngành nào dẫn dắt thị trường Việt Nam",
            "luân chuyển ngành chứng khoán Việt Nam",
            "lãi suất tỷ giá ảnh hưởng chứng khoán Việt Nam"
        ]
    
    for q in queries:
        ans = google_search(q, top_k=3)
        answers.append(ans)
    
    return answers
