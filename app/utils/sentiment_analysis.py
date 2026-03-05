import matplotlib
matplotlib.use('Agg')  # non-interactive backend — safe for server use
import matplotlib.pyplot as plt


def analyze_source_reliability(evidence: dict) -> dict:
    """
    Count trusted vs non-trusted source articles across all evidence blocks.

    Parameters
    ----------
    evidence : dict with keys market_snapshot_hits, company_news_hits, macro_news_hits.
               Each value is a list of hit dicts that include an 'is_trusted' boolean
               set by web_search.is_trusted_numeric_source().

    Returns
    -------
    {
        "trusted":     int,
        "non_trusted": int,
        "by_category": {
            "market_snapshot": {"trusted": int, "non_trusted": int},
            "company_news":    {"trusted": int, "non_trusted": int},
            "macro_news":      {"trusted": int, "non_trusted": int},
        }
    }
    """
    label_map = {
        "market_snapshot_hits": "market_snapshot",
        "company_news_hits":    "company_news",
        "macro_news_hits":      "macro_news",
    }

    totals: dict = {"trusted": 0, "non_trusted": 0, "by_category": {}}

    for key, label in label_map.items():
        hits = evidence.get(key, [])
        cat: dict = {"trusted": 0, "non_trusted": 0}
        for h in hits:
            if h.get("is_trusted"):
                cat["trusted"] += 1
                totals["trusted"] += 1
            else:
                cat["non_trusted"] += 1
                totals["non_trusted"] += 1
        totals["by_category"][label] = cat

    return totals


def generate_source_chart(reliability: dict, ticker: str = "") -> str:
    """
    Draw a two-panel figure:
      Left  - stacked bar chart: trusted vs non-trusted articles per category.
      Right - overall pie chart of the split.

    Saves to  static/source_chart_{TICKER}.png  and returns that path.
    """
    by_category   = reliability.get("by_category", {})
    total_trusted = reliability.get("trusted", 0)
    total_non     = reliability.get("non_trusted", 0)
    total         = total_trusted + total_non

    label_display = {
        "market_snapshot": "Market\nData",
        "company_news":    "Company\nNews",
        "macro_news":      "Macro\nNews",
    }

    categories   = list(by_category.keys())
    cat_labels   = [label_display.get(c, c) for c in categories]
    trusted_vals = [by_category[c]["trusted"]     for c in categories]
    non_vals     = [by_category[c]["non_trusted"] for c in categories]

    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(13, 6))
    title_sfx = f" — {ticker}" if ticker else ""

    # Left: stacked bar
    x = list(range(len(categories)))
    ax1.bar(x, trusted_vals, label="Trusted",      color="#4CAF50")
    ax1.bar(x, non_vals,     label="Non-trusted",  color="#F44336",
            bottom=trusted_vals)
    ax1.set_xticks(x)
    ax1.set_xticklabels(cat_labels, fontsize=10)
    ax1.set_ylabel("Article Count", fontsize=10)
    ax1.set_title(f"Source Coverage by Category{title_sfx}", fontweight="bold")
    ax1.legend(fontsize=9)

    for i, (t, n) in enumerate(zip(trusted_vals, non_vals)):
        if t > 0:
            ax1.text(i, t / 2,     str(t), ha="center", va="center",
                     color="white", fontweight="bold", fontsize=9)
        if n > 0:
            ax1.text(i, t + n / 2, str(n), ha="center", va="center",
                     color="white", fontweight="bold", fontsize=9)

    # Right: overall pie
    if total > 0:
        sizes  = [total_trusted, total_non]
        labels = [f"Trusted\n({total_trusted})", f"Non-trusted\n({total_non})"]
        ax2.pie(sizes, labels=labels, colors=["#4CAF50", "#F44336"],
                autopct="%1.1f%%", startangle=90)
    else:
        ax2.text(0.5, 0.5, "No data", ha="center", va="center",
                 transform=ax2.transAxes)
    ax2.set_title(f"Overall Source Reliability{title_sfx}", fontweight="bold")

    plt.tight_layout()
    filename = (f"static/source_chart_{ticker.upper()}.png"
                if ticker else "static/source_chart.png")
    plt.savefig(filename, dpi=100, bbox_inches="tight")
    plt.close()
    return filename
