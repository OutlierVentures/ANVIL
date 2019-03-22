# ANVIL API Reference

## Net choice

Select one of local, testnet, or mainnet deployment:


### Fetch

Fetch: when running a fetch agent (see API below), set the `net` parameter to `local` or `test` (`test` is default if no value is supplied).

Sovrin: when running `setup_pool(net)`, set the `net` parameter to `local`, `test` or `main` (`local` is default if no value is supplied). Testnet and mainnet are still in development and may require some debugging.


### Sovrin

## Sovrin

Import each of function in the format
```python
from sovrin.[module] import [function]
```

Note that many functions return an actor data structure when this actor is fed in as a parameter. This is an updated structure following some interaction with the Sovrin ledger, and should always be re-assigned to the actor, i.e. 
```python
actor = function(actor)
```

The ANVIL API encrypt and authenticates credential-related messages which can be sent in your chosen manner, for example using a basic HTTP POST:
```python
import requests
requests.post('IP_ADDRESS', message)
```
This can be easily combined with an async web framework like [Quart](https://pgjones.gitlab.io/quart/) (a Flask superset) to build apps. For a reference implementation, see the [actor apps](./anvil).

### Sovrin verifiable claims demo

[Claims.py](./anvil/sovrin/claims.py) demoes the ANVIL API's Sovrin functions. It provides a quick overview of the order of functions to be run when dealing with verifiable credentials.

Run:
```
python3 claims.py
```

### Setup

```python
setup_pool(net = 'local')
```
Sets up the pool for the current actor. Local pools can be started with `sudo ./scripts/start_sovrin.sh`. For irregular home IPs (i.e. not `127.0.0.1`, specify your IP with the `TEST_POOL_IP` environment variable).

Parameters:
- `net`: net type, one of `local`, `test` or `main`.

Returns:
- `pool_name`
- `pool_handle`

<br>

```python
set_self_up(name, id_, key, pool_handle, seed = None)
```
Sets up an actor data structure.

Parameters:
- `name`
- `_id`: wallet address. Pass as `WALLET_ID` environment variable.
- `key`: wallet private key. Pass as `WALLET_KEY` environment variable.
- `pool_handle`: must be set according to `setup_pool()`.
- `seed`: optional seed for instantiating existing ledger entities. Use `000000000000000000000000Steward1` for the local pool Steward.

Returns:
- `actor`: actor data structure (dictionary).

<br>

```python
teardown(pool_name, pool_handle, actor_list = [])
```
Tears down connections after a set of interactions.

Parameters:
- `pool_name`
- `pool_handle`
- `actor_list`: list of actor data structures to tear down, e.g. `[alice, bob]` for data structures `alice` and `bob` created with `set_self_up()`

<br>

### Onboarding

For a full onboarding (add an actor to the ledger), use all 5 functions below (in order). For establishing a secure channel between actors already on the ledger, you only need to use the first 3.

```python
onboarding_anchor_send(_from, unique_onboardee_name)
```
Constructs a connection request in JSON format which can be sent e.g. by POST to another agent. Note that existing trust anchors send connection requests to actors not yet on the ledger.

Parameters:
- `_from`: sending actor data structure.
- `unique_onboardee_name`: unique name of receiving actor (used as a reference).

Returns:
- `_from`: updated actor data structure.
- `connection_request`: connection request JSON to be sent e.g. by POST.

<br>

```python
onboarding_onboardee_reply(to, connection_request, from_pool)
```
Constructs a connection response in JSON format and encrypts it to bytes which can be sent e.g. by POST to the sender of a connection request.

Parameters:
- `to`: receiving actor data structure.
- `connection_request`: connection request JSON.
- `from_pool`: pool handle of the sender's pool.

Returns:
- `to`: updated actor data structure.
- `anoncrypted_connection_response`: Encrypted (but not authenticated) response packet to be sent e.g. by POST.

<br>

```python
onboarding_anchor_receive(_from, anoncrypted_connection_reponse, unique_onboardee_name)
```
Decrypts a connection response and establishes a secure channel with the onboardee.

Parameters:
- `_from`
- `anoncrypted_connection_response`
- `unique_onboardee_name`

Returns:
- `_from`

Note there is nothing to be sent back before calling ```onboarding_onboardee_create_did(to)``` (below) on the receiver's side.

<br>

```python
onboarding_onboardee_create_did(to)
```
Generates a new public DID (Verinym) and creates an authenticated and encrypted packet of bytes with this information which can be sent e.g. by POST to the sender of a connection request.

Parameters:
- `to`

Returns:
- `to`
- `authcrypted_did_info`: authenticated and encrypted DID packet to be sent e.g. by POST to the sender of a connection request.

<br>

```python
onboarding_anchor_register_onboardee_did(_from, unique_onboardee_name, authcrypted_did_info)
```
Decrypts and validates an authcrypted DID message and registers the DID on the Sovrin ledger.

Parameters:
- `_from`
- `unique_onboardee_name`
- `authcrypted_did_info`

Returns:
- `_from`

<br>

### Schema

```python
create_schema(schema, creator)
```
Creates and registers a new credential schema.

Parameters:
- `schema`: schema JSON object as shown below.
- `creator`: actor data structure for actor creating the schema.

Schema objects are JSONs in the format:
```JSON
{
    "name": "Outlier Ventures License to Delegate Access to Data",
    "version": "1.0",
    "attributes": ["bot_name", "data_source", "license", "status", "year", "id"]
}
```
Note that version numbers must be `float`s, not `int`s.

Returns:
- `unique_schema_name`: unique schema name (will be used as a reference).
- `schema_id`
- `creator`

<br>

```python
create_credential_definition(creator, schema_id, unique_schema_name, revocable = False)
```
Applies a credential definition to an existing schema and registers this on the ledger.

Parameters:
- `creator`
- `schema_id`
- `unique_schema_name`
- `revocable`: whether the credential is revocable. If set to `True` you will need to implement a revocation registry: see this [code reference](https://github.com/hyperledger/indy-sdk/blob/8d577007c4d32f6d253e6e83ac0f86821d27dfb8/samples/python/src/anoncreds_revocation.py#L55) and this [guide](https://github.com/hyperledger/indy-sdk/blob/master/docs/getting-started/indy-walkthrough.md#step-6-credential-definition-setup). Revocation registries may be added to the ANVIL API in future.

Returns:
- `creator`

<br>

### Credentials

```python
offer_credential(issuer, unique_schema_name)
```
Create an authcrypted credential offer object to be sent e.g. by POST to a prover. This references the credential schema / definitions stored in the issuer actor's data structure as defined in the funcctions above.

Parameters:
- `issuer`: issuer actor data structure.
- `unique_schema_name`

Returns:
- `issuer`
- `authcrypted_credential_offer`: authenticated and encrypted credential offer packet to be sent e.g. by POST to a credential receiver (prover).

<br>

```python
receive_credential_offer(prover)
```
Decrypts a credential offer and sets up a [master secret](https://github.com/hyperledger/indy-sdk/blob/master/docs/getting-started/indy-walkthrough.md#alice-gets-a-transcript) so that the offered credential can be used.

Parameters:
- `prover`: prover actor data structure.

Returns:
- `prover`

<br>

```python
request_credential(prover, values)
```
Creates an authcrypted credential request object to be sent e.g. by POST to the sender of a credential offer.

Parameters:
- `prover`
- `values`: credential request JSON as below formatted as string (i.e. `json.dumps(credential_request)`)

Credential requests are JSONs in the format:
```JSON
{
    "bot_name": {"raw": "Sophos", "encoded": "123157160150157163"},
    "data_source": {"raw": "GitHub", "encoded": "107151164110165142"},
    "license": {"raw": "LDAD restricted", "encoded": "11410410110440162145163164162151143164145144"},
    "status": {"raw": "active", "encoded": "141143164151166145"},
    "year": {"raw": "2019", "encoded": "62606171"},
    "id": {"raw": "did:ov:xb3i0s5v", "encoded": "1441511447215716672170142631516016365166"}
}
```
Encoding is arbitrary.

Returns:
- `prover`
- `authcrypted_credential_request`: authenticated and encrypted credential request packet to be sent e.g. by POST to the sender of a credential offer.

<br>

```python
create_and_send_credential(issuer)
```
Creates an authcrypted credential packet to be sent e.g. by POST to a credential receiver (prover).

Parameters:
- `issuer`

Returns:
- `issuer`
- `authcrypted_credential`: authenticated and encrypted credential packet to be sent e.g. by POST to the sender of a credential request.

<br>

```python
store_credential(prover)
```
Decrypts a received credential and stores it in the receiver's wallet (as specified in `set_self_up()` above).

Parameters:
- `prover`

Returns:
- `prover`

<br>

### Proofs

```python
request_proof_of_credential(verifier, proof_request = {})
```
Creates an authcrypted proof request packet to be sent e.g. by POST to a prover.

Parameters:
- `verifier`: verifier actor data structure.
- `proof_request`: proof request JSON as below formatted as string (i.e. `json.dumps(proof_request)`)

Proof requests are JSONs in the format:
```JSON
{
    "nonce": "0123456789012345678901234",
    "name": "LDAD restricted proof",
    "version": "0.1",
    "requested_attributes": {
        "attr1_referent": {
            "name": "bot_name"
        },
        "attr2_referent": {
            "name": "data_source"
        },
        "attr3_referent": {
            "name": "license"
        },
        "attr4_referent": {
            "name": "status"
        },
        "attr5_referent": {
            "name": "id"
        }
    },
    "requested_predicates": {
        "predicate1_referent": {
            "name": "year",
            "p_type": ">=",
            "p_value": 2019
        }
    }
}
```
An attribute is just `name = 'Sophos'`. A predicate is a comparison that evaluates to true or false, e.g. `age >= 18`. Note that, as with all Sovrin nonces, the proof request nonce must be fully numeric (you can use ANVIL's `sovrin.generate_nonce(25)`).

Returns:
- `verifier`
- `authcrypted_proof_request`: authenticated and encrypted proof request packet to be sent e.g. by POST to a prover.

<br>

```python
create_proof_of_credential(prover, self_attested_attrs = {}, requested_attrs = [], requested_preds = [], non_issuer_attributes = [])
```
Decrypts a proof request and constructs a proof according to it.

Parameters:
- `self_attested_attrs`: JSON of self-attributes.
- `requested_attrs`: list of indices of requested attributes.
- `requested_preds`: list of indices of requested predicates.
- `non_issuer_attributes`: list of indices of attributes that are not in the issued credential, and therefore can't be retrieved from the ledger.

Example proof paramters according to the above example data:
```python
self_attested_attrs = {
    "attr1_referent": "Sophos",
    "attr5_referent": "did:ov:xb3i0s5v"
}
requested_attrs = [2, 3, 4]
requested_preds = [1]
non_issuer_attrs = []
```

Returns:
- `prover`
- `authcrypted_proof`: authenticated and encrypted proof packet to be sent e.g. by POST to a verifier.

<br>

```python
verify_proof(verifier, assertions_to_make)
```
Decrypts a proof and verifies it according to your chosen assertions.


Parameters:
- `verifier`
- `assertions_to_make`: JSON of assertions to make on proof attributes, i.e. ensure attribute X is equal to Y.

Assertions to make are a JSON in the format:
```JSON
{
    "revealed": {
        "attr2_referent": "GitHub",
        "attr3_referent": "LDAD restricted",
        "attr4_referent": "active"
    },
    "self_attested": {
        "attr1_referent": "Sophos",
        "attr5_referent": "did:ov:xb3i0s5v"
    }
}
```

Returns:
- `verifier`

<br>

### Utilities

```python
write_json(data, filename)
```
Writes to a JSON file in the current directory.

Parameters:
- `data`
- `filename`

<br>

```python
read_json(filename):
```
Reads a JSON file with the name supplied from the current directory.

Parameters:
- `filename`

Returns:
- `data`: the data in the file.

<br>

```python
generate_nonce(length)
```
Generates a Sovrin-compatible numeric nonce.

Parameters:
- `length`: how many characters the nonce should be.

Returns:
- `nonce`: the nonce.

<br>

```python
generate_base58(length)
```
Generates a base58 string.

Parameters:
- `length`: how many characters the base58 string should be.

Returns:
- `base58`: the base58 string.

<br>

```python
send_data(data, channel = 0):
```
Network simulation send function, writes to a bytes file. Useful for quick testing where agents are in separate files.

Parameters:
- `data`: data to send.
- `channel`: network channel, useful if you want to test lots of pariwise connections at once – just run each on a different channel.


<br>

```python
receive_data(channel = 0)
```
Network simulation receive function, reads from a bytes file. Useful for quick testing where agents are in separate files.

Parameters:
- `channel`

Returns:
- `data`: received data.

<br>


## Fetch

The following assumers you have a running Fetch.AI node. You can start one with `./scripts/start_fetch.sh`.

Imports:
```python
from fetch.agents import [function]
```

### Search the OEF

```python
search(search_terms, path_to_fetch_folder = './fetch', net = 'test')
```

Parameters:
- `search_terms`: search terms string split with underscores, e.g. `license_fetch_iota_ocean`.
- `path_to_fetch_folder`: path to the `ANVIL/anvil/fetch` folder. If you are running agents from the `anvil` folder (e.g. adapting the actor apps you don't need this paramter.)
- `net`: net type, one of `local` or `test`.

Result:
- Writes search results to file `search_results.json`.

Alternatively, run the agent directly from bash:
```
python3 ./path/to/searcher.py 'search_terms_split_with_underscores'
```

### Offer a service (run a seller / prover)

```python
offer_service(price, service_path, path_to_fetch_folder = './fetch', net = 'test')
```

Parameters:
- `price`: the price of your service in Fetch.AI tokens.
- `service_path`: path to JSON data models describing your fetch service, e.g. [the Sophos data service](./anvil/example_data/fetch_service).
- `path_to_fetch_folder`: path to the `ANVIL/anvil/fetch` folder. If you are running agents from the `anvil` folder (e.g. adapting the actor apps you don't need this paramter.)
- `net`: net type, one of `local` or `test`.

Result:
- Sends data to a purchaser in exchange for Fetch.AI tokens if someone purchases the service.

Alternatively, run the agent directly from bash:
```
python3 ./path/to/prover.py ./service/path price
```


### Purchase a service (run a buyer / verifier)

```python
purchase_service(max_price, search_terms, path_to_fetch_folder = './fetch', net = 'test')
```

Parameters:
- `max_price`: the maximum price you are willing to pay for the service in Fetch.AI tokens.
- `search_terms`: search terms string split with underscores, e.g. `license_fetch_iota_ocean`. If running a `searcher` agent first for service discovery, store the terms used in a variable and feed that in as the the search string here.
- `path_to_fetch_folder`: path to the `ANVIL/anvil/fetch` folder. If you are running agents from the `anvil` folder (e.g. adapting the actor apps you don't need this paramter.)
- `net`: net type, one of `local` or `test`.

Result:
- Pays a seller in Fetch tokens on a match and the AEA receives the requested data.

Alternatively, run the agent directly from bash:
```
python3 ./path/to/verifier.py search_terms_split_with_underscores max_price
```


## Debugging

### CommonInvalidStructure or DidAlreadyExistsError

Error: `indy.error.IndyError: ErrorCode.CommonInvalidStructure` or `indy.error.IndyError: ErrorCode.DidAlreadyExistsError`

Fix: `rm ~/.indy_client` and re-run.

### Dlopen/dylib errors

Error: `OSError: dlopen(libindy.dylib, 6): image not found` or similar `dlopen` referencing `libsodium`

Fix: set `LD_LIBRARY_PATH` and `DYLD_LIBRARY_PATH` environment variables to `/path/to/indy/libindy/target/debug`. If that doesn't work, run `./scripts/test.sh`, which will detail the failure. This is most likely due to a `libsodium` upgrade, where Indy will look for `libsodium.XX.dyld` and you have `libsodium.YY.dyld`. Navigate to the referenced folder and make a copy of your `libsodium.YY.dyld` and rename the copy to `libsodium.XX.dyld`.

### Undocumented eccentricities

- Nonces should be fully numeric for Hyperledger Indy. This is a common cause of the `CommonInvalidStructure` error (code 113). There is an Indy-compatible nonce generator in the `sovrin/utilities` module.
- Schema versions must be floats to be compatible with Sovrin.
- Quart forms do not allow underscores in the `name` field.
