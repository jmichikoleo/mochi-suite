# Mochi's Assistant - Daily Briefing Engine

A personal daily briefing bot that delivers a comprehensive dashboard every morning at 6am KST.

## What's Included

- **Smart Task Prioritization** - Eisenhower matrix scoring with energy-aware ordering
- **Habit & Behavior Intelligence** - Streak tracking, completion rates, and correlations with sleep/focus
- **Personal Metrics** - Sleep, focus, and spending analysis with trends
- **AI Paper Recommendations** - 2 daily ArXiv papers on LLM routing & AI, with research connection mapping
- **Substack Pick** - Daily recommendation from curated feeds (self-help, productivity, essays, mindset)
- **News Summaries** - Political + finance news (Korean, Indonesian, American markets)
- **Focus Plan** - 3-block daily plan (morning/afternoon/evening) adjusted by sleep quality

## Quick Start

```bash
# Install dependencies
python3 -m pip install -r requirements.txt

# Run a briefing now
python3 -m src.main --no-slack

# Run with Slack delivery
python3 -m src.main
```

## Setup Slack Delivery

1. Go to [api.slack.com/apps](https://api.slack.com/apps) and click **Create New App**
2. Choose **From scratch**, name it "Mochi's Assistant", select your workspace
3. In the left sidebar, click **Incoming Webhooks**
4. Toggle **Activate Incoming Webhooks** to On
5. Click **Add New Webhook to Workspace**
6. Select the channel or DM where you want briefings delivered
7. Copy the webhook URL
8. Paste it in `config/settings.yaml` under `slack.webhook_url`

## Data Files

Edit these JSON files in `data/` to customize your briefing:

| File | Purpose |
|------|---------|
| `tasks.json` | Your tasks, deadlines, and reminders |
| `habits.json` | Habits you're tracking with daily completion history |
| `metrics.json` | Daily sleep hours, focus score (1-10), spending by category |
| `paper_history.json` | Auto-managed: tracks papers read and recommendations |

## Mark a Paper as Read

```bash
python3 -m src.main --mark-read 2604.01221v1
```

## Commands

```bash
python3 -m src.main              # Full briefing + Slack
python3 -m src.main --no-slack   # Briefing without Slack
python3 -m src.main --print      # Terminal output only
python3 -m src.main --mark-read <arxiv_id>  # Track a paper as read
```

## Customization

- **Add Substack feeds**: Edit `config/interests.yaml` under `substack.feeds`
- **Change research topics**: Edit `config/interests.yaml` under `research`
- **Add news sources**: Edit `config/settings.yaml` under `news`
- **Adjust paper search**: Edit `config/settings.yaml` under `papers.search_queries`
