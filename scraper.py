import datetime

from celery import Celery
from celery.utils.log import get_task_logger

logger = get_task_logger(__name__)

app = Celery(__name__, broker='amqp://admin:mypass@rabbit:5672', backend='rpc://',
             include=['scraper'])


@app.task(bind=True, exponential_backoff=2, retry_kwargs={'max_retries': 5}, retry_jitter=True)
def get_user_posts(self, username):
    try:
        logger.info(username)
    except Exception as exc:
        raise self.retry(exc=exc)


@app.on_after_configure.connect
def setup_periodic_tasks(sender, **kwargs):
    users = ['realDonaldTrump', 'aghossey']
    for user in users:
        sender.add_periodic_task(
            120.0,
            get_user_posts.s(user),
        )
