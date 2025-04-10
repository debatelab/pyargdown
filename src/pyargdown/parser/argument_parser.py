# TODO:
# Define the parser class
# - lark python grammer for argument-map blocks
# - lark python grammer for argument blocks
# - lark transformer for parsed argdown trees to ArgMap objects

import copy
import logging
from textwrap import dedent
import uuid

import lark
from lark import Lark, Transformer, UnexpectedInput

from pyargdown.model import (
    Argdown,
    ArgdownEdge,
    Argument,
    Conclusion,
    DialecticalType,
    Proposition,
    PropositionReference,
    Valence,
)
from pyargdown.parser.base import ArgdownParser, ArgdownSyntaxError, ReasonRelation, _UNNAMED_ARGUMENT, _UNNAMED_PROPOSITION

logger = logging.getLogger(__name__)

_UNIQUE_PLACEHOLDER = uuid.uuid4().hex

ARGDOWN_ARGUMENT_GRAMMAR = r"""
    start: _NL* (argument_head _NL _NL+)? argument_body _NL*
    argument_head: ARGUMENT_LABEL [":" TEXT]
    argument_body: premise (_NL premise | _NL conclusion | _NL reason)*
    premise: PCS_LABEL _proposition
    conclusion: (INFERENCE_LINE | INFERENCE_INFO) PCS_LABEL _proposition
    _proposition: (PROPOSITION_LABEL | PROPOSITION_LABEL ":" TEXT | TEXT)
    reason: _relation (_label | _label ":" TEXT | TEXT)
    _label: PROPOSITION_LABEL | ARGUMENT_LABEL
    _relation: LEFT_PRO | LEFT_CON | RIGHT_PRO | RIGHT_CON | CONTRADICT | LEFT_UNDERCUT | RIGHT_UNDERCUT

    ARGUMENT_LABEL: "<" /[^\>]+/ ">"
    PROPOSITION_LABEL: "[" /[^\]]+/ "]"
    PCS_LABEL: "(" /[A-Z]*\d+/ ")"
    TEXT: /([^\n]+)/
    INFERENCE_LINE: "--" /-+\n/
    INFERENCE_INFO: "--" _NL? /(.+?)/ _NL? "--\n"
    LEFT_PRO: "+ " | "<+ "
    RIGHT_PRO: "+> "
    LEFT_CON: "- " | "<- "
    RIGHT_CON: "-> "
    LEFT_UNDERCUT: "<_ "
    RIGHT_UNDERCUT: "_> "
    CONTRADICT: ">< "

    %import common.CNAME -> NAME
    %import common.ESCAPED_STRING   -> STRING
    %import common.WS_INLINE
    %ignore WS_INLINE

    _NL: /(\r?\n[\t ]*)/
"""


class ArgdownArgumentMissingEmptyLine(ArgdownSyntaxError):
    label = "Missing separating empty line"


class ArgdownArgumentMissingPremise(ArgdownSyntaxError):
    label = "Expecting argument to start with premise"


class ArgdownArgumentMissingArgumentLabelColon(ArgdownSyntaxError):
    label = "Missing colon after argument label"


class ArgdownArgumentMissingPropositionLabelColon(ArgdownSyntaxError):
    label = "Missing colon after proposition label"


class ArgdownArgumentMissingArgumentLabel(ArgdownSyntaxError):
    label = "Block does not start with argument label"


class ArgdownArgumentInvalidInferenceLine(ArgdownSyntaxError):
    label = "Invalidly formatted inference line"


class ArgdownArgumentInvalidPropositionLabel(ArgdownSyntaxError):
    label = "Invalidly formatted proposition label"


class ArgdownArgumentTooManyLinebreaks(ArgdownSyntaxError):
    label = "Invalidly formatted proposition label"


