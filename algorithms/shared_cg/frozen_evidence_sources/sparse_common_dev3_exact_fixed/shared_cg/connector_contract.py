"""City-neutral source/sink connector identity for the shared finite-time CG core.

The commodity sink is encoded by its dynamic terminal node and connector ID.
The descriptive to_physical_node_id may use either the terminal sentinel or
its original physical destination, as seen in accepted source builders.
"""


def sink_arc_matches(arc, demand_id, destination_node_id):
    prefix = f'sink_{demand_id}_'
    terminal_prefix = f'sink_{demand_id}_t'
    destination = str(destination_node_id)
    return (
        arc.get('arc_type') == 'sink_connector'
        and arc.get('arc_id', '').startswith(prefix)
        and arc.get('to_node_time_id', '').startswith(terminal_prefix)
        and arc.get('from_physical_node_id') == destination
        and arc.get('to_physical_node_id') in {destination, f'sink_{demand_id}'}
    )


def terminal_node_for_demand(demand, arcs):
    demand_id = str(demand['demand_id'])
    destination = str(demand['destination_node_id'])
    terminal_nodes = {arc['to_node_time_id'] for arc in arcs
                      if sink_arc_matches(arc, demand_id, destination)}
    if len(terminal_nodes) != 1:
        raise ValueError(f'{demand_id}: expected one unique legal sink terminal, got {len(terminal_nodes)}')
    return terminal_nodes.pop()
