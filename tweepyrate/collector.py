import time


class Collector:
    def __init__(self, process_tweets, minutes, **kwargs):
        self.process_tweets = process_tweets
        self.args = kwargs
        self.args["count"] = 1000
        self.minutes = minutes
        self.args["tweet_mode"] = "extended"

    def get_query(self):
        query = self.args.copy()

        return query

    def fetch(self, app):
        """
        Fetches new tweets

        Arguments:
        ----------

        app: tweepy App
        """

        query = self.get_query()

        print("Querying {}".format(query))
        new_tweets = app.search(**query)
        self.process_tweets(new_tweets, query)

        return new_tweets


class NewTweetsCollector(Collector):
    """
    Objects of this class are in charge of looking for new tweets for a given
    query
    """
    def __init__(self, process_tweets, since_id=None, **kwargs):
        """Constructor

        Arguments:
        ---------

        """
        super().__init__(process_tweets, **kwargs)
        self.since_id = since_id

    def get_query(self):
        query = super().get_query()

        if self.since_id:
            query["since_id"] = self.since_id

        return query

    def fetch(self, app):
        """
        Fetches new tweets

        Arguments:
        ----------

        app: tweepy App
        """

        new_tweets = super().fetch(app)

        if len(new_tweets) > 0:
            print("{} new tweets".format(len(new_tweets)))
            self.since_id = max(tw.id for tw in new_tweets) + 1
        else:
            # Busy waiting
            msg = "Search exhausted!!! Sleeping for {} minutes".format(
                self.minutes)
            print(msg)
            time.sleep(self.minutes * 60)

        return new_tweets


class PastTweetsCollector(Collector):
    """
    Objects of this class are in charge of looking for new tweets for a given
    query
    """
    def __init__(self, process_tweets, max_id=None, **kwargs):
        """Constructor

        Arguments:
        ---------

        """
        super().__init__(process_tweets, **kwargs)
        self.max_id = max_id

    def get_query(self):
        query = super().get_query()

        if self.max_id:
            query["max_id"] = self.max_id

        return query

    def fetch(self, app):
        """
        Fetches new tweets

        Arguments:
        ----------

        app: tweepy App
        """
        new_tweets = super().fetch(app)

        if len(new_tweets) > 0:
            print("{} new tweets".format(len(new_tweets)))
            self.max_id = min(tw.id for tw in new_tweets) - 1
        else:
            raise StopIteration("No more tweets left!")

        return new_tweets
