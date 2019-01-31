import time

from indy import anoncreds, crypto, did, ledger, pool, wallet

import json
import logging

import argparse
import sys
from ctypes import *

from indy.error import ErrorCode, IndyError

from sovrin_utilities import get_pool_genesis_txn_path, run_coroutine

from config import PROTOCOL_VERSION





'''
v OPTIONS v
'''
# Wallet IDs and keys are currently mocked
# NOTE always pass keys as environment variables

POOL_NAME = 'ANVIL'

STEWARD_NAME = 'Sovrin Steward'
STEWARD_WALLET_ID = 'steward_wallet_id' 
STEWARD_WALLET_KEY = 'steward_wallet_key'
# Local pool setup demands this exact seed
STEWARD_SEED = '000000000000000000000000Steward1'

PROVER_NAME = 'Prover'
PROVER_WALLET_ID = 'prover_wallet_id'
PROVER_WALLET_KEY = 'prover_wallet_key'

ISSUER_NAME = 'Issuer'
ISSUER_WALLET_ID = 'issuer_wallet_id'
ISSUER_WALLET_KEY = 'issuer_wallet_key'

VERIFIER_NAME = 'Verifier'
VERIFIER_WALLET_ID = 'verifier_wallet_id'
VERIFIER_WALLET_KEY = 'verifier_wallet_key'
'''
^ OPTIONS ^
'''




logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.WARN)

parser = argparse.ArgumentParser(description='Run python getting-started scenario (Prover/Issuer)')
parser.add_argument('-t', '--storage_type', help='load custom wallet storage plug-in')
parser.add_argument('-l', '--library', help='dynamic library to load for plug-in')
parser.add_argument('-e', '--entrypoint', help='entry point for dynamic library')
parser.add_argument('-c', '--config', help='entry point for dynamic library')
parser.add_argument('-s', '--creds', help='entry point for dynamic library')

args = parser.parse_args()


# check if we need to dyna-load a custom wallet storage plug-in
if args.storage_type:
    if not (args.library and args.entrypoint):
        parser.print_help()
        sys.exit(0)
    stg_lib = CDLL(args.library)
    result = stg_lib[args.entrypoint]()
    if result != 0:
        print("Error unable to load wallet storage", result)
        parser.print_help()
        sys.exit(0)

    print("Success, loaded wallet storage", args.storage_type)


