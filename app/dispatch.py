import os

import redis


class DispatchQueue:
    @property
    def brokered(self):
        return False

    def publish(self, case_id: str):
        return None

    def consume(self, timeout_seconds: int = 1):
        return None


class RedisDispatchQueue(DispatchQueue):
    def __init__(self):
        self.client = redis.Redis.from_url(
            os.getenv("REDIS_URL", "redis://localhost:6379/0"),
            decode_responses=True,
        )
        self.queue = os.getenv("REDIS_QUEUE_NAME", "intelligent-automation:execution")

    @property
    def brokered(self):
        return True

    def publish(self, case_id: str):
        self.client.rpush(self.queue, case_id)

    def consume(self, timeout_seconds: int = 1):
        result = self.client.blpop(self.queue, timeout=timeout_seconds)
        return result[1] if result else None


def get_dispatch_queue():
    if os.getenv("DISPATCH_BACKEND", "database").lower() == "redis":
        return RedisDispatchQueue()
    return DispatchQueue()
