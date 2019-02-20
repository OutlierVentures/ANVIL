'''
Prover: AEA receiving the CFP.
'''

import json
from oef.agents import OEFAgent
from oef.schema import AttributeSchema, DataModel, Description
from oef.messages import CFP_TYPES


class Prover(OEFAgent):


    def __init__(self, public_key, oef_addr, oef_port, data_model_json, service_description_json, data_to_send_json, price):
        OEFAgent.__init__(self, public_key, oef_addr, oef_port)
        self.data_model = modlify(data_model_json)
        self.service = Description(service_description_json, self.data_model)
        self.data = data_to_send_json
        self.price = price


    # Send a Propose to the sender of the CFP.
    def on_cfp(self, msg_id: int, dialogue_id: int, origin: str, target: int, query: CFP_TYPES):
        print("[{0}]: Received CFP from {1}".format(self.public_key, origin))
        proposal = Description({"price": self.price})
        print("[{}]: Sending propose at price: {}".format(self.public_key, self.price))
        self.send_propose(msg_id + 1, dialogue_id, origin, target + 1, [proposal])


    # Send data if Proposal accepted
    def on_accept(self, msg_id: int, dialogue_id: int, origin: str, target: int):
        print("[{0}]: Received accept from {1}.".format(self.public_key, origin))
        encoded_data = json.dumps(self.data).encode("utf-8")
        print("[{0}]: Sending data to {1}: {2}".format(self.public_key, origin, self.data))
        self.send_message(0, dialogue_id, origin, encoded_data)
        self.stop()


    # Send data if Proposal accepted
    def on_decline(self, msg_id: int, dialogue_id: int, origin: str, target: int):
        print("[{0}]: Received decline from {1}.".format(self.public_key, origin))
        self.stop()


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


if __name__ == '__main__':
    data_model_json = load_json_file('../example_data/data_model.json')
    service_description_json = load_json_file('../example_data/service_description.json')
    data_to_send_json = load_json_file('../example_data/data_to_send.json')
    agent = Prover('Prover', oef_addr = '127.0.0.1', oef_port = 3333, data_model_json = data_model_json, service_description_json = service_description_json, data_to_send_json = data_to_send_json, price = 100)
    agent.connect()
    agent.register_service(0, agent.service)
    print('Waiting for verifier...')
    try:
        agent.run()
    finally:
        agent.stop()
        agent.disconnect()
