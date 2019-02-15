import os, requests, json, time
from quart import Quart, render_template, redirect, url_for, session, request, jsonify
from sovrin.utilities import generate_base58, run_coroutine
from sovrin.setup import setup_pool, set_self_up, teardown
from sovrin.onboarding import onboarding_anchor_send, onboarding_onboardee_receive_and_send
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


@app.route('/')
def index():
    global issuer, received_data
    setup = True if issuer != {} else False
    have_data = True if received_data != '' else False
    return render_template('issuer.html', actor = 'issuer', setup = setup, have_data = have_data)
 

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
    global issuer, received_data
    data = json.loads(received_data)
    issuer, anoncrypted_connection_response = await onboarding_onboardee_receive_and_send(issuer, data, pool_handle, 'steward')
    requests.post('http://' + request.remote_addr + ':' + str(receiver_port) + '/establish_channel', anoncrypted_connection_response)
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
