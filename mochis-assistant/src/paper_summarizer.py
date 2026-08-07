"""Paper summarizer using OpenAI GPT API."""

import json
import uuid
from datetime import date
from pathlib import Path

import requests
from bs4 import BeautifulSoup


def load_summaries(data_path: str) -> dict:
    path = Path(data_path)
    if not path.exists():
        return {"summaries": []}
    with open(path) as f:
        return json.load(f)


def save_summaries(data_path: str, data: dict):
    with open(data_path, "w") as f:
        json.dump(data, f, indent=2)


def fetch_paper_text(url: str) -> str:
    """Fetch paper abstract and details from an arXiv or paper URL."""
    try:
        headers = {"User-Agent": "Mozilla/5.0 (compatible; MochiBot/1.0)"}
        r = requests.get(url, headers=headers, timeout=15)
        soup = BeautifulSoup(r.text, "html.parser")

        # Try arXiv abstract page
        abstract_tag = soup.find("blockquote", class_="abstract")
        if abstract_tag:
            title = soup.find("h1", class_="title")
            title_text = title.get_text().replace("Title:", "").strip() if title else ""
            abstract_text = abstract_tag.get_text().replace("Abstract:", "").strip()
            return f"Title: {title_text}\n\nAbstract: {abstract_text}"

        # Fallback: try og:description and page text
        og_desc = soup.find("meta", property="og:description")
        og_title = soup.find("meta", property="og:title")
        title = og_title["content"] if og_title and og_title.get("content") else ""
        desc = og_desc["content"] if og_desc and og_desc.get("content") else ""

        # Get main text content
        body_text = ""
        for tag in soup.find_all(["p", "section"]):
            body_text += tag.get_text() + "\n"
            if len(body_text) > 3000:
                break

        return f"Title: {title}\n\nDescription: {desc}\n\nContent: {body_text[:3000]}"
    except Exception as e:
        return f"Could not fetch paper: {e}"


def summarize_paper(paper_text: str, api_key: str, model: str = "gpt-4o-mini") -> dict:
    """Call OpenAI API to generate structured summary."""
    try:
        from openai import OpenAI
        client = OpenAI(api_key=api_key)

        prompt = f"""Summarize this academic paper in the following structured format. Be concise but thorough.

Paper content:
{paper_text[:4000]}

Respond in this exact JSON format:
{{
  "title": "Paper title",
  "problem": "What problem does this paper address? (1-2 sentences)",
  "idea": "What is the core idea/approach? (2-3 sentences)",
  "setup": {{
    "dataset": "What datasets were used?",
    "metrics": "What evaluation metrics?",
    "baselines": "What baselines were compared against?"
  }},
  "results": "Key results and findings (2-3 sentences)",
  "weakness": "Potential weaknesses or limitations (1-2 sentences)",
  "tags": ["tag1", "tag2", "tag3"]
}}

Return ONLY valid JSON, no markdown fences."""

        response = client.chat.completions.create(
            model=model,
            messages=[{"role": "user", "content": prompt}],
            temperature=0.3,
            max_tokens=1000,
        )

        result_text = response.choices[0].message.content.strip()
        # Clean potential markdown fences
        if result_text.startswith("```"):
            result_text = result_text.split("\n", 1)[1]
            if result_text.endswith("```"):
                result_text = result_text[:-3]

        return json.loads(result_text)
    except Exception as e:
        return {
            "title": "Error summarizing paper",
            "problem": str(e),
            "idea": "", "setup": {"dataset": "", "metrics": "", "baselines": ""},
            "results": "", "weakness": "", "tags": []
        }


def save_summary(data_path: str, source_url: str, summary: dict) -> str:
    data = load_summaries(data_path)
    sid = str(uuid.uuid4())[:8]
    entry = {
        "id": sid,
        "date": date.today().isoformat(),
        "source_url": source_url,
        **summary,
    }
    data["summaries"].insert(0, entry)
    save_summaries(data_path, data)
    return sid


def delete_summary(data_path: str, summary_id: str) -> bool:
    data = load_summaries(data_path)
    original = len(data["summaries"])
    data["summaries"] = [s for s in data["summaries"] if s.get("id") != summary_id]
    if len(data["summaries"]) < original:
        save_summaries(data_path, data)
        return True
    return False
