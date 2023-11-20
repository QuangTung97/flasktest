import redis
from memproxy import CacheClient, RedisClient
from memproxy.proxy import ServerStats, ReplicatedRoute, ProxyCacheClient


def init_cache_client() -> CacheClient:
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
