import os, requests, json, time
from quart import Quart, render_template, redirect, url_for, request
from common import common_setup, common_respond, common_get_verinym, common_reset, common_connection_request, common_establish_channel, common_verinym_request
from sovrin.schema import create_schema, create_credential_definition
from sovrin.credentials import offer_credential, create_and_send_credential
app = Quart(__name__)

debug = True # Do not enable in production
host = '0.0.0.0'
# In production everyone runs on same port, use 2 here for same-machine testing 
port = 5003
receiver_port = 5000
prover_port = 5002

# Globals approach will be dropped once session persistence in Python is fixed.
verifier = {}
request_ip = anchor_ip = received_data = counterparty_name = False
pool_handle = 1
created_schema = []


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
    prover_registered = True if 'prover_registered' in verifier else False
    have_verinym = True if 'did_info' in verifier else False
    credential_requested = True if 'authcrypted_cred_request' in verifier else False
    return render_template('verifier.html', actor = 'verifier', setup = setup, have_data = have_data, request_ip = request_ip, responded = responded, channel_established = channel_established, have_verinym = have_verinym, created_schema = created_schema, prover_registered = prover_registered, credential_requested = credential_requested, counterparty_name = counterparty_name)
 

@app.route('/setup', methods = ['GET', 'POST'])
async def setup():
    global verifier, pool_handle
    verifier, pool_handle = await common_setup(verifier, pool_handle, 'verifier')
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
    verifier, anchor_ip = await common_respond(verifier, received_data, pool_handle, receiver_port)
    return redirect(url_for('index'))


@app.route('/get_verinym', methods = ['GET', 'POST'])
async def get_verinym():
    global verifier
    verifier = await common_get_verinym(verifier, anchor_ip, receiver_port)
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
    verifier['prover_registered'] = 'yes'
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
        verifier = await request_proof_of_credential(verifier, proof_request)
        requests.post('http://' + anchor_ip + ':' + str(prover_port) + '/proof_request', verifier['authcrypted_proof_request'])
        return redirect(url_for('index'))
    except:
        return 'Invalid schema. Check formatting.'


@app.route('/reset')
def reset():
    global verifier, pool_handle, received_data, anchor_ip
    verifier, pool_handle = common_reset([verifier], pool_handle)
    received_data = ''
    anchor_ip = ''
    return redirect(url_for('index'))


@app.route('/reload')
def reload():
    return redirect(url_for('index'))


if __name__ == '__main__':
    app.secret_key = os.getenv('ANVIL_KEY', 'MUST_BE_STATIC')
    app.run(host, port, debug)
