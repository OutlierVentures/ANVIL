import os, requests
from quart import Quart, render_template, redirect, url_for, session, request, jsonify
from sovrin.utilities import generate_base58
from sovrin.setup import setup_pool, set_self_up
from sovrin.onboarding import onboarding_anchor_send
#from sovrin.utilities import generate_base58
app = Quart(__name__)

debug = True # Do not enable in production
host = '0.0.0.0'
port = 5000


@app.route('/')
def index():
    steward = session.get('steward')
    setup = True if steward else False
    return render_template('anvil.html', actor = 'steward', setup = setup)


@app.route('/setup', methods = ['GET', 'POST'])
async def setup():
    session['pool_name'], session['pool_handle'] = await setup_pool('ANVIL')
    pool_handle = session.get('pool_handle')
    id_ = os.getenv('ANVIL_ID', generate_base58(64))
    key = os.getenv('ANVIL_KEY', generate_base58(64))
    seed = os.getenv('ANVIL_SEED', '000000000000000000000000Steward1')
    session['steward'] = await set_self_up('steward', id_, key, session['pool_handle'], seed = seed)
    print(pool_handle, session['steward'])
    return redirect(url_for('index'))


@app.route('/connection_request', methods = ['GET', 'POST'])
async def connection_request():
    steward = session.get('steward')
    form = await request.form
    ip = form['ip_address']
    name = form['name']
    name = ''.join(e for e in name if e.isalnum())
    steward, connection_request = await onboarding_anchor_send(steward, name)
    print(ip, name, steward, connection_request)
    requests.post('http://' + ip + '/onboarding', connection_request)
    return redirect(url_for('index'))


if __name__ == '__main__':
    app.secret_key = generate_base58(64)
    app.run(host, port, debug)
