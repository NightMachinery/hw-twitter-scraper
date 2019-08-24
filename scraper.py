import subprocess
from celery import Celery
from celery.utils.log import get_task_logger

logger = get_task_logger(__name__)

app = Celery(__name__, broker='amqp://admin:mypass@rabbit:5672', backend='rpc://',
             include=['scraper'])


@app.task(bind=True, exponential_backoff=2, retry_kwargs={'max_retries': 5}, retry_jitter=True)
def get_user_posts(self, username):
    try:
        subprocess.run(["python", "t2n.py", "usertweets", username])
    except Exception as exc:
        raise self.retry(exc=exc)


@app.task(bind=True, exponential_backoff=2, retry_kwargs={'max_retries': 5}, retry_jitter=True)
def get_user_info(self, username):
    try:
        subprocess.run(["python", "t2n.py", "userinfo", username])
    except Exception as exc:
        raise self.retry(exc=exc)


@app.task(bind=True, exponential_backoff=2, retry_kwargs={'max_retries': 5}, retry_jitter=True)
def get_user_follow_graph(self, username):
    try:
        subprocess.run(["python", "t2n.py", "userfollowgraph", username])
    except Exception as exc:
        raise self.retry(exc=exc)


@app.on_after_finalize.connect
def setup_periodic_tasks(sender, **kwargs):
    users = ['realDonaldTrump', 'aghossey']
    for user in users:
        sender.add_periodic_task(
            60.0,
            get_user_posts.s(user),
        )
        sender.add_periodic_task(
            120.0,
            get_user_info.s(user),
        )
        sender.add_periodic_task(
            120.0,
            get_user_follow_graph.s(user),
        )
