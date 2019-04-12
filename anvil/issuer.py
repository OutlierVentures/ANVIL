import os, requests, json, time
from quart import Quart, render_template, redirect, url_for, request
from common import common_setup, common_respond, common_get_verinym, common_reset, common_connection_request, common_establish_channel, common_verinym_request
from sovrin.schema import create_schema, create_credential_definition
from sovrin.credentials import offer_credential, create_and_send_credential
app = Quart(__name__)

debug = False # Do not enable in production
host = '0.0.0.0'
# In production everyone runs on same port, use 2 here for same-machine testing 
port = 5001
anchor_port = 5000
prover_port = 5002

# We use globals for our server-side session since this is not supported in Quart yet.
issuer = {}
request_ip = anchor_ip = received_data = counterparty_name = False
pool_handle = 1
created_schema = []


@app.route('/')
def index():
    setup = True if issuer else False
    have_data = True if received_data else False
    responded = True if 'connection_response' in issuer else False
    '''
    The onboardee depends on the anchor to finish establishing the secure channel.
    However the request-reponse messaging means the onboardee cannot proceed until it is:
    the functions made available by the channel_established variable wait until the
    relevant response from the anchor is returned, which is only possible if the channel
    is set up on the anchor end.
    '''
    channel_established = True if anchor_ip else False
    prover_registered = True if 'prover_ip' in issuer else False
    have_verinym = True if 'did_info' in issuer else False
    credential_requested = True if 'authcrypted_cred_request' in issuer else False
    created_schema_string = ', '.join(schema for schema in created_schema)
    return render_template('issuer.html', actor = 'ISSUER', setup = setup, have_data = have_data, request_ip = request_ip, responded = responded, channel_established = channel_established, have_verinym = have_verinym, created_schema = created_schema_string, prover_registered = prover_registered, credential_requested = credential_requested)
 

@app.route('/setup', methods = ['GET', 'POST'])
async def setup():
    global issuer, pool_handle
    issuer, pool_handle = await common_setup(issuer, pool_handle, 'issuer')
    return redirect(url_for('index'))


@app.route('/receive', methods = ['GET', 'POST'])
async def data():
    global received_data, request_ip
    received_data = await request.data
    request_ip = request.remote_addr
    print(received_data)
    return '200'


@app.route('/respond', methods = ['GET', 'POST'])
async def respond():
    global issuer, anchor_ip
    issuer, anchor_ip = await common_respond(issuer, received_data, pool_handle, anchor_port)
    return redirect(url_for('index'))


@app.route('/get_verinym', methods = ['GET', 'POST'])
async def get_verinym():
    global issuer
    issuer = await common_get_verinym(issuer, anchor_ip, anchor_port)
    return redirect(url_for('index'))


@app.route('/connection_request', methods = ['GET', 'POST'])
async def connection_request():
    global issuer, counterparty_name
    issuer, counterparty_name = await common_connection_request(issuer)
    return redirect(url_for('index'))


@app.route('/establish_channel', methods = ['GET', 'POST'])
async def establish_channel():
    global issuer
    issuer = await common_establish_channel(issuer, counterparty_name)
    # Connection with multiple actor types (e.g. steward + prover) demands registering this at the app level
    issuer['prover_ip'] = request.remote_addr
    return '200'


@app.route('/verinym_request', methods = ['GET', 'POST'])
async def verinym_request():
    global issuer
    issuer = await common_verinym_request(issuer, counterparty_name)
    return '200'


'''
Set revocation support here if needed.
'''
@app.route('/create_credential', methods = ['GET', 'POST'])
async def create_credential():
    global issuer, created_schema
    try:
        form = await request.form
        schema = json.loads(form['schema'])
        unique_schema_name, schema_id, issuer = await create_schema(schema, issuer)
        issuer = await create_credential_definition(issuer, schema_id, unique_schema_name, revocable = False)
        created_schema.append(unique_schema_name)
        return redirect(url_for('index'))
    except:
        return 'Invalid schema. Check formatting.'



@app.route('/offer_credential', methods = ['GET', 'POST'])
async def offer_credential_to_ip():
    global issuer
    form = await request.form
    schema_name = form['schema_name']
    if schema_name in created_schema:
        issuer, cred_offer = await offer_credential(issuer, schema_name)
        requests.post('http://' + form['ip_address'] + '/credential_inbox', cred_offer)
        return redirect(url_for('index'))
    else:
        return 'Schema does not exist. Check name input.'


@app.route('/credential_request', methods = ['GET', 'POST'])
async def credential_request():
    global issuer, request_ip
    issuer['authcrypted_cred_request'] = await request.data
    # Old request IP now has name anchor IP so can safely overwrite
    request_ip = request.remote_addr
    return '200'


@app.route('/send_credential', methods = ['GET', 'POST'])
async def send_credential():
    global issuer
    issuer, credential = await create_and_send_credential(issuer)
    requests.post('http://' + request_ip + ':' + str(prover_port) + '/credential_store', credential)
    # Hides send credential function until next credential request
    issuer.pop('authcrypted_cred_request', None)
    return redirect(url_for('index'))


@app.route('/reset')
async def reset():
    global issuer, pool_handle, received_data, anchor_ip
    issuer, pool_handle = await common_reset([issuer], pool_handle)
    received_data = False
    anchor_ip = False
    return redirect(url_for('index'))


@app.route('/reload')
def reload():
    return redirect(url_for('index'))


if __name__ == '__main__':
    app.secret_key = os.getenv('ANVIL_KEY', 'MUST_BE_STATIC')
    app.run(host, port, debug)
