#!/usr/bin/env python3
"""
MochisHub morning brief — standalone, serverless edition.

Assembles the *public-data* half of the MochisHub brief (weather, your stocks,
a forex rate, Substack posts, arXiv papers), optionally has GPT phrase it warmly,
and POSTs it to a Discord channel webhook. Designed to run on GitHub Actions cron,
so the brief arrives every morning regardless of whether the Mac is on.

Stdlib only — no pip install needed. Each data source is wrapped in try/except so
one flaky API never kills the whole brief.

Env:
  DISCORD_WEBHOOK_URL  (required to actually post; if unset, prints a dry run)
  OPENAI_API_KEY       (optional; if set, GPT phrases the brief, else a template)
"""

import os
import json
import urllib.request
import urllib.parse
import xml.etree.ElementTree as ET
from datetime import datetime
from email.utils import parsedate_to_datetime
from zoneinfo import ZoneInfo

HERE = os.path.dirname(os.path.abspath(__file__))

WMO = {
    0: "Clear sky", 1: "Mainly clear", 2: "Partly cloudy", 3: "Overcast",
    45: "Foggy", 48: "Foggy", 51: "Light drizzle", 53: "Drizzle", 55: "Dense drizzle",
    61: "Light rain", 63: "Rain", 65: "Heavy rain", 71: "Light snow", 73: "Snow",
    75: "Heavy snow", 80: "Rain showers", 81: "Heavy showers", 82: "Violent showers",
    95: "Thunderstorm", 96: "Thunderstorm w/ hail", 99: "Thunderstorm w/ hail",
}
RAIN_CODES = {51, 53, 55, 61, 63, 65, 80, 81, 82, 95, 96, 99}


def load_config():
    with open(os.path.join(HERE, "config.json")) as f:
        return json.load(f)


def http_get(url, headers=None, timeout=25):
    req = urllib.request.Request(url, headers=headers or {"User-Agent": "MochisHubBrief/1.0"})
    with urllib.request.urlopen(req, timeout=timeout) as r:
        return r.read()


def http_get_json(url, headers=None):
    return json.loads(http_get(url, headers))


# ---- data sources -----------------------------------------------------------

def fetch_weather(cfg):
    loc, tz = cfg["location"], cfg.get("timezone", "UTC")
    url = (
        "https://api.open-meteo.com/v1/forecast"
        f"?latitude={loc['latitude']}&longitude={loc['longitude']}"
        "&current=temperature_2m,weather_code,relative_humidity_2m"
        "&daily=temperature_2m_max,temperature_2m_min,precipitation_probability_max,weather_code"
        f"&timezone={urllib.parse.quote(tz)}&forecast_days=1"
    )
    d = http_get_json(url)
    cur, day = d["current"], d["daily"]
    code = day["weather_code"][0]
    precip = day["precipitation_probability_max"][0]
    return {
        "temp": round(cur["temperature_2m"]),
        "max": round(day["temperature_2m_max"][0]),
        "min": round(day["temperature_2m_min"][0]),
        "precip": precip,
        "cond": WMO.get(code, "—"),
        "rainy": (code in RAIN_CODES) or (precip >= 50),
    }


def fetch_stock(symbol, label):
    url = (
        "https://query1.finance.yahoo.com/v8/finance/chart/"
        f"{urllib.parse.quote(symbol)}?range=5d&interval=1d"
    )
    d = http_get_json(url, headers={"User-Agent": "Mozilla/5.0"})
    meta = d["chart"]["result"][0]["meta"]
    price = meta["regularMarketPrice"]
    prev = meta.get("chartPreviousClose") or 0
    pct = ((price - prev) / prev * 100) if prev else 0.0
    return {"label": label, "price": price, "currency": meta.get("currency", ""), "pct": pct}


def fetch_forex(base, quote):
    d = http_get_json(f"https://open.er-api.com/v6/latest/{base}")
    if d.get("result") != "success":
        return None
    rate = d.get("rates", {}).get(quote)
    return {"base": base, "quote": quote, "rate": rate} if rate else None


