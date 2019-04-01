'''
Sovrin setup/teardown functions:

1. Pool setup.
2. Set self up: establish dictionary data structure, create and open wallet.
3. Actor teardown.
'''

import json, urllib, argparse
from pathlib import Path
from tempfile import gettempdir
from os import environ
from indy import pool, wallet, did
from indy.error import ErrorCode, IndyError
parser = argparse.ArgumentParser(description='Run python getting-started scenario (Prover/Issuer)')
parser.add_argument('-t', '--storage_type', help='load custom wallet storage plug-in')
parser.add_argument('-l', '--library', help='dynamic library to load for plug-in')
parser.add_argument('-e', '--entrypoint', help='entry point for dynamic library')
parser.add_argument('-c', '--config', help='entry point for dynamic library')
parser.add_argument('-s', '--creds', help='entry point for dynamic library')
args = parser.parse_known_args()[0]


PROTOCOL_VERSION = 2


async def setup_pool(net = 'local'):
    print('Setting up pool...')
    name = 'ANVIL' if net == 'local' else net
    pool_list = await pool.list_pools()
    for pool_dict in pool_list:
        if pool_dict['pool'] == name:
            return name, 1
    pool_ = {
        'name': name
    }
    pool_['genesis_txn_path'] = get_pool_genesis_txn_path(pool_['name'], net)
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
        if 'wallet' in actor:
            await wallet.close_wallet(actor['wallet'])
            await wallet.delete_wallet(actor['wallet_config'], actor['wallet_credentials'])
    if await pool.list_pools():
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


def path_home() -> Path:
    return Path.home().joinpath(".indy_client")


def get_pool_genesis_txn_path(pool_name, net ='local'):
    path_temp = Path(gettempdir()).joinpath("indy")
    path = path_temp.joinpath("{}.txn".format(pool_name))
    save_pool_genesis_txn_file(path, net)
    return path


