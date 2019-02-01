# ANVIL

Agent Negotiation Verifiable Interaction Layer – an app in the Convergence Stack.

Bridges Fetch.AI and Sovrin, mitigating risk in AEA FIPA negotiations with verifiable claims.


## Requirements

- Linux or MacOS
- Docker


## Basics

Install: `./install.sh`

Start Fetch node: `./start_fetch_node.sh`

Spin up Sovrin node pool: `./start_sovrin_pool.sh`

Test install (requires a running Sovrin pool): `./test_install.sh`

Stop Fetch node: `./stop_fetch_node.sh`

Stop Sovrin node pool: `./stop_sovrin_pool.sh`

Nodes are currently local.

The Fetch node sits on port 3333.

The Sovrin node pool sits on ports 9701 through 9708.

### Run Fetch AEAs

Go to the `fetch` folder.

In one terminal window:
```
python3 client_agent.py
```

In another:
```
python3 server_agent.py
```

### Run Sovrin verifiable claims

Go to the `sovrin` folder.

Run:
```
python3 claims.py
```


## Roadmap

### Next up

0. Refactor `claims.py` into modular comnponents (half done).
1. Restructure: Fetch, Sovrin and ANVIL folders (0.0.5).
2. Map Fetch AEAs to Sovrin trust anchors.
3. FIPA negotiation between Alice and Bob:
	1. Alice initiates a Call For Proposal (CFP) pointing to a verifiable claim in a Fetch `DataModel`.
	2. Bob verifies claim & accepts or rejects the CFP.
4. CLI interface for FIPA negotiations with verifiable claims (0.1).

### Backlog

1. Split Fetch, Sovrin and ANVIL into separate repositories.
2. Loading bar for `install.sh`.

### Could-haves

1. Run ANVIL in a Python `venv` (possibly as a Python shell CLI)
2. Revocation registries (under credential issuance).
3. Verifiable claim that the Fetch transaction took place after accepting CFP.


## Issue fixes

Indy failures may be due to missing environment variables, see install.sh for variables. These may need to be set in `.bashrc` (non-login interactive shells) instead of `.bash_profile`.

Indy clashes such as already existsing DIDs and pools may be fixed by deleting the `.indy_client` in your home folder.


## Sovrin credential issuance steps

Actors: User, Establishment (credential issuer e.g. college), Steward

DID: two types
	Verinym: legal ID
	Pseudonym: blinded ID for private connections (‘pairwise unique’ if used for single relationship)

NYM = person on ledger. NYM transaction fields:
	Dest: target DID
	Role: role of user
	Verkey: target verification key

Trust anchor = existing person/organisation on ledger.
To use the ledger you need to become a trust anchor.
This means contacting someone already on the ledger, e.g. Stewards, which are always trust anchors.

STEP 1: Connect to nodes pool, e.g local test pool, Sovrin pool.

In code: create pool ledger config & open pool ledger

STEP 2: Give Steward agent ownership of DID for Steward role on ledger.

In code: Steward - create wallet, open wallet, create & store DID for self.

STEP 3: Onboarding of Establishment.

Step 3.1: Establishment connects to Steward with pairwise-unique DIDs.

Steward:
- Create pairwise DID for connection with Establishment
- Write tx to ledger
- Send connection request to Establishment.

Establishment:
- Accepts request
- Creates wallet for themselves
- Creates pairwise DID for connection with Steward, adds to wallet
- Create connection response (did, verkey, nonce)
- Get Steward’s verkey & encrypt connection response with it, send to Steward. NOTE: only recipient can decrypt, can verify integrity but not sender identity.

Steward:
- Decrypt & authenticate connection
- Write Establishment’s DID *for this connection* to ledger

Step 3.2: Establishment creates their NYM.

Establishment:
- Create did in wallet, authenticate & encrypt did+verkey, send to Steward

Steward:
- Decrypt, ask ledger for Establishment’s verkey & compare to authenticate
- Write NYM tx to ledger

STEP 4: Set up credential schema (e.g. certificate).

Any trust anchor can create schema & send to ledger. Can’t change once on ledger.

STEP 5: Set up credential definition (attach sining key information to schema).

Any trust anchor.  Get schema, create def & send tx to ledger.

STEP 6: User establishes a connection with Establishment (a trust anchor), making them a trust anchor.

STEP 7: Establishment creates certificate credential offer for the user.

STEP 8: User creates a Master Secret in their wallet so they can use the credential.

Master Secret used by Prover to guarantee credential applies uniquely to them.

STEP 9: User gets credential definition from ledger & creates credential request.

STEP 10: Establishment writes credential attributes & issues.

STEP 11: User stores issued credential in their wallet.


TODO: Verification (‘Apply for a job’ section in Indy).


