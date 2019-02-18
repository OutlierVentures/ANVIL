'''
Common functionality between actors.
'''


import os, requests
from quart import request, redirect, url_for
from sovrin.utilities import generate_base58
from sovrin.setup import setup_pool, set_self_up, teardown
from sovrin.onboarding import onboarding_anchor_send, onboarding_anchor_receive, onboarding_anchor_register_onboardee_did

async def common_setup(anchor, pool_handle):
    _, pool_handle = await setup_pool('ANVIL')
    id_ = os.getenv('WALLET_ID', generate_base58(64))
    key = os.getenv('WALLET_KEY', generate_base58(64))
    seed = os.getenv('SOVRIN_SEED', '000000000000000000000000Steward1')
    anchor = await set_self_up('steward', id_, key, pool_handle, seed = seed)
    return anchor, pool_handle


async def common_connection_request(anchor, form):
    ip = form['ip_address']
    name = ''.join(e for e in form['name'] if e.isalnum())
    #print(anchor)
    anchor, connection_request = await onboarding_anchor_send(anchor, name)
    requests.post('http://' + ip + '/receive', json = connection_request)
    return anchor


async def common_establish_channel(anchor):
    received_data = await request.data
    anchor = await onboarding_anchor_receive(anchor, received_data, 'issuer')
    print(anchor.keys())
    print('CHANNEL ESTABLISHED ========')
    return anchor


'''
Creates a Verinym for onboardees with which a secure channel has been established,
throws an error otherwise. Establishes the onboardee as a new trust anchor on the ledger.
'''
async def common_verinym_request(anchor):
    verinym_request = await request.data
    anchor = await onboarding_anchor_register_onboardee_did(anchor, 'issuer', verinym_request)
    print(verinym_request)
    print('REGISTERED NEW TRUST ANCHOR ========')
    return anchor


def common_reset(actor_list, pool_handle):
    teardown('ANVIL', pool_handle, actor_list)
    for actor in actor_list:
        actor = {}
    return actor
