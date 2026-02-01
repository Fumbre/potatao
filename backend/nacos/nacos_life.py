# nacos_life.py
from contextlib import asynccontextmanager
from fastapi import FastAPI
import asyncio

# Core system resources
from nacos.nacos_client import Nacosclient
from utils.config_load import load_local_config, get_local_ip
from utils.redisUtils import RedisClient
from database.database_config import init_db, SessionLocal
from utils.snowflake_id_util import init_snowflake

_initialized_bloom = False

service_config: dict = {}
service_config_from_nacos: dict = {}
nacos_client: Nacosclient | None = None
redis_client: RedisClient | None = None

# Custom lifespan to manage system resources
@asynccontextmanager
async def lifespan(app: FastAPI, service_name: str):
    global service_config, service_config_from_nacos, nacos_client, redis_client

    # Load local application configuration
    nacosConfig = load_local_config(service_name)
    service_config["service_name"] = nacosConfig["app"]["name"]
    service_config["ip"] = get_local_ip()
    service_config["port"] = nacosConfig["server"]["port"]

    # Register service in Nacos
    nacos_client = Nacosclient(nacosConfig)
    await nacos_client.register_service(service_config)
    app.state.nacos_client = nacos_client

    # Fetch configuration from Nacos
    init_conf = await nacos_client.get_config()
    service_config_from_nacos.update(init_conf)

    # Initialize Redis if configured
    if service_config_from_nacos.get("redis") is not None:
        redis_client = RedisClient(service_config_from_nacos)
        app.state.redis_client = redis_client

    # Initialize database if configured
    if service_config_from_nacos.get("database") is not None:
        init_db(service_config_from_nacos["database"])

    # Start background task to listen for configuration changes
    asyncio.create_task(nacos_client.listen_config(listen_change))

    # Start asynchronous Bloom filter initialization (decoupled business logic)
    asyncio.create_task(safe_bloom_init())

    # Initialize Snowflake ID if configured
    if service_config_from_nacos.get("snowflake") is not None:
        init_snowflake(service_config_from_nacos)

    print(f"[Lifespan] {service_name} system started")
    yield

    # Shutdown logic
    if SessionLocal:
        SessionLocal().bind.dispose()
    await nacos_client.deregister_service(service_config)
    print(f"[Lifespan] {service_name} system closed")


# Asynchronous task wrapper to safely run init_bloom
async def safe_bloom_init():
    try:
        await init_bloom()
    except Exception as e:
        print(f"[Bloom Init] failed: {e}")


# Bloom filter initialization (decoupled business logic)
async def init_bloom():
    """
    Initialize Bloom filter with user data from DB.
    Fully safe: checks Redis client and method existence.
    """
    global _initialized_bloom, redis_client, service_config

    if _initialized_bloom:
        print("[Bloom Init] Already initialized, skipping")
        return
    _initialized_bloom = True

    # Check if Redis client is available
    if redis_client is None:
        print("[Bloom Init] Redis client not initialized, skipping Bloom filter")
        return

    # Check if Redis client has async method 'abloom_add'
    if not hasattr(redis_client, "abloom_add") or not callable(getattr(redis_client, "abloom_add", None)):
        print("[Bloom Init] Redis client has no callable 'abloom_add', skipping Bloom filter")
        return

    # Delayed import to avoid circular dependency
    try:
        from sso.service import user_service 
        print(user_service.selectUserList_async)
    except ImportError as e:
        print(f"[Bloom Init] Failed to import sso_service: {e}")
        return

    # Fetch users from DB
    try:
        user_list = await user_service.selectUserList_async()
    except Exception as e:
        print(f"[Bloom Init] Failed to fetch users from DB: {e}")
        return

    if not user_list:
        print("[Bloom Init] No users found in DB, skipping Bloom filter")
        return

    print(f"[Bloom Init] Loaded {len(user_list)} users from DB")

    # Add users to Bloom filter
    for user in user_list:
        try:
            await redis_client.abloom_add("bf:sso:username", user.username)
            await redis_client.abloom_add("bf:sso:email", user.email)
            # await redis_client.abloom_add("bf:sso:phone", user.phone)
        except Exception as e:
            print(f"[Bloom Init] Failed for user {user.username}: {e}")

    print("[Bloom Init] Completed successfully")


# Nacos configuration change listener
async def listen_change(new_config: dict):
    global service_config_from_nacos, redis_client
    service_config_from_nacos.clear()
    service_config_from_nacos.update(new_config)

    if service_config_from_nacos.get("redis") is not None:
        await redis_client.refresh(service_config_from_nacos)

    if service_config_from_nacos.get("database") is not None:
        if SessionLocal:
            init_db(service_config_from_nacos["database"])

    print("[Nacos] config updated:", service_config_from_nacos)

def service_match(path: str) -> str | None:
    routes = service_config_from_nacos.get("route", [])
    for service in routes:
        route_path = str(service.get("path", ""))
        if route_path.endswith("*"):
            prefix = route_path[:-1]
            if path.startswith(prefix):
                return service.get("service")
        elif route_path == path:
            return service.get("service")
    return None
