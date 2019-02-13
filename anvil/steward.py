import os, asyncio
from quart import Quart, render_template, redirect, url_for, session
from sovrin.utilities import generate_base58
from sovrin.setup import setup_pool, set_self_up
#from sovrin.utilities import generate_base58
app = Quart(__name__)

debug = True # Do not enable in production
host = '0.0.0.0'
port = 5000


@app.route('/')
def index():
    return render_template('anvil.html', actor = 'anchor')


@app.route('/setup', methods = ['GET', 'POST'])
async def setupl():
    session['pool_name'], session['pool_handle'] = await setup_pool('ANVIL')
    pool_handle = session.get('pool_handle')
    print(pool_handle)
    return redirect(url_for('index'))


@app.route('/connection_request', methods = ['GET', 'POST'])
async def connection_request():
    id_ = os.getenv('ANVIL_ID', generate_base58(64))
    key = os.getenv('ANVIL_KEY', generate_base58(64))
    seed = os.getenv('ANVIL_SEED', '000000000000000000000000Steward1')
    session['steward'] = await set_self_up('steward', id_, key, session['pool_handle'], seed = seed)
    steward = session.get('steward')
    print(steward)
    return redirect(url_for('index'))


if __name__ == '__main__':
    app.secret_key = generate_base58(64)
    app.run(host, port, debug)
