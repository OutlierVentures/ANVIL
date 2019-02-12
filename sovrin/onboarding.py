'''
Sovrin onboarding functions.

Basic steps for establishing a pairwise connection:
1. Alice sends DID to Bob in plain.
2. Bob uses the `anon_crypt` scheme to send their `verkey` to Alice.
3. It is now possible to proceed with `auth_crypt`.
'''

import json
from indy import ledger, wallet, did, crypto
from indy.error import IndyError, ErrorCode
from sovrin_utilities import generate_nonce

import argparse

parser = argparse.ArgumentParser(description='Run python getting-started scenario (Prover/Issuer)')
parser.add_argument('-t', '--storage_type', help='load custom wallet storage plug-in')
parser.add_argument('-l', '--library', help='dynamic library to load for plug-in')
parser.add_argument('-e', '--entrypoint', help='entry point for dynamic library')
parser.add_argument('-c', '--config', help='entry point for dynamic library')
parser.add_argument('-s', '--creds', help='entry point for dynamic library')

args = parser.parse_args()


'''
This function onboards an actor with another when both are passed as arguments.
This demands both actors exist within the same process, i.e. same file.
It is not helpful in real-life situations where actors exist on separate machines.
For a real network, execute the functions below this one on the two machines in turn.
The onboardee needs to have set_self_up() before calling this function.
'''
async def demo_onboard(anchor, onboardee):
    name = onboardee['name']
    anchor, connection_request = await onboarding_anchor_send(anchor, name) # Encrypt connection request?
    onboardee, anoncrypted_connection_reponse = await onboarding_onboardee_receive_and_send(onboardee, connection_request, anchor['pool'], anchor['name'])
    anchor = await onboarding_anchor_receive(anchor, anoncrypted_connection_reponse, name)
    onboardee, authcrypted_did_info = await onboarding_onboardee_create_did(onboardee, anchor['name'])
    anchor = await onboarding_anchor_register_onboardee_did(anchor, name, authcrypted_did_info)
    return anchor, onboardee


# Set self up: establish dictionary data structure, create and open wallet
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


# Onboarding 1: Anchor sends connection request
async def onboarding_anchor_send(_from, unique_onboardee_name):
    (from_to_did, from_to_key) = await did.create_and_store_my_did(_from['wallet'], "{}")
    _from[unique_onboardee_name + '_did'] = from_to_did
    _from[unique_onboardee_name + '_key'] = from_to_key
    await send_nym(_from['pool'], _from['wallet'], _from['did'], from_to_did, from_to_key, None)
    nonce = generate_nonce(9)
    _from['connection_request'] = {
        'did': from_to_did,
        'nonce': nonce
    }
    return _from, _from['connection_request']


# Onboarding 2: Onboardee sends connection response
async def onboarding_onboardee_receive_and_send(to, connection_request, from_pool, unique_anchor_name):
    #to[unique_anchor_name + '_key_for_' + to['name']] = connection_request['key']
    (to_from_did, to_from_key) = await did.create_and_store_my_did(to['wallet'], "{}")
    to[unique_anchor_name + '_did'] = to_from_did
    to[unique_anchor_name + '_key'] = to_from_key
    to['from_to_verkey'] = await did.key_for_did(from_pool, to['wallet'], connection_request['did'])
    to['connection_response'] = json.dumps({
        'did': to_from_did,
        'verkey': to_from_key,
        'nonce': connection_request['nonce']
    })
    to['anoncrypted_connection_response'] = \
        await crypto.anon_crypt(to['from_to_verkey'], to['connection_response'].encode('utf-8'))
    return to, to['anoncrypted_connection_response'] # latter to be sent to the _from agent


# Onboarding 3: Anchor recieves connection response, establishing a secure channel
async def onboarding_anchor_receive(_from, anoncrypted_connection_reponse, unique_onboardee_name):
    _from['anoncrypted_connection_response'] = anoncrypted_connection_reponse
    _from['connection_response'] = \
        json.loads((await crypto.anon_decrypt(_from['wallet'], _from[unique_onboardee_name + '_key'],
                                              _from['anoncrypted_connection_response'])).decode("utf-8"))
    assert _from['connection_request']['nonce'] == _from['connection_response']['nonce']
    await send_nym(_from['pool'], _from['wallet'], _from['did'], _from['connection_response']['did'], _from['connection_response']['verkey'], None)
    return _from


# Onboarding 4: Onboardee creates their DID and sends it to the Anchor
async def onboarding_onboardee_create_did(to, unique_anchor_name):
    (to_did, to_key) = await did.create_and_store_my_did(to['wallet'], "{}")
    to['did'] = to_did
    to['did_info'] = json.dumps({
        'did': to_did,
        'verkey': to_key
    })
    to['authcrypted_did_info'] = \
        await crypto.auth_crypt(to['wallet'], to[unique_anchor_name + '_key'], to['from_to_verkey'], to['did_info'].encode('utf-8'))
    return to, to['authcrypted_did_info']


# Onboarding 5: Anchor registers the Onboardee as a new trust anchor on the ledger
async def onboarding_anchor_register_onboardee_did(_from, unique_onboardee_name, authcrypted_did_info):
    sender_verkey, _, authdecrypted_did_info = \
        await auth_decrypt(_from['wallet'], _from[unique_onboardee_name + '_key'], authcrypted_did_info)
    assert sender_verkey == await did.key_for_did(_from['pool'], _from['wallet'], _from['connection_response']['did'])
    await send_nym(_from['pool'], _from['wallet'], _from['did'], authdecrypted_did_info['did'],
                   authdecrypted_did_info['verkey'], 'TRUST_ANCHOR') # Using to['role'] instead of trust anchor may fix issues
    return _from


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
