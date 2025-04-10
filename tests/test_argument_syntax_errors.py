
import pytest

from textwrap import dedent

from lark.indenter import DedentError

from pyargdown.parser import ArgumentParser
from pyargdown.parser.argument_parser import (
    ArgdownArgumentMissingArgumentLabel,
    ArgdownArgumentMissingEmptyLine,
    ArgdownArgumentMissingPremise,
    ArgdownArgumentMissingArgumentLabelColon,
    ArgdownArgumentMissingPropositionLabelColon,
    ArgdownArgumentInvalidInferenceLine,
    ArgdownArgumentInvalidPropositionLabel,
    ArgdownArgumentTooManyLinebreaks,
)

from pyargdown.parser import ArgumentMapParser
from pyargdown.parser.argument_map_parser import (
    ArgdownMapUnknownRelation,
    ArgdownArgumentMapMissingArgumentLabelColon,
    ArgdownArgumentMapMissingPropositionLabelColon,
)

@pytest.fixture
def erroneous_argdown_texts():
    return {
        ArgdownArgumentMissingArgumentLabel: [
            dedent("""
                The gist of this arguemnt is blah.
                
                (1) First Premise.
                (2) Second Premise.
                ----
                (3) Conclusion.
            """).strip(),
            dedent("""
                [Prop-Label]: The gist of this arguemnt is blah.
                
                    (1) First Premise.
                    (2) Second Premise.
                    ----
                    (3) Conclusion.
            """).strip(),
        ],
        ArgdownArgumentMissingEmptyLine: [
            dedent("""
                <Splendid Argument>
                (1) Premise.
                ----
                (2) Conclusion.
            """).strip(),
            dedent("""
                <Argument 1>: Gist.
                    (1) Premise.
                    (2) Premise.
                    ----
                    (3) Conclusion.
            """).strip(),
        ],
        ArgdownArgumentMissingPremise: [
            dedent("""
                <Argument 1>
                
                ----
                (1) Conclusion.
            """).strip(),
            dedent("""
                <Argument 1>

                            
                -- inference --
                (1) Conclusion.
            """).strip(),
        ],
        ArgdownArgumentMissingArgumentLabelColon: [
            dedent("""
                <Label> Argument body.
                
                (1) Premise.
                ----
                (2) Conclusion.
            """).strip(),
            dedent("""
                <Labelius-Label>Bodily body.
                
                (1) Premise.
                ----
                (2) Conclusion.
            """).strip(),
            dedent("""
                <Labelius-Label>
                
                (1) Premise.
                (2) Premise.
                   +> <Reason> Reason.
                ----
                (3) Conclusion.
            """).strip(),
        ],
        ArgdownArgumentMissingPropositionLabelColon: [
            dedent("""
                <Argument 1>: Supper nice.
                
                (1) Premise.
                ----
                (2) Conclusion.
                -- mp --
                (3) [Label] Conclusion.
            """).strip(),
            dedent("""
                <Argument 1>: Supper nice.
                
                (1) Premise.
                   -> [Label2] Reason.
                -- mp --
                (3) [Label]: Conclusion.
            """).strip(),
            dedent("""
                <Argument 1>: Supper nice.
                
                (1) Premise.
                -- mp --
                (2) [Label]: Conclusion.
                -- mp --
                (3) [Label]: Conclusion.
                   <_ [Label2] Reason.
            """).strip(),
        ],
        ArgdownArgumentInvalidInferenceLine: [
            dedent("""
                <Argument 1>
                
                (P1) Premise.
                -- inference info -- 
                (C2) Conclusion.
            """).strip(),
            dedent("""
                <Argument 1>
                
                (P1) Premise.
                –– inference {"a": "--"} ––
                (P2) Conclusion.
            """).strip(),
            dedent("""
                <Argument 1>
                
                (1) Premise.
                (2) Premise.
                -------- 
                (3) Conclusion.
            """).strip(),
        ],
        ArgdownArgumentInvalidPropositionLabel: [
            dedent("""
                <Argument 1>
                
                (1) Premise.
                ----
                [2] Conclusion.
            """).strip(),
            dedent("""
                <Argument 1>
                
                1 Premise.
                ----
                2 Conclusion.
            """).strip(),
        ],
        ArgdownArgumentTooManyLinebreaks: [
            dedent("""
                <Argument 1>
                
                (1) Premise.
                
                (2) Premise.
                (3) Premise.
                ----
                (4) Conclusion.
            """).strip(),
            dedent("""
                <Argument 1>
                
                (1) Premise.
                ----
                
                (2) Conclusion.
            """).strip(),
        ],
    }

@pytest.fixture
def erroneous_argdownmap_texts():
    return {
        DedentError: [
            dedent("""
            [root]: root text
              - reason
             - reason
            """),
            dedent("""
            [root]: root text
              + reason
                - reason
               - reason
            """),
            dedent("""
            [root]: root text
              + reason
                + reason
                  - reason
                 - reason
            """),
        ],
        ArgdownMapUnknownRelation: [
            dedent("""
                [root]: root text
                    < [child]: child text
            """).strip(),
            dedent("""
                [root]: root text
                    + reason
                    > [child]: child text
            """).strip(),
            dedent("""
                [root]: root text
                    <~ [child]: child text
            """).strip(),
            dedent("""
                [root]: root text
                    ~> [child]: child text
            """).strip(),
            dedent("""
                [root]: root text
                    <– [child]: child text
            """).strip(),
            dedent("""
                [root]: root text
                    –> [child]: child text
            """).strip(),
            dedent("""
                [root]: root text
                    <? [child]: child text
            """).strip(),
            dedent("""
                [root]: root text
                    ?> [child]: child text
            """).strip(),
            dedent("""
                [root]: root text
                    ~ [child]: child text
            """).strip(),
            dedent("""
                [root]: root text
                    = [child]: child text
            """).strip(),
        ],
        ArgdownArgumentMapMissingArgumentLabelColon: [
            dedent("""
                [root]: root text
                    + reason
                        -> <child> child text
            """).strip(),
            dedent("""
                [root]: root text
                        -> <child> child text
            """).strip(),
            dedent("""
                [root]: root text
                    + reason
                        + reason
                    -> <child> child text
            """).strip(),
        ],
        ArgdownArgumentMapMissingPropositionLabelColon: [
            dedent("""
                [root]: root text
                    + reason
                        -> [child] child text
            """).strip(),
            dedent("""
                [root]: root text
                    + reason
                        -> [child] child text
            """).strip(),
            dedent("""
                [root]: root text
                    + reason
                        + reason
                        + reason
                    -> [child] child text
            """).strip(),
        ],
    }

def test_syntax_errros(erroneous_argdown_texts):
    for errorclass, argdown_texts in erroneous_argdown_texts.items():
        print(f"\n +++++ {errorclass} +++++")
        for ad in argdown_texts:
            print("\n======")
            print(ad)
            with pytest.raises(errorclass):
                ArgumentParser().parse(ad)


def test_syntax_errors_map(erroneous_argdownmap_texts):
    for errorclass, argdown_texts in erroneous_argdownmap_texts.items():
        print(f"\n +++++ {errorclass} +++++")
        for ad in argdown_texts:
            print("\n======")
            print(ad)
            with pytest.raises(errorclass):
                ArgumentMapParser().parse(ad)
