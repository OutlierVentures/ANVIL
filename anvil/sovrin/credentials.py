'''
Sovrin credential issuance functions:

1. Offer a credential.
2. Receive a credential offer.
3. Request a credential.
4. Create and send a credential.
5. Store a credential.
'''

import json
from indy import anoncreds, crypto, did, ledger


async def offer_credential(issuer, unique_schema_name):
    print('Issuer offering credential to Prover...')
    issuer['unique_schema_name'] = unique_schema_name
    issuer[issuer['unique_schema_name'] + '_cred_offer'] = \
        await anoncreds.issuer_create_credential_offer(issuer['wallet'], issuer[issuer['unique_schema_name'] + '_cred_def_id'])
    # Get key for prover's DID
    issuer['prover_key_for_issuer'] = \
        await did.key_for_did(issuer['pool'], issuer['wallet'], issuer['connection_response']['did'])
    # Create offer object
    offer = {
        'name': issuer['unique_schema_name'],
        'cred_offer': issuer[issuer['unique_schema_name'] + '_cred_offer']
    }
    # Authenticate, encrypt and send
    issuer['authcrypted_cred_offer'] = \
        await crypto.auth_crypt(issuer['wallet'], issuer['prover_key'], issuer['prover_key_for_issuer'],
                                json.dumps(offer).encode('utf-8'))
    return issuer, issuer['authcrypted_cred_offer']


async def receive_credential_offer(prover):
    print('Prover getting credential offer from Issuer...')
    # Decrypt
    prover['issuer_key_for_prover'], _, json_cred_offer = \
        await auth_decrypt(prover['wallet'], prover['issuer_key'], prover['authcrypted_cred_offer'])
    prover['unique_schema_name'] = json_cred_offer['name']
    prover[prover['unique_schema_name'] + '_cred_offer'] = json_cred_offer['cred_offer']
    authdecrypted_cred_offer = json.loads(json_cred_offer['cred_offer'])
    prover[prover['unique_schema_name'] + '_schema_id'] = authdecrypted_cred_offer['schema_id']
    prover[prover['unique_schema_name'] + '_cred_def_id'] = authdecrypted_cred_offer['cred_def_id']
    # Prover creates master secret so they can use the credential
    prover['master_secret_id'] = await anoncreds.prover_create_master_secret(prover['wallet'], None)
    # Get credential definition from ledger
    (prover['issuer_cred_def_id'], prover['issuer_cred_def']) = \
        await get_cred_def(prover['pool'], prover['issuer_did'], authdecrypted_cred_offer['cred_def_id'])
    return prover


async def request_credential(prover, values):
    print('Prover requesting credential itself...')
    prover[prover['unique_schema_name'] + '_cred_values'] = values
    (prover[prover['unique_schema_name'] + '_cred_request'], prover[prover['unique_schema_name'] + '_cred_request_metadata']) = \
        await anoncreds.prover_create_credential_req(prover['wallet'], prover['issuer_did'],
                                                     prover[prover['unique_schema_name'] + '_cred_offer'], prover['issuer_cred_def'],
                                                     prover['master_secret_id'])
    # Create credential request object
    cred_request = {
        'request': prover[prover['unique_schema_name'] + '_cred_request'],
        'values': values
    }
    # Authenticate, encrypt and send
    prover['authcrypted_cred_request'] = \
        await crypto.auth_crypt(prover['wallet'], prover['issuer_key'], prover['issuer_key_for_prover'],
                                json.dumps(cred_request).encode('utf-8'))
    return prover, prover['authcrypted_cred_request']



async def create_and_send_credential(issuer):
    print('Issuer creating credential and sending to Prover...')
    # Decrypt
    issuer['prover_key_for_issuer'], _, cred_request = \
        await auth_decrypt(issuer['wallet'], issuer['prover_key'], issuer['authcrypted_cred_request'])
    issuer[issuer['unique_schema_name'] + '_cred_request'] = cred_request['request']
    issuer['prover_cred_values'] = cred_request['values']
    # Create the credential according to the request
    issuer[issuer['unique_schema_name'] + '_cred'], _, _ = \
        await anoncreds.issuer_create_credential(issuer['wallet'], issuer[issuer['unique_schema_name'] + '_cred_offer'],
                                                 issuer[issuer['unique_schema_name'] + '_cred_request'],
                                                 issuer['prover_cred_values'], None, None)
    # Authenticate, encrypt and send
    issuer['authcrypted_cred'] = \
        await crypto.auth_crypt(issuer['wallet'], issuer['prover_key'], issuer['prover_key_for_issuer'],
                                issuer[issuer['unique_schema_name'] + '_cred'].encode('utf-8'))
    return issuer, issuer['authcrypted_cred']


async def store_credential(prover):
    print('Prover storing credential...')
    # Decrypt, get definition and store credential
    _, prover[prover['unique_schema_name'] + '_cred'], _ = \
        await auth_decrypt(prover['wallet'], prover['issuer_key'], prover['authcrypted_cred'])
    _, prover[prover['unique_schema_name'] + '_cred_def'] = await get_cred_def(prover['pool'], prover['issuer_did'],
                                                         prover[prover['unique_schema_name'] + '_cred_def_id'])
    await anoncreds.prover_store_credential(prover['wallet'], None, prover[prover['unique_schema_name'] + '_cred_request_metadata'],
                                            prover[prover['unique_schema_name'] + '_cred'], prover[prover['unique_schema_name'] + '_cred_def'], None)
    return prover



async def get_cred_def(pool_handle, _did, cred_def_id):
    get_cred_def_request = await ledger.build_get_cred_def_request(_did, cred_def_id)
    get_cred_def_response = await ledger.submit_request(pool_handle, get_cred_def_request)
    return await ledger.parse_get_cred_def_response(get_cred_def_response)


async def auth_decrypt(wallet_handle, key, message):
    from_verkey, decrypted_message_json = await crypto.auth_decrypt(wallet_handle, key, message)
    decrypted_message_json = decrypted_message_json.decode("utf-8")
    decrypted_message = json.loads(decrypted_message_json)
    return from_verkey, decrypted_message_json, decrypted_message