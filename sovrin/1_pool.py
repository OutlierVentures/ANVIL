import time
from setup import setup_pool, setup_steward
from onboarding import simple_onboard, onboard_for_proving
from sovrin_utilities import run_coroutine, write_json

async def run():
    pool_name, pool_handle = await setup_pool('ANVIL')
    pool_config = {
        'pool_name': pool_name,
        'pool_handle': pool_handle
    }
    
    steward = await setup_steward(pool_handle = pool_config['pool_handle'],
                                  name = 'Steward',
                                  id_ = 'mocked_steward_id',
                                  key = 'mocked_steward_key',
                                  seed = '000000000000000000000000Steward1')
    
    issuer, steward = await simple_onboard(pool_handle = pool_handle,
                                           anchor = steward,
                                           name = 'issuer',
                                           id_ = 'mocked_issuer_id',
                                           key = 'mocked_issuer_key')

    prover, issuer = await onboard_for_proving(pool_handle = pool_handle,
                                               anchor = issuer,
                                               name = 'prover',
                                               id_ = 'mocked_prover_id',
                                               key = 'mocked_prover_key')

    verifier, steward = await simple_onboard(pool_handle = pool_handle,
                                             anchor = steward,
                                             name = 'verifier',
                                             id_ = 'mocked_verifier_id',
                                             key = 'mocked_verifier_key')
    write_json(pool_config, 'pool_config')
    write_json(steward, 'steward_config')
    write_json(issuer, 'issuer_config')
    write_json(prover, 'prover_config')
    write_json(verifier, 'verifier_config')

if __name__ == '__main__':
    run_coroutine(run)
