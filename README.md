# tweepyrate


A python library which adds some functionalities on top of [`tweepy`](https://github.com/tweepy/tweepy)


## Streaming

`tweepyrate` aids you to avoid getting overwhelmed because of streaming queries that generate a lot of content. For instance, if you try to save tweets inside a `tweepy` listener, chances are high that your connection gets killed by Twitter because it processes them slowly.

To avoid that, we create a queue that just "saves" our tweets, while you can provide another class that does the heavylifting. For instance, let's suppose you want to stream tweets about Messi:

```python
from tweepyrate.streaming import create_queue, stream_query

class TweetWorker:

    def work(self, status, query):
        # Do the heavylifting here: saving to database, preprocess, etc
        print(status["text"])

# Create tweepy app
app = create_app(...)
# Create queue and workers
queue = create_queue(num_workers, TweetWorker)

stream_query("Messi", app, queue)
```
