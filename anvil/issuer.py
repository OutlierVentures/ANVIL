import os, requests, json, time
from quart import Quart, render_template, redirect, url_for, session, request, jsonify
from sovrin.utilities import generate_base58, run_coroutine
from sovrin.setup import setup_pool, set_self_up, teardown
from sovrin.onboarding import onboarding_onboardee_receive_and_send, onboarding_onboardee_create_did
from common import common_setup, common_respond, common_get_verinym, common_reset
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
anchor_name = ''
anchor_ip = ''


@app.route('/')
def index():
    global issuer, received_data
    setup = True if issuer != {} else False
    have_data = True if received_data != '' else False
    responded = True if 'connection_response' in issuer else False
    '''
    The onboardee depends on the anchor to finish establishing the secure channel.
    However the request-reponse messaging means the onboardee cannot proceed until it is:
    the functions made available by the channel_established variable wait until the
    relevant response from the anchor is returned, which is only possible if the channel
    is set up on the anchor end.
    '''
    channel_established = True if anchor_ip != '' else False
    have_verinym = True if 'did_info' in issuer else False
    return render_template('issuer.html', actor = 'issuer', setup = setup, have_data = have_data, responded = responded, channel_established = channel_established, have_verinym = have_verinym)
 

@app.route('/setup', methods = ['GET', 'POST'])
async def setup():
    global issuer, pool_handle
    issuer, pool_handle = await common_setup(issuer, pool_handle, 'issuer')
    return redirect(url_for('index'))


@app.route('/receive', methods = ['GET', 'POST'])
async def data():
    global received_data
    received_data = await request.data
    print(received_data)
    return '200'


@app.route('/respond', methods = ['GET', 'POST'])
async def respond():
    global issuer, anchor_ip
    issuer, anchor_ip = await common_respond(issuer, received_data, pool_handle, receiver_port)
    return redirect(url_for('index'))


@app.route('/get_verinym', methods = ['GET', 'POST'])
async def get_verinym():
    global issuer
    issuer = await common_get_verinym(issuer, anchor_ip, receiver_port)
    return redirect(url_for('index'))


@app.route('/reset')
def reset():
    global issuer, pool_handle, received_data, anchor_ip
    issuer, pool_handle = common_reset([issuer], pool_handle)
    received_data = ''
    anchor_ip = ''
    return redirect(url_for('index'))


@app.route('/reload')
def reload():
    return redirect(url_for('index'))


if __name__ == '__main__':
    app.secret_key = os.getenv('ANVIL_KEY', 'MUST_BE_STATIC')
    app.run(host, port, debug)
