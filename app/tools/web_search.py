import requests
import time
from app.utils.config import SERPAPI_API_KEY, TAVILY_API_KEY, DEFAULT_TOP_K

SERP_ENDPOINT = "https://serpapi.com/search"
TAVILY_ENDPOINT = "https://api.tavily.com/search"

# Trusted sources for numeric facts (financials, valuations, prices)
TRUSTED_NUMERIC_SOURCES = {
    "cafef.vn",
    "vietstock.vn", 
    "tcbs.com.vn",
    "hsx.vn",  # HOSE
    "hnx.vn",  # HNX
    "cophieu68.vn",
    "fireant.vn",
    "investing.com",
    "vneconomy.vn",
    "stockbiz.vn"
}

def is_trusted_numeric_source(url: str) -> bool:
    """Check if URL is from a trusted source for numeric data"""
    if not url:
        return False
    url_lower = url.lower()
    return any(domain in url_lower for domain in TRUSTED_NUMERIC_SOURCES)

def _search_with_serpapi(query: str, top_k: int, gl: str, hl: str) -> list:
    """Search using SerpAPI (Google)"""
    if not SERPAPI_API_KEY:
        return None
    
    try:
        params = {
            "engine": "google",
            "q": query,
            "api_key": SERPAPI_API_KEY,
            "num": top_k * 2,  # Fetch extra for filtering
            "gl": gl,
            "hl": hl
        }
        r = requests.get(SERP_ENDPOINT, params=params, timeout=30)
        r.raise_for_status()
        data = r.json()
        
        # Check for rate limit or quota errors
        if "error" in data:
            print(f"⚠️ SerpAPI error: {data.get('error')}")
            return None
        
        results = []
        for item in data.get("organic_results", []):
            link = item.get("link")
            results.append({
                "title": item.get("title"),
                "link": link,
                "snippet": item.get("snippet"),
                "source": item.get("source"),
                "is_trusted": is_trusted_numeric_source(link),
                "search_engine": "serpapi"
            })
        
        return results
        
    except requests.exceptions.HTTPError as e:
        if e.response.status_code == 429:
            print("⚠️ SerpAPI rate limit exceeded")
        else:
            print(f"⚠️ SerpAPI HTTP error: {e}")
        return None
    except Exception as e:
        print(f"⚠️ SerpAPI error: {e}")
        return None

def _search_with_tavily(query: str, top_k: int) -> list:
    """Search using Tavily API"""
    if not TAVILY_API_KEY:
        return None
    
    try:
        payload = {
            "api_key": TAVILY_API_KEY,
            "query": query,
            "max_results": top_k * 2,  # Fetch extra for filtering
            "include_raw_content": False,
            "include_images": False
        }
        r = requests.post(TAVILY_ENDPOINT, json=payload, timeout=30)
        r.raise_for_status()
        data = r.json()
        
        # Check for errors
        if "error" in data:
            print(f"⚠️ Tavily error: {data.get('error')}")
            return None
        
        results = []
        for item in data.get("results", []):
            link = item.get("url")
            results.append({
                "title": item.get("title"),
                "link": link,
                "snippet": item.get("content", ""),
                "source": item.get("url", "").split("/")[2] if link else "",
                "is_trusted": is_trusted_numeric_source(link),
                "search_engine": "tavily"
            })
        
        return results
        
    except requests.exceptions.HTTPError as e:
        if e.response.status_code == 429:
            print("⚠️ Tavily rate limit exceeded")
        else:
            print(f"⚠️ Tavily HTTP error: {e}")
        return None
    except Exception as e:
        print(f"⚠️ Tavily error: {e}")
        return None

def google_search(query: str, top_k: int = DEFAULT_TOP_K, gl="vn", hl="vi", require_trusted_numeric: bool = False):
    """
    Multi-provider search with automatic fallback.
    Priority: SerpAPI → Tavily → (future: more providers)
    
    Returns list of {title, link, snippet, source, is_trusted, search_engine}
    
    Args:
        query: Search query
        top_k: Number of results to return
        gl: Geographic location
        hl: Language
        require_trusted_numeric: If True, only return results from trusted numeric sources
    """
    
    # Try providers in order of priority
    providers = [
        ("SerpAPI", lambda: _search_with_serpapi(query, top_k, gl, hl)),
        ("Tavily", lambda: _search_with_tavily(query, top_k)),
    ]
    
    results = None
    successful_provider = None
    
    for provider_name, search_func in providers:
        try:
            results = search_func()
            if results is not None:
                successful_provider = provider_name
                break
        except Exception as e:
            print(f"⚠️ {provider_name} failed: {e}")
            continue
    
    # If all providers failed
    if results is None:
        raise RuntimeError("All search providers failed or exhausted. Check API keys and quotas.")
    
    # Filter for trusted sources if required
    if require_trusted_numeric:
        results = [r for r in results if r.get("is_trusted", False)]
    
    # Limit to top_k results
    results = results[:top_k]
    
    # Log which provider was used
    if results and successful_provider:
        query_preview = (query or "")[:50]
        print(f"🔍 Search via {successful_provider}: {len(results)} results for '{query_preview}...'")
    
    return results
