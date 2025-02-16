import tweepy
import pandas as pd
from textblob import TextBlob
import config
import logging
from datetime import datetime, timedelta

class TwitterAnalyzer:
    def __init__(self):
        # Initialize Twitter API v2
        self.client = tweepy.Client(
            bearer_token=config.TWITTER_BEARER_TOKEN,
            consumer_key=config.TWITTER_API_KEY,
            consumer_secret=config.TWITTER_API_SECRET,
            access_token=config.TWITTER_ACCESS_TOKEN,
            access_token_secret=config.TWITTER_ACCESS_SECRET
        )
        
        # Dictionary mapping coins to their related keywords and accounts
        self.coin_keywords = {
            'DOGE': {
                'keywords': ['#dogecoin', '$DOGE', 'doge coin'],
                'key_accounts': ['elonmusk', 'dogecoin'],
            },
            'SHIB': {
                'keywords': ['#SHIB', '$SHIB', 'shiba inu', '#SHIBARMY'],
                'key_accounts': ['Shibtoken', 'ShytoshiKusama'],
            },
            # Add more coins and their related terms
        }

    def get_sentiment_score(self, text):
        """Calculate sentiment score for a tweet"""
        analysis = TextBlob(text)
        return analysis.sentiment.polarity

    def analyze_coin(self, coin_symbol, hours_back=24):
        """Analyze Twitter data for a specific coin"""
        keywords = self.coin_keywords[coin_symbol]['keywords']
        key_accounts = self.coin_keywords[coin_symbol]['key_accounts']
        
        start_time = datetime.utcnow() - timedelta(hours=hours_back)
        
        analysis_results = {
            'tweet_volume': 0,
            'avg_sentiment': 0,
            'influencer_mentions': 0,
            'viral_tweets': 0,
            'sentiment_scores': [],
            'key_mentions': []
        }

        try:
            # Search tweets containing keywords
            for keyword in keywords:
                tweets = self.client.search_recent_tweets(
                    query=f"{keyword} -is:retweet",
                    start_time=start_time,
                    max_results=100,
                    tweet_fields=['public_metrics', 'created_at']
                )
                
                if tweets.data:
                    for tweet in tweets.data:
                        # Calculate metrics
                        sentiment = self.get_sentiment_score(tweet.text)
                        analysis_results['sentiment_scores'].append(sentiment)
                        
                        # Track viral tweets (>1000 likes or retweets)
                        metrics = tweet.public_metrics
                        if metrics['like_count'] > 1000 or metrics['retweet_count'] > 1000:
                            analysis_results['viral_tweets'] += 1
                            analysis_results['key_mentions'].append({
                                'text': tweet.text,
                                'metrics': metrics,
                                'sentiment': sentiment
                            })

            # Get tweets from key accounts
            for account in key_accounts:
                user = self.client.get_user(username=account)
                if user.data:
                    tweets = self.client.get_users_tweets(
                        user.data.id,
                        start_time=start_time,
                        tweet_fields=['public_metrics', 'created_at']
                    )
                    if tweets.data:
                        analysis_results['influencer_mentions'] += len(tweets.data)

            # Calculate averages and totals
            analysis_results['tweet_volume'] = len(analysis_results['sentiment_scores'])
            if analysis_results['sentiment_scores']:
                analysis_results['avg_sentiment'] = sum(analysis_results['sentiment_scores']) / len(analysis_results['sentiment_scores'])

            return analysis_results

        except Exception as e:
            logging.error(f"Error analyzing Twitter data for {coin_symbol}: {str(e)}")
            return None

    def generate_trading_signal(self, analysis_results):
        """Generate trading signal based on Twitter analysis"""
        if not analysis_results:
            return None

        signal = {
            'action': None,
            'strength': 0,
            'reason': []
        }

        # Example signal generation logic
        if analysis_results['avg_sentiment'] > 0.2:
            signal['strength'] += 1
            signal['reason'].append('High positive sentiment')

        if analysis_results['viral_tweets'] >= 3:
            signal['strength'] += 1
            signal['reason'].append('Multiple viral tweets')

        if analysis_results['influencer_mentions'] >= 2:
            signal['strength'] += 1
            signal['reason'].append('Key influencer activity')

        if analysis_results['tweet_volume'] > 1000:
            signal['strength'] += 1
            signal['reason'].append('High tweet volume')

        # Determine action based on signal strength
        if signal['strength'] >= 3:
            signal['action'] = 'buy'
        elif signal['strength'] <= -2:
            signal['action'] = 'sell'

        return signal 