# Logging for debugging AEAs
import logging
from oef.logger import set_logger
set_logger('oef.agents', logging.DEBUG)

# Imports
from typing import List
from oef.agents import OEFAgent
from oef.schema import DataModel
from oef.query import Query

'''
v OPTIONS v
'''
agent_ip = '127.0.0.1'
agent_port = 3333
'''
^ OPTIONS ^
'''

class EchoClientAgent(OEFAgent):

    def on_message(self, origin: str, dialogue_id: int, content: bytes):
        print('Received message: origin={}, dialogue_id={}, content={}'.format(origin, dialogue_id, content))

    def on_search_result(self, search_id: int, agents: List[str]):
        if len(agents) > 0:
            print('Agents found: ', agents)
            msg = b'hello'
            for agent in agents:
                print('Sending {} to {}'.format(msg, agent))
                self.send_message(0, agent, msg)
        else:
            print('No agent found.')

# Create agent and connect it to the OEF
client_agent = EchoClientAgent('echo_client', oef_addr= agent_ip , oef_port= agent_port)
client_agent.connect()

# Find server agent service and run
echo_model = DataModel('echo', [], 'Echo data service.')
echo_query = Query([], echo_model)
client_agent.search_services(search_id = 0, query = echo_query) # Must specify ID (not in docs)
client_agent.run()