_ERROR_EXAMPLES = {
    ArgdownArgumentMissingEmptyLine: [
        dedent("""
            <Argument 1>
            (1) Premise.
            ----
            (2) Conclusion.
        """).strip(),
        dedent("""
            <Argument 1>
                (1) Premise.
                ----
                (2) Conclusion.
        """).strip(),
        dedent("""
            <Argument 1>: Argument body.
            (P1) Premise.
            ----
            (C1) Conclusion.
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

               
            ----
            (1) Conclusion.
        """).strip(),
        dedent("""
            <Argument 1>
            
            -- inference --
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
            <Argument label> Argument body.
               
            (1) Premise.
            ----
            (2) Conclusion.
        """).strip(),
        dedent("""
            <Argument label>Argument body.
               
            (1) Premise.
            ----
            (2) Conclusion.
        """).strip(),
        dedent("""
            <Argument 1>

            (1) Premise.
               + <L> Reason
            ----
            (2) Conclusion.
        """).strip(),
        dedent("""
            <Argument 1>

            (1) Premise.
            ----
            (2) Conclusion.
               + <L> Reason
        """).strip(),
        dedent("""
            <Argument 1>

            (1) Premise.
            ----
            (2) Conclusion.
            ----
            (3) Conclusion.
               + <L> Reason
        """).strip(),
    ],
    ArgdownArgumentMissingPropositionLabelColon: [
        dedent("""
            <Argument 1>
               
            (P1) [Label] Premise.
            ----
            (C1) Conclusion.
        """).strip(),
        dedent("""
            <Argument 1>
               
            (P1) Premise.
            ----
            (C1) [Label] Conclusion.
        """).strip(),
        dedent("""
            <Argument 1>
               
            (P1) Premise.
            (P2) [Label] Premise.
            ----
            (C1) Conclusion.
        """).strip(),
        dedent("""
            <Argument 1>
               
            (P1) Premise.
            (P2) [Label]: Premise.
            ----
            (C1) Conclusion.
            ----
            (C1) [Label] Conclusion.
        """).strip(),
        dedent("""
            <Argument 1>

            (1) Premise.
               + [PL] Reason
            ----
            (2) Conclusion.
        """).strip(),
        dedent("""
            <Argument 1>

            (1) Premise.
            ----
            (2) Conclusion.
               + [PL] Reason
        """).strip(),
        dedent("""
            <Argument 1>

            (1) Premise.
            ----
            (2) Conclusion.
            ----
            (3) Conclusion.
               + [PL] Reason
        """).strip(),
    ],
    ArgdownArgumentMissingArgumentLabel: [
        dedent("""
            Argument 1
            
            (1) Premise.
            ----
            (2) Conclusion.
        """).strip(),
        dedent("""
            Argument 1

                (1) Premise.
                ----
                (2) Conclusion.
        """).strip(),
        dedent("""
            [Argument 1]: Argument body.
            
            (P1) Premise.
            ----
            (C1) Conclusion.
        """).strip(),
    ],
    ArgdownArgumentInvalidInferenceLine: [
        dedent("""
            <Argument 1>
            
            (1) Premise.
            -- inference -- 
            (2) Conclusion.
        """).strip(),
        dedent("""
            <Argument 1>
            
            (1) Premise.
            –– inference ––
            (2) Conclusion.
        """).strip(),
        dedent("""
            <Argument 1>
            
            (1) Premise.
            ---- 
            (2) Conclusion.
        """).strip(),
        dedent("""
            <Argument 1>
            
            (1) Premise.
            ----- 
            (2) Conclusion.
        """).strip(),
        dedent("""
            <Argument 1>
            
            (1) Premise.
            (2) Premise.
            --
            (3) Conclusion.
        """).strip(),
    ],
    ArgdownArgumentInvalidPropositionLabel: [
        dedent("""
            <Argument 1>
            
            P1 Premise.
            ----
            C2 Conclusion.
        """).strip(),
        dedent("""
            <Argument 1>
            
            (P1) Premise.
            ----
            C2 Conclusion.
        """).strip(),
        dedent("""
            <Argument 1>
            
            (P1) Premise.
            -- with magic --
            C2 Conclusion.
        """).strip(),
        dedent("""
            <Argument 1>: Gist.
            
            1 Premise.
            ----
            2 Conclusion.
        """).strip(),
        dedent("""
            <Argument 1>
            
            (1) Premise.
            (2) Premise.
            ----
            C Conclusion.
        """).strip(),
        dedent("""
            <Argument 1>
            
            (1) Premise.
            (2) Premise.
            -- with magic --
            C Conclusion.
        """).strip(),
        dedent("""
            <Argument 1>
            
            Premise.
            ----
            Conclusion.
        """).strip(),
        dedent("""
            <Argument 1>
            
            (1) Premise.
            ----
            (2) Conclusion.
            (3) Premise.
            ----
            (4 ) Conclusion
        """).strip(),
        dedent("""
            <Argument 1>
            
            (1) Premise.
            ----
            (2) Conclusion.
            (3) Premise.
            -- with magic --
            (4 ) Conclusion
        """).strip(),
        dedent("""
            <Argument 1>
            
            [1] Premise.
            ----
            [2] Conclusion.
        """).strip(),
        dedent("""
            <Argument 1>
            
            (Premise1) Premise.
            ----
            (Conclusion1) Conclusion.
        """).strip(),
        dedent("""
            <Argument 1>
            
            1) Premise.
            ----
            2) Conclusion.
        """).strip(),
        dedent("""
            <Argument 1>
            
            (P1) Premise.
            ----
            (C) Conclusion.
        """).strip(),
    ],
    ArgdownArgumentTooManyLinebreaks: [
        dedent("""
            <Argument 1>
            
            (1) Premise.
               
            ----
            (2) Conclusion.
        """).strip(),
        dedent("""
            <Argument 1>
            
            (1) Premise.
            ----

            (2) Conclusion.
        """).strip(),
        dedent("""
            <Argument 1>
            
            (1) Premise.
               
            (2) Premise.
            ----
            (3) Conclusion.
        """).strip(),
    ],
}


