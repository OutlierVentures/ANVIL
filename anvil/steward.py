import os, requests, time
from quart import Quart, render_template, redirect, url_for, session, request, jsonify
from sovrin.utilities import generate_base58, run_coroutine
from sovrin.setup import setup_pool, set_self_up, teardown
from sovrin.onboarding import onboarding_anchor_send
app = Quart(__name__)

debug = True # Do not enable in production
host = '0.0.0.0'
port = 5000

steward = {}
pool_handle = 1


@app.route('/')
def index():
    global steward
    setup = True if steward != {} else False
    return render_template('steward.html', actor = 'steward', setup = setup)


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
    print(steward)
    steward, connection_request = await onboarding_anchor_send(steward, name)
    requests.post('http://' + ip + '/receive', json = connection_request)
    return redirect(url_for('index'))
    
@app.route('/establish_channel', methods = ['GET', 'POST'])
async def establish_channel():
    print('bruh')
    return '200'



@app.route('/reset')
def reset():
    global steward
    teardown('ANVIL', pool_handle, [steward])
    steward = {}
    session.clear() # Possibly unnecessary
    return redirect(url_for('index'))

if __name__ == '__main__':
    app.secret_key = os.getenv('ANVIL_KEY', 'MUST_BE_STATIC')
    app.run(host, port, debug)
    
