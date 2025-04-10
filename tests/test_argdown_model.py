"test argdown data model"

import pytest

from pyargdown import (
    ArgdownMultiDiGraph,
    ArgdownEdge,
    Argument,
    Conclusion,
    DialecticalType,
    Proposition,
    PropositionReference,
    Valence,
)

@pytest.fixture
def propositions1():
    return [
        Proposition("P1", ["Proposition 1"], data={"k": 1}),
        Proposition("P2", ["Proposition 2"], data={"k": 2}),
        Proposition("P3", ["Proposition 3"], data={"k": 3}),
    ]

@pytest.fixture
def arguments1():
    pcs = [
        PropositionReference("P1", "1"),
        Conclusion("P2", "2", inference_info="Modus ponens", inference_data={"uses": ["1"]}),
    ]
    return [
        Argument("A1", ["Argument 1"], data={"k": 1}),
        Argument("A2", ["Argument 2"], data={"k": 1}),
        Argument("A3", ["Argument 3"], data={"k": 1}, pcs=pcs),
    ]

@pytest.fixture
def edges1():
    return [
        ArgdownEdge("A1", "P2", valence=Valence.SUPPORT, dialectics=[DialecticalType.SKETCHED]),
        ArgdownEdge("A2", "P3", valence=Valence.SUPPORT, dialectics=[DialecticalType.GROUNDED]),
        ArgdownEdge("A3", "A2", valence=Valence.ATTACK, dialectics=[DialecticalType.SKETCHED]),
    ]

@pytest.fixture
def edges1_rev():
    return [
        ArgdownEdge("A1", "P2", valence=Valence.SUPPORT, dialectics=[DialecticalType.AXIOMATIC]),
        ArgdownEdge("A1", "P2", valence=Valence.SUPPORT, data={"k": 1}),
        ArgdownEdge("A1", "P2", valence=Valence.SUPPORT, data={"k": 2}),
        ArgdownEdge("A1", "P2", valence=Valence.ATTACK, data={"k": 3}),
    ]



def test_propositions(propositions1):
    argdown = ArgdownMultiDiGraph()
    for prop in propositions1:
        argdown.add_proposition(prop)

    print(argdown)
    assert len(argdown.nodes) == len(propositions1)
    assert len(argdown.nodes) == len(argdown.propositions)

    assert all(isinstance(p, Proposition) for p in argdown.propositions)


    for prop in propositions1:
        print(prop)
        assert argdown.get_proposition(prop.label).data == prop.data

def test_arg_needs_props(arguments1):
    argdown = ArgdownMultiDiGraph()
    for arg in arguments1:
        if arg.pcs:
            with pytest.raises(ValueError):
                argdown.add_argument(arg)
        else:
            argdown.add_argument(arg)

    print(argdown)
    assert len(argdown.nodes) == len([a for a in arguments1 if not a.pcs])

def test_arguments(propositions1, arguments1):
    argdown = ArgdownMultiDiGraph()
    for prop in propositions1:
        argdown.add_proposition(prop)
    for arg in arguments1:
        argdown.add_argument(arg)

    print(argdown)
    assert len(argdown.nodes) == len(arguments1) + len(propositions1)
    assert len(argdown.arguments) == len(arguments1)

    assert all(isinstance(a, Argument) for a in argdown.arguments)

    for arg in arguments1:
        assert argdown.get_argument(arg.label).data == arg.data

def test_edges(propositions1, arguments1, edges1):
    argdown = ArgdownMultiDiGraph()

    for edge in edges1:
        with pytest.raises(ValueError):
            argdown.add_dialectical_relation(edge)

    for prop in propositions1:
        argdown.add_proposition(prop)
    for arg in arguments1:
        argdown.add_argument(arg)
    for edge in edges1:
        argdown.add_dialectical_relation(edge)

    print(argdown)
    assert len(argdown.edges) == len(edges1)
    assert len(argdown.dialectical_relations) == len(edges1)

    print(argdown.dialectical_relations)
    assert len([r for r in argdown.dialectical_relations if DialecticalType.SKETCHED in r.dialectics]) == 2

    for edge in edges1:
        print(edge)
        assert argdown.get_dialectical_relation(edge.source, edge.target)[0].valence == edge.valence
        assert argdown.get_dialectical_relation(edge.source, edge.target)[0].dialectics == edge.dialectics
        assert argdown.get_dialectical_relation(edge.source, edge.target)[0].data == edge.data

def test_update_edges(propositions1, arguments1, edges1, edges1_rev):
    argdown = ArgdownMultiDiGraph()

    for prop in propositions1:
        argdown.add_proposition(prop)
    for arg in arguments1:
        argdown.add_argument(arg)
    for edge in edges1:
        argdown.add_dialectical_relation(edge)

    print(argdown)

    for edge in edges1_rev:
        old = argdown.get_dialectical_relation(edge.source, edge.target)[0]
        if edge.valence != old.valence:
            with pytest.raises(ValueError):
                argdown.update_dialectical_relation(edge)
        else:
            argdown.update_dialectical_relation(edge)

    edges = argdown.get_dialectical_relation(source="A1", target="P2")
    print(edges)
    assert len(edges) == 1
    assert edges[0].data["k"] == 2

    for edge in edges1_rev:
        old = argdown.get_dialectical_relation(edge.source, edge.target)[0]
        if edge.valence != old.valence:
            with pytest.raises(ValueError):
                argdown.add_dialectical_relation(edge, allow_exists=False)
            argdown.add_dialectical_relation(edge, allow_exists=True)

    print(argdown)
    edges = argdown.get_dialectical_relation(source="A1", target="P2")
    print(edges)
    assert len(edges) == 2
    for e in edges:
        if e.valence == Valence.SUPPORT:
            assert e.data["k"] == 2
        if e.valence == Valence.ATTACK:
            assert e.data["k"] == 3



def test_update_argdown():
    argdown = ArgdownMultiDiGraph()
    argdown.add_proposition(Proposition("P1", ["Proposition 1"]))
    argdown.add_proposition(Proposition("P2", ["Proposition 2"]))
    argdown.add_proposition(Proposition("P3", ["Proposition 3"]))
    argdown.add_argument(Argument("A1", ["Argument 1"], pcs=[PropositionReference("P1", "1"), Conclusion("P2", "2")]))
    argdown.add_argument(Argument("A2", ["Argument 2"], pcs=[PropositionReference("P2", "1"), Conclusion("P3", "2")]))
    argdown._update()

    rels = argdown.get_dialectical_relation("A1", "A2")
    assert len(rels) == 1
    assert rels[0].valence == Valence.SUPPORT
    assert rels[0].dialectics == [DialecticalType.GROUNDED]

    argdown.add_proposition(Proposition("P4", ["Proposition 4"]))
    argdown.update_argument("A2", Argument("A2", ["Argument 2"], pcs=[PropositionReference("P4", "1"), Conclusion("P3", "2")]))
    argdown._update()
    assert argdown.get_dialectical_relation("A1", "A2") is None

    argdown.add_dialectical_relation(ArgdownEdge("P2", "P4", valence=Valence.CONTRADICT, dialectics=[DialecticalType.AXIOMATIC]))
    argdown._update()
    rels = argdown.get_dialectical_relation("A1", "A2")
    assert len(rels) == 1
    assert rels[0].valence == Valence.ATTACK
    assert rels[0].dialectics == [DialecticalType.GROUNDED]