def _localname(tag):
    return tag.split("}")[-1]


def _parse_date(s):
    if not s:
        return None
    try:
        return parsedate_to_datetime(s)               # RFC 822 (RSS)
    except Exception:
        pass
    try:
        return datetime.fromisoformat(s.replace("Z", "+00:00"))  # ISO 8601 (Atom)
    except Exception:
        return None


def parse_feed(data):
    posts = []
    root = ET.fromstring(data)
    for item in root.iter():
        if _localname(item.tag) not in ("item", "entry"):
            continue
        title, link, date = "", "", ""
        for c in item:
            ln = _localname(c.tag)
            if ln == "title":
                title = (c.text or "").strip()
            elif ln == "link":
                href = c.get("href")
                if href and not link:
                    link = href
                elif c.text and not link:
                    link = c.text.strip()
            elif ln in ("pubDate", "published", "updated", "date"):
                if not date:
                    date = (c.text or "").strip()
        posts.append({"title": " ".join(title.split()), "link": link, "dt": _parse_date(date)})
    return posts


def fetch_substacks(feeds, limit=3):
    posts = []
    for url in feeds:
        try:
            data = http_get(url, headers={
                "User-Agent": "MochisHubBrief/1.0",
                "Accept": "application/rss+xml,application/atom+xml,application/xml,text/xml",
            })
            posts += parse_feed(data)
        except Exception:
            continue
    posts.sort(key=lambda p: (p["dt"] is not None, p["dt"] or datetime.min.replace(tzinfo=ZoneInfo("UTC"))), reverse=True)
    return posts[:limit]


def fetch_arxiv(query, mx):
    if not query.strip():
        return []
    low = query.lower()
    has_field = any(p in low for p in ("cat:", "all:", "ti:", "au:", "abs:"))
    sq = query if has_field else f"all:{query}"
    url = (
        "https://export.arxiv.org/api/query"
        f"?search_query={urllib.parse.quote(sq)}"
        f"&sortBy=submittedDate&sortOrder=descending&max_results={mx}"
    )
    return parse_feed(http_get(url))[:mx]


# ---- compose ----------------------------------------------------------------

def build_facts(cfg):
    facts = []
    name = cfg.get("name", "")
    now_local = datetime.now(ZoneInfo(cfg.get("timezone", "UTC")))
    if name:
        facts.append(f"User's name: {name}")
    facts.append(f"Today is {now_local.strftime('%A, %B %d')} in {cfg['location']['name']}.")

    try:
        w = fetch_weather(cfg)
        facts.append(
            f"Weather: {w['cond']}; now {w['temp']}°C, high {w['max']}° / low {w['min']}°, "
            f"rain chance {w['precip']}%." + (" RAIN LIKELY — remind to bring an umbrella." if w["rainy"] else "")
        )
    except Exception as e:
        print("weather failed:", e)

    quotes = []
    for s in cfg.get("stocks", []):
        try:
            quotes.append(fetch_stock(s["symbol"], s["label"]))
        except Exception as e:
            print("stock failed:", s, e)
    if quotes:
        lines = "\n".join(
            "  - {arrow} {label}: {price:.2f} {cur} ({sign}{pct:.2f}%)".format(
                arrow="▲" if q["pct"] >= 0 else "▼", label=q["label"], price=q["price"],
                cur=q["currency"], sign="+" if q["pct"] >= 0 else "-", pct=abs(q["pct"]))
            for q in quotes
        )
        facts.append("Markets vs yesterday's close:\n" + lines)

    try:
        fx = fetch_forex(cfg["forex"]["base"], cfg["forex"]["quote"])
        if fx:
            r = fx["rate"]
            facts.append(f"Forex {fx['base']}→{fx['quote']}: {r:.0f}" if r >= 100 else f"Forex {fx['base']}→{fx['quote']}: {r:.4f}")
    except Exception as e:
        print("forex failed:", e)

    try:
        posts = fetch_substacks(cfg.get("substackFeeds", []), limit=3)
        if posts:
            lines = "\n".join(f"  - {p['title']} {p['link']}" for p in posts)
            facts.append("Recent Substack posts they might like:\n" + lines)
    except Exception as e:
        print("substack failed:", e)

    try:
        papers = fetch_arxiv(cfg.get("arxivQuery", ""), cfg.get("arxivMax", 4))
        if papers:
            lines = "\n".join(f"  - {p['title']} {p['link']}" for p in papers[:3])
            facts.append("New arXiv papers in their research areas (AI/LLM/RAG):\n" + lines)
    except Exception as e:
        print("arxiv failed:", e)

    return facts, name


