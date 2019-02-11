'''
Sovrin setup/teardown functions:
1. Pool setup.
2. Steward setup.
3. Actor teardown.
'''

import json
from indy import pool, wallet, did
from indy.error import ErrorCode, IndyError
from config import PROTOCOL_VERSION
from sovrin_utilities import get_pool_genesis_txn_path

async def setup_pool(name = 'ANVIL'):
    print('Setting up pool...')
    pool_ = {'name': name}
    pool_['genesis_txn_path'] = get_pool_genesis_txn_path(pool_['name'])
    pool_['config'] = json.dumps({"genesis_txn": str(pool_['genesis_txn_path'])})
    await pool.set_protocol_version(PROTOCOL_VERSION)
    try:
        await pool.create_pool_ledger_config(pool_['name'], pool_['config'])
    except IndyError as ex:
        if ex.error_code == ErrorCode.PoolLedgerConfigAlreadyExistsError:
            pass
    pool_['handle'] = await pool.open_pool_ledger(pool_['name'], None)
    return pool_['name'], pool_['handle']

async def setup_steward(pool_handle,
                        name = 'Steward',
                        id_ = 'mocked_steward_id',
                        key = 'mocked_steward_key',
                        seed = '000000000000000000000000Steward1'):
    print('Setting up steward...')
    steward = {
        'name': name,
        'wallet_config': json.dumps({'id': id_}),
        'wallet_credentials': json.dumps({'key': key}),
        'pool': pool_handle,
        'seed': seed
    }
    try:
        await wallet.create_wallet(steward['wallet_config'], steward['wallet_credentials'])
    except IndyError as ex:
        if ex.error_code == ErrorCode.WalletAlreadyExistsError:
            pass
    steward['wallet'] = await wallet.open_wallet(steward['wallet_config'], steward['wallet_credentials'])
    # Generate DID from seed
    steward['did_info'] = json.dumps({'seed': steward['seed']})
    steward['did'], steward['key'] = await did.create_and_store_my_did(steward['wallet'], steward['did_info'])
    return steward

async def teardown(pool_name, pool_handle, actor_list = []):
    print('Tearing down connections...')
    for actor in actor_list:
        await wallet.close_wallet(actor['wallet'])
        await wallet.delete_wallet(actor['wallet_config'], actor['wallet_credentials'])
    await pool.close_pool_ledger(pool_handle)
    await pool.delete_pool_ledger_config(pool_name)
    
