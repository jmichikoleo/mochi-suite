#!/usr/bin/env python3
"""Mochi's Assistant - Daily Briefing Engine

Run this script to generate and deliver your daily briefing.
Can be run manually or via a scheduled task.

Usage:
    python src/main.py              # Generate briefing + send to Slack
    python src/main.py --no-slack   # Generate briefing, skip Slack
    python src/main.py --print      # Print briefing to terminal only
"""

import sys
import argparse
from pathlib import Path

import yaml


def get_project_root() -> Path:
    """Get the project root directory."""
    return Path(__file__).parent.parent


def load_config(root: Path) -> dict:
    with open(root / "config" / "settings.yaml") as f:
        return yaml.safe_load(f)


def load_interests(root: Path) -> dict:
    with open(root / "config" / "interests.yaml") as f:
        return yaml.safe_load(f)


def main():
    parser = argparse.ArgumentParser(description="Mochi's Assistant - Daily Briefing")
    parser.add_argument("--no-slack", action="store_true", help="Skip Slack delivery")
    parser.add_argument("--print", dest="print_only", action="store_true", help="Print to terminal only")
    parser.add_argument("--mark-read", type=str, help="Mark a paper as read by ArXiv ID")
    args = parser.parse_args()

    root = get_project_root()
    config = load_config(root)
    interests = load_interests(root)

    # Handle paper marking
    if args.mark_read:
        from src.papers import mark_paper_read
        paper_path = str(root / config["paths"]["paper_history"])
        mark_paper_read(paper_path, args.mark_read)
        print(f"Marked paper {args.mark_read} as read.")
        return

    # Generate briefing
    from src.briefing import generate_briefing, save_briefing

    print("Generating Mochi's Daily Briefing...")
    print("=" * 50)

    briefing = generate_briefing(config, interests, str(root))

    # Save to file
    briefings_dir = str(root / config["paths"].get("briefings_dir", "data/briefings"))
    save_briefing(briefing, briefings_dir)

    # Print to terminal
    if args.print_only:
        print(briefing["markdown"])
        return

    # Always print a summary to terminal
    print(briefing["markdown"])
    print("=" * 50)

    # Send to Slack
    if not args.no_slack:
        from src.slack import send_briefing
        webhook_url = config.get("slack", {}).get("webhook_url", "")
        if config.get("slack", {}).get("enabled", True):
            send_briefing(webhook_url, briefing["markdown"], briefing["date"])


if __name__ == "__main__":
    main()
