'''
Common functionality between actors.
Many of these functions can only be called from the scope of a request and/or app context.
For fine-grained control, use the functions in the Sovrin folder.
'''


import os, requests, json
from quart import request, redirect, url_for
from sovrin.utilities import generate_base58
from sovrin.setup import setup_pool, set_self_up, teardown
from sovrin.onboarding import onboarding_anchor_send, onboarding_anchor_receive, onboarding_anchor_register_onboardee_did, onboarding_onboardee_reply, onboarding_onboardee_create_did


# Steward has unique setup from seed, does not use this
async def common_setup(actor, pool_handle, name):
    _, pool_handle = await setup_pool('local')
    id_ = os.getenv('WALLET_ID', generate_base58(64))
    key = os.getenv('WALLET_KEY', generate_base58(64))
    actor = await set_self_up(name, id_, key, pool_handle)
    return actor, pool_handle


async def common_connection_request(anchor):
    form = await request.form
    ip = form['ip_address']
    name = ''.join(e for e in form['name'] if e.isalnum())
    anchor, connection_request = await onboarding_anchor_send(anchor, name)
    requests.post('http://' + ip + '/receive', json = connection_request)
    return anchor, name


async def common_establish_channel(anchor, counterparty_name):
    received_data = await request.data
    anchor = await onboarding_anchor_receive(anchor, received_data, counterparty_name)
    return anchor


'''
Creates a Verinym for onboardees with which a secure channel has been established,
throws an error otherwise. Establishes the onboardee as a new trust anchor on the ledger.
'''
async def common_verinym_request(anchor, counterparty_name):
    verinym_request = await request.data
    anchor = await onboarding_anchor_register_onboardee_did(anchor, counterparty_name, verinym_request)
    return anchor



async def common_respond(onboardee, received_data, pool_handle, anchor_port):
    anchor_ip = request.remote_addr
    data = json.loads(received_data)
    onboardee, anoncrypted_connection_response = await onboarding_onboardee_reply(onboardee, data, pool_handle)
    onboardee['connection_response'] = json.loads(onboardee['connection_response'])
    requests.post('http://' + anchor_ip + ':' + str(anchor_port) + '/establish_channel', anoncrypted_connection_response)
    return onboardee, anchor_ip


async def common_get_verinym(onboardee, anchor_ip, anchor_port):
    onboardee, authcrypted_did_info = await onboarding_onboardee_create_did(onboardee)
    requests.post('http://' + anchor_ip + ':' + str(anchor_port) + '/verinym_request', authcrypted_did_info)
    return onboardee



async def common_reset(actor_list, pool_handle):
    await teardown('ANVIL', pool_handle, actor_list)
    for actor in actor_list:
        actor = {}
    pool_handle = 1
    return actor, pool_handle
