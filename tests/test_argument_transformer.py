import pytest

import networkx as nx  # type: ignore
from textwrap import dedent

from pyargdown.model import ArgdownMultiDiGraph, Conclusion
from pyargdown.parser import ArgumentParser
from pyargdown.parser.base import _UNNAMED_ARGUMENT

@pytest.fixture
def argdown_block1():
    return dedent("""
        <Argument>: Argument

        (1) Premise.
        + [E1]: Evidence
        -- Modus ponens --
        (2) [C]: Conclusion.                          
    """).strip()

@pytest.fixture
def argdown_block2():
    return dedent("""
        (1) Premise.
        ----
        (2) Conclusion.                          
    """).strip()

@pytest.fixture
def argdown_block3():
    return dedent("""
        <Argument>

        (1) Premise.
            <+ Reason.
        ----
        (2) Conclusion.                          
    """).strip()


@pytest.fixture
def argdown_block4():
    return dedent("""
        <Argument>

        (1) Premise.
            <+ Reason.
        -- {"uses": ["1"]} --
        (2) Conclusion.                          
    """).strip()


@pytest.fixture
def argdown_block_without_head():
    return dedent("""
        (1) Premise.
        -----
        (2) Conclusion.                          
    """).strip()


def test_ingest1(argdown_block1):
    argdown = ArgdownMultiDiGraph()
    print(argdown.nodes.items())
    parser = ArgumentParser()
    tree = parser.parse(argdown_block1)
    print(tree.pretty())
    argdown = parser.ingest_in_argmap(tree, argdown)
    node_link_data = nx.node_link_data(argdown)
    print(node_link_data)
    assert argdown.get_argument("Argument").gists == ["Argument"]
    assert argdown.get_proposition("E1").texts == ["Evidence"]
    assert argdown.get_proposition("C").texts == ["Conclusion."]



def test_ingest2(argdown_block2):
    argdown = ArgdownMultiDiGraph()
    print(argdown.nodes.items())
    parser = ArgumentParser()
    tree = parser.parse(argdown_block2)
    print("Tree:")
    print(tree.pretty())
    argdown = parser.ingest_in_argmap(tree, argdown)
    node_link_data = nx.node_link_data(argdown)
    print(node_link_data)
    assert argdown.get_argument(_UNNAMED_ARGUMENT) is not None
    assert argdown.get_argument(_UNNAMED_ARGUMENT).gists == []


def test_ingest3(argdown_block3):
    argdown = ArgdownMultiDiGraph()
    print(argdown.nodes.items())
    parser = ArgumentParser()
    tree = parser.parse(argdown_block3)
    print("Tree:")
    print(tree.pretty())
    argdown = parser.ingest_in_argmap(tree, argdown)
    node_link_data = nx.node_link_data(argdown)
    print(node_link_data)
    assert argdown.get_argument("Argument").gists == []


def test_ingest4(argdown_block4):
    argdown = ArgdownMultiDiGraph()
    parser = ArgumentParser()
    tree = parser.parse(argdown_block4)
    print("Tree:")
    print(tree.pretty())
    argdown = parser.ingest_in_argmap(tree, argdown)
    print(argdown)
    assert argdown.arguments[0].pcs
    for c in argdown.arguments[0].pcs:
        if isinstance(c, Conclusion):
            assert c.inference_data
            assert c.inference_data["uses"] == ["1"]



def test_ingest_no_head(argdown_block_without_head):
    argdown = ArgdownMultiDiGraph()
    parser = ArgumentParser()
    tree = parser.parse(argdown_block_without_head)
    print("Tree:")
    print(tree.pretty())
    argdown = parser.ingest_in_argmap(tree, argdown)
    print(argdown)
    assert argdown.arguments[0].pcs
    for c in argdown.arguments[0].pcs:
        if isinstance(c, Conclusion):
            assert not(c.inference_data)
    
