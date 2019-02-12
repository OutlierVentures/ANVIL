'''
Sovrin onboarding functions.

A common problem here is referencing attributes of actors using their name as part of the
string, for ex. 'did_for_verifier' or 'prover_connection_response' in code elsewhere.

A general fix is to go through code assigning the actor name to a variable, for ex.
'did_for_' + name or name + '_connection_response'.
'''

import json
from indy import ledger, wallet, did, crypto
from indy.error import IndyError, ErrorCode

import argparse

parser = argparse.ArgumentParser(description='Run python getting-started scenario (Prover/Issuer)')
parser.add_argument('-t', '--storage_type', help='load custom wallet storage plug-in')
parser.add_argument('-l', '--library', help='dynamic library to load for plug-in')
parser.add_argument('-e', '--entrypoint', help='entry point for dynamic library')
parser.add_argument('-c', '--config', help='entry point for dynamic library')
parser.add_argument('-s', '--creds', help='entry point for dynamic library')

args = parser.parse_args()


async def simple_onboard(pool_handle, anchor, name, id_, key):
    print('Onboarding ' + name + '...')
    anchor_name = anchor['name']
    onboardee = {
        'name': name,
        'wallet_config': json.dumps({'id': id_}),
        'wallet_credentials': json.dumps({'key': key}),
        'pool': pool_handle,
        'role': 'TRUST_ANCHOR'
    }
    anchor['did_for_' + name], anchor['key_for_' + name], onboardee['did_for_' + anchor_name], onboardee['key_for_' + anchor_name], _ = \
        await onboarding(anchor, onboardee)
    onboardee['did'] = \
        await get_verinym(anchor, anchor['did_for_' + name], anchor['key_for_' + name],
                          onboardee, onboardee['did_for_' + anchor_name], onboardee['key_for_' + anchor_name])
    return onboardee, anchor


async def onboard_for_proving(pool_handle, anchor, name, id_, key):
    anchor_name = anchor['name']
    print('Onboarding ' + name + ' with ' + anchor_name +'...')  
    onboardee = {
        'name': name,
        'wallet_config': json.dumps({'id': id_}),
        'wallet_credentials': json.dumps({'key': key}),
        'pool': pool_handle
    }
    anchor['did_for_' + name], anchor['key_for_' + name], onboardee['did_for_' + anchor_name], onboardee['key_for_' + anchor_name], \
        anchor[name + '_connection_response'] = await onboarding(anchor, onboardee)
    return onboardee, anchor


async def new_onboard(anchor, name, id_, key, pool_handle):
    from_pool = pool_handle
    onboardee = await set_self_up(name, id_, key, pool_handle)
    anchor, connection_request = await onboarding_anchor_send(anchor, name) # Encrypt connection request?
    onboardee, anoncrypted_connection_reponse = await onboarding_onboardee_receive_and_send(onboardee, connection_request, from_pool, anchor['name'])
    anchor = await onboarding_anchor_receive(anchor, anoncrypted_connection_reponse, name)
    onboardee, authcrypted_did_info = await onboarding_onboardee_create_did(onboardee, anchor['name'])
    anchor = await onboarding_anchor_register_onboardee_did(anchor, name, authcrypted_did_info)
    return anchor, onboardee

async def existing_onboard(anchor, onboardee, id_, key, pool_handle):
    name = onboardee['name']
    from_pool = pool_handle
    anchor, connection_request = await onboarding_anchor_send(anchor, name) # Encrypt connection request?
    onboardee, anoncrypted_connection_reponse = await onboarding_onboardee_receive_and_send(onboardee, connection_request, from_pool, anchor['name'])
    anchor = await onboarding_anchor_receive(anchor, anoncrypted_connection_reponse, name)
    onboardee, authcrypted_did_info = await onboarding_onboardee_create_did(onboardee, anchor['name'])
    anchor = await onboarding_anchor_register_onboardee_did(anchor, name, authcrypted_did_info)
    return anchor, onboardee

