import os, requests, json, time
from quart import Quart, render_template, redirect, url_for, request
from common import common_setup, common_respond, common_get_verinym, common_reset
from sovrin.credentials import receive_credential_offer
app = Quart(__name__)

debug = True # Do not enable in production
host = '0.0.0.0'
# In production everyone runs on same port, use 2 here for same-machine testing 
port = 5002
receiver_port = 5001

# Globals approach will be dropped once session persistence in Python is fixed.
prover = {}
pool_handle = 1
request_ip = anchor_ip = received_data = False
created_schema = []


@app.route('/')
def index():
    setup = True if prover != {} else False
    have_data = True if received_data != False else False
    responded = True if 'connection_response' in prover else False
    '''
    The onboardee depends on the anchor to finish establishing the secure channel.
    However the request-reponse messaging means the onboardee cannot proceed until it is:
    the functions made available by the channel_established variable wait until the
    relevant response from the anchor is returned, which is only possible if the channel
    is set up on the anchor end.
    '''
    channel_established = True if anchor_ip != '' else False
    have_verinym = True if 'did_info' in prover else False
    unique_schema_name = prover['unique_schema_name'] if 'unique_schema_name' in prover else False
    return render_template('prover.html', actor = 'prover', setup = setup, have_data = have_data, request_ip = request_ip, responded = responded, channel_established = channel_established, have_verinym = have_verinym, created_schema = created_schema, unique_schema_name = unique_schema_name)
 

@app.route('/setup', methods = ['GET', 'POST'])
async def setup():
    global prover, pool_handle
    prover, pool_handle = await common_setup(prover, pool_handle, 'prover')
    return redirect(url_for('index'))


@app.route('/receive', methods = ['GET', 'POST'])
async def data():
    global received_data
    received_data = await request.data
    print(received_data)
    return '200'

@app.route('/credential_inbox', methods = ['GET', 'POST'])
async def credential_inbox():
    global prover
    prover['authcrypted_certificate_cred_offer'] = await request.data
    prover = await receive_credential_offer(prover)
    print(prover['authcrypted_certificate_cred_offer'])
    return '200'


@app.route('/respond', methods = ['GET', 'POST'])
async def respond():
    global prover, anchor_ip
    prover, anchor_ip = await common_respond(prover, received_data, pool_handle, receiver_port)
    return redirect(url_for('index'))


@app.route('/get_verinym', methods = ['GET', 'POST'])
async def get_verinym():
    global prover
    prover = await common_get_verinym(prover, anchor_ip, receiver_port)
    return redirect(url_for('index'))


@app.route('/reset')
def reset():
    global prover, pool_handle, received_data, anchor_ip
    prover, pool_handle = common_reset([prover], pool_handle)
    received_data = ''
    anchor_ip = ''
    return redirect(url_for('index'))


@app.route('/reload')
def reload():
    return redirect(url_for('index'))


if __name__ == '__main__':
    app.secret_key = os.getenv('ANVIL_KEY', 'MUST_BE_STATIC')
    app.run(host, port, debug)
