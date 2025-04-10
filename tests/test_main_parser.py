"test main parser"

import pytest

from textwrap import dedent

from pyargdown.model import Conclusion, DialecticalType, Valence
from pyargdown import parse_argdown
from pyargdown.parser.base import ArgdownParser


@pytest.fixture
def argdown_snippet1():
    return dedent("""
    [Claim A]
      + <Reason 1>
      - <Reason 2>
                  
    [Claim B]
      + <Reason 3>
      - <Reason 4>
                  
    <Reason 4>
    
    (1) Premise 1.
    -----
    (2) Conclusion.
    >< [Claim B]
    """)

@pytest.fixture
def argdown_snippet2():
    return dedent("""
    <Reason 3>
      <- <Reason 5>
      -> <Reason 6>
                              
    <Reason 3>
    
    """)

@pytest.fixture
def argdown_snippet3():
    return dedent("""
    [A]
      + <Reason 1>: {"a": 1}
    
    <Reason 1>: {"b": 2}
    
    <Arg>
                  
    (1) P.
    -----
    (2) Q.
    + <Reason 1>: {"a": 2, "c": 3}
    """)


@pytest.fixture
def argdown_snippet4():
    return dedent("""
    [Claim A]
      + <Reason 1>
      - Reason 2
                  
    Claim B
    """)


@pytest.fixture
def argdown_snippet5():
    return dedent("""
        <Argument>

        (1) Premise.
            <+ Reason.
        -- {uses: ["1"]} --
        (2) Conclusion.                          

        <Argument2>

        (1) Premise.
            <+ Reason.
        -- {uses: [1, 2]} --
        (2) Conclusion.                                            
    """).strip()


@pytest.fixture
def argdown_snippet6():
    return dedent("""

    // comment comment :-)

    <Reason 3>
      <- <Reason 5>
      -> <Reason 6>
                              
    <Reason 3>
    
    """)

@pytest.fixture
def argdown_map_freewill():
    return dedent("""
        [Free Will_C]: Humans have free will.
        [Determinism_C]: All events are determined by prior causes.
        [Compatibilism_C]: Free will and determinism are compatible.
        
        <FreeWill>
            + [Free Will_C]
        <Determinism>
            + [Determinism_C]
            -> [Free Will_C]
        <Compatibilism>
            + [Compatibilism_C]
            +> [Free Will_C]
            -> [Determinism_C]
        """).strip()              

def test_freewill(argdown_map_freewill):
    argdown = parse_argdown(argdown_map_freewill)
    print(argdown)

    assert len(argdown.nodes) == 6
    assert len(argdown.propositions) == 3
    assert len(argdown.arguments) == 3

def test_parse1(argdown_snippet1):
    argdown = parse_argdown(argdown_snippet1)
    print(argdown)

    assert len(argdown.nodes) == 8
    assert len(argdown.propositions) == 4
    assert len(argdown.arguments) == 4
    print(argdown.propositions)
    assert sum(ArgdownParser.is_unlabeled(prop) for prop in argdown.propositions) == 0

    rel = argdown.get_dialectical_relation("Reason 4", "Claim B")
    assert len(rel) == 1
    assert rel[0].valence == Valence.ATTACK
    assert set(rel[0].dialectics) == {DialecticalType.SKETCHED, DialecticalType.GROUNDED}

def test_parse2(argdown_snippet1, argdown_snippet2):
    argdown = parse_argdown(argdown_snippet2)
    print(argdown)

    assert len(argdown.nodes) == 3
    assert len(argdown.propositions) == 0
    assert len(argdown.arguments) == 3
    assert all(not ArgdownParser.is_unlabeled(arg) for arg in argdown.arguments)

    argdown = parse_argdown([argdown_snippet1, argdown_snippet2])
    print(argdown)

    assert len(argdown.nodes) == 10
    assert len(argdown.propositions) == 4
    assert len(argdown.arguments) == 6

def test_parse3(argdown_snippet3):
    argdown = parse_argdown(argdown_snippet3)
    print(argdown)

    assert len(argdown.arguments) == 2
    assert argdown.get_argument("Reason 1").data == {"a": 2, "b": 2, "c": 3}


def test_parse4(argdown_snippet4):
    argdown = parse_argdown(argdown_snippet4)
    print(argdown)

    assert len(argdown.nodes) == 4
    assert len(argdown.propositions) == 3
    assert len(argdown.arguments) == 1
    print(argdown.propositions)
    assert sum(ArgdownParser.is_unlabeled(prop) for prop in argdown.propositions) == 2
    assert sum(ArgdownParser.is_unlabeled(arg) for arg in argdown.arguments) == 0


def test_parse5(argdown_snippet5):
    argdown = parse_argdown(argdown_snippet5)
    print(argdown)

    assert len(argdown.arguments) == 2
    assert argdown.arguments[0].pcs
    for c in argdown.arguments[0].pcs:
        if isinstance(c, Conclusion):
            assert c.inference_data
            assert c.inference_data["uses"] == ["1"]

    assert argdown.arguments[1].pcs
    for c in argdown.arguments[1].pcs:
        if isinstance(c, Conclusion):
            assert c.inference_data
            assert c.inference_data["uses"] == [1, 2]



def test_parse6(argdown_snippet2, argdown_snippet6):
    argdown6 = parse_argdown(argdown_snippet6)
    print(argdown6)    
    argdown2 = parse_argdown(argdown_snippet2)
    print(argdown2)

    assert argdown2.nodes == argdown6.nodes


def test_unnamed_premises(argdown_snippet1):
    argdown = parse_argdown(argdown_snippet1)
    print(argdown)

    argument = next(a for a in argdown.arguments if a.pcs)

    print(argument.label.replace(" ","_"))
    print(argument.pcs)
    assert all(pr.proposition_label.startswith(argument.label.replace(" ","_")) for pr in argument.pcs)
