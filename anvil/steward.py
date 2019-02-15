import os, requests, time
from quart import Quart, render_template, redirect, url_for, session, request, jsonify
from sovrin.utilities import generate_base58, run_coroutine
from sovrin.setup import setup_pool, set_self_up, teardown
from sovrin.onboarding import onboarding_anchor_send
app = Quart(__name__)

debug = True # Do not enable in production
host = '0.0.0.0'
port = 5000


@app.route('/')
def index():
    steward = session.get('steward')
    setup = True if steward else False
    return render_template('steward.html', actor = 'steward', setup = setup)


@app.route('/setup', methods = ['GET', 'POST'])
async def setup():
    session['pool_name'], session['pool_handle'] = await setup_pool('ANVIL')
    id_ = os.getenv('WALLET_ID', generate_base58(64))
    key = os.getenv('WALLET_KEY', generate_base58(64))
    seed = os.getenv('SOVRIN_SEED', '000000000000000000000000Steward1')
    session['steward'] = await set_self_up('steward', id_, key, session['pool_handle'], seed = seed)
    print(session['steward'])
    return redirect(url_for('index'))


@app.route('/connection_request', methods = ['GET', 'POST'])
async def connection_request():
    form = await request.form  
    ip = form['ip_address']
    name = ''.join(e for e in form['name'] if e.isalnum())
    steward = session.get('steward')
    while not isinstance(steward, dict):
        steward = session.get('steward')
        time.sleep(0.1)
    else:
        session['steward'], connection_request = await onboarding_anchor_send(steward, name)
        print(type(connection_request))
        while not isinstance(connection_request, dict):
            session['steward'], connection_request = await onboarding_anchor_send(steward, name)
            time.sleep(0.1)
        else:
            requests.post('http://' + ip + '/data', json = connection_request)
    return redirect(url_for('index'))
    




@app.route('/reset')
def reset():
    #teardown(session.get('pool_name'), session.get('pool_handle'), [session.get('steward')])
    session.clear()
    return redirect(url_for('index'))

if __name__ == '__main__':
    app.secret_key = os.getenv('ANVIL_KEY', 'MUST_BE_STATIC')
    app.run(host, port, debug)
    
