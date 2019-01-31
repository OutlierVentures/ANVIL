from data_model import claim_model, claim_claim_model, claim_sig_model
from oef.schema import Description

import json

claim_claim = Description({
    'did': 'did:example:ebfeb1f712ebc6f1c276e12ec21',
    'claim_claim_ageOver': 18,
}, claim_claim_model)

claim_sig = Description({
    'sov_type': 'LinkedDataSignature2015', # NOTE MUST BE CL SIG, will be updated 
    'claim_sig_created': '2019-01-01T00:00:00Z',
    'claim_sig_creator': 'Thorin Oakenshield',
    'claim_sig_domain': 'json-ld.org',
    'claim_sig_nonce': '6165d7e8',
    'claim_sig_signatureValue': 'g4j9UrpHM4/uu32NlTw0HDaSaYF2sykskfuByD7UbuqEcJIKa+IoLJLrLjqDnMz0adwpBCHWaqqpnd47r0NKZbnJarGYrBFcRTwPQSeqGwac8E2SqjylTBbSGwKZkprEXTywyV7gILlC8a+naA7lBRi4y29FtcUJBTFQq4R5XzI=',
}, claim_sig_model)



claim = Description({
    'context': '["https://w3id.org/identity/v1", "https://w3id.org/security/v1"]',
    'did': 'http://middleearth.gov/credentials/wgh3uCwg',
    'sov_type': '["Credential", "ProofOfAgeCredential"]',
    'claim_issuer': 'Thorin Oakenshield',
    'claim_issued': '2019-01-01T00:00:00Z',
    'claim_claim': 'PLACEHOLDER',
    'claim_sig': 'PLACEHOLDER',
}, claim_model)


print(claim.__dict__)