class ArgumentTreeTransformer(Transformer):

    def __init__(self, argdown: Argdown, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.argdown = argdown
        self.current_argument_label = None  # Add this to track current argument

    @lark.v_args(inline=True)
    def start(self, *args):
        if len(args) == 1:
            head, pcs = None, args[0]
        elif len(args) == 2:
            head, pcs = args
        else:
            raise ValueError(
                "Internal error: Argument block must have at most 2 children (head / body). Please report this issue."
            )
        if head is None:
            label = self.argdown.make_label_unique(_UNNAMED_ARGUMENT)
            gists = []
            data = {}
        else:
            label = head["label"]
            gists = [head["text"]] if head["text"] else []
            data = head["data"]

        argument = Argument(
            label=label, gists=gists, data=data, pcs=pcs
        )
        self.argdown.add_argument(argument, allow_exists=True)
        return argument

    @lark.v_args(inline=True)
    def argument_head(self, label, *args):
        kwargs = {t.type: t.value for t in args}
        text = kwargs.get("TEXT")
        text, yaml = ArgdownParser.extract_yaml(text) if text else ("", {})
        text = text.strip()
        self.current_argument_label = label[1:-1]
        return {"label": label[1:-1], "text": text, "data": yaml}

    @lark.v_args(inline=True)
    def argument_body(self, *args):
        pcs: list[PropositionReference] = []
        for item in args:
            if isinstance(item, PropositionReference) or isinstance(item, Conclusion):
                pcs.append(item)
            elif isinstance(item, ArgdownEdge):
                assert pcs, (
                    "Internal error: Embedded reason must be preceeded by premise or conclusion. Please report this issue."
                )
                if item.source == _UNIQUE_PLACEHOLDER:
                    item.source = pcs[-1].proposition_label
                elif item.target == _UNIQUE_PLACEHOLDER:
                    item.target = pcs[-1].proposition_label
                else:
                    raise ValueError(
                        "Internal error: Invalid references in embedded reason node. Please report this issue."
                    )
                self.argdown.add_dialectical_relation(item)
            else:
                raise ValueError(
                    "Unrecognized item in argument body. Please report this issue."
                )
        return pcs

    @lark.v_args(inline=True)
    def premise(self, *args):
        kwargs = {t.type: t.value for t in args}
        label = kwargs["PCS_LABEL"][1:-1]
        prop_label = kwargs.get("PROPOSITION_LABEL")
        prop_label = prop_label[1:-1] if prop_label else None
        if prop_label is None:
            prop_label = f"UNNAMED_PREMISE_{label}"
            cr_arg_lb = self.current_argument_label
            cr_arg_lb = cr_arg_lb.replace(" ", "_") if cr_arg_lb is not None else None
            prop_label = prop_label if cr_arg_lb is None else f"{cr_arg_lb}_{prop_label}"
            prop_label = self.argdown.make_label_unique(prop_label)
        text = kwargs.get("TEXT")
        text, yaml = ArgdownParser.extract_yaml(text) if text else (None, {})
        proposition = Proposition(
            label=prop_label, texts=[text] if text else [], data=yaml
        )
        if self.argdown.get_proposition(prop_label) is None:
            self.argdown.add_proposition(proposition, allow_exists=False)
        else:
            self.argdown.update_proposition(prop_label, proposition)
                
        return PropositionReference(proposition_label=prop_label, label=label)

    @lark.v_args(inline=True)
    def conclusion(self, *args):
        kwargs = {t.type: t.value for t in args}
        label = kwargs["PCS_LABEL"][1:-1]
        prop_label = kwargs.get("PROPOSITION_LABEL")
        prop_label = prop_label[1:-1] if prop_label else None
        if prop_label is None:
            prop_label = f"UNNAMED_CONCLUSION_{label}"
            cr_arg_lb = self.current_argument_label
            cr_arg_lb = cr_arg_lb.replace(" ", "_") if cr_arg_lb is not None else None
            prop_label = prop_label if cr_arg_lb is None else f"{cr_arg_lb}_{prop_label}"
            prop_label = self.argdown.make_label_unique(prop_label)
        inference_info = kwargs.get("INFERENCE_INFO")
        inference_info = (
            inference_info.strip("\n ")[2:-2].strip() if inference_info else None
        )
        inference_info, inference_data = (
            ArgdownParser.extract_yaml(inference_info) if inference_info else (None, {})
        )
        text = kwargs.get("TEXT")
        text, yaml = ArgdownParser.extract_yaml(text) if text else (None, {})
        proposition = Proposition(
            label=prop_label, texts=[text] if text else [], data=yaml
        )
        if self.argdown.get_proposition(prop_label) is None:
            self.argdown.add_proposition(proposition, allow_exists=False)
        else:
            self.argdown.update_proposition(prop_label, proposition)
        return Conclusion(
            proposition_label=prop_label,
            label=label,
            inference_info=inference_info,
            inference_data=inference_data,
        )

    @lark.v_args(inline=True)
    def reason(self, *args):
        kwargs = {t.type: t.value for t in args}
        text = kwargs.get("TEXT")
        text, yaml = ArgdownParser.extract_yaml(text) if text else ("", {})
        text = text.strip()
        rel = next(rel for rel in ReasonRelation if rel.value in kwargs.keys())

        is_proposition = "ARGUMENT_LABEL" not in kwargs

        # update proposition or argument
        if is_proposition:
            label = kwargs.get("PROPOSITION_LABEL")
            label = label[1:-1] if label else None
            if label is None:
                label = self.argdown.make_label_unique(_UNNAMED_PROPOSITION)
            self.argdown.add_proposition(
                Proposition(label=label, texts=[text] if text else [], data=yaml),
                allow_exists=True,
            )
        else:
            label = kwargs.get("ARGUMENT_LABEL")
            label = label[1:-1] if label else None
            if label is None:
                label = self.argdown.make_label_unique(_UNNAMED_ARGUMENT)
            self.argdown.add_argument(
                Argument(label=label, gists=[text] if text else [], data=yaml),
                allow_exists=True,
            )

        if rel in [
            ReasonRelation.LEFT_PRO,
            ReasonRelation.LEFT_CON,
            ReasonRelation.LEFT_UNDERCUT,
            ReasonRelation.CONTRADICT,
        ]:
            source = label
            target = _UNIQUE_PLACEHOLDER
        else:
            source = _UNIQUE_PLACEHOLDER
            target = label

        if rel in [ReasonRelation.LEFT_PRO, ReasonRelation.RIGHT_PRO]:
            valence = Valence.SUPPORT
        elif rel in [
            ReasonRelation.LEFT_CON,
            ReasonRelation.RIGHT_CON,
        ]:
            valence = Valence.ATTACK
        elif rel in [
            ReasonRelation.LEFT_UNDERCUT,
            ReasonRelation.RIGHT_UNDERCUT,
        ]:
            valence = Valence.UNDERCUT
        elif rel == ReasonRelation.CONTRADICT:
            valence = Valence.CONTRADICT
        else:
            raise ValueError(
                f"Internal error: Unknown reason relation in {kwargs}. Please report this issue."
            )
        dialectic = (
            DialecticalType.AXIOMATIC
            if "PROPOSITION_LABEL" in kwargs
            else DialecticalType.SKETCHED
        )
        return ArgdownEdge(
            source=source,
            target=target,
            valence=valence,
            dialectics=[dialectic],
        )


class ArgumentParser(ArgdownParser):
    def __init__(self):
        self.parser = Lark(
            ARGDOWN_ARGUMENT_GRAMMAR, parser="lalr", maybe_placeholders=False
        )

    def parse(self, text: str) -> lark.Tree:
        try:
            text = text.strip()
            tree = self.parser.parse(text)
        except UnexpectedInput as u:
            exc_class = u.match_examples(
                self.parser.parse, _ERROR_EXAMPLES, use_accepts=True
            )
            if not exc_class:
                raise
            raise exc_class(u.get_context(text), u.line, u.column)
        return tree

    @staticmethod
    def ingest_in_argmap(tree: lark.Tree, argdown: Argdown) -> Argdown:
        working_argdown = copy.deepcopy(argdown)
        try:
            ArgumentTreeTransformer(
                argdown=working_argdown, visit_tokens=True
            ).transform(tree)
        except Exception as e:
            logger.error(f"Error when ingesting argdown argument: {e}. Returning original argdown document.")
            return argdown
        working_argdown._update()
        return working_argdown
