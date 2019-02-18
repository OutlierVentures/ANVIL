import os, requests, time, json
from quart import Quart, render_template, redirect, url_for, session, request, jsonify
from sovrin.utilities import generate_base58, run_coroutine
from sovrin.setup import setup_pool, set_self_up, teardown
from sovrin.onboarding import onboarding_anchor_send, onboarding_anchor_receive, onboarding_anchor_register_onboardee_did
app = Quart(__name__)

debug = True # Do not enable in production
host = '0.0.0.0'
port = 5000

# Globals approach will be dropped once session persistence in Python is fixed.
steward = {}
pool_handle = 1


@app.route('/')
def index():
    global steward
    setup = True if steward != {} else False
    channel_established = True if 'connection_response' in steward else False
    return render_template('steward.html', actor = 'steward', setup = setup, channel_established = channel_established)


@app.route('/setup', methods = ['GET', 'POST'])
async def setup():
    global steward, pool_handle
    _, pool_handle = await setup_pool('ANVIL')
    id_ = os.getenv('WALLET_ID', generate_base58(64))
    key = os.getenv('WALLET_KEY', generate_base58(64))
    seed = os.getenv('SOVRIN_SEED', '000000000000000000000000Steward1')
    steward = await set_self_up('steward', id_, key, pool_handle, seed = seed)
    return redirect(url_for('index'))


@app.route('/connection_request', methods = ['GET', 'POST'])
async def connection_request():
    global steward
    form = await request.form  
    ip = form['ip_address']
    name = ''.join(e for e in form['name'] if e.isalnum())
    #print(steward)
    steward, connection_request = await onboarding_anchor_send(steward, name)
    requests.post('http://' + ip + '/receive', json = connection_request)
    return redirect(url_for('index'))


@app.route('/establish_channel', methods = ['GET', 'POST'])
async def establish_channel():
    global steward
    received_data = await request.data
    steward = await onboarding_anchor_receive(steward, received_data, 'issuer')
    print(steward.keys())
    print('CHANNEL ESTABLISHED ========')
    return '200'#redirect(url_for('index'))


'''
Creates a Verinym for onboardees with which a secure channel has been established,
throws an error otherwise. Establishes the onboardee as a new trust anchor on the ledger.
'''
@app.route('/verinym_request', methods = ['GET', 'POST'])
async def data():
    global steward
    verinym_request = await request.data
    steward = await onboarding_anchor_register_onboardee_did(steward, 'issuer', verinym_request)
    print(verinym_request)
    print('REGISTERED NEW TRUST ANCHOR ========')
    return '200'


@app.route('/reset')
def reset():
    global steward
    teardown('ANVIL', pool_handle, [steward])
    steward = {}
    session.clear() # Possibly unnecessary
    return redirect(url_for('index'))


@app.route('/reload')
def reload():
    return redirect(url_for('index'))


if __name__ == '__main__':
    app.secret_key = os.getenv('ANVIL_KEY', 'MUST_BE_STATIC')
    app.run(host, port, debug)
    
