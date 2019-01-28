'''
Data models for Fetch-Sovrin interfacing.
Fetch: see 'Definining Data Models' in oefpy/docs after running installer.
Sovrin: see https://www.w3.org/TR/verifiable-claims-data-model.
'''

from oef.schema import AttributeSchema, DataModel

# Fetch attribute (name, type, required, description)
did = AttributeSchema("did", str, True, "Decentralized Identifier.")
sov_type = AttributeSchema("sov_type", str, True, "Sovrin type array.")
entity_name = AttributeSchema("entity_name", str, False, "Entity name.")
entity_contact = AttributeSchema("entity_contact", str, False, "Entity contact.")

'''
# SOVRIN ENTITY EXAMPLE
{
  "id": "did:example:ebfeb1f712ebc6f1c276e12ec21",
  "type": ["Entity", "Person"],
  "name": "Alice Bobman",
  "contact": "alice@example.com",
}
'''
# Fetch port of Sovrin entity
entity_model = DataModel("entity", [
    did,
    sov_type,
    entity_name,
    entity_contact,
], "A Sovrin entity.")
