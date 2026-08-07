"""Slack webhook delivery for briefings."""

import json
import requests


def send_briefing(webhook_url: str, briefing_md: str, date_str: str) -> bool:
    """Send a briefing to Slack via incoming webhook.

    Converts markdown briefing into Slack Block Kit format.
    """
    if not webhook_url or webhook_url == "YOUR_SLACK_WEBHOOK_URL_HERE":
        print("[Slack] No webhook URL configured. Skipping Slack delivery.")
        return False

    blocks = _markdown_to_blocks(briefing_md, date_str)

    payload = {"blocks": blocks}

    try:
        response = requests.post(
            webhook_url,
            json=payload,
            headers={"Content-Type": "application/json"},
            timeout=10,
        )
        if response.status_code == 200:
            print("[Slack] Briefing sent successfully!")
            return True
        else:
            print(f"[Slack] Failed to send: {response.status_code} {response.text}")
            return False
    except Exception as e:
        print(f"[Slack] Error sending briefing: {e}")
        return False


def _markdown_to_blocks(md: str, date_str: str) -> list:
    """Convert markdown briefing to Slack Block Kit blocks.

    Keeps it simple: headers become header blocks, text becomes section blocks.
    """
    blocks = [
        {
            "type": "header",
            "text": {
                "type": "plain_text",
                "text": f"Mochi's Daily Briefing - {date_str}",
            }
        },
        {"type": "divider"},
    ]

    # Split by ## headers
    sections = md.split("\n## ")

    for section in sections:
        if not section.strip():
            continue

        lines = section.strip().split("\n")
        title = lines[0].replace("## ", "").replace("# ", "").strip()
        body = "\n".join(lines[1:]).strip()

        if title:
            blocks.append({
                "type": "header",
                "text": {
                    "type": "plain_text",
                    "text": title[:150],
                }
            })

        if body:
            # Slack has a 3000 char limit per text block
            chunks = _chunk_text(body, 2900)
            for chunk in chunks:
                blocks.append({
                    "type": "section",
                    "text": {
                        "type": "mrkdwn",
                        "text": _md_to_mrkdwn(chunk),
                    }
                })

        blocks.append({"type": "divider"})

    # Footer
    blocks.append({
        "type": "context",
        "elements": [
            {
                "type": "mrkdwn",
                "text": "Mochi's Assistant | Update your data in `data/` folder | Run `python src/main.py` anytime",
            }
        ]
    })

    return blocks


def _md_to_mrkdwn(text: str) -> str:
    """Convert standard markdown to Slack mrkdwn format."""
    # Slack uses * for bold (not **)
    import re
    text = re.sub(r"\*\*(.+?)\*\*", r"*\1*", text)
    # ### headers become bold lines
    text = re.sub(r"^### (.+)$", r"*\1*", text, flags=re.MULTILINE)
    return text


def _chunk_text(text: str, max_len: int) -> list:
    """Split text into chunks at line boundaries."""
    if len(text) <= max_len:
        return [text]

    chunks = []
    current = ""
    for line in text.split("\n"):
        if len(current) + len(line) + 1 > max_len:
            if current:
                chunks.append(current)
            current = line
        else:
            current = f"{current}\n{line}" if current else line

    if current:
        chunks.append(current)

    return chunks
