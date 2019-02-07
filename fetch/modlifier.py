'''
JSON to Fetch data model functions.
'''

import json

from oef.schema import AttributeSchema, DataModel, Description

def modlify(path_to_data_model):
    with open(path_to_data_model) as file_:
        data = json.load(file_)
    attributes = data['attributes']
    # This is the least restrictive apporach.
    # To make attributes required override the specific one with True as the third argument.
    attribute_list = []
    for key, value in attributes.items():
        attribute_list.append(AttributeSchema(key, bool, False, value))

    data_model = DataModel(data['name'], attribute_list, data['description'])
    return data_model

def descriptionify(data_model, path_to_description):
    with open(path_to_description) as file_:
        data = json.load(file_)
    description = Description(data, data_model)
    return description

