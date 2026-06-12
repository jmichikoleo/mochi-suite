# MochisHub Brief (serverless)

A free, always-on morning brief that posts to a Discord channel every day — independent
of your Mac. It assembles the **public** half of the MochisHub brief (weather, your stocks,
a forex rate, Substack posts, arXiv papers), optionally has GPT phrase it warmly, and posts
to a Discord **webhook**. Runs on GitHub Actions cron. Stdlib Python only — no dependencies.

> It can't see your private MochisHub data (tasks/habits/schedule) — that still lives in
> your iCloud account and needs the Mac app. This guarantees the *public* brief always arrives.

## Setup (≈5 minutes)

1. **Create a Discord webhook** for the channel you want the brief in:
   Discord → that channel → ⚙️ Edit Channel → **Integrations → Webhooks → New Webhook → Copy Webhook URL**.

2. **Put this folder on GitHub**: create a new repo and push these files (see commands below).

3. **Add repository secrets** (GitHub repo → Settings → Secrets and variables → **Actions** → New repository secret):
   - `DISCORD_WEBHOOK_URL` — the webhook URL from step 1 (**required**).
   - `OPENAI_API_KEY` — your OpenAI key (**optional**; without it you get a clean plain-text brief instead of a GPT-phrased one).

4. **Edit `config.json`** to taste — your name, location, stock tickers, forex pair, Substack
   feed URLs, and the arXiv query. (Defaults match your MochisHub: Jakarta, IHSG, KRW→IDR, AI/LLM/RAG.)

5. **Test it now**: repo → **Actions** tab → *Morning Brief* → **Run workflow**. Check the channel.

## Schedule

Edit the cron in `.github/workflows/brief.yml`. GitHub cron is **UTC**:

| You want (local) | Cron (UTC) |
|---|---|
| 07:30 Asia/Jakarta (UTC+7) | `30 0 * * *`  ← current |
| 08:00 Asia/Jakarta | `0 1 * * *` |
| 07:00 Asia/Seoul (UTC+9) | `0 22 * * *` |

GitHub may delay scheduled runs by a few minutes under load — fine for a morning brief.

## Run locally (dry run)

```bash
python3 brief.py                      # prints the brief, doesn't post
DISCORD_WEBHOOK_URL=... python3 brief.py   # actually posts
```

## Push to GitHub

```bash
cd ~/Developer/mochishub-brief
git init && git add -A && git commit -m "MochisHub serverless brief"
gh repo create mochishub-brief --private --source=. --push   # or create on github.com and: git remote add origin <url> && git push -u origin main
```
