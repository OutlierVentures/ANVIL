import time
from setup import setup_pool, setup_steward
from sovrin_utilities import run_coroutine, write_json

async def run():
    pool_name, pool_handle = await setup_pool('ANVIL')
    pool_config = {
        'pool_name': pool_name,
        'pool_handle': pool_handle
    }
    write_json(pool_config, 'pool_config')


if __name__ == '__main__':
    run_coroutine(run)
