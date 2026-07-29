# debate_engine/smoke_test_offline.py
"""
Offline smoke test for evidence.py's sentiment-scoring logic.

This does NOT hit Google News — it monkeypatches fetch_company_news /
fetch_sector_news with a handful of realistic sample headlines, so you can
verify the VADER scoring, labeling, and aggregation logic works correctly
*before* worrying about live network access.

Run from the project root:
    python -m debate_engine.smoke_test_offline
"""

from __future__ import annotations
from unittest.mock import patch

SAMPLE_NVDA_ARTICLES = [
    {"title": "Nvidia shares surge as hyperscalers boost AI chip orders", "description": "Major cloud providers raised capex guidance, citing surging demand for GPUs.", "url": "https://example.com/1", "provider": "Reuters", "published_at": ""},
    {"title": "Analysts raise Nvidia price targets ahead of earnings", "description": "Wall Street firms see continued strength in data-center revenue.", "url": "https://example.com/2", "provider": "Bloomberg", "published_at": ""},
    {"title": "Nvidia stock dips slightly after record run", "description": "Shares pulled back modestly following a multi-week rally.", "url": "https://example.com/3", "provider": "CNBC", "published_at": ""},
    {"title": "Cloud provider expands custom AI chip programme", "description": "A major hyperscaler is investing further in in-house silicon for inference workloads.", "url": "https://example.com/4", "provider": "Financial Times", "published_at": ""},
    {"title": "Nvidia partners with major automakers on AI platforms", "description": "New deals extend Nvidia's reach into autonomous driving software.", "url": "https://example.com/5", "provider": "Yahoo Finance", "published_at": ""},
]

SAMPLE_TECH_SECTOR_ARTICLES = [
    {"title": "Tech earnings season kicks off with strong cloud growth", "description": "Several major software firms beat revenue expectations.", "url": "https://example.com/6", "provider": "Reuters", "published_at": ""},
    {"title": "Semiconductor stocks rally on AI demand outlook", "description": "Chipmakers see upgraded guidance across the board.", "url": "https://example.com/7", "provider": "Bloomberg", "published_at": ""},
    {"title": "Regulators scrutinize big tech over AI practices", "description": "New inquiries raise concerns about competitive impact.", "url": "https://example.com/8", "provider": "Guardian", "published_at": ""},
]


def main() -> None:
    with patch("debate_engine.evidence.fetch_company_news", return_value=SAMPLE_NVDA_ARTICLES), \
         patch("debate_engine.evidence.fetch_sector_news", return_value=SAMPLE_TECH_SECTOR_ARTICLES):

        from debate_engine.evidence import get_company_sentiment, get_sector_sentiment

        print("=== Company sentiment (NVDA, sample articles) ===")
        company = get_company_sentiment("NVIDIA Corporation")
        print(f"avg_score   : {company['avg_score']}")
        print(f"std_score   : {company['std_score']}")
        print(f"label       : {company['label']}")
        print(f"n_articles  : {company['n_articles']}")
        print("top_headlines:")
        for h in company["top_headlines"]:
            print(f"  [{h['score']:+.3f}] ({h['provider']}) {h['title']}")

        print("\n=== Sector sentiment (Technology, sample articles) ===")
        sector = get_sector_sentiment("Technology")
        print(f"avg_score   : {sector['avg_score']}")
        print(f"std_score   : {sector['std_score']}")
        print(f"label       : {sector['label']}")
        print(f"n_articles  : {sector['n_articles']}")

        print("\n=== Unknown sector fallback ===")
        unknown = get_sector_sentiment("Not A Real Sector")
        print(unknown)


if __name__ == "__main__":
    main()
