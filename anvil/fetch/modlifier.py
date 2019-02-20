'''
JSON to Fetch data model functions.
'''

import json

from oef.schema import AttributeSchema, DataModel, Description

def modlify(data):
    attributes = data['attributes']
    # This is the least restrictive apporach.
    # To make attributes required override the specific one with True as the third argument.
    attribute_list = []
    for key, value in attributes.items():
        attribute_list.append(AttributeSchema(key, bool, False, value))
    data_model = DataModel(data['name'], attribute_list, data['description'])
    return data_model


def load_json_file(path):
    with open(path) as file_:
        data = json.load(file_)
    return data


