import os, requests, time, json
from quart import Quart, render_template, redirect, url_for, session, request, jsonify
from sovrin.utilities import generate_base58, run_coroutine
from sovrin.setup import setup_pool, set_self_up, teardown
from sovrin.onboarding import onboarding_anchor_send, onboarding_anchor_receive, onboarding_anchor_register_onboardee_did
from common import common_setup, common_connection_request, common_establish_channel, common_verinym_request, common_reset
app = Quart(__name__)

debug = True # Do not enable in production
host = '0.0.0.0'
port = 5000

# Globals approach will be dropped once session persistence in Python is fixed.
anchor = {}
pool_handle = 1
counterparty_name = ''


@app.route('/')
def index():
    global anchor
    setup = True if anchor != {} else False
    channel_established = True if 'connection_response' in anchor else False
    return render_template('steward.html', actor = 'steward', setup = setup, channel_established = channel_established)


@app.route('/setup', methods = ['GET', 'POST'])
async def setup():
    global anchor, pool_handle
    _, pool_handle = await setup_pool('ANVIL')
    id_ = os.getenv('WALLET_ID', generate_base58(64))
    key = os.getenv('WALLET_KEY', generate_base58(64))
    seed = os.getenv('SOVRIN_SEED', '000000000000000000000000Steward1')
    anchor = await set_self_up('steward', id_, key, pool_handle, seed = seed)
    return redirect(url_for('index'))


@app.route('/connection_request', methods = ['GET', 'POST'])
async def connection_request():
    global anchor, counterparty_name
    anchor, counterparty_name = await common_connection_request(anchor)
    return redirect(url_for('index'))


@app.route('/establish_channel', methods = ['GET', 'POST'])
async def establish_channel():
    global anchor
    anchor = await common_establish_channel(anchor, counterparty_name)
    return '200'


@app.route('/verinym_request', methods = ['GET', 'POST'])
async def verinym_request():
    global anchor
    anchor = await common_verinym_request(anchor, counterparty_name)
    return '200'


@app.route('/reset')
def reset():
    global anchor, pool_handle
    anchor, pool_handle = common_reset([anchor], pool_handle)
    return redirect(url_for('index'))


@app.route('/reload')
def reload():
    return redirect(url_for('index'))


if __name__ == '__main__':
    app.secret_key = os.getenv('ANVIL_KEY', 'MUST_BE_STATIC')
    app.run(host, port, debug)
    
