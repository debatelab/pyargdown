import pytest

import networkx as nx
from textwrap import dedent

from pyargdown.model import ArgdownMultiDiGraph
from pyargdown.parser import ArgumentMapParser
from pyargdown.parser.base import _UNNAMED_ARGUMENT

@pytest.fixture
def argdown_block1():
    return dedent("""
    [C]: Claim.
        + [Pro1]: Pro1.
        - [Con1]: Con1.
            - [Rbt1]: Rebuttal1.
    """).strip()

@pytest.fixture
def argdown_block2():
    return dedent("""
    [Pro1]: Pro1.
        +> [C]: Claim.
            - [Con1]: Con1.
                - [Rbt1]: Rebuttal1.
    """).strip()

# TODO: Add more tests

def test_ingest1(argdown_block1):
    argdown = ArgdownMultiDiGraph()
    print(argdown.nodes.items())
    print(argdown_block1)
    parser = ArgumentMapParser()
    tree = parser(argdown_block1)
    print(tree)
    argdown = parser.ingest_in_argmap(tree, argdown)
    node_link_data = nx.node_link_data(argdown)
    print(node_link_data)
    assert argdown.get_proposition("Rbt1").texts == ["Rebuttal1."]
    assert argdown.get_proposition("C").texts == ["Claim."]
    assert argdown.get_dialectical_relation("Rbt1", "Con1")[0].valence.name == "ATTACK"
    assert argdown.get_dialectical_relation("Con1", "C")[0].valence.name == "ATTACK"
    assert argdown.get_dialectical_relation("Pro1", "C")[0].valence.name == "SUPPORT"
    assert argdown.number_of_edges() == 3

def test_equiv12(argdown_block1, argdown_block2):
    argdown = ArgdownMultiDiGraph()
    parser = ArgumentMapParser()
    tree1 = parser(argdown_block1)
    argdown1 = parser.ingest_in_argmap(tree1, argdown)
    tree2 = parser(argdown_block2)
    argdown2 = parser.ingest_in_argmap(tree2, argdown)
    assert argdown1.number_of_nodes() == argdown2.number_of_nodes()
    assert argdown1.number_of_edges() == argdown2.number_of_edges()    
    for node in argdown1.nodes:
        assert argdown1.nodes[node] == argdown2.nodes[node]
    for source, target, _ in argdown1.edges:
        assert argdown1.get_dialectical_relation(source,target) == argdown2.get_dialectical_relation(source,target)
