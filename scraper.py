import subprocess
from celery import Celery
from celery.schedules import crontab
from celery.utils.log import get_task_logger
import twint

logger = get_task_logger(__name__)

app = Celery(__name__, broker='amqp://admin:mypass@localhost:5672', backend='rpc://',
             include=['scraper'])


@app.task(bind=True, exponential_backoff=2, retry_kwargs={'max_retries': 5}, retry_jitter=True)
def get_user_posts(self, username):
    try:
        subprocess.run(["python", "t2n.py", "usertweets", username], check=True)
    except Exception as exc:
        raise self.retry(exc=exc)


@app.task(bind=True, exponential_backoff=2, retry_kwargs={'max_retries': 5}, retry_jitter=True)
def get_user_info(self, username):
    try:
        subprocess.run(["python", "t2n.py", "userinfo", username], check=True)
    except Exception as exc:
        raise self.retry(exc=exc)


@app.task(bind=True, exponential_backoff=2, retry_kwargs={'max_retries': 5}, retry_jitter=True)
def get_user_follow_graph(self, username):
    try:
        subprocess.run(["python", "t2n.py", "userfollowgraph", username], check=True)
    except Exception as exc:
        raise self.retry(exc=exc)


@app.on_after_finalize.connect
def setup_periodic_tasks(sender, **kwargs):
    users = {'realDonaldTrump'}
    queue = ['realDonaldTrump']
    for i in range(0x100000000):
        user = queue.pop()
        c = twint.Config
        c.User_full = True
        c.Hide_output = True
        c.Store_object = True
        c.Username = user
        twint.run.Following(c)
        for following in c.output.follows_list:
            if following not in users:
                users.add(following)
                queue.append(following)
        twint.run.Followers(c)
        for follower in c.output.follows_list:
            if follower not in users:
                users.add(follower)
                queue.append(follower)
    for user in users:
        sender.add_periodic_task(900.0, get_user_posts.s(user))
        sender.add_periodic_task(900.0, get_user_info.s(user))
        sender.add_periodic_task(3600.0, get_user_follow_graph.s(user))
