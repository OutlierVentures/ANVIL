'''
Verifier: AEA sending the CFP.
'''

import json
from typing import List
from oef.agents import OEFAgent
from oef.schema import AttributeSchema
from oef.messages import PROPOSE_TYPES
from oef.query import Query, Constraint, Eq
from aea_config import agent_ip, agent_port
from modlifier import modlify, load_json_file

class Verifier(OEFAgent):

    def __init__(self, public_key, oef_addr, oef_port, price_threshold_for_accept):
        OEFAgent.__init__(self, public_key, oef_addr, oef_port)
        self.price_threshold = price_threshold_for_accept

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

    '''
    DANGER: DEFAULT ACCEPTING ALL.
    # Accept Proposals that this agent sent a CFP for.
    '''
    def on_propose(self, msg_id: int, dialogue_id: int, origin: str, target: int, proposals: PROPOSE_TYPES):
        print('[{0}]: Received propose from agent {1}'.format(self.public_key, origin))
        for i, p in enumerate(proposals):
            print('[{0}]: Proposal {1}: {2}'.format(self.public_key, i, p.values))
            if p.values['price'] < self.price_threshold:
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


if __name__ == '__main__':
    agent = Verifier('Verifier', oef_addr = agent_ip, oef_port = agent_port, price_threshold_for_accept = 99)
    agent.connect()
    data_model = modlify(load_json_file('../example_data/data_model.json'))
    query = Query([Constraint(AttributeSchema('license', bool, False, 'value').name, Eq(True)),
                Constraint(AttributeSchema('fetch', bool, False, 'value').name, Eq(True)),
                Constraint(AttributeSchema('iota', bool, False, 'value').name, Eq(True)),
                Constraint(AttributeSchema('ocean', bool, False, 'value').name, Eq(True))],
                data_model)
    agent.search_services(0, query)
    try:
        agent.run()
    finally:
        agent.stop()
        agent.disconnect()
    