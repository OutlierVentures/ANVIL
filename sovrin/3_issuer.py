from sovrin_utilities import run_coroutine, read_json, write_json, send_data, receive_data
from onboarding import simple_onboard

from credentials import create_schema, create_credential_definition
from issue import offer_credential

async def run():
    pool_config = read_json('pool_config')
    steward = read_json('steward_config')
    print(steward)
    issuer, steward = await simple_onboard(pool_handle = pool_config['pool_handle'],
                                           anchor = steward,
                                           name = 'issuer',
                                           id_ = 'mocked_issuer_id',
                                           key = 'mocked_issuer_key')
    
    write_json(issuer, 'steward_config')
    # Create schema and corresponding definition
    schema_dict = read_json('../example_data/service_example/credential_schema')
    schema = schema_dict['restricted']
    unique_schema_name, schema_id, issuer = await create_schema(schema, issuer)
    issuer = await create_credential_definition(issuer, schema_id, unique_schema_name, revocable = False)
    # Issue credential
    issuer = await offer_credential(issuer, unique_schema_name)
    send_data(issuer['authcrypted_certificate_cred_offer'], 0)
    send_data(unique_schema_name, 1)

if __name__ == '__main__':
    run_coroutine(run)