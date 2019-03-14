# ANVIL API Reference

## Sovrin

Import each of these in the format `from sovrin.[module] import [function]`

Note that many functions return the actor data structure. This is an updated structure following some interaction with the Sovrin ledger, and should always be re-assigned to the actor, i.e. 
```python
actor = function(actor)
```

The ANVIL API encrypt and authenticates credential-related messages which can be sent in your chosen manner, for example using a basic HTTP POST:
```python
import requests
requests.post('IP_ADDRESS', message)
```
This can be easily combined with an async web framework like [Quart](https://pgjones.gitlab.io/quart/) (a Flask superset) to build apps. For a reference implementation, see the [actor apps](./anvil).


### Setup

```python
setup_pool(name = 'ANVIL')
```
Sets up the pool for the current actor specified by the IP `TEST_POOL_IP` environment variable. For a local testnet pool there is no need to set this.

Parameters:
- `name`

Returns:
- `pool_name`
- `pool_handle`

<br><br>

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

<br><br>

```python
teardown(pool_name, pool_handle, actor_list = [])
```
Tears down connections after a set of interactions.

Parameters:
- `pool_name`
- `pool_handle`
- `actor_list`: list of actor data structures to tear down, e.g. `[alice, bob]` for data structures `alice` and `bob` created with `set_self_up()`

<br><br>

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

<br><br>

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
- `anoncrypted_connection_response`: Encrypted (but not authenticated) response bytes to be sent e.g. by POST.

<br><br>

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

<br><br>

```python
onboarding_onboardee_create_did(to)
```
Generates a new public DID (Verinym) and creates an authenticated and encrypted packet of bytes with this information which can be sent e.g. by POST to the sender of a connection request.

Parameters:
- `to`

Returns:
- `to`
- `authcrypted_did_info`: authenticated and encrypted DID packet to be sent e.g. by POST to the sender of a connection request.

<br><br>

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

<br><br>


### Sovrin verifiable claims demo

`claims.py` in the `sovrin` folder demoes the ANVIL abstractions for Hyperledger Indy. This includes a network simulator for sending data and may serve as a base for building Sovrin into various interactions.

Run:
```
python3 claims.py
```


## Debugging

### CommonInvalidStructure or DidAlreadyExistsError

Error: `indy.error.IndyError: ErrorCode.CommonInvalidStructure` or `indy.error.IndyError: ErrorCode.DidAlreadyExistsError`

Fix:`rm ~/.indy_client` and re-run.

### Dlopen/dylib errors

Error: `OSError: dlopen(libindy.dylib, 6): image not found` or similar `dlopen` referencing `libsodium`

Fix: set `LD_LIBRARY_PATH` and `DYLD_LIBRARY_PATH` environment variables to `/path/to/indy/libindy/target/debug`. If that doesn't work, run `./scripts/test.sh`, which will detail the failure. This is most likely due to a `libsodium` upgrade, where Indy will look for `libsodium.XX.dyld` and you have `libsodium.YY.dyld`. Navigate to the referenced folder and make a copy of your `libsodium.YY.dyld` and rename the copy to `libsodium.XX.dyld`.

### Undocumented eccentricities

- Nonces should be fully numeric for Hyperledger Indy. This is a common cause of the `CommonInvalidStructure` error (code 113). There is an Indy-compatible nonce generator in the `sovrin/utilities` module.
- Schema versions must be floats to be compatible with Sovrin.
- Quart forms do not allow underscores in the `name` field.
