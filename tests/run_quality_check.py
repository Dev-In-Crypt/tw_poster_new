import asyncio
import sys
import os
sys.path.insert(0, "/app")

from generator.thread_generator import ThreadGenerator

TOPIC = "Why Bitcoin ETFs changed crypto forever"
STYLE = "educational"
NUM_TWEETS = 7

async def main():
    gen = ThreadGenerator()
    print(f"Generating thread: '{TOPIC}' / {STYLE} / {NUM_TWEETS} tweets\n")

    tweets = await gen.generate_thread(
        topic=TOPIC, style=STYLE, num_tweets=NUM_TWEETS, recent_topics=[]
    )

    print(f"{'#':<3} {'CHARS':<6} {'OK':<4} TWEET")
    print("-" * 80)

    all_ok = True
    for i, t in enumerate(tweets, 1):
        length = len(t)
        ok = length <= 250
        flag = "✅" if ok else "❌"
        if not ok:
            all_ok = False
        print(f"{i:<3} {length:<6} {flag}  {t}")
        print()

    print("-" * 80)
    print(f"Total tweets: {len(tweets)}")
    print(f"All under 250 chars: {'YES ✅' if all_ok else 'NO ❌'}")
    over = [len(t) for t in tweets if len(t) > 250]
    if over:
        print(f"Over-length: {over}")

asyncio.run(main())
