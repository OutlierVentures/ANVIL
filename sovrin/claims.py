import logging, argparse, sys, json, time, os, secrets

from ctypes import CDLL

from sovrin_utilities import run_coroutine

from setup import setup_pool, setup_steward
from onboarding import simple_onboard, onboard_for_proving, onboarding
from schema import * # Schema to use in this file
from credentials import create_schema, create_credential_definition
from issue import offer_credential, receive_credential_offer, request_credential, create_and_send_credential, store_credential
from verify import request_proof_of_credential, create_proof_of_credential, verify_proof


# OPTIONS
schema = degree


logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.WARN)

parser = argparse.ArgumentParser(description='Run python getting-started scenario (Prover/Issuer)')
parser.add_argument('-t', '--storage_type', help='load custom wallet storage plug-in')
parser.add_argument('-l', '--library', help='dynamic library to load for plug-in')
parser.add_argument('-e', '--entrypoint', help='entry point for dynamic library')
parser.add_argument('-c', '--config', help='entry point for dynamic library')
parser.add_argument('-s', '--creds', help='entry point for dynamic library')

args = parser.parse_args()


# Check if we need to dyna-load a custom wallet storage plug-in
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

    cred_request, schema, proof_request, self_attested_attributes, requested_attributes, \
    requested_predicates, non_issuer_attributes = load_example_data()

    # Add a nonce to the proof request and stringify
    proof_request['nonce'] = secrets.token_hex(16)

    # Requests need to be json formatted
    proof_request = json.dumps(proof_request)
    cred_request = json.dumps(cred_request)

    # Set up actors
    pool_ = await setup_pool('ANVIL')
    steward = await setup_steward(pool_ = pool_,
                                  name = 'Steward',
                                  id_ = 'mocked_steward_id',
                                  key = 'mocked_steward_key',
                                  seed = '000000000000000000000000Steward1')
    issuer, steward = await simple_onboard(pool_ = pool_,
                                           anchor = steward,
                                           name = 'issuer',
                                           id_ = 'mocked_issuer_id',
                                           key = 'mocked_issuer_key')
    prover, issuer = await onboard_for_proving(pool_ = pool_,
                                               anchor = issuer,
                                               name = 'prover',
                                               id_ = 'mocked_prover_id',
                                               key = 'mocked_prover_key')
    verifier, steward = await simple_onboard(pool_ = pool_,
                                             anchor = steward,
                                             name = 'verifier',
                                             id_ = 'mocked_verifier_id',
                                             key = 'mocked_verifier_key')
    
    
    # Create schema and corresponding definition
    unique_schema_name, schema_id, issuer = await create_schema(schema, issuer)
    issuer = await create_credential_definition(issuer, schema_id, unique_schema_name, revocable = False)

    '''
    # Specify cred_request for credential request
    cred_request = json.dumps({
        "first_name": {"raw": "Prover", "encoded": "1139481716457488690172217916278103335"},
        "last_name": {"raw": "SecondName", "encoded": "5321642780241790123587902456789123452"},
        "degree": {"raw": "Bachelor of Science, Marketing", "encoded": "12434523576212321"},
        "status": {"raw": "graduated", "encoded": "2213454313412354"},
        "ssn": {"raw": "123-45-6789", "encoded": "3124141231422543541"},
        "year": {"raw": "2015", "encoded": "2015"},
        "average": {"raw": "5", "encoded": "5"}
    })
    '''

    # Issue credential
    issuer, prover = await offer_credential(issuer, prover, unique_schema_name)
    prover = await receive_credential_offer(prover, unique_schema_name)
    prover, issuer = await request_credential(prover, issuer, cred_request, unique_schema_name)
    issuer, prover = await create_and_send_credential(issuer, prover, unique_schema_name)
    prover = await store_credential(prover, unique_schema_name)


    '''
    # Specify proof request
    proof_request = json.dumps({
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
                #'restrictions': [{'cred_def_id': issuer[unique_schema_name + '_cred_def_id']}]
            },
            'attr4_referent': {
                'name': 'status',
                #'restrictions': [{'cred_def_id': issuer[unique_schema_name + '_cred_def_id']}]
            },
            'attr5_referent': {
                'name': 'ssn',
                #'restrictions': [{'cred_def_id': issuer[unique_schema_name + '_cred_def_id']}]
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
                #'restrictions': [{'cred_def_id': issuer[unique_schema_name + '_cred_def_id']}]
            }
        }
    })
    '''

    verifier, prover = await request_proof_of_credential(verifier, prover, proof_request)
    '''
    self_attested_attributes = {
        'attr1_referent': 'Prover',
        'attr2_referent': 'SecondName',
        'attr6_referent': '123-45-6789'
    }
    requested_attributes = [3, 4, 5] # Used in proof creation and verification
    requested_predicates = [1]
    # Specify attributes that should not be queried of the issuer
    non_issuer_attributes = [6]
    '''

    prover, verifier = await create_proof_of_credential(prover, verifier, self_attested_attributes,
                                                        requested_attributes, requested_predicates,
                                                        non_issuer_attributes)


    assertions_to_make = {
        'revealed': {
            'attr3_referent': 'Bachelor of Science, Marketing',
            'attr4_referent': 'graduated',
            'attr5_referent': '123-45-6789'
        },
        'self_attested': {
            'attr1_referent': 'Prover',
            'attr2_referent': 'SecondName',
            'attr6_referent': '123-45-6789',
        }
        
    }

    verifier = await verify_proof(verifier, assertions_to_make)

    print('Credential verified.')


# Loads examples in the example_data folder
def load_example_data():
    example_data = {}
    for filename in os.listdir('../example_data'):
        with open('../example_data/' + filename) as file_:
            example_data[filename.replace('.json', '')] = json.load(file_)
    cred_request = example_data['credential_request']
    # Specify version of schema since defined two in example file
    schema = example_data['credential_schema']#['restricted'] # Restricted for new example data
    print(schema)
    print(type(schema))
    proof_request = example_data['proof_request']
    # Don't json.dump this
    self_attested_attributes = example_data['proof_creation']['self_attested_attributes']
    requested_attributes = example_data['proof_creation']['requested_attributes']
    requested_predicates = example_data['proof_creation']['requested_predicates']
    non_issuer_attributes = example_data['proof_creation']['non_issuer_attributes']
    return cred_request, schema, proof_request, self_attested_attributes, \
           requested_attributes, requested_predicates, non_issuer_attributes

if __name__ == '__main__':
    run_coroutine(run)
    time.sleep(1)  # FIXME waiting for libindy thread complete
