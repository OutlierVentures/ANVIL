'''
Verifier: AEA sending the CFP.
'''

import json, sys
from typing import List
from oef.agents import OEFAgent
from oef.schema import AttributeSchema, DataModel
from oef.messages import PROPOSE_TYPES
from oef.query import Query, Constraint, Eq


class Verifier(OEFAgent):


    def __init__(self, public_key, oef_addr, oef_port, max_price):
        OEFAgent.__init__(self, public_key, oef_addr, oef_port)
        self.price_threshold = max_price


    # For every agent returned in the service search, send a CFP to obtain resources from them.
    def on_search_result(self, search_id: int, agents: List[str]):
        if len(agents) == 0:
            print('[{}]: No agent found. Stopping...'.format(self.public_key))
            self.stop()
            return
        print('[{0}]: Agent found: {1}'.format(self.public_key, agents))
        # 'None' query returns all the resources the prover can propose.
        for agent in agents:
            print('[{0}]: Sending to agent {1}'.format(self.public_key, agent))
            query = None
            self.send_cfp(1, 0, agent, 0, query)


    # Accept Proposals that this agent sent a CFP for.
    def on_propose(self, msg_id: int, dialogue_id: int, origin: str, target: int, proposals: PROPOSE_TYPES):
        print('[{0}]: Received propose from agent {1}'.format(self.public_key, origin))
        for i, p in enumerate(proposals):
            print('[{0}]: Proposal {1}: {2}'.format(self.public_key, i, p.values))
            if p.values['price'] > self.price_threshold:
                print('[{0}]: Declining Propose.'.format(self.public_key))
                self.send_decline(msg_id, dialogue_id, origin, msg_id + 1)
                self.stop()
                return
        print('[{0}]: Accepting Propose.'.format(self.public_key))
        self.send_accept(msg_id, dialogue_id, origin, msg_id + 1)
        self.stop()


    # Get data from incoming messages from the prover.
    def on_message(self, msg_id: int, dialogue_id: int, origin: str, content: bytes):
        data = json.loads(content.decode('utf-8'))
        print('[{0}]: Received measurement from {1}: {2}'.format(self.public_key, origin, data))
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
    search_terms = sys.argv[1].split('_')
    max_price = float(sys.argv[2])
    query_array = []
    for term in search_terms:
        query_array.append(Constraint(term, Eq(True)))
    query = Query(query_array)
    agent = Verifier('Verifier', oef_addr = 'oef.economicagents.com', oef_port = 3333, max_price = max_price)
    agent.connect()
    agent.search_services(0, query)
    try:
        agent.run()
    finally:
        agent.stop()
        agent.disconnect()
