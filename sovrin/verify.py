import json
from indy import anoncreds, did, crypto, ledger
from onboarding import onboarding

async def request_proof_of_credential(verifier, proof_request = {}):
    print('Verifier requesting proof of credential...')
    # Create proof request
    verifier['proof_request'] = proof_request
    # Get key for prover DID
    verifier['prover_key_for_verifier'] = \
        await did.key_for_did(verifier['pool'], verifier['wallet'], verifier['prover_connection_response']['did'])
    # Authenticate, encrypt and send
    verifier['authcrypted_proof_request'] = \
        await crypto.auth_crypt(verifier['wallet'], verifier['key_for_prover'], verifier['prover_key_for_verifier'],
                                verifier['proof_request'].encode('utf-8'))
    return verifier


'''
Self-attested attributes are provided as a dictionary with format
{'attr[i]_referent': '[value_of_attr_i]',...}
Requested attributes, predicates, and non-issuer attributes are provided as an array of indices. 
Non-issuer attributes refer to attributes in the proof request that the credential issuer does not have on file.
Self-attested predicates aren't included since they are (presumably) not helpful.
'''
async def create_proof_of_credential(prover, self_attested_attrs = {}, requested_attrs = [], requested_preds = [], non_issuer_attributes = []):
    print('Prover getting credential and creating proof...')
    num_attributes_to_search = len(self_attested_attrs) + len(requested_attrs) - len(non_issuer_attributes) 
    num_predicates = len(requested_preds)
    # Decrypt
    prover['verifier_key_for_prover'], prover['proof_request'], _ = \
        await auth_decrypt(prover['wallet'], prover['key_for_verifier'], prover['authcrypted_proof_request'])
    # Search for a proof request and get the credential attributes needed
    search_for_proof_request = \
        await anoncreds.prover_search_credentials_for_proof_req(prover['wallet'],
                                                                prover['proof_request'], None)
    # Grab attributes and predicates required
    cred_attrs = {}
    for i in range(1, num_attributes_to_search + 1):
        stri = str(i)
        print(stri) # REMOVE THIS LINE
        cred_attrs['cred_for_attr' + stri] = await get_credential_for_referent(search_for_proof_request, 'attr' + stri + '_referent')
    cred_predicates = {}
    for i in range(1, num_predicates + 1):
        stri = str(i)
        print(stri) # REMOVE THIS LINE
        cred_predicates['cred_for_predicate' + stri] = await get_credential_for_referent(search_for_proof_request, 'predicate' + stri + '_referent')
    await anoncreds.prover_close_credentials_search_for_proof_req(search_for_proof_request)
    # Put the needed attributes in Indy-readable format
    creds_for_proof = {}
    for _, value in cred_attrs.items():
        creds_for_proof[value['referent']] = value
    for _, value in cred_predicates.items():
        creds_for_proof[value['referent']] = value
    prover['creds_for_proof'] = creds_for_proof
    # Get attributes from ledger
    prover['schemas'], prover['cred_defs'], prover['revoc_states'] = \
        await prover_get_entities_from_ledger(prover['pool'], prover['did_for_verifier'],
                                              prover['creds_for_proof'], prover['name'])
    # Create the proof, specifiying what to reveal (NOTE: all verifiable whether revealed or not)
    requested_attrs_dict = {}
    for i in requested_attrs:
        stri = str(i)
        requested_attrs_dict['attr' + stri + '_referent'] = {'cred_id': cred_attrs['cred_for_attr' + stri]['referent'], 'revealed': True}
    requested_predicates_dict = {}
    for i in requested_preds:
        stri = str(i)
        requested_predicates_dict['predicate' + stri + '_referent'] = {'cred_id': cred_predicates['cred_for_predicate' + stri]['referent']}
    proof_request_reply_from_prover = json.dumps({
        'self_attested_attributes': self_attested_attrs,
        'requested_attributes': requested_attrs_dict,
        'requested_predicates': requested_predicates_dict
    })
    prover['requested_creds'] = proof_request_reply_from_prover
    prover['proof'] = \
        await anoncreds.prover_create_proof(prover['wallet'], prover['proof_request'],
                                            prover['requested_creds'], prover['master_secret_id'],
                                            prover['schemas'], prover['cred_defs'], prover['revoc_states'])
    # Authenticate, encrypt and send
    prover['authcrypted_proof'] = \
        await crypto.auth_crypt(prover['wallet'], prover['key_for_verifier'], prover['verifier_key_for_prover'],
                                prover['proof'].encode('utf-8'))
    return prover

