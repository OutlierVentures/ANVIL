import os, requests, json, time, asyncio, subprocess
from quart import Quart, render_template, redirect, url_for, request
from common import common_setup, common_respond, common_get_verinym, common_reset, common_connection_request, common_establish_channel, common_verinym_request
from sovrin.schema import create_schema, create_credential_definition
from sovrin.credentials import offer_credential, create_and_send_credential
from sovrin.proofs import request_proof_of_credential, verify_proof
from fetch.verifier import Verifier
from oef.query import Query, Constraint, Eq
app = Quart(__name__)

debug = False # Do not enable in production
host = '0.0.0.0'
# In production everyone runs on same port, use multiple here for same-machine testing 
port = 5003
anchor_port = 5000
prover_port = 5002

# Globals approach will be dropped once session persistence in Python is fixed.
verifier = {}
request_ip = anchor_ip = received_data = counterparty_name = search = False
pool_handle = 1


@app.route('/')
def index():
    setup = True if verifier else False
    have_data = True if received_data else False
    responded = True if 'connection_response' in verifier else False
    '''
    The onboardee depends on the anchor to finish establishing the secure channel.
    However the request-reponse messaging means the onboardee cannot proceed until it is:
    the functions made available by the channel_established variable wait until the
    relevant response from the anchor is returned, which is only possible if the channel
    is set up on the anchor end.
    '''
    channel_established = True if anchor_ip else False
    prover_registered = True if 'prover_ip' in verifier else False
    have_verinym = True if 'did_info' in verifier else False
    credential_requested = True if 'authcrypted_cred_request' in verifier else False
    have_proof = True if 'authcrypted_proof' in verifier else False
    search_results = verifier['search_results'].strip('"[]\'').replace(',', ', ') if 'search_results' in verifier else False
    return render_template('verifier.html', actor = 'VERIFIER', setup = setup, have_data = have_data, request_ip = request_ip, responded = responded, channel_established = channel_established, have_verinym = have_verinym, prover_registered = prover_registered, credential_requested = credential_requested, have_proof = have_proof, search_results = search_results)
 

@app.route('/setup', methods = ['GET', 'POST'])
async def setup():
    global verifier, pool_handle
    verifier, pool_handle = await common_setup(verifier, pool_handle, 'verifier')
    return redirect(url_for('index'))


'''
Rudimentary Fetch search engine.
Fairly easy to flesh out given the rich query sub-language – see Fetch SDK docs.
'''
@app.route('/search_for_services', methods = ['GET', 'POST'])
async def search_for_services():
    global verifier
    form = await request.form
    search_terms = form['searchterms'].replace(' ', '_').replace(',', '_')
    verifier['search_terms'] = search_terms
    subprocess.run('python3 ./fetch/searcher.py ' + search_terms, shell = True)
    if os.path.isfile('search_results.json'):
        with open('search_results.json') as file_:
            verifier['search_results'] = json.load(file_)
    return redirect(url_for('index'))



@app.route('/receive', methods = ['GET', 'POST'])
async def data():
    global received_data, request_ip
    received_data = await request.data
    request_ip = request.remote_addr
    print(received_data)
    return '200'


@app.route('/respond', methods = ['GET', 'POST'])
async def respond():
    global verifier, anchor_ip
    verifier, anchor_ip = await common_respond(verifier, received_data, pool_handle, anchor_port)
    return redirect(url_for('index'))


@app.route('/get_verinym', methods = ['GET', 'POST'])
async def get_verinym():
    global verifier
    verifier = await common_get_verinym(verifier, anchor_ip, anchor_port)
    return redirect(url_for('index'))


@app.route('/connection_request', methods = ['GET', 'POST'])
async def connection_request():
    global verifier, counterparty_name
    verifier, counterparty_name = await common_connection_request(verifier)
    return redirect(url_for('index'))


@app.route('/establish_channel', methods = ['GET', 'POST'])
async def establish_channel():
    global verifier
    verifier = await common_establish_channel(verifier, counterparty_name)
    # Connection with multiple actor types (e.g. steward + prover) demands registering this at the app level
    verifier['prover_ip'] = request.remote_addr
    return '200'


@app.route('/verinym_request', methods = ['GET', 'POST'])
async def verinym_request():
    global verifier
    verifier = await common_verinym_request(verifier, counterparty_name)
    return '200'


@app.route('/request_proof', methods = ['GET', 'POST'])
async def request_proof():
    global verifier
    try:
        form = await request.form
        proof_request = json.loads(form['proofrequest'])
        '''
        Proof requests have 2 parts:
        1. Request: the requested attributes/predicates (to be sent to prover).
        2. Assertions: the assertions about the attributes/predicates to ensure are true.
        '''
        request_json = json.dumps(proof_request['request'])
        verifier['assertions_to_make'] = proof_request['assertions_to_make']
        verifier = await request_proof_of_credential(verifier, request_json)
        requests.post('http://' + verifier['prover_ip'] + ':' + str(prover_port) + '/proof_request', verifier['authcrypted_proof_request'])
        return redirect(url_for('index'))
    except:
        return 'Invalid proof request. Check formatting.'


@app.route('/proof_inbox', methods = ['GET', 'POST'])
async def proof_inbox():
    global verifier
    verifier['authcrypted_proof'] = await request.data
    return '200'


@app.route('/verify', methods = ['GET', 'POST'])
async def verify():
    global verifier
    try:
        verifier = await verify_proof(verifier, verifier['assertions_to_make'])
        # Hide verify function until next proof received
        verifier.pop('authcrypted_proof', None)
        return redirect(url_for('index'))
    except:
        return 'Proof invalid. Potentially check your own assertions on the values.'


@app.route('/purchase_service', methods = ['GET', 'POST'])
async def purchase_service():
    form = await request.form
    max_price = form['maxprice']
    search_terms = verifier['search_terms']
    subprocess.run('python3 ./fetch/verifier.py ' + search_terms + ' ' + max_price, shell = True)
    return redirect(url_for('index'))


@app.route('/reset')
async def reset():
    global verifier, pool_handle, received_data, anchor_ip
    verifier, pool_handle = await common_reset([verifier], pool_handle)
    received_data = False
    anchor_ip = False
    return redirect(url_for('index'))


@app.route('/reload')
def reload():
    return redirect(url_for('index'))


if __name__ == '__main__':
    app.secret_key = os.getenv('ANVIL_KEY', 'MUST_BE_STATIC')
    app.run(host, port, debug)