def pool_genesis_txn_data(net = 'local'):
    # Mainnet and testnet do not appear to have different genesis transaction data
    if (net == 'test' or net == 'main'):
        with urllib.request.urlopen('https://raw.githubusercontent.com/sovrin-foundation/sovrin/stable/sovrin/pool_transactions_sandbox_genesis') as url:
            data = json.loads(url.read().decode())
        return data
    else:
        pool_ip = environ.get("TEST_POOL_IP", "127.0.0.1")
        return "\n".join([
            '{{"reqSignature":{{}},"txn":{{"data":{{"data":{{"alias":"Node1","blskey":"4N8aUNHSgjQVgkpm8nhNEfDf6txHznoYREg9kirmJrkivgL4oSEimFF6nsQ6M41QvhM2Z33nves5vfSn9n1UwNFJBYtWVnHYMATn76vLuL3zU88KyeAYcHfsih3He6UHcXDxcaecHVz6jhCYz1P2UZn2bDVruL5wXpehgBfBaLKm3Ba","blskey_pop":"RahHYiCvoNCtPTrVtP7nMC5eTYrsUA8WjXbdhNc8debh1agE9bGiJxWBXYNFbnJXoXhWFMvyqhqhRoq737YQemH5ik9oL7R4NTTCz2LEZhkgLJzB3QRQqJyBNyv7acbdHrAT8nQ9UkLbaVL9NBpnWXBTw4LEMePaSHEw66RzPNdAX1","client_ip":"{}","client_port":9702,"node_ip":"{}","node_port":9701,"services":["VALIDATOR"]}},"dest":"Gw6pDLhcBcoQesN72qfotTgFa7cbuqZpkX3Xo6pLhPhv"}},"metadata":{{"from":"Th7MpTaRZVRYnPiabds81Y"}},"type":"0"}},"txnMetadata":{{"seqNo":1,"txnId":"fea82e10e894419fe2bea7d96296a6d46f50f93f9eeda954ec461b2ed2950b62"}},"ver":"1"}}'.format(
                pool_ip, pool_ip),
            '{{"reqSignature":{{}},"txn":{{"data":{{"data":{{"alias":"Node2","blskey":"37rAPpXVoxzKhz7d9gkUe52XuXryuLXoM6P6LbWDB7LSbG62Lsb33sfG7zqS8TK1MXwuCHj1FKNzVpsnafmqLG1vXN88rt38mNFs9TENzm4QHdBzsvCuoBnPH7rpYYDo9DZNJePaDvRvqJKByCabubJz3XXKbEeshzpz4Ma5QYpJqjk","blskey_pop":"Qr658mWZ2YC8JXGXwMDQTzuZCWF7NK9EwxphGmcBvCh6ybUuLxbG65nsX4JvD4SPNtkJ2w9ug1yLTj6fgmuDg41TgECXjLCij3RMsV8CwewBVgVN67wsA45DFWvqvLtu4rjNnE9JbdFTc1Z4WCPA3Xan44K1HoHAq9EVeaRYs8zoF5","client_ip":"{}","client_port":9704,"node_ip":"{}","node_port":9703,"services":["VALIDATOR"]}},"dest":"8ECVSk179mjsjKRLWiQtssMLgp6EPhWXtaYyStWPSGAb"}},"metadata":{{"from":"EbP4aYNeTHL6q385GuVpRV"}},"type":"0"}},"txnMetadata":{{"seqNo":2,"txnId":"1ac8aece2a18ced660fef8694b61aac3af08ba875ce3026a160acbc3a3af35fc"}},"ver":"1"}}'.format(
                pool_ip, pool_ip),
            '{{"reqSignature":{{}},"txn":{{"data":{{"data":{{"alias":"Node3","blskey":"3WFpdbg7C5cnLYZwFZevJqhubkFALBfCBBok15GdrKMUhUjGsk3jV6QKj6MZgEubF7oqCafxNdkm7eswgA4sdKTRc82tLGzZBd6vNqU8dupzup6uYUf32KTHTPQbuUM8Yk4QFXjEf2Usu2TJcNkdgpyeUSX42u5LqdDDpNSWUK5deC5","blskey_pop":"QwDeb2CkNSx6r8QC8vGQK3GRv7Yndn84TGNijX8YXHPiagXajyfTjoR87rXUu4G4QLk2cF8NNyqWiYMus1623dELWwx57rLCFqGh7N4ZRbGDRP4fnVcaKg1BcUxQ866Ven4gw8y4N56S5HzxXNBZtLYmhGHvDtk6PFkFwCvxYrNYjh","client_ip":"{}","client_port":9706,"node_ip":"{}","node_port":9705,"services":["VALIDATOR"]}},"dest":"DKVxG2fXXTU8yT5N7hGEbXB3dfdAnYv1JczDUHpmDxya"}},"metadata":{{"from":"4cU41vWW82ArfxJxHkzXPG"}},"type":"0"}},"txnMetadata":{{"seqNo":3,"txnId":"7e9f355dffa78ed24668f0e0e369fd8c224076571c51e2ea8be5f26479edebe4"}},"ver":"1"}}'.format(
                pool_ip, pool_ip),
            '{{"reqSignature":{{}},"txn":{{"data":{{"data":{{"alias":"Node4","blskey":"2zN3bHM1m4rLz54MJHYSwvqzPchYp8jkHswveCLAEJVcX6Mm1wHQD1SkPYMzUDTZvWvhuE6VNAkK3KxVeEmsanSmvjVkReDeBEMxeDaayjcZjFGPydyey1qxBHmTvAnBKoPydvuTAqx5f7YNNRAdeLmUi99gERUU7TD8KfAa6MpQ9bw","blskey_pop":"RPLagxaR5xdimFzwmzYnz4ZhWtYQEj8iR5ZU53T2gitPCyCHQneUn2Huc4oeLd2B2HzkGnjAff4hWTJT6C7qHYB1Mv2wU5iHHGFWkhnTX9WsEAbunJCV2qcaXScKj4tTfvdDKfLiVuU2av6hbsMztirRze7LvYBkRHV3tGwyCptsrP","client_ip":"{}","client_port":9708,"node_ip":"{}","node_port":9707,"services":["VALIDATOR"]}},"dest":"4PS3EDQ3dW1tci1Bp6543CfuuebjFrg36kLAUcskGfaA"}},"metadata":{{"from":"TWwCRQRZ2ZHMJFn9TzLp7W"}},"type":"0"}},"txnMetadata":{{"seqNo":4,"txnId":"aa5e817d7cc626170eca175822029339a444eb0ee8f0bd20d3b0b76e566fb008"}},"ver":"1"}}'.format(
                pool_ip, pool_ip)
        ])


def save_pool_genesis_txn_file(path, net = 'local'):
    data = pool_genesis_txn_data(net)

    path.parent.mkdir(parents=True, exist_ok=True)

    with open(str(path), "w+") as f:
        f.writelines(data)


# This function sets up all actors for same-file demoes.
async def setup_demo():
    pool_name, pool_handle = await setup_pool('local')
    steward = await set_self_up('steward', 'STEWARD_DEMO_DID', 'STEWARD_DEMO_KEY', pool_handle, seed = '000000000000000000000000Steward1')
    issuer = await set_self_up('issuer', 'ISSUER_DEMO_DID', 'ISSUER_DEMO_KEY', pool_handle)
    prover = await set_self_up('prover', 'PROVER_DEMO_DID', 'PROVER_DEMO_KEY', pool_handle)
    verifier = await set_self_up('verifier', 'VERIFIER_DEMO_DID', 'VERIFIER_DEMO_KEY', pool_handle)
    return pool_name, pool_handle, steward, issuer, prover, verifier

