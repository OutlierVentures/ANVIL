# ANVIL

Agent Negotiation Verifiable Interaction Layer – an app in the Convergence Stack.

Bridges Fetch.AI and Sovrin, mitigating risk in AEA FIPA negotiations with verifiable claims.


## Requirements

- Linux or MacOS
- Docker


## Setup

Install: `./install.sh`

Start Fetch node: `./startnode.sh`

Stop Fetch node: `./stopnode.sh`


## Notes for OV Labs

Indy failures may be due to missing environment variables, see install.sh for variables. These may need to be set in `.bashrc` (non-login interactive shells) instead of `.bash_profile`.


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


