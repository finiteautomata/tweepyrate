import tweepy
import json
import time
import random
from tqdm import tqdm
from multiprocessing import Pool
from itertools import cycle
from .collector import NewTweetsCollector, PastTweetsCollector


def create_app(**kwargs):
    auth = tweepy.OAuthHandler(
            consumer_key=kwargs['consumer_key'],
            consumer_secret=kwargs['consumer_secret']
    )
    auth.set_access_token(kwargs['access_token'], kwargs['access_secret'])

    app = tweepy.API(auth)

    app.name = kwargs['username']

    return app


def is_retweet(status):
    return hasattr(status, "retweeted_status")


def create_apps(json_file="config/my_apps.json"):
    with open(json_file) as f:
        app_keys = json.load(f)

    apps = [create_app(**app_key) for app_key in app_keys]
    print("{} apps created".format(len(apps)))
    return apps


class NoAppLeft(Exception):
    pass


def _handle_tweep_error(app, e):
    if e.api_code == 50:
        """User not found => reraise exception"""
        print("Reraising")
        raise e
    elif e.api_code == 63:
        """User suspended => reraise exception"""
        print("Reraising")
        raise e
    else:
        raise e


def _fetch_status(*args):
    # TODO: Fix this. I don't know why I should do this way
    app, tweet_id = args[0]
    backoff = 15
    while True:
        try:
            status = app.get_status(tweet_id, tweet_mode="extended")
            return (tweet_id, status)
        except tweepy.RateLimitError as e:
            print(f"Rate limit -- sleeping for {backoff}s")
            time.sleep(backoff)
            backoff *= 2
        except tweepy.TweepError as e:
            return (tweet_id, e)


def get_user_tweets(app, user_id, **kwargs):
    """
    Fetch all the tweets of a given user
    """
    tweets = []

    new_tweets = app.user_timeline(user_id, tweet_mode="extended", **kwargs)
    while new_tweets:
        tweets += new_tweets
        min_id = min(tw.id for tw in new_tweets)
        new_tweets = app.user_timeline(user_id, max_id=min_id, tweet_mode="extended", **kwargs)

    return tweets

def get_tweets(apps, tweet_ids, tweet_callback, error_callback):
    """
    Fetch tweets using multiple apps in a parallel fashion

    Arguments:
    ----------
    apps: list containing Tweepy apps
        The apps to be used to fetch the tweets

    tweet_ids: list of Tweet ids
        List of ids of tweets to be fetched

    tweet_callback: a callback
        Function receiving tweet_id and response when tweet could be fetched

    error_callback: a callback
        Function receiving tweet_id and response when tweet couldn't be fetched

    Returns:
    --------

    new_tweets, new_errors: pair of integers
        Number of new tweets or errors
    """
    with Pool(len(apps)) as p:
        random.shuffle(tweet_ids)
        iterator = p.imap(
            _fetch_status,
            zip(cycle(apps), tweet_ids)
        )

        # This hack is just to make tqdm work.
        ret = tqdm(iterator, total=len(tweet_ids))

        new_tweets = 0
        new_errors = 0

        for tweet_id, response in ret:
            if type(response) is tweepy.Status:
                tweet_callback(tweet_id, response)
                new_tweets += 1
            elif type(response) is tweepy.TweepError:
                error_callback(tweet_id, response)
                new_errors += 1
            else:
                print(response)
                print(type(response))
                assert False, "Response should be Status or Error"

        return new_tweets, new_errors



def call_for_each_app(apps, func):
    for app in apps:
        try:
            return func(app)
        except tweepy.RateLimitError as e:
            print("{} app exhausted".format(app.name))
            continue
        except tweepy.TweepError as e:
            print("{} app raised another error {}".format(app.name, e))
            _handle_tweep_error(app, e)

    raise NoAppLeft("No app left")


def fetch_tweets(apps, process_tweets, minutes=15, mode='new', **kwargs):
    """
    Fetches using Search API

    Arguments:

    apps: a list of tweepy api's

    process_tweets: callable
        Process batch of (tweets, query)

    minutes: int
        Minutes to sleep when exhausted or limit rate occurs.

    mode: "past" or "new", default: "new"
        Mode in which we should discover tweets: polling for new ones or
        diving into the past.
    """
    print("Search {} with params = {}".format(mode, kwargs))

    if mode == 'new':
        collector = NewTweetsCollector(
            process_tweets, minutes=minutes, **kwargs)
    elif mode == 'past':
        collector = PastTweetsCollector(
            process_tweets, minutes=minutes, **kwargs)
    else:
        raise ValueError("mode {} is not recognised, should be new or past".format(mode))

    print("Starting to collect...")
    while True:
        one_worked = False
        for app in apps:
            try:
                app_user = app.me()
                print("Trying app {}".format(app_user.screen_name))

                while True:
                    # Iteramos hasta que reviente esta app
                    new_tweets = collector.fetch(app)
                    one_worked = True

            except tweepy.TweepError as e:
                print("app {} - {}".format(app_user.screen_name, e))

        if not one_worked:
            print("Sleeping for {} minutes".format(minutes))
            print("="*80)
            print("="*80)

            time.sleep(60 * minutes)
        else:
            print("Trying again")
