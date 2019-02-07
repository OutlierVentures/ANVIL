'''
Prover: AEA receiving the CFP.
'''

from oef.agents import OEFAgent
from oef.schema import Description
from modlifier import modlify, descriptionify

from aea_config import agent_ip, agent_port

class Prover(OEFAgent):

    data_model = modlify('../example_data/data_model.json')
    service = descriptionify(data_model, '../example_data/service_description.json')

    # Send a Propose to the sender of the CFP.
    def on_cfp(self, origin: str,
               dialogue_id: int,
               msg_id: int,
               target: int,
               # Not documented. Marked CFP_TYPES so assuming bool means binary yes/no.
               query: bool):
        print('Received CFP from {0} with Query: {1}'
              .format(origin, query))
        proposal = Description({'price': 50})
        self.send_propose(dialogue_id, origin, [proposal], msg_id + 1, target + 1)

    # Send data if Proposal accepted
    def on_accept(self, origin: str,
                  dialogue_id: int,
                  msg_id: int,
                  target: int):
        print('Received accept from {0} cif {1} msgId {2} target {3}'
              .format(origin, dialogue_id, msg_id, target))

        '''
        # ACTUALLY SEND DATA, e.g.
        self.send_message(dialogue_id, origin, b'sovrin_tx_vel:0.82')
        '''
        
if __name__ == '__main__':
      agent = Prover('Prover', oef_addr = agent_ip, oef_port = agent_port)
      agent.connect()
      agent.register_service(agent.service)
      print('Waiting for verifier...')
      agent.run()
