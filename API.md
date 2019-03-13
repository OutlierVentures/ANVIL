# ANVIL API Reference

## Sovrin

Import each of these in the format `from sovrin.[module] import [function]`

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


```python
teardown(pool_name, pool_handle, actor_list = [])
```
Tears down connections after a set of interactions.

Parameters:
- `pool_name`
- `pool_handle`
- `actor_list`: list of actor data structures to tear down, e.g. `[alice, bob]` for data structures `alice` and `bob` created with `set_self_up()`





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
