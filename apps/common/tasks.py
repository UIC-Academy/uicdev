import time

from celery import shared_task


@shared_task
def test_task():
    time.sleep(3)
    print("Task finished")
    return True
