from snowflake import SnowflakeGenerator

gen = None

def init_snowflake(service_config_from_nacos:dict):
    global gen
    snowflake_cfg = service_config_from_nacos.get("snowflake", {})
    worker_id = int(snowflake_cfg.get("work_id", 0))
    gen = SnowflakeGenerator(instance=worker_id)

def get_snowflake_id() -> int:
    return next(gen)