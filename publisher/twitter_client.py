import tweepy
import os
from config import Config


class TwitterPublisher:
    def __init__(self):
        auth = tweepy.OAuth1UserHandler(
            Config.TWITTER_API_KEY,
            Config.TWITTER_API_SECRET,
            Config.TWITTER_ACCESS_TOKEN,
            Config.TWITTER_ACCESS_TOKEN_SECRET,
        )
        self.api_v1 = tweepy.API(auth)
        self.client = tweepy.Client(
            consumer_key=Config.TWITTER_API_KEY,
            consumer_secret=Config.TWITTER_API_SECRET,
            access_token=Config.TWITTER_ACCESS_TOKEN,
            access_token_secret=Config.TWITTER_ACCESS_TOKEN_SECRET,
        )

    def post_thread(
        self, tweets: list[str], image_path: str | None = None
    ) -> str:
        """Posts thread, returns first tweet ID."""
        media_id = None
        if image_path and os.path.exists(image_path):
            media = self.api_v1.media_upload(filename=image_path)
            media_id = media.media_id

        first_kwargs = {}
        if media_id:
            first_kwargs["media_ids"] = [media_id]

        first_tweet = self.client.create_tweet(
            text=tweets[0], **first_kwargs
        )
        first_id = first_tweet.data["id"]
        prev_id = first_id

        for tweet_text in tweets[1:]:
            reply = self.client.create_tweet(
                text=tweet_text, in_reply_to_tweet_id=prev_id
            )
            prev_id = reply.data["id"]

        return first_id

    def delete_tweet(self, tweet_id: str):
        self.client.delete_tweet(tweet_id)