SYSTEM = (
    "You are MochisHub's morning-brief assistant. Using ONLY the facts below, write a warm, "
    "concise good-morning message. Greet by name if given. If rain is likely, remind them to "
    "bring an umbrella. Give each stock's move and the forex rate as one short line. Briefly "
    "recommend the Substack posts and arXiv papers (1-3 each, why interesting) and KEEP their "
    "links. Use Discord markdown and a few tasteful emoji, under 1500 characters. The user is "
    "comfortable in Korean and English, so a little Korean warmth (e.g. 출근, 화이팅) is welcome. "
    "Never invent facts that aren't given."
)


def gpt(system, user):
    key = os.environ.get("OPENAI_API_KEY")
    if not key:
        return None
    payload = json.dumps({
        "model": "gpt-4o-mini",
        "messages": [{"role": "system", "content": system}, {"role": "user", "content": user}],
        "max_tokens": 700,
    }).encode()
    req = urllib.request.Request(
        "https://api.openai.com/v1/chat/completions", data=payload,
        headers={"Content-Type": "application/json", "Authorization": f"Bearer {key}"},
    )
    try:
        with urllib.request.urlopen(req, timeout=60) as r:
            d = json.loads(r.read())
        return d["choices"][0]["message"]["content"].strip()
    except Exception as e:
        print("gpt failed, using template:", e)
        return None


def template(name, facts):
    hi = "Good morning! ☀️" if not name else f"Good morning, {name}! ☀️"
    return "\n".join([hi, ""] + facts)


def chunks(s, n):
    return [s[i:i + n] for i in range(0, len(s), n)] or [s]


def post_discord(webhook, content):
    # Discord (behind Cloudflare) 403s the default Python-urllib UA — send a real one.
    headers = {
        "Content-Type": "application/json",
        "User-Agent": "MochisHubBrief/1.0 (+https://github.com/jmichikoleo/mochishub-brief)",
    }
    for chunk in chunks(content, 1990):
        payload = json.dumps({"content": chunk}).encode()
        req = urllib.request.Request(webhook, data=payload, headers=headers)
        with urllib.request.urlopen(req, timeout=30) as r:
            r.read()


def main():
    cfg = load_config()
    facts, name = build_facts(cfg)
    fact_text = "\n".join(facts)
    content = gpt(SYSTEM, fact_text) or template(name, facts)

    # Secrets pasted into GitHub often carry a trailing newline / stray spaces,
    # which makes urllib raise "unknown url type". Strip before using.
    webhook = (os.environ.get("DISCORD_WEBHOOK_URL") or "").strip()
    if not webhook:
        print("[dry run — set DISCORD_WEBHOOK_URL to actually post]\n")
        print(content)
        return
    if not webhook.startswith(("http://", "https://")):
        raise SystemExit(
            "DISCORD_WEBHOOK_URL is set but is not a valid URL "
            "(must start with https://). Re-add the secret — it likely "
            "lost its scheme or has hidden whitespace."
        )
    post_discord(webhook, content)
    print("Brief posted.")


if __name__ == "__main__":
    main()
