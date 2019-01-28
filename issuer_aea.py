'''
AEA claim issuer.
Claim is defined as a Fetch data model with Sovrin claims structure.
Verifiable claims architecture: https://www.w3.org/TR/verifiable-claims-data-model/
'''

from data_model import entity_model
from oef.schema import Description


issuer = Description({
    'did':              'did:example:ebfeb1f712ebc6f1c276e12ec21',
    'sov_type':         '["Entity", "Person"]',
    'entity_name':      'Thorin Oakenshield',
    'entity_contact':   'king@lonelymountain.com',
}, entity_model)

#print(issuer.__dict__) # See format
print(issuer.__dict__['values']['did'])
