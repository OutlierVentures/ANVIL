![ANVIL](./docs/img/anvil_logo_colour.svg)

<p align="center">
    <a href="https://github.com/fetchai" alt="Fetch.AI version">
        <img src="./docs/img/fetch_pr2.svg" />
    </a>
    <a href="https://github.com/hyperledger/indy-sdk" alt="Hyperledger Indy version">
        <img src="./docs/img/indy_1.8.svg" />
    </a>
</p>

Agent Negotiation Verifiable Interaction Layer: an app in the Convergence Stack.

ANVIL bridges Fetch.AI and Sovrin, bringing trusted agents to the Open Economic Framework. In short, ANVIL mitigates risk in AEA [FIPA](https://en.wikipedia.org/wiki/Foundation_for_Intelligent_Physical_Agents) negotiations with verifiable claims.


## Requirements

- Linux/MacOS and Docker.

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

The Fetch node sits on port 3333.

The Sovrin node pool sits on ports 9701 through 9708.

ANVIL apps sit on ports 5000 through 5003.

### Using apps

Default mocked testing accounts are already set up for use without the Sovrin mainnet. If just testing, there's no need to set up the wallets section below.

#### Wallets

For real accounts, set up your address and key as environment variables *on the relevant machine and in the same session (terminal) as running the app for each actor*. You only need to set up the components you are using, e.g. in the case where actor are already Sovrin-onboarded, where there is no need for a Steward.

```
WALLET_ID=
WALLET_KEY=
```

Optionally, also set `SOVRIN_SEED=` when initialising an acotor from a seed (generally only for Steward setup).

### Run actor apps

Go to the `anvil` subfolder. Run the agent(s) of choice:

```
python3 steward.py
```
```
python3 issuer.py
```
```
python3 prover.py
```
```
python3 verifier.py
```

### Run Sovrin verifiable claims demo

Go to the `sovrin` folder.

Run:
```
python3 claims.py
```

#### Example data

Encoding used is personal preference. For Sophos, octal has been chosen.


#### Network simulator

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

On a proof reply (creating a proof), the requested attributes field is what will be revealed.


### Undocumented eccentricities found while writing this software

Nonces should be fully numeric for Hyperledger Indy. This is a common cause of the `CommonInvalidStructure` error (code 113). There is an Indy-compatible nonce generator in the `sovrin/utilities` module.

Schema versions must be floats to be compatible with Sovrin.

Quart forms do not allow underscores in the `name` field.
