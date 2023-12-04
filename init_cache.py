from threading import Lock
from typing import Optional, Any

import redis
from flask import g
from memproxy import CacheClient, RedisClient, Pipeline
from memproxy.proxy import ServerStats, ReplicatedRoute, ProxyCacheClient
from prometheus_client import Counter


def _init_cache_client() -> CacheClient:
    opts = {
        'socket_timeout': 1,
        'socket_connect_timeout': 1,
        'retry_on_timeout': 1,
    }

    redis_client1 = redis.Redis(**opts)  # type: ignore
    redis_client2 = redis.Redis(port=6380, **opts)  # type: ignore

    servers = [21, 22]

    clients = {
        21: redis_client1,
        22: redis_client2,
    }

    def new_client(server_id: int) -> CacheClient:
        return RedisClient(r=clients[server_id])

    stats = ServerStats(clients=clients, sleep_min=100, sleep_max=200)

    route = ReplicatedRoute(
        server_ids=servers,
        stats=stats,
    )

    return ProxyCacheClient(
        server_ids=servers,
        new_func=new_client,
        route=route,
    )


cache_info_counter = Counter(
    name='cache_info', documentation='',
    labelnames=['cls', 'type'],
)

_cache_client: Optional[CacheClient] = None
_cache_mutex = Lock()


def _get_client() -> CacheClient:
    global _cache_client

    if _cache_client is not None:
        return _cache_client

    with _cache_mutex:
        # double-checked locking
        if _cache_client is not None:
            return _cache_client

        _cache_client = _init_cache_client()
        return _cache_client


PIPE_KEY = 'cache_pipeline'


def get_pipeline() -> Pipeline:
    if PIPE_KEY not in g:
        g.cache_pipeline = _get_client().pipeline()
    return g.cache_pipeline


STATS_KEY = 'stats'


def add_item_stats(class_name: str, stat: Any):
    if STATS_KEY not in g:
        g.stats = {}
    s = g.stats
    s[class_name] = stat


def cleanup_caching() -> None:
    stats = g.pop(STATS_KEY, None)
    if stats is not None:
        print("UPDATE STATS=======")
        for cls, st in stats.items():
            cache_info_counter.labels(cls, 'hit').inc(st.hit_count)
            if st.fill_count > 0:
                cache_info_counter.labels(cls, 'fill').inc(st.fill_count)
            cache_info_counter.labels(cls, 'bytes_read').inc(st.bytes_read)

    pipe: Optional[Pipeline] = g.pop(PIPE_KEY, None)
    if pipe is not None:
        print("FINISH PIPE=======")
        pipe.finish()
