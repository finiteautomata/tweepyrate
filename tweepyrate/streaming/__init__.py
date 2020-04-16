import tweepy
import threading
from queue import Queue
from .tweet_listener import TweetListener

def create_worker(queue, worker_class):
    """
    Creates a non-stop worker to gather tweets

    Arguments:
    ----------

    queue: queue.Queue
        A queue to gather tasks from

    worker_class: class or function returning an object
        The returned object must respond to `work(status, query)`

    Returns:
    --------

    worker: function

        A function to be used to start a working thread
    """
    tweet_worker = worker_class()

    def worker():
        while True:
            args = queue.get(block=True)
            tweet_worker.work(*args)
            queue.task_done()

    return worker

def create_queue(num_workers, worker_class):
    """
    Creates a queue of workers to process incoming tweets for streaming

    Arguments:
    ----------

    num_workers: int
        Number of workers to create

    worker_class: class or function returning an object
        The returned object must respond to `work(status, query)`

    Returns:
    --------

    a_queue: queue.Queue
        Queue to push new statuses to
    """
    queue = Queue()
    threads = []
    for i in range(num_workers):
        t = threading.Thread(target=create_worker(queue, worker_class))
        t.start()
        threads.append(t)

    return queue

def stream_query(query, app, queue, listener_class=TweetListener, **kwargs):
    """

    Start streaming query using app and pushing to some queue

    Arguments:
    ----------

    query: a string
        The words we want to stream

    app: tweepy.app

    queue: queue.Queue
        The queue to push new statuses to

    Other argumentes are passed to the `filter` function of tweepy.Stream

    """
    myStreamListener = listener_class(query, queue)
    myStream = tweepy.Stream(auth = app.auth, listener=myStreamListener)
    myStream.filter(track=[query], is_async=True, **kwargs)
    return myStreamListener
