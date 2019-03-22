'''
Fetch AEA functions:

1. Search the OEF.
2. Offer a Fetch service.
3. Purchase a Fetch service.
'''


import subprocess


def search(search_terms, path_to_fetch_folder = './fetch', net = 'test'):
    subprocess.run('python3 ' + path_to_fetch_folder + '/searcher.py ' + search_terms + ' ' + net, shell = True)


def offer_service(price, service_path, path_to_fetch_folder = './fetch', net = 'test'):
    subprocess.Popen('python3 ' + path_to_fetch_folder + '/prover.py ' + service_path + ' ' + str(price) + ' ' + net, shell = True)


def purchase_service(max_price, search_terms, path_to_fetch_folder = './fetch', net = 'test'):
    subprocess.run('python3 ' + path_to_fetch_folder + '/verifier.py ' + search_terms + ' ' + str(max_price) + ' ' + net, shell = True)