async def verify_proof(verifier, assertions_to_make):
    print('Verifier getting proof and verifying credential...')
    # Decrypt
    _, verifier['proof'], decrypted_proof = \
        await auth_decrypt(verifier['wallet'], verifier['key_for_prover'], verifier['authcrypted_proof'])
    # Get credential attribute values from ledger
    verifier['schemas'], verifier['cred_defs'], verifier['revoc_ref_defs'], verifier['revoc_regs'] = \
        await verifier_get_entities_from_ledger(verifier['pool'], verifier['did'],
                                                decrypted_proof['identifiers'], verifier['name'])
    # Assert everything is as claimed by the prover and verify
    for key, value in assertions_to_make['revealed'].items():
        assert value == decrypted_proof['requested_proof']['revealed_attrs'][key]['raw']
    for key, value in assertions_to_make['self_attested'].items():
        assert value == decrypted_proof['requested_proof']['self_attested_attrs'][key]
    assert await anoncreds.verifier_verify_proof(verifier['proof_request'], verifier['proof'],
                                                 verifier['schemas'], verifier['cred_defs'], verifier['revoc_ref_defs'],
                                                 verifier['revoc_regs'])
    return verifier


async def auth_decrypt(wallet_handle, key, message):
    from_verkey, decrypted_message_json = await crypto.auth_decrypt(wallet_handle, key, message)
    decrypted_message_json = decrypted_message_json.decode("utf-8")
    decrypted_message = json.loads(decrypted_message_json)
    return from_verkey, decrypted_message_json, decrypted_message


async def get_credential_for_referent(search_handle, referent):
    credentials = json.loads(
        await anoncreds.prover_fetch_credentials_for_proof_req(search_handle, referent, 10))
    return credentials[0]['cred_info']


async def prover_get_entities_from_ledger(pool_handle, _did, identifiers, actor):
    schemas = {}
    cred_defs = {}
    rev_states = {}
    for item in identifiers.values():
        (received_schema_id, received_schema) = await get_schema(pool_handle, _did, item['schema_id'])
        schemas[received_schema_id] = json.loads(received_schema)
        (received_cred_def_id, received_cred_def) = await get_cred_def(pool_handle, _did, item['cred_def_id'])
        cred_defs[received_cred_def_id] = json.loads(received_cred_def)
        if 'rev_reg_seq_no' in item:
            pass # Revocation states not yet implemented in Sovrin's Python wrapper
    return json.dumps(schemas), json.dumps(cred_defs), json.dumps(rev_states)


async def get_schema(pool_handle, _did, schema_id):
    get_schema_request = await ledger.build_get_schema_request(_did, schema_id)
    get_schema_response = await ledger.submit_request(pool_handle, get_schema_request)
    return await ledger.parse_get_schema_response(get_schema_response)


async def get_cred_def(pool_handle, _did, cred_def_id):
    get_cred_def_request = await ledger.build_get_cred_def_request(_did, cred_def_id)
    get_cred_def_response = await ledger.submit_request(pool_handle, get_cred_def_request)
    return await ledger.parse_get_cred_def_response(get_cred_def_response)


async def verifier_get_entities_from_ledger(pool_handle, _did, identifiers, actor):
    schemas = {}
    cred_defs = {}
    rev_reg_defs = {}
    rev_regs = {}
    for item in identifiers:
        (received_schema_id, received_schema) = await get_schema(pool_handle, _did, item['schema_id'])
        schemas[received_schema_id] = json.loads(received_schema)
        (received_cred_def_id, received_cred_def) = await get_cred_def(pool_handle, _did, item['cred_def_id'])
        cred_defs[received_cred_def_id] = json.loads(received_cred_def)
        if 'rev_reg_seq_no' in item:
            pass # Revocation states not yet implemented in Sovrin's Python wrapper
    return json.dumps(schemas), json.dumps(cred_defs), json.dumps(rev_reg_defs), json.dumps(rev_regs)
