"""Political and finance news aggregation via RSS feeds."""

import feedparser
from datetime import datetime, date


def fetch_feed(url: str, max_items: int = 5) -> list:
    """Fetch and parse an RSS feed, returning top items."""
    try:
        feed = feedparser.parse(url)
        items = []
        for entry in feed.entries[:max_items]:
            published = ""
            if hasattr(entry, "published_parsed") and entry.published_parsed:
                try:
                    published = datetime(*entry.published_parsed[:6]).strftime("%Y-%m-%d %H:%M")
                except Exception:
                    published = getattr(entry, "published", "")

            description = getattr(entry, "summary", getattr(entry, "description", ""))
            # Clean HTML tags from description
            description = _strip_html(description)
            if len(description) > 200:
                description = description[:200] + "..."

            items.append({
                "title": getattr(entry, "title", "Untitled"),
                "link": getattr(entry, "link", ""),
                "description": description,
                "published": published,
            })
        return items
    except Exception as e:
        return [{"title": f"Feed unavailable: {url}", "link": "", "description": str(e), "published": ""}]


def _strip_html(text: str) -> str:
    """Simple HTML tag stripper."""
    import re
    clean = re.sub(r"<[^>]+>", "", text)
    clean = re.sub(r"\s+", " ", clean).strip()
    return clean


def fetch_all_news(news_config: dict) -> dict:
    """Fetch all configured news feeds.

    Args:
        news_config: The 'news' section from settings.yaml
    """
    results = {
        "political": [],
        "finance": {
            "korean": [],
            "indonesian": [],
            "american": [],
        },
    }

    # Political news
    for feed_config in news_config.get("political", []):
        items = fetch_feed(feed_config["url"], max_items=3)
        for item in items:
            item["source"] = feed_config["name"]
        results["political"].extend(items)

    # Finance news by region
    finance = news_config.get("finance", {})
    for region in ["korean", "indonesian", "american"]:
        for feed_config in finance.get(region, []):
            items = fetch_feed(feed_config["url"], max_items=3)
            for item in items:
                item["source"] = feed_config["name"]
            results["finance"][region].extend(items)

    return results


def format_news_section(news_data: dict) -> str:
    """Format news into a readable briefing section."""
    lines = []

    # Political news
    lines.append("## Political News")
    lines.append("")
    if news_data["political"]:
        for item in news_data["political"][:5]:
            lines.append(f"- **{item['title']}** ({item['source']})")
            if item["description"]:
                lines.append(f"  {item['description']}")
            if item["link"]:
                lines.append(f"  [Read more]({item['link']})")
        lines.append("")
    else:
        lines.append("No political news available.\n")

    # Finance news
    lines.append("## Finance News")
    lines.append("")

    region_labels = {
        "korean": "Korean Finance",
        "indonesian": "Indonesian Finance",
        "american": "American Finance",
    }

    for region, label in region_labels.items():
        items = news_data["finance"].get(region, [])
        lines.append(f"### {label}")
        if items:
            for item in items[:3]:
                lines.append(f"- **{item['title']}** ({item['source']})")
                if item["description"]:
                    lines.append(f"  {item['description']}")
                if item["link"]:
                    lines.append(f"  [Read more]({item['link']})")
        else:
            lines.append("No news available.")
        lines.append("")

    return "\n".join(lines)
