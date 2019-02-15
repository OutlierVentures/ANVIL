import os, requests, json, time
from quart import Quart, render_template, redirect, url_for, session, request, jsonify
from sovrin.utilities import generate_base58, run_coroutine
from sovrin.setup import setup_pool, set_self_up, teardown
from sovrin.onboarding import onboarding_anchor_send, onboarding_onboardee_receive_and_send
app = Quart(__name__)

debug = True # Do not enable in production
host = '0.0.0.0'
port = 5001


@app.route('/')
def index():
    issuer = session.get('issuer')
    setup = True if issuer else False
    return render_template('issuer.html', actor = 'issuer', setup = setup)


@app.route('/setup', methods = ['GET', 'POST'])
async def setup():
    session['pool_name'], session['pool_handle'] = await setup_pool('ANVIL')
    pool_handle = session.get('pool_handle')
    id_ = os.getenv('WALLET_ID', generate_base58(64))
    key = os.getenv('WALLET_KEY', generate_base58(64))
    session['issuer'] = await set_self_up('issuer', id_, key, session['pool_handle'])
    print(type(session['issuer']))
    return redirect(url_for('index'))


@app.route('/data', methods = ['GET', 'POST'])
async def data():
    data = await request.data
    issuer = session.get('issuer')
    pool_handle = session.get('pool_handle')
    while not issuer:
        issuer = session.get('issuer')
        time.sleep(0.1)
    else:
        session['issuer'], anoncrypted_connection_response = await onboarding_onboardee_receive_and_send(issuer, data, pool_handle, 'steward')
    while not anoncrypted_connection_response:
        time.sleep(0.1)
    else:
        requests.post('http://' + request.remote_addr + ':' + request.remote_port + '/data', json = anoncrypted_connection_response)
    return 'yup'#data




@app.route('/reset')
def reset():
    #teardown(session.get('pool_name'), session.get('pool_handle'), [session.get('issuer')])
    session.clear()
    return redirect(url_for('index'))


if __name__ == '__main__':
    app.secret_key = os.getenv('ANVIL_KEY', 'MUST_BE_STATIC')
    app.run(host, port, debug)
