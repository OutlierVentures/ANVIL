'''
Verifier: AEA sending the CFP.
'''


from oef.agents import OEFAgent, List
from oef.schema import AttributeSchema
from oef.query import Query, Constraint, Eq
from aea_config import agent_ip, agent_port
from modlifier import modlify

class Verifier(OEFAgent):

    # For every agent returned in the service search, send a CFP to obtain resources from them.
    def on_search_result(self, search_id: int, agents: List[str]):
        print('Agent found: {0}'.format(agents))
        for agent in agents:
            print('Sending to agent {0}'.format(agent))
            # Send a query with no constraints, i.e. 'give me all the resources you can propose.'
            query = Query([])
            self.send_cfp(0, agent, query)

    '''
    DANGER: DEFAULT ACCEPTING ALL.
    # Accept Proposals that this agent sent a CFP for.
    '''
    def on_propose(self, origin: str, dialogue_id: int,
                   msg_id: int, target: int,
                   # Not documented. Marked PROPOSE_TYPES so assuming bool means binary yes/no.
                   proposals: bool):
        print('Received propose from agent {0}'.format(origin))
        for i, p in enumerate(proposals):
            print('Proposal {}: {}'.format(i, p.values))
        print('Accepting Propose.')
        self.send_accept(dialogue_id, origin, msg_id + 1, msg_id)

    # Get data from incoming messages from the Prover.
    def on_message(self, origin: str,
                   dialogue_id: int,
                   content: bytes):
        key, value = content.decode().split(':')
        print('Received measurement from {}: {}={}'.format(origin, key, float(value)))


if __name__ == '__main__':
    agent = Verifier("Verifier", oef_addr = agent_ip, oef_port = agent_port)
    agent.connect()
    data_model = modlify('../example_data/data_model.json')
    query = Query([Constraint(AttributeSchema('license', bool, False, 'value'), Eq(True)),
                Constraint(AttributeSchema('fetch', bool, False, 'value'), Eq(True)),
                Constraint(AttributeSchema('iota', bool, False, 'value'), Eq(True)),
                Constraint(AttributeSchema('ocean', bool, False, 'value'), Eq(True))],
                data_model)
    # Search ID undocumented
    agent.search_services(search_id = 0, query = query)
    agent.run()
    