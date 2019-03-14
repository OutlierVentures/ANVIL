'''
Sovrin core utilities.
'''

import asyncio, json, random


def run_coroutine(coroutine, loop = None):
    if loop is None:
        loop = asyncio.get_event_loop()
    loop.run_until_complete(coroutine())


def write_json(data, filename):
    with open(filename + '.json', 'w') as outfile:
        json.dump(data, outfile)


def read_json(filename):
    with open(filename + '.json', 'r') as infile:
        data = json.loads(infile.read())
    return data


# Network simulation only. Use requests.post() or similar for real transfers.
def send_data(data, channel = 0):
    f = open('net_sim_' + str(channel), 'wb')
    f.write(data)
    f.close()


# Network simulation only.
def receive_data(channel = 0):
    f = open('net_sim_' + str(channel), 'rb')
    data = f.read()
    f.close()
    return data


def generate_nonce(length):
    nonce = ''.join(random.choice('0123456789') for i in range(length))
    return nonce


def generate_base58(length):
    base58 = ''.join(random.choice('123456789abcdefghijkmnopqrstuvwxyzABCDEFGHJKLMNPQRSTUVWXYZ') for i in range(length))
    return base58
