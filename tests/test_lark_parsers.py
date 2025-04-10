import pytest

from textwrap import dedent

from pyargdown.parser import ArgumentMapParser, ArgumentParser
from pyargdown.parser.base import ArgdownParser

@pytest.fixture
def argmapblock1():
    return dedent("""
    [A]: A
        + [B]: B
            - [C]: C
                >< [D]: D
            + [E]: E
        + [F]: F
            - [G]: G
    \t
    """)

@pytest.fixture
def argmapblock2():
    return dedent("""
    [A]: A
    \t+ [B]: B
    \t\t- [C]: C
    \t\t\t>< [D]: D
    \t\t+ [E]: E
    \t+ [F]: F
    \t\t- [G]: G
    """)

@pytest.fixture
def argmapblock3():
    return dedent("""
    [C]: Claim.
        + [Pro1]: Pro1.
        - [Con1]: Con1.
            - [Rbt1]: Rebuttal1.
    """).strip()

@pytest.fixture
def funny_arguments():
    return [
        dedent("""
        <Argument>: Argument

        (1) Premise.
        ----
        (2) Conclusion.                          
        """).strip(),
        dedent("""
        <Argument>: Argument

               
        (1) Premise.
        ----
        (2) Conclusion.                          
        """).strip(),
        dedent("""
        <Argument>: Argument 
               
        (1) Premise.
        -- Inference scheme -> Modus ponens :-) --
        (2) Conclusion.                          
        """).strip(),
        dedent("""
        <Argument>: Argument

          (1) Premise.
          ----
          (2) Conclusion.                   
        """).strip(),
        dedent("""
        <Argument>: Argument 
               
        (P1) Premise.
        (P2) Premise.
        -- {"ee": "--"} --
        (C3) Conclusion.                          
        -- {"ee": "--"} --
        (C4) Conclusion.                          
        """).strip(),
        dedent("""
        <Reason 4>
        
        (1) Premise 1.
        ----
        (3) Conclusion.
        >< [Claim B]
        """).strip(),
    ]

@pytest.fixture
def erroneous_arguments():
    return [
        # illegal conclusion label
        dedent("""
        <Argument>: Argument
               
        (1) Premise.
        ----
        (C) Conclusion.                          
        """).strip(),
        # illegal premise label
        dedent("""
        <Argument>: Argument
               
        (P) Premise.
        ----
        (2) Conclusion.                          
        """).strip(),
        # extra empty line
        dedent("""
        <Argument>: Argument
               
        (1) Premise.
               
        ----
        (2) Conclusion.                          
        """).strip(),
        # missing opening argument bracket
        dedent("""
        Argument>: Argument
               
        (1) Premise.
        ----
        (2) Conclusion.                          
        """).strip(),
        # missing closing argument bracket        
        dedent("""
        <Argument: Argument
               
        (1) Premise.
        ----
        (2) Conclusion.                          
        """).strip(),
        # missing colon after argument label
        dedent("""
        <Argument> Argument
               
        (1) Premise.
        ----
        (2) Conclusion.                          
        """).strip(),
        # missing opening premise bracket
        dedent("""
        <Argument>: Argument
               
        1) Premise.
        ----
        (2) Conclusion.                          
        """).strip(),
        # missing closing premise bracket
        dedent("""
        <Argument>: Argument
               
        (1 Premise.
        ----
        (2) Conclusion.                          
        """).strip(),
        # missing opening conclusion bracket
        dedent("""
        <Argument>: Argument
               
        (1) Premise.
        ----
        2) Conclusion.                          
        """).strip(),
        # missing closing conclusion bracket
        dedent("""
        <Argument>: Argument
               
        (1) Premise.
        ----
        (2 Conclusion.                          
        """).strip(),
        # missing colon after proposition label
        dedent("""
        <Argument>: Argument
               
        (1) [Claim] Premise.
        ----
        (2) Conclusion.                          
        """).strip(),
        # illplaced inargument dialectical relation after inference info
        dedent("""
        <Argument>: Argument
               
        (1) Premise.
        -- {"ee": "--"} --
          +> [Reason]
        (2) Conclusion.
        """).strip(),
        # illplaced inargument dialectical relation before first premise
        dedent("""
        <Argument>: Argument
               
        <+ [Reason]
        (1) Premise.
        ----
        (2) Conclusion.
        """).strip(),
        # illplaced inline yaml after inference rule
        dedent("""
        <Argument>: Argument
               
        (1) Premise.
        -- inference info -- {"ee": "--"}
        (2) Conclusion.
        """).strip(),
    ]

def test_yaml_extraction():
    fn = ArgdownParser.extract_yaml
    assert fn("text") == ("text", {})
    assert fn("text {'a': 1}") == ("text", {"a": 1})
    assert fn("text {} {'a': 1}") == ("text {}", {"a": 1})
    assert fn("text [{'a': 1}]") == ("text [{'a': 1}]", {})

def test_parseblock1(argmapblock1):
    parser = ArgumentMapParser()
    tree = parser(argmapblock1)
    print(tree.pretty())
    print(tree)

def test_equiv_1_2(argmapblock1, argmapblock2):
    parser = ArgumentMapParser()
    tree1 = parser(argmapblock1)
    tree2 = parser(argmapblock2)
    assert tree1 == tree2

def test_parseblock3(argmapblock3):
    parser = ArgumentMapParser()
    tree = parser(argmapblock3)
    print(tree.pretty())
    print(tree)

def test_arguments(funny_arguments):
    parser = ArgumentParser()
    trees = []
    for arg in funny_arguments:
        print(arg+"\n")
        tree = parser(arg)
        trees.append(tree)
        print(tree.pretty())
    assert trees[0] == trees[3]

def test_erroneous_arguments(erroneous_arguments):
    parser = ArgumentParser()
    for arg in erroneous_arguments:
        with pytest.raises(Exception):
            tree = parser(arg)
            print(arg)
            print("=======")
            print(tree.pretty())
