'''
Sovrin functions for creating credential schema and credential definitions.
'''

import json, time, random
from indy import anoncreds, ledger

    
async def create_schema(schema, creator):
    creator_name = creator['name'].capitalize()
    print(creator_name + ' creating credential schema...')
    '''
    Unique schema name: helps prevent clashes in the schema referenced.
    If 10 independent schema with identical names are used in the same session
    and between the same parties, the percentage chance of a clash is
    (1 - ((26^4 - 1) / 26^4)^10) * 100 = 0.002%
    This comes at the cost of 4 random characters in the attribute string.
    '''
    unique_schema_name = schema['name'].replace(' ', '_').replace('-', '_').lower()# + '_'.join(random.choice('abcdefghijklmnopqrstuvwxyz') for i in range(4))
    (creator['schema_id'], creator[unique_schema_name + '_schema']) = \
        await anoncreds.issuer_create_schema(creator['did'], schema['name'], schema['version'],
                                             json.dumps(schema['attributes']))
    schema_id = creator['schema_id']
    # Send schema to ledger
    await send_schema(creator['pool'], creator['wallet'], creator['did'], creator[unique_schema_name + '_schema'])
    return unique_schema_name, schema_id, creator
    

async def create_credential_definition(creator, schema_id, unique_schema_name, revocable = False):
    creator_name = creator['name'].capitalize()
    print(creator_name + ' applying credential definition...')
    time.sleep(1)  # sleep 1 second before getting schema
    (creator['schema_id'], creator[unique_schema_name + '_schema']) = \
        await get_schema(creator['pool'], creator['did'], schema_id)
    # Create and store credential definition in wallet
    certificate_cred_def = {
        'tag': 'TAG1',
        'type': 'CL',
        'config': {
            "support_revocation": revocable
        }
    }
    (creator[unique_schema_name + '_cred_def_id'], creator[unique_schema_name + '_cred_def']) = \
        await anoncreds.issuer_create_and_store_credential_def(creator['wallet'], creator['did'],
                                                               creator[unique_schema_name + '_schema'], certificate_cred_def['tag'],
                                                               certificate_cred_def['type'],
                                                               json.dumps(certificate_cred_def['config']))
    # Send definition to ledger
    await send_cred_def(creator['pool'], creator['wallet'], creator['did'], creator[unique_schema_name + '_cred_def'])
    return creator


async def send_schema(pool_handle, wallet_handle, _did, schema):
    schema_request = await ledger.build_schema_request(_did, schema)
    await ledger.sign_and_submit_request(pool_handle, wallet_handle, _did, schema_request)


async def get_schema(pool_handle, _did, schema_id):
    get_schema_request = await ledger.build_get_schema_request(_did, schema_id)
    get_schema_response = await ledger.submit_request(pool_handle, get_schema_request)
    return await ledger.parse_get_schema_response(get_schema_response)


async def send_cred_def(pool_handle, wallet_handle, _did, cred_def_json):
    cred_def_request = await ledger.build_cred_def_request(_did, cred_def_json)
    await ledger.sign_and_submit_request(pool_handle, wallet_handle, _did, cred_def_request)