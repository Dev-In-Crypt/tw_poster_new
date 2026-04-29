# Twitter Thread Bot

A Dockerized Python bot that generates AI-powered Twitter/X threads on Crypto/Web3 and Tech/AI topics, attaches an AI-generated cover image to the first tweet, and posts the full thread automatically. Managed via a private Telegram bot.

## Features

- Generates 5–10 tweet threads via OpenRouter (any LLM)
- Three writing styles: Educational, Hot Take, News Breakdown
- AI cover image for first tweet (DALL-E 3 or Replicate)
- Auto topic selection with deduplication (no repeated topics)
- Cron-based scheduler — posts at configured times daily
- Full Telegram bot interface: manual post, queue, schedule, history
- SQLite storage — thread history + topic deduplication
- Single Docker container, zero external dependencies

## Stack

| Layer | Tech |
|---|---|
| Language | Python 3.12 |
| Telegram bot | python-telegram-bot 21 |
| Twitter posting | tweepy 4 (API v2, Free tier) |
| LLM | OpenRouter (Claude / Gemini / any) |
| Image gen | DALL-E 3 (pluggable: Replicate) |
| HTTP client | httpx |
| Scheduler | APScheduler |
| Storage | SQLite3 |
| Container | Docker + docker-compose |

## Quick Start

### 1. Clone

```bash
git clone https://github.com/Dev-In-Crypt/tw_poster_new.git
cd tw_poster_new
```

### 2. Configure

```bash
cp .env.example .env
# Fill in all tokens (see below)
```

### 3. Run

```bash
docker compose up -d
```

## Environment Variables

| Variable | Description |
|---|---|
| `TELEGRAM_BOT_TOKEN` | From [@BotFather](https://t.me/BotFather) |
| `TELEGRAM_ADMIN_ID` | Your Telegram user ID ([@userinfobot](https://t.me/userinfobot)) |
| `TWITTER_API_KEY` | Twitter Developer App key |
| `TWITTER_API_SECRET` | Twitter Developer App secret |
| `TWITTER_ACCESS_TOKEN` | Twitter access token |
| `TWITTER_ACCESS_TOKEN_SECRET` | Twitter access token secret |
| `OPENROUTER_API_KEY` | [openrouter.ai](https://openrouter.ai) API key |
| `OPENROUTER_MODEL` | Model ID (default: `anthropic/claude-sonnet-4-20250514`) |
| `IMAGE_PROVIDER` | `openai` (default) or `replicate` |
| `OPENAI_API_KEY` | OpenAI key for DALL-E 3 |
| `DEFAULT_POST_HOUR` | Scheduled post hour UTC (default: `10`) |
| `DEFAULT_POST_MINUTE` | Scheduled post minute (default: `0`) |
| `TIMEZONE` | Scheduler timezone (default: `UTC`) |

## Telegram Commands

| Command / Button | Action |
|---|---|
| `/start`, `/menu` | Main menu |
| `/post` | Manual post — enter topic → choose style |
| 🚀 Post Now | Auto topic + instant post |
| 📋 Queue | View draft threads |
| ⏰ Schedule | View active schedule |
| 📊 History | Last 10 posted topics |

## Project Structure

```
├── main.py                 — entry point
├── pipeline.py             — orchestrator: generate → image → post
├── config.py               — env config
├── bot/
│   ├── handlers.py         — Telegram command handlers
│   └── keyboards.py        — inline keyboards
├── generator/
│   ├── thread_generator.py — OpenRouter thread generation
│   ├── image_generator.py  — DALL-E / Replicate (pluggable)
│   └── prompts.py          — prompt templates
├── publisher/
│   └── twitter_client.py   — tweepy thread posting
├── scheduler/
│   └── scheduler.py        — APScheduler cron jobs
├── storage/
│   ├── database.py         — SQLite operations
│   └── migrations.py       — table creation
├── tests/
│   └── test_storage.py
└── data/
    └── topics.json         — seed topic list
```

## Twitter Free Tier Limits

| Limit | Value |
|---|---|
| Tweets per month | 1,500 |
| At 7 tweets/thread | ~214 threads/month |
| At 1 thread/day | Well within limit |

## License

MIT
