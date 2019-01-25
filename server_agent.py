# Logging for debugging AEAs
import logging
from oef.logger import set_logger
set_logger('oef.agents', logging.DEBUG)

# Imports
from oef.agents import OEFAgent
from oef.schema import DataModel, Description

'''
v OPTIONS v
'''
agent_ip = '127.0.0.1'
agent_port = 3333
'''
^ OPTIONS ^
'''

class EchoServiceAgent(OEFAgent):

    # Called on message receipt, echoing the text back to origin.
    def on_message(self, origin: str, dialogue_id: int, content: bytes):
        print('Received message: origin={}, dialogue_id={}, content={}'.format(origin, dialogue_id, content))
        print('Sending {} back to {}'.format(content, origin))
        self.send_message(dialogue_id, origin, content)

# Create agent and connect it to the OEF
server_agent = EchoServiceAgent('echo_server', oef_addr = agent_ip, oef_port = agent_port)
server_agent.connect()

# Define data model
echo_model = DataModel('echo', [], 'echo data service.')
echo_description = Description({}, echo_model)

# Register the agent service and start it
server_agent.register_service(echo_description)
server_agent.run()
print('Service ready.')