# Set self up
async def set_self_up(name, id_, key, pool_handle):
    actor = {
        'name': name,
        'wallet_config': json.dumps({'id': id_}),
        'wallet_credentials': json.dumps({'key': key}),
        'pool': pool_handle,
        'role': 'TRUST_ANCHOR' # Do not change for individualised connections
    }
    try:
        await wallet.create_wallet(wallet_config("create", actor['wallet_config']), wallet_credentials("create", actor['wallet_credentials']))
    except IndyError as ex:
        if ex.error_code == ErrorCode.PoolLedgerConfigAlreadyExistsError:
            pass
    actor['wallet'] = await wallet.open_wallet(wallet_config("open", actor['wallet_config']), wallet_credentials("open", actor['wallet_credentials']))
    return actor

# Onboarding 1
async def onboarding_anchor_send(_from, unique_onboardee_name):
    (from_to_did, from_to_key) = await did.create_and_store_my_did(_from['wallet'], "{}")
    _from[unique_onboardee_name + '_did'] = from_to_did
    _from[unique_onboardee_name + '_key'] = from_to_key
    await send_nym(_from['pool'], _from['wallet'], _from['did'], from_to_did, from_to_key, None)
    _from['connection_request'] = {
        'did': from_to_did,
        'key': from_to_key, # ##### FOR THE LOVE OF GOD ENCRYPT. #####
        'nonce': 123456789 #NOTE TO SELF TRY REAL 9 NUMBER NONCE HERE
    }
    return _from, _from['connection_request']

# Onboarding 2
async def onboarding_onboardee_receive_and_send(to, connection_request, from_pool, unique_anchor_name):
    to[unique_anchor_name + '_key_for_' + to['name']] = connection_request['key']
    (to_from_did, to_from_key) = await did.create_and_store_my_did(to['wallet'], "{}")
    to[unique_anchor_name + '_did'] = to_from_did
    to[unique_anchor_name + '_key'] = to_from_key
    from_to_verkey = await did.key_for_did(from_pool, to['wallet'], connection_request['did'])
    to['connection_response'] = json.dumps({
        'did': to_from_did,
        'verkey': to_from_key,
        'nonce': connection_request['nonce']
    })
    to['anoncrypted_connection_response'] = \
        await crypto.anon_crypt(from_to_verkey, to['connection_response'].encode('utf-8'))
    return to, to['anoncrypted_connection_response'] # latter to be sent to the _from agent

# Onboarding 3
async def onboarding_anchor_receive(_from, anoncrypted_connection_reponse, unique_onboardee_name):
    _from['anoncrypted_connection_response'] = anoncrypted_connection_reponse
    _from['connection_response'] = \
        json.loads((await crypto.anon_decrypt(_from['wallet'], _from[unique_onboardee_name + '_key'],
                                              _from['anoncrypted_connection_response'])).decode("utf-8"))
    assert _from['connection_request']['nonce'] == _from['connection_response']['nonce']
    await send_nym(_from['pool'], _from['wallet'], _from['did'], _from['connection_response']['did'], _from['connection_response']['verkey'], None)
    return _from

# Verinym 1
async def onboarding_onboardee_create_did(to, unique_anchor_name):
    (to_did, to_key) = await did.create_and_store_my_did(to['wallet'], "{}")
    to['did'] = to_did
    to['did_info'] = json.dumps({
        'did': to_did,
        'verkey': to_key
    })
    to['authcrypted_did_info'] = \
        await crypto.auth_crypt(to['wallet'], to[unique_anchor_name + '_key'], to[unique_anchor_name + '_key_for_' + to['name']], to['did_info'].encode('utf-8'))
    return to, to['authcrypted_did_info']

