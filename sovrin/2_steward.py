from sovrin_utilities import run_coroutine, read_json, write_json
from setup import setup_steward

async def run():
    pool_config = read_json('pool_config')
    steward = await setup_steward(pool_handle = pool_config['pool_handle'],
                                  name = 'Steward',
                                  id_ = 'mocked_steward_id',
                                  key = 'mocked_steward_key',
                                  seed = '000000000000000000000000Steward1')
    write_json(steward, 'steward_config')

if __name__ == '__main__':
    run_coroutine(run)
