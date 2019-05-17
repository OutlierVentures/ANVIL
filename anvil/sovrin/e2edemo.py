'''
E2E pairwise encryption demo.
'''


import sys, time, json
from utilities import run_coroutine, generate_nonce, generate_base58
from setup import setup_pool, set_self_up, teardown
from onboarding import demo_onboard, onboarding_anchor_send, onboarding_onboardee_reply, onboarding_anchor_receive, onboarding_onboardee_create_did, onboarding_anchor_register_onboardee_did, auth_encrypt, auth_decrypt
from indy import did

'''
MOCK SEND / RECEIVE FUNCTIONS
Takes BYTES, writes to / reads from disk.
In a real multi-machine scenario, just use requests.post('URL', MESSAGE)
See ANVIL Apps (anvil folder) for these real transfers.
'''
from utilities import send_data, receive_data


async def run():


    '''
    1.
    General Sovrin set-up. Let the ANVIL API handle the complexities for us.
    Account IDs and keys are random base58 strings here.
    '''
    pool_name, pool_handle = await setup_pool('local')
    steward = await set_self_up('steward', generate_base58(64), generate_base58(64), pool_handle,
                                seed = '000000000000000000000000Steward1')
    alice = await set_self_up('alice', generate_base58(64), generate_base58(64), pool_handle)
    bob = await set_self_up('bob', generate_base58(64), generate_base58(64), pool_handle)
    

    '''
    2.
    Get one of our actors (Alice) into the the trust ecosystem of Sovrin by having a steward onboard her.
    This gives her a DID, a public key on the ledger - a username that works anywhere, tied to her private key (the password).
    We use a demo function here for simplicity - the exact same process as with Alice and Bob (below) takes place however.
    '''
    steward, alice = await demo_onboard(steward, alice)


    '''
    3.
    Have Alice make a connection request to Bob.
    json.dumps turns the dict into a string, then encode turns it to bytes for sending to Bob.
    '''
    alice, connection_request = await onboarding_anchor_send(alice, 'bob')
    bytes_to_send = json.dumps(connection_request).encode('utf-8')
    send_data(bytes_to_send)
    

    '''
    4.
    Bob receives and loads the data, then sends a connection response to Alice.
    At this point we are encrypted but not authenticated.
    Note Sovrin encryption functions already output bytes so there's no need to convert before sending.
    '''
    bob_inbox = receive_data()
    unbytes = json.loads(bob_inbox.decode('utf-8'))
    bob, anoncrypted_connection_response = await onboarding_onboardee_reply(bob, unbytes, alice['pool'])
    send_data(anoncrypted_connection_response)


    '''
    5.
    Alice receives the connection response and decrypts it.
    She now has enough information to know when Bob sends her a message.
    Any future messages from Bob are authenticated, encrypted and only decryptable by the entities involved.
    There is now a pairwise channel between Alice and Bob.
    '''
    alice_inbox = receive_data()
    alice = await onboarding_anchor_receive(alice, alice_inbox, 'bob')


    '''
    6.
    Bob creates a message, encrypts and authenticates it, then send it to Alice.
    Note that ANVIL expects json messages.
    '''
    message = {
        'text': 'That hurt like a buttcheek on a stick.'
    }
    authcrypted_message = await auth_encrypt(bob['wallet'], bob['alice_key'], bob['from_to_verkey'], message)
    print('Bob: SENDING ENCRYPTED MESSAGE...')
    send_data(authcrypted_message)

        
    '''
    7.
    Alice receives the message and decrypts it.
    She (optionally) verifies that the sender is indeed Bob by checking his DID (key_for_did() is deterministic).
    '''
    alice_inbox = receive_data()
    sender_verkey, _, decrypted_message = await auth_decrypt(alice['wallet'], alice['bob_key'], alice_inbox)
    assert sender_verkey == await did.key_for_did(alice['pool'], alice['wallet'], alice['connection_response']['did'])
    print('Alice: RECEIVED: ' + decrypted_message['text'])




    '''
    ADVANCED BELOW
    =========================================================================================================================
    You can now do pairwise E2E encryption with Sovrin.
    Below is how to use Alice to onboard Bob to the Sovrin trust ecosystem.
    This allows Bob to start opening pairwise channels with others.
    =========================================================================================================================
    '''


    '''
    8.
    Bob can now send E2E encrypted messages.
    Bob would still like to be a part of Sovrin's trust ecosystem so he can open secure channels with others.
    Bob creates a DID for himself and sends it to Alice using their pairwise channel.
    '''
    bob, authcrypted_did_info = await onboarding_onboardee_create_did(bob)
    send_data(authcrypted_did_info)


    '''
    9.
    Alice, who is already in the trust ecosystem, decrypts Bob's DID and writes it to the ledger.
    Bob is now part of the Sovrin ecosystem, so can onboard others too.
    '''
    alice_inbox = receive_data()
    alice = await onboarding_anchor_register_onboardee_did(alice, 'bob', alice_inbox)

 
    '''
    10.
    Tear down any connections. Let the ANVIL API handle the complexities for us.
    '''
    await teardown(pool_name, pool_handle, [steward, alice, bob])
    print('That\'s how you do pairwise channels!')


if __name__ == '__main__':
    run_coroutine(run)
    time.sleep(1)  # FIXME waiting for libindy thread complete
