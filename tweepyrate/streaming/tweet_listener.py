import tweepy

class TweetListener(tweepy.StreamListener):
    """
    Listener of Twitter Streaming API

    This class does not do any real time processing. It just pushes the
    received status to the respective queue, so another processes do the heavy lifting

    We do this to avoid being overwhelmed by the stream. See this link for further information:

    https://github.com/tweepy/tweepy/issues/448
    """
    def __init__(self, query, queue):
        self.query = query
        self.queue = queue
        self.count = 0
        super().__init__()

    def on_status(self, status):
        self.queue.put((status, self.query))
        self.count += 1
        if self.count % 100 == 0:
            print(f"{self.count / 1000:.2f} tweets for {self.query}")

    def on_error(self, status_code):
        print(f"Error tipo: {status_code} para query {self.query}")
        print("We have to wait...")
        return True
