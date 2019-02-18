import os, requests, json, time
from quart import Quart, render_template, redirect, url_for, session, request, jsonify
from sovrin.utilities import generate_base58, run_coroutine
from sovrin.setup import setup_pool, set_self_up, teardown
from sovrin.onboarding import onboarding_onboardee_receive_and_send, onboarding_onboardee_create_did
app = Quart(__name__)

debug = True # Do not enable in production
host = '0.0.0.0'
# In production everyone runs on same port, use 2 here for same-machine testing 
port = 5001
receiver_port = 5000 

# Globals approach will be dropped once session persistence in Python is fixed.
issuer = {}
pool_handle = 1
received_data = ''
steward_ip = ''


@app.route('/')
def index():
    global issuer, received_data
    setup = True if issuer != {} else False
    have_data = True if received_data != '' else False
    '''
    The onboardee depends on the anchor to finish establishing the secure channel.
    However the request-reponse messaging means the onboardee cannot proceed until it is:
    the functions made available by the channel_established variable wait until the
    relevant response from the anchor is returned, which is only possible if the channel
    is set up on the anchor end.
    '''
    channel_established = True if steward_ip != '' else False
    return render_template('issuer.html', actor = 'issuer', setup = setup, have_data = have_data, channel_established = channel_established)
 

@app.route('/setup', methods = ['GET', 'POST'])
async def setup():
    global issuer
    _, pool_handle = await setup_pool('ANVIL')
    id_ = os.getenv('WALLET_ID', generate_base58(64))
    key = os.getenv('WALLET_KEY', generate_base58(64))
    issuer = await set_self_up('issuer', id_, key, pool_handle)
    return redirect(url_for('index'))


@app.route('/receive', methods = ['GET', 'POST'])
async def data():
    global received_data
    received_data = await request.data
    print(received_data)
    return '200'


@app.route('/respond', methods = ['GET', 'POST'])
async def respond():
    global issuer, received_data, steward_ip
    steward_ip = request.remote_addr
    data = json.loads(received_data)
    issuer, anoncrypted_connection_response = await onboarding_onboardee_receive_and_send(issuer, data, pool_handle, 'steward')
    requests.post('http://' + steward_ip + ':' + str(receiver_port) + '/establish_channel', anoncrypted_connection_response)
    return redirect(url_for('index'))


@app.route('/get_verinym', methods = ['GET', 'POST'])
async def get_verinym():
    global issuer, steward_ip
    issuer, authcrypted_did_info = await onboarding_onboardee_create_did(issuer, 'steward')
    requests.post('http://' + steward_ip + ':' + str(receiver_port) + '/verinym_request', authcrypted_did_info)
    return redirect(url_for('index'))


@app.route('/reset')
def reset():
    global issuer
    teardown('ANVIL', pool_handle, [issuer])
    issuer = {}
    session.clear() # Possibly unnecessary
    return redirect(url_for('index'))


@app.route('/reload')
def reload():
    return redirect(url_for('index'))


if __name__ == '__main__':
    app.secret_key = os.getenv('ANVIL_KEY', 'MUST_BE_STATIC')
    app.run(host, port, debug)
