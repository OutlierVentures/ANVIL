import json, sys
from typing import List
from oef.agents import OEFAgent
from oef.query import Query, Constraint, Eq


results = False


class Searcher(OEFAgent):

    def on_search_result(self, search_id: int, agents: List[str]):
        with open('search_results.json', 'w') as outfile:
            json.dump(str(agents), outfile)
        self.stop()
        return


if __name__ == '__main__':
    search_terms = sys.argv[1].split('_')
    query_array = []
    for term in search_terms:
        query_array.append(Constraint(term, Eq(True)))
    query = Query(query_array)
    agent = Searcher('Searcher', oef_addr = '127.0.0.1', oef_port = 3333)
    agent.connect()
    agent.search_services(0, query)
    try:
        agent.run()
    finally:
        agent.stop()
        agent.disconnect()

