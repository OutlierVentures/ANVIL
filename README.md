![ANVIL](./docs/img/anvil-transparent.png)

<p>
    <a href="https://github.com/fetchai" alt="Fetch.AI version">
        <img src="./docs/img/fetch-pr2.svg" />
    </a>
    <a href="https://github.com/hyperledger/indy-sdk" alt="Hyperledger Indy version">
        <img src="./docs/img/indy-1.8.svg" />
    </a>
</p>

Agent Negotiation Verifiable Interaction Layer – an app in the Convergence Stack.

ANVIL bridges Fetch.AI and Sovrin, bringing trusted agents to the Open Economic Framework. In short, ANVIL mitigates risk in AEA [FIPA](https://en.wikipedia.org/wiki/Foundation_for_Intelligent_Physical_Agents) negotiations with verifiable claims.

Encrypt your ANVIL connections with the `ANVIL_KEY` environment variable.

#### NOTE DURING DEV OF INDVIDUAL ACTOR FILES: CLEAR .indy_client AND RUN 1_, 2_, ... IN ORDER EACH TIME

## Requirements

- MacOS
  - Docker.
- Linux
  - Docker.
  - Python 3.7+ with your `python3` command linked to this version.

## Actors

There are four key parties involved in an ANVIL interaction:
1. Steward: an exisiting trust anchor on the Sovrin ledger used to onboard the other parties to Sovrin.
2. Issuer: the issuer of the credential used by:
3. Prover: the seller in a FIPA negotiation, proving they have the credential to make them trustworthy.
4. Verifier: the buyer in a FIPA negotiation, verifying the Prover's credential.


## Basics

The installer and install tester should be run from the root directory (the one containg this readme).

Install: `./scripts/install.sh`

Start Fetch node: `./scripts/start_fetch.sh`

Spin up Sovrin node pool: `./scripts/start_sovrin.sh`

Test install (requires a running Fetch node and Sovrin pool): `./scripts/test.sh`

Stop Fetch node: `./scripts/stop_fetch.sh`

Stop Sovrin node pool: `./scripts/stop_sovrin.sh`

Nodes are currently local.

The Fetch node sits on port 3333.

The Sovrin node pool sits on ports 9701 through 9708.

### Using apps


ANVIL sessions are encrypted in addition to the security of Sovrin and Fetch. As any actor using ANVIL, you must set an encryption key / password as an environment variable:
```
ANVIL_KEY=
```

Default mocked testing accounts are alredy set up for use without the Sovrin mainnet. If just testing, there's no need to set up the below.

For real accounts, set up your address and key as environment variables *on the relevant machine and in the same session (terminal) as running the app for each actor*. You only need to set up the components you are using, e.g. in the case where actor are already Sovrin-onboarded, where there is no need for a Steward.

```
WALLET_ID=
WALLET_KEY=
```

Optionally, also set `SOVRIN_SEED=` when initialising an acotor from a seed (generally only for Steward setup).

### Run Fetch AEAs

Go to the `fetch` folder.

In one terminal window, run the AEA providing the service:
```
python3 verifier.py
```

In another, run the AEA purchasing it:
```
python3 prover.py
```

### Run Sovrin verifiable claims

Go to the `sovrin` folder.

Run:
```
python3 claims.py
```

### Example data

Encoding used is personal preference. For Sophos, octal has been chosen.


### Network simulator

Import `send_data` and `receive_data`.

Sending:
```
send_data(data, channel)
```

Receiving:
```
receive_data(channel)
```


## Debugging

Error: `indy.error.IndyError: ErrorCode.CommonInvalidStructure` or `indy.error.IndyError: ErrorCode.DidAlreadyExistsError`

Fix:`rm ~/.indy_client` and re-run.

Indy failures may be due to missing environment variables, see install.sh for which ones have been modified. These may need to be set in `.bashrc` (non-login interactive shells) instead of `.bash_profile`.

Both the Prover and Verifier should have `data_model.json`. *ASK FETCH!! VERIFIER-SIDE: WHY DO I NEED THE DATA MODEL OF THE SERVICES I AM SEARCHING FOR (USED TO STRUCTURE QUERY)? I CAN'T POSSIBLY KNOW THE DATA MODEL BEFORE I HAVE PURCHASED THE SERVICE.*

On a proof reply (creating a proof), the requested attributes field is what will be revealed.


### Undocumented eccentricities found while writing this software

Nonces should be fully numeric for Hyperledger Indy. This is a common cause of the `CommonInvalidStructure` error (code 113). There is an Indy-compatible nonce generator in the `sovrin/utilities` module.

Schema versions must be floats to be compatible with Sovrin.

Quart forms do not allow underscores in the `name` field.