async def run():


    pool_ = {
        'name': POOL_NAME
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


    print('Setting up Steward...')
    steward = {
        'name': STEWARD_NAME,
        'wallet_config': json.dumps({'id': STEWARD_WALLET_ID}),
        'wallet_credentials': json.dumps({'key': STEWARD_WALLET_KEY}),
        'pool': pool_['handle'],
        'seed': STEWARD_SEED
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


    print('Onboarding issuer...')
    issuer = {
        'name': ISSUER_NAME,
        'wallet_config': json.dumps({'id': ISSUER_WALLET_ID}),
        'wallet_credentials': json.dumps({'key': ISSUER_WALLET_KEY}),
        'pool': pool_['handle'],
        'role': 'TRUST_ANCHOR'
    }
    steward['did_for_issuer'], steward['key_for_issuer'], issuer['did_for_steward'], issuer['key_for_steward'], _ = \
        await onboarding(steward, issuer)
    issuer['did'] = \
        await get_verinym(steward, steward['did_for_issuer'], steward['key_for_issuer'],
                          issuer, issuer['did_for_steward'], issuer['key_for_steward'])


    print('Onboarding verifier...')
    verifier = {
        'name': VERIFIER_NAME,
        'wallet_config': json.dumps({'id': VERIFIER_WALLET_ID}),
        'wallet_credentials': json.dumps({'key': VERIFIER_WALLET_KEY}),
        'pool': pool_['handle'],
        'role': 'TRUST_ANCHOR'
    }
    steward['did_for_verifier'], steward['key_for_verifier'], verifier['did_for_steward'], verifier['key_for_steward'], _ = \
        await onboarding(steward, verifier)
    verifier['did'] = await get_verinym(steward, steward['did_for_verifier'], steward['key_for_verifier'],
                                    verifier, verifier['did_for_steward'], verifier['key_for_steward'])


    print('Issuer creating credential schema...')
    transcript = {
        'name': 'Transcript',
        'version': '1.2',
        'attributes': ['first_name', 'last_name', 'degree', 'status', 'year', 'average', 'ssn']
    }
    (issuer['transcript_schema_id'], issuer['transcript_schema']) = \
        await anoncreds.issuer_create_schema(issuer['did'], transcript['name'], transcript['version'],
                                             json.dumps(transcript['attributes']))
    transcript_schema_id = issuer['transcript_schema_id']
    # Send schema to ledger
    await send_schema(issuer['pool'], issuer['wallet'], issuer['did'], issuer['transcript_schema'])
    

    print('Issuer applying credential definition...')
    time.sleep(1)  # sleep 1 second before getting schema
    (issuer['transcript_schema_id'], issuer['transcript_schema']) = \
        await get_schema(issuer['pool'], issuer['did'], transcript_schema_id)
    # Create and store credential definition in wallet
    transcript_cred_def = {
        'tag': 'TAG1',
        'type': 'CL',
        'config': {"support_revocation": False}
    }
    (issuer['transcript_cred_def_id'], issuer['transcript_cred_def']) = \
        await anoncreds.issuer_create_and_store_credential_def(issuer['wallet'], issuer['did'],
                                                               issuer['transcript_schema'], transcript_cred_def['tag'],
                                                               transcript_cred_def['type'],
                                                               json.dumps(transcript_cred_def['config']))
    # Send definition to ledger
    await send_cred_def(issuer['pool'], issuer['wallet'], issuer['did'], issuer['transcript_cred_def'])

    print('Onboarding credential for Prover...')
    prover = {
        'name': PROVER_NAME,
        'wallet_config': json.dumps({'id': PROVER_WALLET_ID}),
        'wallet_credentials': json.dumps({'key': PROVER_WALLET_KEY}),
        'pool': pool_['handle'],
        'role': 'TRUST_ANCHOR'
    }
    issuer['did_for_prover'], issuer['key_for_prover'], prover['did_for_issuer'], prover['key_for_issuer'], \
    issuer['prover_connection_response'] = await onboarding(issuer, prover)


    print('Issuer offering credential to Prover...')
    issuer['transcript_cred_offer'] = \
        await anoncreds.issuer_create_credential_offer(issuer['wallet'], issuer['transcript_cred_def_id'])
    # Get key for prover's DID
    issuer['alic_key_for_issuer'] = \
        await did.key_for_did(issuer['pool'], issuer['wallet'], issuer['prover_connection_response']['did'])
    # Authenticate, encrypt and send
    issuer['authcrypted_transcript_cred_offer'] = \
        await crypto.auth_crypt(issuer['wallet'], issuer['key_for_prover'], issuer['alic_key_for_issuer'],
                                issuer['transcript_cred_offer'].encode('utf-8'))
    prover['authcrypted_transcript_cred_offer'] = issuer['authcrypted_transcript_cred_offer']

    print('Prover getting credential offer from Issuer...')
    # Decrypt
    prover['issuer_key_for_prover'], prover['transcript_cred_offer'], authdecrypted_transcript_cred_offer = \
        await auth_decrypt(prover['wallet'], prover['key_for_issuer'], prover['authcrypted_transcript_cred_offer'])
    prover['transcript_schema_id'] = authdecrypted_transcript_cred_offer['schema_id']
    prover['transcript_cred_def_id'] = authdecrypted_transcript_cred_offer['cred_def_id']
    # Prover creates master secret so they can use the credential
    prover['master_secret_id'] = await anoncreds.prover_create_master_secret(prover['wallet'], None)
    # Get credential definition from ledger
    (prover['issuer_transcript_cred_def_id'], prover['issuer_transcript_cred_def']) = \
        await get_cred_def(prover['pool'], prover['did_for_issuer'], authdecrypted_transcript_cred_offer['cred_def_id'])

    print('Prover requesting credential itself...')
    (prover['transcript_cred_request'], prover['transcript_cred_request_metadata']) = \
        await anoncreds.prover_create_credential_req(prover['wallet'], prover['did_for_issuer'],
                                                     prover['transcript_cred_offer'], prover['issuer_transcript_cred_def'],
                                                     prover['master_secret_id'])
    # Authenticate, encrypt and send
    prover['authcrypted_transcript_cred_request'] = \
        await crypto.auth_crypt(prover['wallet'], prover['key_for_issuer'], prover['issuer_key_for_prover'],
                                prover['transcript_cred_request'].encode('utf-8'))
    issuer['authcrypted_transcript_cred_request'] = prover['authcrypted_transcript_cred_request']
    
    # Specify values of credential request
    prover['transcript_cred_values'] = json.dumps({
        "first_name": {"raw": "Prover", "encoded": "1139481716457488690172217916278103335"},
        "last_name": {"raw": "SecondName", "encoded": "5321642780241790123587902456789123452"},
        "degree": {"raw": "Bachelor of Science, Marketing", "encoded": "12434523576212321"},
        "status": {"raw": "graduated", "encoded": "2213454313412354"},
        "ssn": {"raw": "123-45-6789", "encoded": "3124141231422543541"},
        "year": {"raw": "2015", "encoded": "2015"},
        "average": {"raw": "5", "encoded": "5"}
    })


    print('Issuer creating credential and sending to Prover...')
    # Get request and decrypt
    issuer['prover_transcript_cred_values'] = prover['transcript_cred_values']
    issuer['prover_key_for_issuer'], issuer['transcript_cred_request'], _ = \
        await auth_decrypt(issuer['wallet'], issuer['key_for_prover'], issuer['authcrypted_transcript_cred_request'])
    # Create the credential according to the request
    issuer['transcript_cred'], _, _ = \
        await anoncreds.issuer_create_credential(issuer['wallet'], issuer['transcript_cred_offer'],
                                                 issuer['transcript_cred_request'],
                                                 issuer['prover_transcript_cred_values'], None, None)
    # Authenticate, encrypt and send
    issuer['authcrypted_transcript_cred'] = \
        await crypto.auth_crypt(issuer['wallet'], issuer['key_for_prover'], issuer['prover_key_for_issuer'],
                                issuer['transcript_cred'].encode('utf-8'))
    prover['authcrypted_transcript_cred'] = issuer['authcrypted_transcript_cred']

    print('Prover storing credential...')
    # Decrypt, get definition and store credential
    _, prover['transcript_cred'], _ = \
        await auth_decrypt(prover['wallet'], prover['key_for_issuer'], prover['authcrypted_transcript_cred'])
    _, prover['transcript_cred_def'] = await get_cred_def(prover['pool'], prover['did_for_issuer'],
                                                         prover['transcript_cred_def_id'])
    await anoncreds.prover_store_credential(prover['wallet'], None, prover['transcript_cred_request_metadata'],
                                            prover['transcript_cred'], prover['transcript_cred_def'], None)


    print('Verifier requesting proof of credential...')
    # Prover onboarded with verifier
    verifier['did_for_prover'], verifier['key_for_prover'], prover['did_for_verifier'], prover['key_for_verifier'], \
    verifier['prover_connection_response'] = await onboarding(verifier, prover)

    # Create proof request
    verifier['job_application_proof_request'] = json.dumps({
        'nonce': '1432422343242122312411212',
        'name': 'Job-Application',
        'version': '0.1',
        'requested_attributes': {
            'attr1_referent': {
                'name': 'first_name'
            },
            'attr2_referent': {
                'name': 'last_name'
            },
            'attr3_referent': {
                'name': 'degree',
                'restrictions': [{'cred_def_id': issuer['transcript_cred_def_id']}]
            },
            'attr4_referent': {
                'name': 'status',
                'restrictions': [{'cred_def_id': issuer['transcript_cred_def_id']}]
            },
            'attr5_referent': {
                'name': 'ssn',
                'restrictions': [{'cred_def_id': issuer['transcript_cred_def_id']}]
            },
            'attr6_referent': {
                'name': 'phone_number'
            }
        },
        'requested_predicates': {
            'predicate1_referent': {
                'name': 'average',
                'p_type': '>=',
                'p_value': 4,
                'restrictions': [{'cred_def_id': issuer['transcript_cred_def_id']}]
            }
        }
    })
    # Get key for prover DID
    verifier['prover_key_for_verifier'] = \
        await did.key_for_did(verifier['pool'], verifier['wallet'], verifier['prover_connection_response']['did'])

    # Authenticate, encrypt and send
    verifier['authcrypted_job_application_proof_request'] = \
        await crypto.auth_crypt(verifier['wallet'], verifier['key_for_prover'], verifier['prover_key_for_verifier'],
                                verifier['job_application_proof_request'].encode('utf-8'))
    prover['authcrypted_job_application_proof_request'] = verifier['authcrypted_job_application_proof_request']


    print('Prover getting credential and creating proof...')
    # Decrypt
    prover['verifier_key_for_prover'], prover['job_application_proof_request'], _ = \
        await auth_decrypt(prover['wallet'], prover['key_for_verifier'], prover['authcrypted_job_application_proof_request'])
    # Search for a proof request and get the credential attributes needed
    search_for_job_application_proof_request = \
        await anoncreds.prover_search_credentials_for_proof_req(prover['wallet'],
                                                                prover['job_application_proof_request'], None)
    cred_for_attr1 = await get_credential_for_referent(search_for_job_application_proof_request, 'attr1_referent')
    cred_for_attr2 = await get_credential_for_referent(search_for_job_application_proof_request, 'attr2_referent')
    cred_for_attr3 = await get_credential_for_referent(search_for_job_application_proof_request, 'attr3_referent')
    cred_for_attr4 = await get_credential_for_referent(search_for_job_application_proof_request, 'attr4_referent')
    cred_for_attr5 = await get_credential_for_referent(search_for_job_application_proof_request, 'attr5_referent')
    cred_for_predicate1 = await get_credential_for_referent(search_for_job_application_proof_request, 'predicate1_referent')
    await anoncreds.prover_close_credentials_search_for_proof_req(search_for_job_application_proof_request)
    # Put the needed attributes in Indy-readable format
    prover['creds_for_job_application_proof'] = {cred_for_attr1['referent']: cred_for_attr1,
                                                cred_for_attr2['referent']: cred_for_attr2,
                                                cred_for_attr3['referent']: cred_for_attr3,
                                                cred_for_attr4['referent']: cred_for_attr4,
                                                cred_for_attr5['referent']: cred_for_attr5,
                                                cred_for_predicate1['referent']: cred_for_predicate1}
    # Get attributes from ledger
    prover['schemas'], prover['cred_defs'], prover['revoc_states'] = \
        await prover_get_entities_from_ledger(prover['pool'], prover['did_for_verifier'],
                                              prover['creds_for_job_application_proof'], prover['name'])
    # Create the proof, specifiying what to reveal (all are verifiable, though here for ex. personal info stays hidden)
    prover['job_application_requested_creds'] = json.dumps({
        'self_attested_attributes': {
            'attr1_referent': 'Prover',
            'attr2_referent': 'SecondName',
            'attr6_referent': '123-45-6789'
        },
        'requested_attributes': {
            'attr3_referent': {'cred_id': cred_for_attr3['referent'], 'revealed': True},
            'attr4_referent': {'cred_id': cred_for_attr4['referent'], 'revealed': True},
            'attr5_referent': {'cred_id': cred_for_attr5['referent'], 'revealed': True},
        },
        'requested_predicates': {'predicate1_referent': {'cred_id': cred_for_predicate1['referent']}}
    })
    prover['job_application_proof'] = \
        await anoncreds.prover_create_proof(prover['wallet'], prover['job_application_proof_request'],
                                            prover['job_application_requested_creds'], prover['master_secret_id'],
                                            prover['schemas'], prover['cred_defs'], prover['revoc_states'])
    # Authenticate, encrypt and send
    prover['authcrypted_job_application_proof'] = \
        await crypto.auth_crypt(prover['wallet'], prover['key_for_verifier'], prover['verifier_key_for_prover'],
                                prover['job_application_proof'].encode('utf-8'))
    verifier['authcrypted_job_application_proof'] = prover['authcrypted_job_application_proof']


    print('Verifier getting proof and verifying credential...')
    # Decrypt
    _, verifier['job_application_proof'], decrypted_job_application_proof = \
        await auth_decrypt(verifier['wallet'], verifier['key_for_prover'], verifier['authcrypted_job_application_proof'])
    # Get credential attribute values from ledger
    verifier['schemas'], verifier['cred_defs'], verifier['revoc_ref_defs'], verifier['revoc_regs'] = \
        await verifier_get_entities_from_ledger(verifier['pool'], verifier['did'],
                                                decrypted_job_application_proof['identifiers'], verifier['name'])
    # Assert everything is as claimed by the prover and verify
    assert 'Bachelor of Science, Marketing' == \
           decrypted_job_application_proof['requested_proof']['revealed_attrs']['attr3_referent']['raw']
    assert 'graduated' == \
           decrypted_job_application_proof['requested_proof']['revealed_attrs']['attr4_referent']['raw']
    assert '123-45-6789' == \
           decrypted_job_application_proof['requested_proof']['revealed_attrs']['attr5_referent']['raw']

    assert 'Prover' == decrypted_job_application_proof['requested_proof']['self_attested_attrs']['attr1_referent']
    assert 'SecondName' == decrypted_job_application_proof['requested_proof']['self_attested_attrs']['attr2_referent']
    assert '123-45-6789' == decrypted_job_application_proof['requested_proof']['self_attested_attrs']['attr6_referent']
    assert await anoncreds.verifier_verify_proof(verifier['job_application_proof_request'], verifier['job_application_proof'],
                                                 verifier['schemas'], verifier['cred_defs'], verifier['revoc_ref_defs'],
                                                 verifier['revoc_regs'])

    print('Credential verified.')
    print(steward.keys())
    print(issuer.keys())
    print(prover.keys())
    print(verifier.keys())




async def onboarding(_from, to):
    logger.info("\"{}\" -> Create and store in Wallet \"{} {}\" DID".format(_from['name'], _from['name'], to['name']))
    (from_to_did, from_to_key) = await did.create_and_store_my_did(_from['wallet'], "{}")

    logger.info("\"{}\" -> Send Nym to Ledger for \"{} {}\" DID".format(_from['name'], _from['name'], to['name']))
    await send_nym(_from['pool'], _from['wallet'], _from['did'], from_to_did, from_to_key, None)

    logger.info("\"{}\" -> Send connection request to {} with \"{} {}\" DID and nonce"
                .format(_from['name'], to['name'], _from['name'], to['name']))
    connection_request = {
        'did': from_to_did,
        'nonce': 123456789
    }

    if 'wallet' not in to:
        logger.info("\"{}\" -> Create wallet".format(to['name']))
        try:
            await wallet.create_wallet(wallet_config("create", to['wallet_config']), wallet_credentials("create", to['wallet_credentials']))
        except IndyError as ex:
            if ex.error_code == ErrorCode.PoolLedgerConfigAlreadyExistsError:
                pass
        to['wallet'] = await wallet.open_wallet(wallet_config("open", to['wallet_config']), wallet_credentials("open", to['wallet_credentials']))

    logger.info("\"{}\" -> Create and store in Wallet \"{} {}\" DID".format(to['name'], to['name'], _from['name']))
    (to_from_did, to_from_key) = await did.create_and_store_my_did(to['wallet'], "{}")

    logger.info("\"{}\" -> Get key for did from \"{}\" connection request".format(to['name'], _from['name']))
    from_to_verkey = await did.key_for_did(_from['pool'], to['wallet'], connection_request['did'])

    logger.info("\"{}\" -> Anoncrypt connection response for \"{}\" with \"{} {}\" DID, verkey and nonce"
                .format(to['name'], _from['name'], to['name'], _from['name']))
    to['connection_response'] = json.dumps({
        'did': to_from_did,
        'verkey': to_from_key,
        'nonce': connection_request['nonce']
    })
    to['anoncrypted_connection_response'] = \
        await crypto.anon_crypt(from_to_verkey, to['connection_response'].encode('utf-8'))

    logger.info("\"{}\" -> Send anoncrypted connection response to \"{}\"".format(to['name'], _from['name']))
    _from['anoncrypted_connection_response'] = to['anoncrypted_connection_response']

    logger.info("\"{}\" -> Anondecrypt connection response from \"{}\"".format(_from['name'], to['name']))
    _from['connection_response'] = \
        json.loads((await crypto.anon_decrypt(_from['wallet'], from_to_key,
                                              _from['anoncrypted_connection_response'])).decode("utf-8"))

    logger.info("\"{}\" -> Authenticates \"{}\" by comparision of Nonce".format(_from['name'], to['name']))
    assert connection_request['nonce'] == _from['connection_response']['nonce']

    logger.info("\"{}\" -> Send Nym to Ledger for \"{} {}\" DID".format(_from['name'], to['name'], _from['name']))
    await send_nym(_from['pool'], _from['wallet'], _from['did'], to_from_did, to_from_key, None)

    return from_to_did, from_to_key, to_from_did, to_from_key, _from['connection_response']

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

async def get_verinym(_from, from_to_did, from_to_key, to, to_from_did, to_from_key):
    logger.info("\"{}\" -> Create and store in Wallet \"{}\" new DID".format(to['name'], to['name']))
    (to_did, to_key) = await did.create_and_store_my_did(to['wallet'], "{}")

    logger.info("\"{}\" -> Authcrypt \"{} DID info\" for \"{}\"".format(to['name'], to['name'], _from['name']))
    to['did_info'] = json.dumps({
        'did': to_did,
        'verkey': to_key
    })
    to['authcrypted_did_info'] = \
        await crypto.auth_crypt(to['wallet'], to_from_key, from_to_key, to['did_info'].encode('utf-8'))

    logger.info("\"{}\" -> Send authcrypted \"{} DID info\" to {}".format(to['name'], to['name'], _from['name']))

    logger.info("\"{}\" -> Authdecrypted \"{} DID info\" from {}".format(_from['name'], to['name'], to['name']))
    sender_verkey, authdecrypted_did_info_json, authdecrypted_did_info = \
        await auth_decrypt(_from['wallet'], from_to_key, to['authcrypted_did_info'])

    logger.info("\"{}\" -> Authenticate {} by comparision of Verkeys".format(_from['name'], to['name'], ))
    assert sender_verkey == await did.key_for_did(_from['pool'], _from['wallet'], to_from_did)

    logger.info("\"{}\" -> Send Nym to Ledger for \"{} DID\" with {} Role"
                .format(_from['name'], to['name'], to['role']))
    await send_nym(_from['pool'], _from['wallet'], _from['did'], authdecrypted_did_info['did'],
                   authdecrypted_did_info['verkey'], to['role'])

    return to_did


async def send_nym(pool_handle, wallet_handle, _did, new_did, new_key, role):
    nym_request = await ledger.build_nym_request(_did, new_did, new_key, None, role)
    await ledger.sign_and_submit_request(pool_handle, wallet_handle, _did, nym_request)


async def send_schema(pool_handle, wallet_handle, _did, schema):
    schema_request = await ledger.build_schema_request(_did, schema)
    await ledger.sign_and_submit_request(pool_handle, wallet_handle, _did, schema_request)


async def send_cred_def(pool_handle, wallet_handle, _did, cred_def_json):
    cred_def_request = await ledger.build_cred_def_request(_did, cred_def_json)
    await ledger.sign_and_submit_request(pool_handle, wallet_handle, _did, cred_def_request)


async def get_schema(pool_handle, _did, schema_id):
    get_schema_request = await ledger.build_get_schema_request(_did, schema_id)
    get_schema_response = await ledger.submit_request(pool_handle, get_schema_request)
    return await ledger.parse_get_schema_response(get_schema_response)


async def get_cred_def(pool_handle, _did, cred_def_id):
    get_cred_def_request = await ledger.build_get_cred_def_request(_did, cred_def_id)
    get_cred_def_response = await ledger.submit_request(pool_handle, get_cred_def_request)
    return await ledger.parse_get_cred_def_response(get_cred_def_response)


async def get_credential_for_referent(search_handle, referent):
    credentials = json.loads(
        await anoncreds.prover_fetch_credentials_for_proof_req(search_handle, referent, 10))
    return credentials[0]['cred_info']


async def prover_get_entities_from_ledger(pool_handle, _did, identifiers, actor):
    schemas = {}
    cred_defs = {}
    rev_states = {}
    for item in identifiers.values():
        logger.info("\"{}\" -> Get Schema from Ledger".format(actor))
        (received_schema_id, received_schema) = await get_schema(pool_handle, _did, item['schema_id'])
        schemas[received_schema_id] = json.loads(received_schema)

        logger.info("\"{}\" -> Get Claim Definition from Ledger".format(actor))
        (received_cred_def_id, received_cred_def) = await get_cred_def(pool_handle, _did, item['cred_def_id'])
        cred_defs[received_cred_def_id] = json.loads(received_cred_def)

        if 'rev_reg_seq_no' in item:
            pass  # TODO Create Revocation States

    return json.dumps(schemas), json.dumps(cred_defs), json.dumps(rev_states)


async def verifier_get_entities_from_ledger(pool_handle, _did, identifiers, actor):
    schemas = {}
    cred_defs = {}
    rev_reg_defs = {}
    rev_regs = {}
    for item in identifiers:
        logger.info("\"{}\" -> Get Schema from Ledger".format(actor))
        (received_schema_id, received_schema) = await get_schema(pool_handle, _did, item['schema_id'])
        schemas[received_schema_id] = json.loads(received_schema)

        logger.info("\"{}\" -> Get Claim Definition from Ledger".format(actor))
        (received_cred_def_id, received_cred_def) = await get_cred_def(pool_handle, _did, item['cred_def_id'])
        cred_defs[received_cred_def_id] = json.loads(received_cred_def)

        if 'rev_reg_seq_no' in item:
            pass  # TODO Get Revocation Definitions and Revocation Registries

    return json.dumps(schemas), json.dumps(cred_defs), json.dumps(rev_reg_defs), json.dumps(rev_regs)


async def auth_decrypt(wallet_handle, key, message):
    from_verkey, decrypted_message_json = await crypto.auth_decrypt(wallet_handle, key, message)
    decrypted_message_json = decrypted_message_json.decode("utf-8")
    decrypted_message = json.loads(decrypted_message_json)
    return from_verkey, decrypted_message_json, decrypted_message


if __name__ == '__main__':
    run_coroutine(run)
    time.sleep(1)  # FIXME waiting for libindy thread complete