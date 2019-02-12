'''
Sovrin setup/teardown functions:

1. Pool setup.
2. Set self up: establish dictionary data structure, create and open wallet.
3. Actor teardown.
'''

import json, argparse
from indy import pool, wallet, did
from indy.error import ErrorCode, IndyError
from utilities import get_pool_genesis_txn_path
parser = argparse.ArgumentParser(description='Run python getting-started scenario (Prover/Issuer)')
parser.add_argument('-t', '--storage_type', help='load custom wallet storage plug-in')
parser.add_argument('-l', '--library', help='dynamic library to load for plug-in')
parser.add_argument('-e', '--entrypoint', help='entry point for dynamic library')
parser.add_argument('-c', '--config', help='entry point for dynamic library')
parser.add_argument('-s', '--creds', help='entry point for dynamic library')
args = parser.parse_args()


PROTOCOL_VERSION = 2


async def setup_pool(name = 'ANVIL'):
    print('Setting up pool...')
    pool_ = {
        'name': name
    }
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


# Set self up: establish dictionary data structure, create and open wallet.
# If initialised from seed, create and store DID on the spot (for Steward Anchors).
async def set_self_up(name, id_, key, pool_handle, seed = None):
    print('Setting up ' + name + '...')
    actor = {
        'name': name,
        'wallet_config': json.dumps({'id': id_}),
        'wallet_credentials': json.dumps({'key': key}),
        'pool': pool_handle,
        'role': 'TRUST_ANCHOR' # Do not change role for individualised connections to work.
    }
    try:
        await wallet.create_wallet(wallet_config("create", actor['wallet_config']), wallet_credentials("create", actor['wallet_credentials']))
    except IndyError as ex:
        if ex.error_code == ErrorCode.PoolLedgerConfigAlreadyExistsError:
            pass
    actor['wallet'] = await wallet.open_wallet(wallet_config("open", actor['wallet_config']), wallet_credentials("open", actor['wallet_credentials']))
    if seed:
        # Generate DID from seed - generally only used for existing Steward Anchor.
        actor['seed'] = seed
        actor['did_info'] = json.dumps({'seed': actor['seed']})
        actor['did'], actor['key'] = await did.create_and_store_my_did(actor['wallet'], actor['did_info'])
    return actor


async def teardown(pool_name, pool_handle, actor_list = []):
    print('Tearing down connections...')
    for actor in actor_list:
        await wallet.close_wallet(actor['wallet'])
        await wallet.delete_wallet(actor['wallet_config'], actor['wallet_credentials'])
    await pool.close_pool_ledger(pool_handle)
    await pool.delete_pool_ledger_config(pool_name)
    

def wallet_config(operation, wallet_config_str):
    if not args.storage_type:
        return wallet_config_str
    wallet_config_json = json.loads(wallet_config_str)
    wallet_config_json['storage_type'] = args.storage_type
    if args.config:
        wallet_config_json['storage_config'] = json.loads(args.config)
    #print(operation, json.dumps(wallet_config_json))
    return json.dumps(wallet_config_json)


def wallet_credentials(operation, wallet_credentials_str):
    if not args.storage_type:
        return wallet_credentials_str
    wallet_credentials_json = json.loads(wallet_credentials_str)
    if args.creds:
        wallet_credentials_json['storage_credentials'] = json.loads(args.creds)
    #print(operation, json.dumps(wallet_credentials_json))
    return json.dumps(wallet_credentials_json)
