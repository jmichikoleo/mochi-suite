"""Substack RSS recommendation engine."""

import random
import hashlib
from datetime import date

import feedparser


def fetch_substack_feeds(feeds_config: list) -> list:
    """Fetch posts from configured Substack feeds."""
    all_posts = []

    for feed_info in feeds_config:
        try:
            feed = feedparser.parse(feed_info["url"])
            for entry in feed.entries[:5]:
                description = getattr(entry, "summary", getattr(entry, "description", ""))
                # Simple HTML strip
                import re
                description = re.sub(r"<[^>]+>", "", description)
                description = re.sub(r"\s+", " ", description).strip()
                if len(description) > 250:
                    description = description[:250] + "..."

                published = ""
                if hasattr(entry, "published_parsed") and entry.published_parsed:
                    from datetime import datetime
                    try:
                        published = datetime(*entry.published_parsed[:6]).strftime("%Y-%m-%d")
                    except Exception:
                        published = getattr(entry, "published", "")

                all_posts.append({
                    "title": getattr(entry, "title", "Untitled"),
                    "link": getattr(entry, "link", ""),
                    "description": description,
                    "published": published,
                    "source": feed_info["name"],
                    "tags": feed_info.get("tags", []),
                })
        except Exception:
            continue

    return all_posts


def score_post(post: dict, topic_keywords: list) -> float:
    """Score a post based on keyword relevance to interests."""
    text = f"{post['title']} {post['description']}".lower()
    score = 0.0

    for keyword in topic_keywords:
        if keyword.lower() in text:
            score += 1.0

    # Bonus for recency
    if post.get("published"):
        try:
            pub_date = date.fromisoformat(post["published"])
            days_old = (date.today() - pub_date).days
            if days_old <= 1:
                score += 2.0
            elif days_old <= 3:
                score += 1.0
            elif days_old <= 7:
                score += 0.5
        except ValueError:
            pass

    # Tag matching bonus
    for tag in post.get("tags", []):
        if tag.lower() in " ".join(topic_keywords).lower():
            score += 0.5

    return score


def recommend_post(feeds_config: list, topic_keywords: list) -> dict:
    """Recommend one Substack post based on interests.

    Uses a daily rotation seed to avoid recommending the same post
    on consecutive runs within the same day.
    """
    posts = fetch_substack_feeds(feeds_config)

    if not posts:
        return {
            "title": "No Substack posts available",
            "link": "",
            "description": "Check your feed URLs in config/interests.yaml",
            "source": "",
            "score": 0,
        }

    # Score all posts
    scored = [(post, score_post(post, topic_keywords)) for post in posts]
    scored.sort(key=lambda x: x[1], reverse=True)

    # Use date as seed to get consistent daily pick but vary day-to-day
    today_seed = hashlib.md5(date.today().isoformat().encode()).hexdigest()
    random.seed(today_seed)

    # Pick from top 5 to add variety while staying relevant
    top_posts = scored[:5]
    if top_posts:
        chosen, score = random.choice(top_posts)
        chosen["score"] = round(score, 1)
        random.seed()  # Reset seed
        return chosen

    random.seed()
    return scored[0][0] if scored else {"title": "No posts found", "link": "", "description": "", "source": "", "score": 0}


def format_substack_section(post: dict) -> str:
    """Format Substack recommendation into a readable section."""
    lines = []
    lines.append("## Substack Pick of the Day")
    lines.append("")

    if post.get("link"):
        lines.append(f"### {post['title']}")
        lines.append(f"**From**: {post.get('source', 'Unknown')} | **Published**: {post.get('published', 'Unknown')}")
        lines.append(f"**Link**: {post['link']}")
        lines.append("")
        if post.get("description"):
            lines.append(f"> {post['description']}")
        lines.append("")
    else:
        lines.append("No recommendation available today. Check your Substack feed configuration.")
        lines.append("")

    return "\n".join(lines)
