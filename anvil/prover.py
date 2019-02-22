import os, requests, json, time, subprocess
from quart import Quart, render_template, redirect, url_for, request
from common import common_setup, common_respond, common_get_verinym, common_reset
from sovrin.credentials import receive_credential_offer, request_credential, store_credential
from sovrin.proofs import create_proof_of_credential
app = Quart(__name__)

debug = True # Do not enable in production
host = '0.0.0.0'
# In production everyone runs on same port, use 2 here for same-machine testing 
port = 5002
issuer_port = 5001
verifier_port = 5003

# Globals approach will be dropped once session persistence in Python is fixed.
prover = {}
request_ip = anchor_ip = received_data = multiple_onboard = service_published = False
pool_handle = 1
stored_credentials = []


@app.route('/')
def index():
    setup = True if prover else False
    have_data = True if received_data else False
    responded = True if 'connection_response' in prover else False
    '''
    The onboardee depends on the anchor to finish establishing the secure channel.
    However the request-reponse messaging means the onboardee cannot proceed until it is:
    the functions made available by the channel_established variable wait until the
    relevant response from the anchor is returned, which is only possible if the channel
    is set up on the anchor end.
    '''
    channel_established = True if anchor_ip else False
    have_verinym = True if 'did_info' in prover else False
    unique_schema_name = prover['unique_schema_name'] if 'unique_schema_name' in prover else False
    have_proof_request = True if 'authcrypted_proof_request' in prover else False
    return render_template('prover.html', actor = 'prover', setup = setup, have_data = have_data, request_ip = request_ip, responded = responded, channel_established = channel_established, have_verinym = have_verinym, stored_credentials = stored_credentials, unique_schema_name = unique_schema_name, have_proof_request = have_proof_request, multiple_onboard = multiple_onboard, service_published = service_published)
 

@app.route('/setup', methods = ['GET', 'POST'])
async def setup():
    global prover, pool_handle
    prover, pool_handle = await common_setup(prover, pool_handle, 'prover')
    return redirect(url_for('index'))


@app.route('/publish_service', methods = ['GET', 'POST'])
async def publish_service():
    global service_published
    form = await request.form
    service_path = form['servicepath']
    price = form['price']
    subprocess.Popen('python3 ./fetch/prover.py ' + service_path + ' ' + price, shell = True)
    service_published = True
    return redirect(url_for('index'))


@app.route('/receive', methods = ['GET', 'POST'])
async def data():
    global prover, received_data, request_ip, anchor_ip
    received_data = await request.data
    request_ip = request.remote_addr
    # Drop any old connections
    prover.pop('connection_response', None)
    anchor_ip = False
    return '200'


@app.route('/respond', methods = ['GET', 'POST'])
async def respond():
    global prover, anchor_ip, issuer_port, multiple_onboard
    port = issuer_port
    # have_verinym as condition here doesn't work - see scoping
    if 'did_info' in prover:
        multiple_onboard = True
         # If all running on same machine, set manually
        port = verifier_port
    prover, anchor_ip = await common_respond(prover, received_data, pool_handle, port)
    return redirect(url_for('index'))


@app.route('/get_verinym', methods = ['GET', 'POST'])
async def get_verinym():
    global prover, multiple_onboard
    # If all running on same machine, set manually
    port = verifier_port if 'did_info' in prover else issuer_port
    prover = await common_get_verinym(prover, anchor_ip, port)
    # Hide get Verinym function if no new connection requests and all existing are set up
    multiple_onboard = False
    return redirect(url_for('index'))


@app.route('/credential_inbox', methods = ['GET', 'POST'])
async def credential_inbox():
    global prover
    prover['authcrypted_cred_offer'] = await request.data
    prover = await receive_credential_offer(prover)
    return '200'


@app.route('/request_credential', methods = ['GET', 'POST'])
async def request_credential_from_issuer():
    global prover
    try:
        form = await request.form
        credential_request = form['credrequest'] # Request credential demands a string-formatted JSON
        prover = await request_credential(prover, credential_request)
        requests.post('http://' + anchor_ip + ':' + str(issuer_port) + '/credential_request', prover['authcrypted_cred_request'])
        return redirect(url_for('index'))
    except:
        return 'Invalid credential request. Check formatting.'


@app.route('/credential_store', methods = ['GET', 'POST'])
async def credential_store():
    global prover, stored_credentials
    try:
        prover['authcrypted_cred'] = await request.data
        prover = await store_credential(prover)
        # May cause failure of block if schema exists but name hasnt been stored, store name if so
        stored_credentials.append(prover['unique_schema_name'])
        return '200'
    except:
        return 'Invalid credential. Check you are authcrypting with the verification key for this actor.'


@app.route('/proof_request', methods = ['GET', 'POST'])
async def proof_request():
    global prover, request_ip
    prover['authcrypted_proof_request'] = await request.data
    # Old request IP now has name anchor IP so can safely overwrite
    request_ip = request.remote_addr
    return '200'


@app.route('/create_and_send_proof', methods = ['GET', 'POST'])
async def create_and_send_proof():
    global prover
    try:
        form = await request.form
        proof = json.loads(form['proof'])
        prover = await create_proof_of_credential(prover, proof['self_attested_attributes'], proof['requested_attributes'],
                                                  proof['requested_predicates'], proof['non_issuer_attributes'])
        requests.post('http://' + request_ip + ':' + str(verifier_port) + '/proof_inbox', prover['authcrypted_proof'])
        # Stop ability to send proof until next request
        prover.pop('authcrypted_proof_request', None)
        return redirect(url_for('index'))
    except:
        return 'Invalid proof. Check formatting.'


@app.route('/reset')
def reset():
    global prover, pool_handle, received_data, anchor_ip, service_published
    prover, pool_handle = common_reset([prover], pool_handle)
    received_data = False
    anchor_ip = False
    service_published = False
    return redirect(url_for('index'))


@app.route('/reload')
def reload():
    return redirect(url_for('index'))


if __name__ == '__main__':
    app.secret_key = os.getenv('ANVIL_KEY', 'MUST_BE_STATIC')
    app.run(host, port, debug)
