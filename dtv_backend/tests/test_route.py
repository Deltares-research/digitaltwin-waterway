import networkx as nx
import shapely

import pytest

import dtv_backend.fis


@pytest.fixture
def FG():
    FG = nx.read_gpickle('../notebooks/fis-network/result/network_digital_twin_v0.3.pickle')
    for n, node in FG.nodes.items():
        node['geometry'] = shapely.geometry.shape(node['geometry'])
    for e, edge in FG.edges.items():
        edge['geometry'] = shapely.geometry.shape(edge['geometry'])
    return FG

@pytest.fixture
def nodes():
    test_nodes = [
        {"n": "8862371", "route_to_sea": False},
        {"n": "8864002", "route_to_sea": True}
    ]
    return test_nodes


def test_route_to_sea(FG, nodes):
    for row in nodes:
        result = dtv_backend.fis.route_to_sea(row["n"], FG)
        assert row['route_to_sea'] == result, "route to sea expected: {row['route_to_sea']}, observed: {result}"
