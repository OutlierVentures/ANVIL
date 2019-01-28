'''
Data models for Fetch-Sovrin interfacing.

entity_model is a Sovrin entity instantiated as a Fetch data model.
claim_model is a Sovrin verifiable claim instantiated as a Fetch data model.
claim_model contains three sub-models: claim, revocation and signature.

Fetch: see 'Definining Data Models' in oefpy/docs after running installer.
Sovrin: JSON-LD, see https://www.w3.org/TR/verifiable-claims-data-model.

=======================================================================
TODO:
Signatures MUST be Camenisch-Lysyanskaya (CL) signatures
=======================================================================

'''

from oef.schema import AttributeSchema, DataModel

# Fetch attribute (name, type, required, description)

# Universal
context = AttributeSchema("context", str, True, "JSON-LD context.")
did = AttributeSchema("did", str, True, "Decentralized Identifier.")
sov_type = AttributeSchema("sov_type", str, True, "Sovrin type array or sig/revoc type.")


# Entity-specific
entity_name = AttributeSchema("entity_name", str, False, "Entity name.")
entity_contact = AttributeSchema("entity_contact", str, False, "Entity contact.")

# Claim-specific
claim_issuer = AttributeSchema("claim_issuer", str, True, "Claim issuer.")
claim_issued = AttributeSchema("claim_issued", str, True, "Claim issue date.")
# Specific to age-related claims - will be updated to be dynamic NOTE IS INT
claim_claim_ageOver = AttributeSchema("claim_claim_ageOver", int, False, "Age over claim.")
claim_sig_created = AttributeSchema("claim_sig_created", str, True, "Signature creation date.")
claim_sig_creator = AttributeSchema("claim_sig_creator", str, True, "Signature creator.")
claim_sig_domain = AttributeSchema("claim_sig_domain", str, False, "Signature domain.")
claim_sig_nonce = AttributeSchema("claim_sig_nonce", str, True, "Signature nonce.")
claim_sig_signatureValue = AttributeSchema("claim_sig_signatureValue", str, True, "Signature value.")

# Placeholders for recursive models (WIP)
claim_claim = AttributeSchema("claim_claim", str, True, "Claim submodel placeholder.")
claim_sig = AttributeSchema("claim_sig", str, True, "Signature submodel placeholder.")



'''
# SOVRIN ENTITY EXAMPLE
{
  "@context": "https://w3id.org/identity/v1",
  "id": "did:example:ebfeb1f712ebc6f1c276e12ec21",
  "type": ["Entity", "Person"],
  "name": "Thorin Oakenshield",
  "contact": "king@lonelymountain.com"
}
'''
# Fetch port of Sovrin entity
entity_model = DataModel("entity", [
    context,
    did,
    sov_type,
    entity_name,
    entity_contact,
], "Sovrin entity.")


'''
SOVRIN VERIFIABLE CLAIM EXAMPLE
{
  "@context": [
    "https://w3id.org/identity/v1",
    "https://w3id.org/security/v1"
  ],
  "id": "http://example.gov/credentials/3732",
  "type": ["Credential", "ProofOfAgeCredential"],
  "issuer": "https://dmv.example.gov",
  "issued": "2010-01-01",
  "claim": {
    "id": "did:example:ebfeb1f712ebc6f1c276e12ec21",
    "ageOver": 21
  },
  "signature": {
    "type": "LinkedDataSignature2015",
    "created": "2016-06-18T21:10:38Z",
    "creator": "https://example.com/jdoe/keys/1",
    "domain": "json-ld.org",
    "nonce": "6165d7e8",
    "signatureValue": "g4j9UrpHM4/uu32NlTw0HDaSaYF2sykskfuByD7UbuqEcJIKa+IoLJLrLjqDnMz0adwpBCHWaqqpnd47r0NKZbnJarGYrBFcRTwPQSeqGwac8E2SqjylTBbSGwKZkprEXTywyV7gILlC8a+naA7lBRi4y29FtcUJBTFQq4R5XzI="
  }
}
'''

claim_claim_model = DataModel("claim_claim", [
    did,
    claim_claim_ageOver, # Will be switched to certificate-based claims in future
], "Claim field of a claim.")

claim_sig_model = DataModel("claim_sig", [
    sov_type,
    claim_sig_created,
    claim_sig_creator,
    claim_sig_domain,
    claim_sig_nonce,
    claim_sig_signatureValue,
], "Signature field of a claim.")

claim_model = DataModel("claim", [
    context,
    did,
    sov_type,
    claim_issuer,
    claim_issued,
    claim_claim,
    claim_sig,
], "Verifiable claim.")
