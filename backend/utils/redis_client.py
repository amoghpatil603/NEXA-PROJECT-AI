import os
import redis
from rq import Queue

# Initialize Redis connection
REDIS_HOST = os.getenv("REDIS_HOST", "localhost")
REDIS_PORT = int(os.getenv("REDIS_PORT", 6379))
REDIS_DB = int(os.getenv("REDIS_DB", 0))

redis_conn = redis.Redis(
    host=REDIS_HOST,
    port=REDIS_PORT,
    db=REDIS_DB,
    socket_connect_timeout=0.2,
    socket_timeout=0.2
)

# Initialize RQ Queues
task_queue = Queue('nexa_tasks', connection=redis_conn)

def get_redis():
    return redis_conn

def get_queue():
    return task_queue
