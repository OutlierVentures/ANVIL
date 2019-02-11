import logging, argparse, sys, json, time, os, secrets

from ctypes import CDLL

from sovrin_utilities import run_coroutine

from setup import setup_pool, setup_steward, teardown
from onboarding import simple_onboard, onboard_for_proving, onboarding
from credentials import create_schema, create_credential_definition
from issue import offer_credential, receive_credential_offer, request_credential, create_and_send_credential, store_credential
from proofs import request_proof_of_credential, create_proof_of_credential, verify_proof


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
        print('Error unable to load wallet storage', result)
        parser.print_help()
        sys.exit(0)

    print('Success, loaded wallet storage', args.storage_type)


async def run():

    cred_request, schema, proof_request, assertions_to_make, self_attested_attributes, \
    requested_attributes, requested_predicates, non_issuer_attributes \
    = load_example_data('../example_data/service_example/')

    # Add a nonce to the proof request and stringify
    proof_request['nonce'] = secrets.token_hex(16)

    # Requests need to be json formatted
    proof_request = json.dumps(proof_request)
    cred_request = json.dumps(cred_request)

    # Set up actors - LOAD KEYS AS ENVIRONMENT VARIABLES
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

    # Issue credential
    issuer = await offer_credential(issuer, unique_schema_name)
    send_data(issuer['authcrypted_certificate_cred_offer'])
    prover['authcrypted_certificate_cred_offer'] = receive_data()

    prover = await receive_credential_offer(prover, unique_schema_name)
    prover = await request_credential(prover, cred_request, unique_schema_name)
    send_data(prover['authcrypted_certificate_cred_request'])
    issuer['authcrypted_certificate_cred_request'] = receive_data()


    issuer['prover_certificate_cred_values'] = prover[unique_schema_name + '_cred_values']
    issuer = await create_and_send_credential(issuer, unique_schema_name)
    send_data(issuer['authcrypted_certificate_cred'])
    prover['authcrypted_certificate_cred'] = receive_data()

    prover = await store_credential(prover, unique_schema_name)
    

    # Prover onboarded with verifier
    verifier['did_for_prover'], verifier['key_for_prover'], prover['did_for_verifier'], prover['key_for_verifier'], \
    verifier['prover_connection_response'] = await onboarding(verifier, prover)
    verifier = await request_proof_of_credential(verifier, proof_request)
    send_data(verifier['authcrypted_proof_request'])
    prover['authcrypted_proof_request'] = receive_data()


    try:
        prover = await create_proof_of_credential(prover, self_attested_attributes, requested_attributes,
                                              requested_predicates, non_issuer_attributes)
    except:
        print('ERROR: PROOF CREATION FAILED.\n\
IF THE ERROR CODE ABOVE IS 113, THIS IS A KNOWN BUG OF HYPERLEDGER INDY.\n\
FIX: JUST RUN THE CLAIMS PROCESS AGAIN.')
        await teardown(pool_, [steward, issuer, prover, verifier])
    
    send_data(prover['authcrypted_proof'])
    verifier['authcrypted_proof'] = receive_data()

    verifier = await verify_proof(verifier, assertions_to_make)

    await teardown(pool_, [steward, issuer, prover, verifier])

    print('Credential verified.')


# Loads examples in the example_data folder
def load_example_data(path):
    example_data = {}
    for filename in os.listdir(path):
        with open(path + filename) as file_:
            example_data[filename.replace('.json', '')] = json.load(file_)
    cred_request = example_data['credential_request']
    # Specify schema version
    schema = example_data['credential_schema']['restricted']
    proof_request = example_data['proof_request']['request']
    assertions_to_make = example_data['proof_request']['assertions_to_make']
    # Don't json.dump this
    self_attested_attributes = example_data['proof_creation']['self_attested_attributes']
    requested_attributes = example_data['proof_creation']['requested_attributes']
    requested_predicates = example_data['proof_creation']['requested_predicates']
    non_issuer_attributes = example_data['proof_creation']['non_issuer_attributes']
    return cred_request, schema, proof_request, assertions_to_make, self_attested_attributes, \
           requested_attributes, requested_predicates, non_issuer_attributes


# Send data to another actor. Currently saves to a network simulation temp file.
def send_data(data):
    f = open('temp', 'wb')
    f.write(data)
    f.close()

# Receive data from another actor. Currently loads data from a network simulation file.
def receive_data():
    f = open('temp', 'rb')
    data = f.read()
    f.close()
    return data


if __name__ == '__main__':
    run_coroutine(run)
    time.sleep(1)  # FIXME waiting for libindy thread complete