# Verinym 2
async def onboarding_anchor_register_onboardee_did(_from, unique_onboardee_name, authcrypted_did_info):
    sender_verkey, authdecrypted_did_info_json, authdecrypted_did_info = \
        await auth_decrypt(_from['wallet'], _from[unique_onboardee_name + '_key'], authcrypted_did_info)
    assert sender_verkey == await did.key_for_did(_from['pool'], _from['wallet'], _from['connection_response']['did'])
    await send_nym(_from['pool'], _from['wallet'], _from['did'], authdecrypted_did_info['did'],
                   authdecrypted_did_info['verkey'], 'TRUST_ANCHOR') # Using to['role'] instead of trust anchor may fix issues
    return _from



async def onboarding(_from, to):
    (from_to_did, from_to_key) = await did.create_and_store_my_did(_from['wallet'], "{}")
    await send_nym(_from['pool'], _from['wallet'], _from['did'], from_to_did, from_to_key, None)
    connection_request = {
        'did': from_to_did,
        'nonce': 123456789
    }
    if 'wallet' not in to:
        try:
            await wallet.create_wallet(wallet_config("create", to['wallet_config']), wallet_credentials("create", to['wallet_credentials']))
        except IndyError as ex:
            if ex.error_code == ErrorCode.PoolLedgerConfigAlreadyExistsError:
                pass
        to['wallet'] = await wallet.open_wallet(wallet_config("open", to['wallet_config']), wallet_credentials("open", to['wallet_credentials']))
    (to_from_did, to_from_key) = await did.create_and_store_my_did(to['wallet'], "{}")
    from_to_verkey = await did.key_for_did(_from['pool'], to['wallet'], connection_request['did'])
    to['connection_response'] = json.dumps({
        'did': to_from_did,
        'verkey': to_from_key,
        'nonce': connection_request['nonce']
    })
    to['anoncrypted_connection_response'] = \
        await crypto.anon_crypt(from_to_verkey, to['connection_response'].encode('utf-8'))
    _from['anoncrypted_connection_response'] = to['anoncrypted_connection_response']
    _from['connection_response'] = \
        json.loads((await crypto.anon_decrypt(_from['wallet'], from_to_key,
                                              _from['anoncrypted_connection_response'])).decode("utf-8"))
    assert connection_request['nonce'] == _from['connection_response']['nonce']
    await send_nym(_from['pool'], _from['wallet'], _from['did'], to_from_did, to_from_key, None)
    return from_to_did, from_to_key, to_from_did, to_from_key, _from['connection_response']


async def get_verinym(_from, from_to_did, from_to_key, to, to_from_did, to_from_key):
    (to_did, to_key) = await did.create_and_store_my_did(to['wallet'], "{}")
    to['did_info'] = json.dumps({
        'did': to_did,
        'verkey': to_key
    })
    to['authcrypted_did_info'] = \
        await crypto.auth_crypt(to['wallet'], to_from_key, from_to_key, to['did_info'].encode('utf-8'))
    sender_verkey, authdecrypted_did_info_json, authdecrypted_did_info = \
        await auth_decrypt(_from['wallet'], from_to_key, to['authcrypted_did_info'])
    assert sender_verkey == await did.key_for_did(_from['pool'], _from['wallet'], to_from_did)
    await send_nym(_from['pool'], _from['wallet'], _from['did'], authdecrypted_did_info['did'],
                   authdecrypted_did_info['verkey'], to['role'])
    return to_did

async def send_nym(pool_handle, wallet_handle, _did, new_did, new_key, role):
    nym_request = await ledger.build_nym_request(_did, new_did, new_key, None, role)
    await ledger.sign_and_submit_request(pool_handle, wallet_handle, _did, nym_request)

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

async def auth_decrypt(wallet_handle, key, message):
    from_verkey, decrypted_message_json = await crypto.auth_decrypt(wallet_handle, key, message)
    decrypted_message_json = decrypted_message_json.decode("utf-8")
    decrypted_message = json.loads(decrypted_message_json)
    return from_verkey, decrypted_message_json, decrypted_message
